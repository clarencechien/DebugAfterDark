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
- `player.html`：播放器，三種風格。沒有第三方 script、沒有 storage API（照 imitator `style/STYLE.md`），字型用系統的 Noto CJK。
  - `slide`：現行 make_video.py 的版面搬到網頁。**留給 Shorts 用**（使用者 11/27），長片不用。
  - `paper`：資料新聞風，**深色**（深夜的調性；使用者 11/27 確認可以）。
  - 兩種開場都先放**開機封面**：開機訊息（掛載這集的報告、載入幾個 finding 和章節、啟動 ping@debugafterdark），
    接著打出 EP 編號和這集的標題。標題打完後至少停留到能慢慢念完的時間（每秒 4.5 字，最少 4 秒；
    EP36 的 23 字標題停約 5 秒，封面總長約 6.8 秒）。封面疊在 cold open 的聲音上，不加長影片，字幕照常顯示。
  - `opening`（**A 版**）：**建議的長片組合**（使用者 11/27）。cold open 用 trace 畫面，之後整集接 `paper`。整集都是終端機會太多，
    所以 debug 感只放在開場。trace 畫面是可觀測性工具的樣子：終端機的使用者是 `ping`（節目主持人），跑
    `trace tail --episode <ep> --follow`，cold open 的每張卡片變成一個 span（瀑布圖跟著旁白長出來），下方是結構化 log
    （INFO／WARN／ERROR）。報告自己提出的第一個論點標成 ERROR 和「root cause?」，就是這集要追的問題。
    span 名稱、數值、出處都是卡片本身的內容；trace id 由集數算出來，固定不變。
  - `opening-b`（**B 版**）：同一個開機封面，cold open 直接用深色 paper 的大數字卡，整集都是 paper。跟 A 只差 cold open 那約 40 秒。
  - `terminal`：有 debug 代入感的終端機。每張數字卡變成一道指令（提示字元是 `ping@debugafterdark`）：前後對比的數字用 SQL 查詢，結果是表格加長條；
    單一數字用 SQL 回傳一列；其他用 `trace grep`、`trace plot`，結果是 TUI 方框。指令會先打字、
    「查詢中」一下再出結果，結果剛好落在旁白講到那句的時候。底部是 tmux 式的狀態列（集數、章節、進度、出處），換章就清畫面。
    **介於真實與 mock 之間**：指令、資料表名、`trace` 這個工具是佈景；畫面上的每個數字、說明和出處都是那張卡片本身的內容，
    不另外編。CJK 等寬字型的框線字是全形，對不齊，所以方框和表格用 CSS 邊框畫。
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

11/27 第二版（terminal 改成 SQL／CLI，paper 改深色）：paper 每分鐘 21 秒，terminal 每分鐘 28 到 29 秒。
第三版 `opening`（前 60 秒，其中 43 秒是 trace，瀑布圖一直在長）：每分鐘 38 秒。

照這個速度，9 分鐘的 EP36 整集約 3.5 到 8 分鐘，跟現行 make_video.py（約 9 分鐘）差不多或更快。
樣片和截圖在專案資料夾 `video/web-video-options/ep36-sample/`（第二版在 `v2/`，opening 在 `v3/`），只在本機產出，沒有上傳。

原型還沒做的：數字卡和字幕的驗收（目前直接沿用 make_video.py 的檢查結果）、slide 的 Shorts 直式版面、
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
3. 主風格。11/27 使用者的方向：長片用 `opening`（trace 開場 + 深色 paper），slide 只做 Shorts。

## 開場 A/B 實驗（提案，還沒開始）

問題：cold open 用 trace 畫面（A）還是直接用大數字卡（B），觀眾比較會留下來？
A 和 B 只差 cold open 那約 40 秒，開機封面、標題、縮圖版型、後面的 paper 都一樣，所以差別可以算在開場上。

- **怎麼分組**：YouTube 的「測試與比較」只能換標題和縮圖，不能換影片內容，所以用集數輪流。
  **在類型裡面輪流**（使用者 11/27 想按類型分）：AI 題照 ABBA BAAB 排，錢的題目也照 ABBA 排，兩邊各自輪。
  如果直接「AI 全用 A、錢全用 B」，開場和題目綁在一起，看到差別也分不出是開場還是題目造成的（錢題的數字本來就不同，
  見 `topic-mix` 的 11/21 數據），所以那樣只能當參考。分層輪流的話，兩件事都看得到：整體哪個開場好，以及 AI 和錢是不是各自適合不同開場。
  看完後如果真的是「AI 適合 A、錢適合 B」，再改成按類型固定。同一個上架時段、都不下廣告。
  錢的題目比較少（五天一個錢日、兩集），湊滿錢的 4 集大約要兩輪錢日（10 天）；AI 的 8 集大約 5 天。
- **看什麼**：只看自然流量（排除廣告），每集第 7 天的數字。
  - 主要：**30 秒留存**（開場剛結束的時候還剩幾成人）。
  - 次要：1 分鐘留存、平均觀看百分比。
  - 點閱率不看：觀眾點進來之前看不到開場，點閱率差異只會來自題目。
- **怎麼判斷**（事先定好，免得看到數字再改標準）：A 的 30 秒留存中位數比 B 高 5 個百分點以上，而且 AI 的 4 組裡至少 3 組
  方向一樣，就用 A；錢的部分組數少，只當參考；B 比 A 高同樣幅度就用 B；其他情況算平手，用 B（錄製快一半，畫面也比較單純）。
- **什麼時候跑**：等三件事都結束才開始：今天 17:00 EP36 影片版第 7 天的結果、決定要不要做影片版、上架時間實驗
  （到 12/4，12/10 檢討）。最早 12/11 起；AI 的部分約 5 天排完，錢的部分約 10 天。
- **不能用的集數**：正在其他實驗裡的集數（EP01–23、EP07、EP28–39，見 `strategy.md`）。

樣片（EP36 前 60 秒，只在本機）：專案資料夾 `video/web-video-options/ep36-sample/ab/` 的 `A-0-60.mp4`、`B-0-60.mp4`。
