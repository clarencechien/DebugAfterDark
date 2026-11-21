# cron-worker：準時觸發 GitHub Actions

GitHub 的 `schedule` 在尖峰時段會延遲好幾小時或整次跳過（2026-11-20 實測：20:07 的 Pages 建置拖到 04:04，
yt-autofix 18 小時只跑 2 次）。上架時間實驗要準時，所以改由 Cloudflare Worker 的 Cron Trigger 呼叫
GitHub 的 `workflow_dispatch`。workflow 裡原本的 `schedule` 保留當備援，重複觸發沒關係（有 concurrency 排隊，結果一樣）。

| 台北時間 | cron（UTC） | 觸發 |
|---|---|---|
| 每天 08:02 | `2 0 * * *` | `pages.yml`（08:00、08:01 上架的集數進 feed） |
| 每天 20:02 | `2 12 * * *` | `pages.yml` |
| 每小時 :17 | `17 * * * *` | `yt-autofix.yml` |

要改時間：同時改 `worker.js` 的 `SCHEDULE` 和 `wrangler.toml` 的 `crons`（後台部署的話是 Trigger events），
`node --test cron-worker/worker.test.mjs` 會檢查兩邊一致。

## 目前狀態（2026-11-21）

- Cloudflare Worker `debugafterdark-cron` 已部署（2026-11-21 02:26 UTC），三個 cron 都設好，workers.dev 網址關閉。
- Secret `GH_TOKEN` 已由 Clarence 在 Cloudflare 後台加好（值只存在 Cloudflare，不在 repo、不在聊天裡）。
- 程式碼以這個資料夾的 `worker.js` 為準，部署的版本跟它一樣。

## GitHub token 怎麼建（到期或要換時）

1. 開 <https://github.com/settings/personal-access-tokens/new>（Fine-grained token）
2. Token name：`debugafterdark-cron`；Expiration：選 Custom，設一年後
3. Repository access：選 **Only select repositories** → 選 `clarencechien/debugafterdark`
4. Permissions：按 **Add permissions** → 勾 **Actions** → 把 Actions 的存取改成 **Read and write**（其他都不用加）
5. Generate token，複製（只會顯示一次，不要貼到聊天裡）
6. Cloudflare 後台 → Workers & Pages → `debugafterdark-cron` → **Settings** → **Variables and Secrets** →
   編輯 `GH_TOKEN`（Type: Secret），貼上新 token → **Deploy**

## 改程式碼後怎麼重新部署

- 後台：Worker 頁面 → **Edit code** → 貼上新的 `worker.js` → **Deploy**。secret 不會被清掉。
- wrangler：`cd cron-worker && npx wrangler deploy`（secret 也會保留）。
- Cloudflare API（Claude 用 connector 部署時）：PUT `/accounts/{account_id}/workers/scripts/debugafterdark-cron`，
  metadata 要帶 `"keep_bindings": ["secret_text"]`，不然 `GH_TOKEN` 會被清掉。
- 改時間的話，後台 **Settings** → **Trigger Events** 的 cron 也要一起改。

## 確認有在跑

每小時 :17 過後，到 GitHub Actions 的 YouTube autofix 看，會有一筆 Event 是 `workflow_dispatch` 的執行
（GitHub 自己的備援排程那筆 Event 是 `schedule`，可能晚很多或沒有）。
Cloudflare 那邊在 Worker 的 **Logs** 會看到 `{"cron":"17 * * * *","results":[{"workflow":"yt-autofix.yml","ok":true,...}]}`。
失敗（例如 token 過期回 401）也會在 Logs 和 Cron Events 顯示。

## 維護

- token 一年後（約 2027-11）到期，到期前照上面步驟重建一個，更新 Worker 的 `GH_TOKEN`。
- 免費方案的 Cron Trigger 夠用（每天 26 次）。
