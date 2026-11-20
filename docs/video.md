# 影片版：第 9 步（handoff v2）

給要做影片版的 agent：照這份把一集做成 YouTube 長片和 Shorts，經使用者確認後 commit，再由 GitHub Action 上傳。
先讀 [`docs/recipe.md`](recipe.md)（第 0 到 8 步）和 [`docs/hooks.md`](hooks.md)「YouTube：標題、縮圖、說明欄」。

v1 是 2026-11-16 的 handoff（只做 EP07、手動上傳）。v2（2026-11-20）根據對 repo 的核對、YouTube 工作室數據，
以及參考 @foxh 的做法改寫。這份只寫流程與規格，程式還沒寫。

## 為什麼要做，先做什麼

YouTube 工作室 2026-11-04 到 11-18 的數據（全頻道）：

| 指標 | 數字 | 意思 |
|---|---|---|
| 曝光 | 21,736，93% 來自推薦影片 | YouTube 有在推 |
| 點閱率 | 0.71%（推薦影片 0.54%） | **最大的瓶頸**：看到的人幾乎不點 |
| 觀看 | 746，45% 來自廣告 | 比較時要排除廣告 |
| 留存（EP07） | 前約 30 秒掉到三成，之後幾乎持平 | 第二個瓶頸：開頭 |

所以順序是：

1. **包裝**（標題、縮圖、說明欄）：已寫進 `hooks.md`，EP38 起 `episode.json` 有 `youtube` 欄位；EP07 正在跑標題與縮圖的 A/B 測試。
2. **影片版**（這份）：處理開頭 30 秒的流失。
3. **Shorts**：用每集的 cold open，從庫存每天排一支。

## 先修的兩個 bug（做影片之前）

母帶的順序是：片頭音效 3.2 秒 → 0.4 秒空白 → s00（cold open）→ 0.6 秒 → **固定開場**（`show/ident/ident.flac`，9.12 秒）→ 0.6 秒 → 其餘各段，段間 0.6 秒 → 0.4 秒 → 片尾音效 3.2 秒（`tools/make_podcast.py` 的 `cmd_master`）。

- `tools/consistency_check.py` 的 `start` 和 `tools/stt_check.py` 的 `episode_time` 都從 3.6 秒開始累加，**漏掉了固定開場**，所以 s00 之後的時間都早了約 9.7 秒。
  EP39 實測（mp3 的 silencedetect）：s00 結束在 48.4 秒，固定開場在約 49.8 到 58.1 秒，s01 實際從約 59.2 秒開始，`consistency.json` 卻寫 0:49。
- `recipe.md` 第 1 步要說明欄的章節時間取 `qa/consistency.json` 的 `start`，所以 **EP38、EP39 說明欄的章節時間都偏早**，上架前要重算。

修法：兩個工具在第一段之後加上「固定開場長度 + 0.6 秒」（長度從 `ident.flac` 讀，不要寫死），再用 mp3 的靜音段驗證每個交界誤差 ≤ 0.15 秒。

## 流程

跟 podcast 一樣：Claude 在同一個互動 session 裡產出，使用者確認，commit，之後交給 GitHub。

| 步驟 | 誰 | 做什麼 | 產出 |
|---|---|---|---|
| 9a 產出 | 同一個 session，接在第 8 步後面 | `tools/make_video.py <ep>` | `episodes/<ep>/video/` 的所有檔案、Release 上的 mp4 |
| 9b 確認 | 使用者 | 看 6 張預覽截圖、2 張縮圖、Shorts 的頭尾截圖、YouTube 標題、章節 | 要改就改 `visuals.json` 或 `episode.json` 的 `youtube`，重跑 9a（不重新擷取圖表） |
| 9c commit | 同一個 session | 只 commit 文字檔（下表），mp4 上傳到 Release | PR 或直接 commit |
| 9d 發佈 | GitHub Action | 用 YouTube Data API 上傳、排程公開 | 影片 id 寫回 `youtube/uploads.json` |

### 9a 的產出

| 檔案 | 進 git | 內容 |
|---|---|---|
| `video/<ep>.mp4` | 否，上傳到 Release `video-<ep>` | 1920×1080 長片 |
| `video/<ep>-short.mp4` | 否，同一個 Release | 1080×1920 Shorts |
| `video/<ep>.srt` | 是 | 長片字幕（繁中） |
| `video/<ep>-short.srt` | 是 | Shorts 字幕 |
| `video/chapters.txt` | 是 | 影片版的章節（跟 mp3 版差 3.6 秒，見下文） |
| `video/thumbnail-a.png`、`-b.png` | 是（約 1 MB 以內） | 1280×720，`youtube.thumbnail` 的兩組字 |
| `video/visuals.json` | 是 | 每段的圖、數字卡、出處標註，可以手改 |
| `video/render_log.json` | 是 | 各段起訖、驗收結果、mp4 的 sha256 |
| `video/preview/*.jpg` | 否 | 給 9b 看的截圖 |

mp4 放 Release，不在 Action 裡重新產生：重新產生要 Playwright、字型和 imitator repo 的報告 HTML，而且產出不一定 byte-for-byte 一樣。
放 Release 的話，上傳的就是使用者看過的那一份；Action 下載後先比對 `render_log.json` 裡的 sha256，不一致就不上傳。

### `episode.json` 的 `youtube` 欄位

EP38 起已經有 `title`、`thumbnail`、`synthetic_content`（`recipe.md` 第 1 步）。影片版再加：

```json
"youtube": {
  "title": "…",
  "thumbnail": [["白字主題", "紅底結論"], ["…", "…"]],
  "synthetic_content": true,
  "publish_at": "2026-11-27T21:00:00+08:00",
  "short": {"title": "…", "publish_at": "2026-11-28T12:00:00+08:00"},
  "playlist": "podcast"
}
```

- 說明欄直接用 `episode.json` 的 `description`（已經照 `hooks.md` 的順序），只把章節換成 `video/chapters.txt`。
- 沒有 `publish_at` 的集數，Action 不處理：這是開關。
- 影片 id 不寫回 `episode.json`，寫在 `youtube/uploads.json`（`{"<ep>": {"video": "…", "short": "…"}}`）。Action 用它判斷是否已經上傳過，避免重傳。

## 9a 的做法

### 時間

- 段落起點：照上面的母帶順序算，固定開場的長度從 `ident.flac` 讀；再用 mp3 的 silencedetect 驗證，每個交界誤差 ≤ 0.15 秒，對不上就停下來，不要硬套。
- `levels.json` 只有響度沒有長度，正規化後的段落 wav 在 `out/`（不進 git），所以長度要從 mp3 量，或在第 6 步把各段長度寫進 `qa/levels.json`（建議順手加上）。
- 已實作（`tools/make_video.py`，2026-11-20，EP36 第一集）：雲端沒有 `out/` 的段落 wav，所以固定開場用 `ident.flac` 對 mp3 做互相關（精確到取樣），之後每段用選中 take 的句子起點去對 mp3 的語音起點，再夾進段落前 0.6 秒的靜音裡。各段起點和檢查結果寫在 `render_log.json` 的 `boundaries`。
- 句子的時間戳：EP10 以後在 `qa/select_log.json` 選中那次 take 的 `segments`；EP01 到 EP09 沒有，改用 `qa/stt_check.json` 的 `whisper_segments`。
  兩者都只有每句的**起點**（`[start, text]`），終點用下一句的起點；段落最後一句的終點用段落終點。

### 聲音

- **拿掉開頭的 3.6 秒**（片頭音效加空白），第一秒就是 cold open 的第一句。YouTube 的觀眾在第一秒就決定要不要滑走。
- 其他不動：不重新混音，片尾音效留著。響度跟 mp3 的差 ≤ 0.5 LU。
- 因為少了 3.6 秒，影片版的章節時間是 mp3 版減 3.6 秒，`chapters.txt` 要另外算，不能直接沿用說明欄裡的章節。

### 字幕

- 文字一律用 `script.json`，不用轉寫（轉寫有錯字）。去掉 `<short pause>` 這類標記。
- 一句一條；超過 16 字斷成兩行，最多兩行。
- **燒進畫面**（手機上多數人不開字幕），同時上傳 `.srt`（給搜尋和翻譯用）。兩者文字一樣。

### 畫面

一個畫面只放一個重點，持續在換。參考 @foxh：大數字、出處、字幕三件事一直在換。

```
┌──────────────────────────────────────────┐
│ ● 深夜 Debug              章節名稱        │  ← 小字，固定
│                                          │
│   ［大數字卡］或［報告圖表］或［封面］       │
│                         引用：報告〈…〉    │  ← 出處，小字
│   ════ 字幕，大字，底部三分之一 ════        │
└──────────────────────────────────────────┘
```

- **大數字卡**：稿子裡有具體數字的句子（`script_lint` 已經會抓數字），畫面換成「一個大數字 + 一行說明」，例如紅色大字「180 億美元」配「外資一週匯出」。數字以 `script.json` 為準，寫法用阿拉伯數字。
- **報告圖表**：Playwright 開 `archive/report/<slug>.html`（imitator repo），把 `figure`、`svg`、`table`、`canvas` 各擷取一張；對照 `sources/<段>.txt` 決定每段配哪張，最多一張。
- **出處標註**：每張數字卡和圖表右下角標「引用：〈報告標題〉」，數字是報告引用別人的，標原始來源（例如「中央銀行」「Reuters」）。
- **開頭第一格**：不是封面，是 cold open 的鉤子：大數字卡或縮圖的那兩段字。
- 都沒有的時候：節目的 banner（`show/art/banner-v2-*.jpg`）加深色遮罩，`show/bg/loop.mp4` 存在就用它。
- **動態（`--motion`，2026-11-20 使用者選定「quiet」）**：只用低調的動態，配合深夜的調性。數字卡淡入並上浮 12 像素；背景在一段裡慢慢推近 4%；底部一條細進度條，章節處有刻度。不要數字跑動、彈跳或花俏轉場。
- **每段的背景圖**：`visuals.json` 每段可設 `background`（相對 `video/`）和 `background_label`。EP36 用 Gemini 生成的插畫，風格跟節目封面一樣，不畫人、字、商標，畫面左下標「示意圖：AI 生成」，提示詞存在圖旁邊。公開素材只少量用（Wikimedia Commons、政府開放資料，說明欄標作者與授權）；不用新聞畫面或劇照。
- 換段落時章節卡疊 1.5 秒（不加長影片）；圖淡入淡出 0.3 秒。
- 字型：Noto Sans TC Black（字幕、數字卡），LXGW WenKai TC（節目名，跟網站和 og 圖一致）。

`visuals.json`：

```json
{
  "segments": [
    {"id": "s07_foreign", "chapter": "十月急貶：外資進出太大",
     "items": [
       {"type": "number", "anchor": "外資幾天就匯出了快兩百億美元", "value": "180 億美元", "label": "外資一週匯出", "source": "中央銀行"},
       {"type": "figure", "anchor": "外資手上的錢，是央行存底的三倍多", "image": "visuals/fig03.png", "source": "〈台灣錢淹腳目 again？〉"}
     ]}
  ]
}
```

`anchor` 是稿子裡的句子，畫面從這句開始出現；找不到就從段落開頭。

### 縮圖

- 版型固定（`hooks.md`）：深色底（banner）、白字主題、紅底結論，左上「● 深夜 Debug」。字從 `youtube.thumbnail` 讀。
- 範例：`/mnt/project-files/ep07-ab/` 的三張（EP07 A/B 測試用，2026-11-20）。
- **只出縮圖的模式**：`make_video.py <ep> --thumbnail-only`，給已經上架的舊集數換縮圖用，不需要 mp3 以外的任何東西。

### Shorts

- 素材：cold open（s00），通常 35 到 45 秒。拿掉片頭音效，結尾接 2 秒「完整版在頻道」的卡（無聲或淡出）。
- 1080×1920，字幕更大（約 72px）、放在中間偏下；第一格是大數字卡。
- 標題用 `youtube.short.title`，說明欄第一行放長片連結（上傳長片後 Action 才知道網址，所以 Shorts 要排在長片之後）。
- 庫存：EP01 到 EP37 都有 cold open，可以先批次產出，`publish_at` 每天排一支。
- 工具：`tools/make_short.py`，每集的內容寫在 `episodes/<ep>/short.json`（聲音起訖、字幕、卡片、片尾卡；範例 EP24）。
  1. `python3 tools/make_short.py episodes/<ep> --align` 印出 cold open 的逐字時間和停頓（faster-whisper small，`pip install faster-whisper`），照它寫 `cues`。
  2. 寫 `cards`：`number`（大字＋紅底）、`choice`（問句、選項逐一出現）、`contrast`（「很多人說」對「報告說」）、`list`（逐列打勾）。同一張卡的逐步顯示用同一個 `group`，不淡入。
  3. `--previews` 只出預覽圖給使用者看，確認後再出 mp4。
  4. 結尾句子太像系列說明（「這集是……三部曲」）就切掉，停在懸念上，Short 控制在 35 到 45 秒。
  5. 字體要 `fonts-noto-cjk` 加 `fonts-noto-cjk-extra`（Black、Medium）。

## 9d：GitHub Action 上傳

上傳本身由 `tools/yt_upload.py` 做（標準函式庫、可續傳、重試；`--dry-run` 看會送出什麼，`--check` 確認憑證綁的頻道）。`.github/workflows/youtube.yml`（還沒寫）呼叫它，觸發：push 到預設分支且 `episodes/*/episode.json` 有變動，或手動。

1. 找出有 `youtube.publish_at`、但不在 `youtube/uploads.json` 裡的集數。
2. 從 Release `video-<ep>` 下載 mp4，比對 sha256。
3. YouTube Data API v3：
   - `videos.insert`：`snippet`（標題、說明欄、`defaultLanguage: zh-TW`、分類）、`status.privacyStatus: private` 加 `status.publishAt`（排程公開）、`status.containsSyntheticMedia: true`（「變造或合成內容」）
   - `thumbnails.set`：`thumbnail-a.png`
   - `captions.insert`：`.srt`
   - `playlistItems.insert`：podcast 播放清單
4. 把影片 id 寫回 `youtube/uploads.json` 並 commit（Action 要 `contents: write`）。
5. 長片完成後才上 Shorts，說明欄填入長片網址。

憑證放 GitHub Secrets：OAuth client id、client secret、refresh token。授權那一次要使用者本人登入。
安全做法照 `pages.yml`：只用官方 actions、釘 commit SHA、不用 `pull_request_target`。

### 要先處理的事（使用者，一次性）

- **API 稽核**：網站的 `/privacy/`、`/terms/` 與頁尾的 YouTube 標示是稽核要的（文字在 `tools/legal_pages.py`，工具的用途或存的資料變了要一起改）。新建的 Google Cloud 專案沒有通過稽核前，用 API 上傳的影片會被**鎖成私人**。稽核要幾天到幾週，**最先開始**。
- **額度**：預設每天 10,000 單位。上傳的單位數以官方的 quota 計算器為準（以往一支約 1,600），加上縮圖、字幕、播放清單，保守估一天 5 到 6 支。每天長片一支加 Shorts 一支沒問題，庫存的 Shorts 不要一次全傳。
- **測試與比較**（縮圖 A/B）沒有 API，只能在工作室手動設定。

## 跟 RSS 的關係

- RSS（`feed.xml`，由 `pages.yml` 發佈）繼續餵 Apple、Spotify 和其他平台，不受影響。
- YouTube 的 RSS 匯入**先不要關**。影片版還在測試時，測試那一集要手動處理：影片版上傳後，把 RSS 匯入的那支改成私人（不要刪，刪了會被重新抓回來）。
- 在工作室編輯過標題或說明欄的影片，只會停止那一支的 RSS 同步（2026-11-20 工作室確認）。
- 影片版證實有效後，才關掉 YouTube 的 RSS 匯入，改由 Action 上傳每一集；不然同一集會出現兩支。

## 怎麼判斷有沒有效

- **開發**用 EP07 當樣本（使用者先看成品），但**不上傳**：EP07 正在跑標題與縮圖的 A/B 測試，兩支同內容的影片會互搶曝光，也分不出差別是畫面還是包裝造成的。
- **實際比較**用下一集新集數：影片版上傳後第 7 天，跟 EP28 到 EP39（RSS 版）各自第 7 天的數字比。
- 只看自然流量：在進階模式用「流量來源」篩掉「YouTube 廣告」。測試的那一集不要放進廣告活動。
- 看四個數字：點閱率、30 秒留存、1 分鐘留存、平均觀看百分比。單集樣本小，先看方向，連續三集都比較好再下結論。

## 驗收（9a）

| 項目 | 通過條件 |
|---|---|
| 段落起點 | 跟 mp3 的靜音段比對，每個交界誤差 ≤ 0.15 秒（含固定開場） |
| 字幕同步 | 抽 5 個時間點（開頭、結尾、一個數字句、固定開場後第一句、最後一段中間），誤差 ≤ 0.3 秒 |
| 字幕文字 | 跟 `script.json` 逐字一致（去掉標記後）；沒有超過兩行的字幕 |
| 長度 | 影片 = mp3 − 3.6 秒，誤差 ≤ 0.1 秒 |
| 聲音 | 跟 mp3 的響度差 ≤ 0.5 LU |
| 章節 | `00:00` 開始、至少三個、每個至少 10 秒；固定開場併進下一章 |
| 數字卡 | 每張的數字都在 `script.json` 裡找得到，且有出處 |
| 圖表 | 1080p 下文字看得清楚；沒有截到一半的圖 |
| 畫面 | 沒有空白或黑畫面超過 1 秒；第一格不是封面 |
| Shorts | 1080×1920、60 秒以內、第一格是數字卡 |

## 順序

| 里程碑 | 內容 | 誰 |
|---|---|---|
| M0 | 修兩個時間 bug，重算 EP38、EP39 的章節 | agent |
| M0' | 開 Google Cloud 專案、送 API 稽核（跟其他步驟並行） | 使用者 |
| M1 | `make_video.py`，用 EP07 做出長片、Shorts、縮圖，給使用者看 | agent |
| M2 | 下一集新集數：產出、確認，**手動上傳**，開始比較 | agent + 使用者 |
| M3 | `youtube.yml` 上傳 Action（稽核通過後） | agent |
| M4 | 庫存 Shorts 批次產出，每天排一支 | agent |
| M5 | 連續三集有效之後：關掉 YouTube 的 RSS 匯入，第 9 步寫進 `recipe.md` | 使用者決定 |

## 不做

- 不生成 AI 影片素材（Veo 之類）：先驗證「圖表 + 數字卡 + 字幕」夠不夠。
- 不重新混音、不改第 0 到 8 步的產出（拿掉開頭 3.6 秒是影片版自己的剪輯，mp3 不變）。
- 不用真人照片或新聞照片（版權不明）。
