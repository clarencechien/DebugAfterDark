# Short 與影片版：半自動上片（規劃，2026-11-20）

目標：Short 和影片版跟 podcast 一樣，**Clarence 審一次、commit，其餘交給 GitHub**。
這份是規劃，程式還沒寫；11/27 看完 Short 和影片版的成效、決定要不要日更之後才實作（見 [`strategy.md`](strategy.md)）。
產出的做法在 [`video.md`](video.md)（影片版）和 [`recipe.md`](recipe.md) 第 10 步（Short）。

## 前提：API 上傳已經可以排程（11/20 驗證）

- Google 11/20 結案 API 稽核：用 API 上傳的影片不會再被自動鎖成私人。
- 同一天實測：`tools/yt_upload.py` 上傳一支測試 Short（private、`publishAt` 2027-06-01）到深夜 Debug，處理完仍是 private，`publishAt` 保留，`uploadStatus: processed`，沒有 rejection 或 failure 原因；測完已刪除。
- 所以 `private` 加 `publishAt` 就是排程公開，不用再進工作室改。

## 跟 podcast 對照

| | Podcast（現在） | Short、影片版（規劃） |
|---|---|---|
| 產出 | agent 照 `recipe.md` 做 | 同一個 thread 接著做（第 9、10 步） |
| 審核 | Clarence 聽成品（關卡 B） | Clarence 看一張**上片審核單**（下面） |
| 同意 | commit 到 main | 一樣：commit `episode.json` 的 `youtube.short` / `publish_at` 就是同意 |
| 上架 | `pages.yml` 發 RSS，YouTube 匯入，`yt-autofix` 補 AI 標示並公開 | Action 從 Release 下載 mp4、比對 sha256、用 API 上傳排程，寫回 `youtube/uploads.json` |
| 事後檢查 | 週報 | Action 讀回狀態；有問題開 issue（或下次週報列出） |
| 最後一道 | — | 影片在 `publishAt` 前都是私人：Clarence 可以在工作室看到真的上傳版本，不對就改成私人取消 |

## 上片審核單（Clarence 要看的全部）

每集一份，放專案檔案 `shorts/<ep>/review.md`（影片版放 `video/<ep>/review.md`），跟 podcast 的 PR 一起給：

1. 預覽總表（contact sheet）和封面
2. 標題（三選一，有推薦）、說明欄全文、tags
3. 排程時間（台北時間）和會用到的 API 額度
4. 自動檢查結果：字幕對齊誤差、長度、響度、第一格、sha256
5. 要人工做的事（目前只剩「相關影片」，見下表）

Clarence 回「好」或指定標題，agent 把選定的內容寫進 `episode.json`、mp4 傳到 Release，commit。之後不用再動。

## 每個人工項目能不能自動

| 項目 | 現在 | 規劃 | 依據 |
|---|---|---|---|
| 上傳、排程 | 工作室手動 | **自動**：`yt_upload.py`，`private` + `publishAt` | 11/20 實測 |
| 標題、說明欄、tags | 手貼 | **自動**：從 `episode.json` | `videos.insert` snippet |
| 說明欄第一行的長片網址 | 手查 | **自動**：用 EP 編號在頻道找長片（同 `yt_autofix.py` 的比對），找到才上傳 Short | 長片是 RSS 匯入，id 不在 `uploads.json` |
| 「變造或合成內容」 | 工作室勾 | **自動**：上傳時 `containsSyntheticMedia: true`（`yt_upload.py` 已有） | API 只能寫、讀不回來；第一次 API 上傳時在工作室確認一次 |
| 不進 podcast 播放清單 | 手動確認 | **自動**：Short 不呼叫 `playlistItems.insert`，上傳後讀回確認 | |
| 封面 | 手機選第 0 秒 | **不用做**：Short 的第一格就是封面卡（`make_short.py` 已這樣做）。長片用 `thumbnails.set` | Shorts 動態牆不一定用自訂縮圖；第一次 API 上傳時試 `thumbnails.set` 看有沒有生效 |
| 字幕檔 | 手動上傳（選填） | **自動**：`captions.insert`，但要**重新授權加 `youtube.force-ssl`** | 11/20 測 `captions.list` 回 403 insufficient scopes；Short 字幕已燒進畫面，不急 |
| 字幕對齊 | agent 寫、人看預覽 | **半自動**：`--align` 的逐字時間跟 cue 自動比，誤差 > 0.3 秒才列在審核單 | 文字仍照 `script.json`，母帶念錯的地方要人確認 |
| Short 卡片內容（`short.json`） | agent 寫 | 不變，agent 在同一個 thread 寫，Clarence 從預覽總表看 | 這是內容判斷，不自動 |
| 「相關影片」 | 工作室選長片 | **仍要人工**，約 30 秒；Clarence 在工作室看排程影片時順手設 | Data API 沒有這個欄位。沒設也不影響上架，說明欄第一行已有長片連結 |
| 影片版 AI 背景圖 | 一次性手動生成 | **自動**：`gen_art.py` 加 `background` 模式（同一個 `gemini-3-pro-image`），從各段 `sources/` 寫提示詞，提示詞存在圖旁；Clarence 從預覽截圖看 | |
| 影片版的 RSS 匯入那支 | 手動改私人、加進 `KEEP_PRIVATE` | **自動**：`yt_autofix.py` 遇到 `uploads.json` 已有影片版的集數，RSS 匯入那支保持私人 | 等關掉 RSS 匯入後就不需要 |

結果：Clarence 每集要做的只剩**看審核單、回覆同意**；「相關影片」是可選的 30 秒。

## Action 怎麼跑

沿用 `yt-autofix.yml`（每小時 :17，由 `cron-worker/` 準時觸發），多一個步驟，或另開 `youtube.yml`：

1. 找 `episode.json` 有 `youtube.short.publish_at`（或影片版的 `youtube.publish_at`）、但不在 `youtube/uploads.json` 的集數。
2. Short：先確認長片已經在頻道上且公開，沒有就等下一輪。
3. 從 Release `short-<ep>` / `video-<ep>` 下載 mp4，比對 `episode.json` 裡記的 sha256，不一致不上傳。
4. `yt_upload.py` 上傳；讀回 `uploadStatus`、`privacyStatus`、`publishAt`、`rejectionReason`、`failureReason`，以及播放清單。
5. 影片 id 寫回 `youtube/uploads.json` 並 commit（workflow 要 `contents: write`）。
6. 失敗或狀態不對：不重試上傳（避免重複上片和燒額度），開 issue 通知。

安全照 `pages.yml`：只用官方 actions、釘 commit SHA、不用 `pull_request_target`。

## 額度（每天 10,000 單位）

以官方 quota 計算器為準，保守估：

| 呼叫 | 單位 |
|---|---|
| `videos.insert` | 約 1,600 |
| `thumbnails.set` | 50 |
| `captions.insert` | 400 |
| `playlistItems.insert` | 50 |
| 讀回檢查 | 個位數 |
| `yt-autofix` 每小時 | 每天約 100，加每集 50 |

- 每天 2 支 Short：約 3,300。
- 每天 2 支 Short + 2 支影片版：約 7,500，還在額度內，但重傳一次就可能超過。
- 所以：一輪最多傳 4 支；庫存 Short 不要一次全傳；要更多就填 YouTube API Quota Request Form（Google 結案信裡提到）。

## 實作順序（11/27 決定要做之後）

| 步驟 | 內容 | 要 Clarence |
|---|---|---|
| 1 | 重新授權加 `youtube.force-ssl`（`get_refresh_token.py` 的 SCOPES），更新雲端環境變數和 repo secrets | 是，Chromebook 上跑一次 |
| 2 | `episode.json` 加 `youtube.short`（title、description、publish_at、sha256）；`make_short.py` 產審核單和自動對齊檢查 | 看第一份審核單 |
| 3 | `yt_upload.py --short`：找長片網址、讀回檢查 | |
| 4 | 第一支用 API 上傳的 Short：在 thread 裡手動跑，Clarence 在工作室確認 AI 標示、封面 | 是 |
| 5 | Action 化（上面那節） | 審 PR |
| 6 | 影片版：`gen_art.py background`、`yt_autofix` 保持影片版那集的 RSS 匯入私人 | 等影片版成效 |
