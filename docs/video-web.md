# 影片版 v3 候選：做一頁網頁，再逐格錄成影片（草稿）

狀態：**草稿，還沒決定要做**。2026-11-27 開，等 EP36 影片版第 7 天的數字（11/27 17:00）出來再細調，
之後可能另開一個 A/B 測試。實驗隔離照舊：在使用者決定之前，不上傳任何新的影片版，也不碰實驗中的集數。

現行的影片做法見 [`video.md`](video.md)（`tools/make_video.py`），這份只寫另一條路，跟它的差別。
比較頁（六種畫面風格示意、成本表）：<https://claude.ai/artifact/XmMBuTwUxBknyUrdPBtb6Q>。

## 這條路是什麼

AI SDLC 課程 A1 的 demo 重播（專案資料夾 `ai-sdlc-course/a1-runs/replay-src/`）用了這個做法：

1. 一頁 HTML 提供 `seek(t)`：給一個秒數，就把畫面畫成那一刻的樣子。畫面只由資料和 `t` 決定，沒有計時器。
2. Playwright 打開這頁，逐格呼叫 `seek(i / fps)` 再截圖，PNG 直接餵給 ffmpeg，接上 mp3 成為 mp4。

它不是錄螢幕：同一份資料每次輸出一樣的影片，要改字只要改資料再重算。

跟現行的 `make_video.py`（Pillow 畫卡片、ffmpeg 合成）比：

| | make_video.py（現行） | 網頁錄製 |
|---|---|---|
| 換風格 | 改 Python 畫圖的程式 | 換一份 CSS |
| 報告的圖表 | 從報告截圖，整張出現 | 可以重畫成 SVG，跟著旁白逐條出現、標重點 |
| 動態 | 淡入、推近、進度條（ffmpeg 濾鏡） | 網頁能做的都能做，仍然可以只用低調的動態 |
| Shorts | `make_short.py` 另外一套 | 同一份資料換直式版面 |
| 時間、字幕、驗收 | 已經做好 | 先沿用 make_video.py 的產出 |

## 原型（這個 PR）

`tools/webvideo/`，沿用 make_video.py 已經算好的時間，所以不用重新對時：

- `build_timeline.py episodes/<ep>`：讀 `video/<ep>.srt`（字幕）、`video/render_log.json`（卡片時間、章節、段落起點）、
  `video/visuals.json`（卡片文字、每段背景），寫成一份 `timeline.json`。
- `player.html`：播放器，三種風格 `slide`（現行版面搬到網頁）、`paper`（資料新聞風）、`terminal`（終端機，跟 A1 重播同一套）。
  沒有第三方 script、沒有 storage API（照 imitator `style/STYLE.md`），字型用系統的 Noto CJK。
- `render.js timeline.json out.mp4 --theme paper --from 0 --to 30`：逐格錄製。`seek()` 回傳一個 key，
  key 沒變的格子直接重用上一張截圖，所以畫面靜止的時候幾乎不花時間。`--still 15.5 x.png` 只出一張預覽。

```bash
apt-get install -y fonts-noto-cjk fonts-noto-cjk-extra    # 雲端容器要先裝
python3 tools/webvideo/build_timeline.py episodes/ep36-credit-line -o /tmp/tl.json
node tools/webvideo/render.js /tmp/tl.json /tmp/paper.mp4 --theme paper --from 0 --to 30
```

### 2026-11-27 實測（EP36 前 30 秒，4 核雲端容器）

| 風格 | 30 秒裡真的截圖的格數（共 900 格） | 花的時間 | 換算每分鐘影片 |
|---|---|---|---|
| slide（背景一直慢慢推近） | 133 | 26.5 秒 | 53 秒 |
| paper | 93 | 11.4 秒 | 23 秒 |
| terminal（有打字效果） | 173 | 12.6 秒 | 25 秒 |

照這個速度，9 分鐘的 EP36 整集約 3.5 到 8 分鐘，跟現行 make_video.py（約 9 分鐘）差不多或更快。
樣片和截圖在專案資料夾 `video/web-video-options/ep36-sample/`，只在本機產出，沒有上傳。

原型還沒做的：數字卡和字幕的驗收（目前直接沿用 make_video.py 的檢查結果）、Shorts 直式版面、
資料新聞風的「圖表重畫成 SVG」（目前只放報告截圖）、報告導讀風格。

## 如果要做，接進流程的方式

```
imitator 報告 HTML ─┐
script.json、mp3 ───┼─> 分鏡（新）：scenes.json ─> player.html + 風格 CSS ─> render.js ─> 驗收 ─> 使用者看 ─> 9c、9d（不變）
每句的時間 ─────────┘
```

- **分鏡**：先沿用 `visuals.json`（已經有 anchor、數字卡、出處）。之後要做圖表重畫時，再讓模型從報告抽出圖表資料寫進 scenes，
  數字一律跟報告或 `script.json` 比對，比不到就不出現（跟現在 `numbers_not_in_script` 的檢查一樣）。
- **風格**：同一份 scenes 可以換 CSS，也可以混用（例如平常資料新聞風，AI 題的段落插終端機）。
- 9b 確認、9c commit、9d 上傳都不變。mp4 一樣放 Release、比對 sha256。

## 等數字出來要決定的事

1. EP36 影片版第 7 天跟 EP28–EP39（RSS 版）比，自然流量有沒有比較好。沒有的話，先查是畫面還是包裝的問題，再決定要不要換畫面風格。
2. 要不要做風格的 A/B：同一集只能上一支影片，所以比較的方式是「連續幾集輪流用不同風格」，每集看第 7 天的點閱率、30 秒和 1 分鐘留存，只看自然流量。
   上架時間實驗（到 12/4，檢討 12/10）還在跑，風格測試要排在它之後，或至少不要跟它用同一批集數。
3. 主風格。比較頁的建議是：主體資料新聞，每天保底用報告導讀，AI 題插終端機，油畫只用在開頭。
