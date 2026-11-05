# DebugAfterDark — 深夜 Debug｜Debug After Dark

把 [imitator](https://imitator.ai-apps.work/) 上的報告改寫成給人聽的 podcast：台灣華語、單人主持、AI 語音合成，
目的是讓還沒讀過報告的人也聽得懂、聽完想去看全文。主持人是 AI 角色 **Ping**。

| 集數 | 內容 | 狀態 |
|---|---|---|
| [EP00](episodes/ep00-intro/) | 嘿，還醒著嗎？（預告集，節目自介） | 定稿 |
| [EP01](episodes/ep01-fifth-move/) | 記住了第一招，漏掉了第五招 | 定稿；用新產線重做（ttspoc 的 POC 版在 `poc/`） |
| [EP02](episodes/ep02-harness-probe/) | 第五招的實驗：跑從來不是問題，看才是 | 定稿（s01 補上回顧上一集） |
| [EP03](episodes/ep03-one-point-cost/) | 每加一分，就扣一分（帳單三部曲 1/3） | 定稿 |
| [EP04](episodes/ep04-bill-to-code-map/) | 帳單響了之後，你手上有沒有地圖（帳單三部曲 2/3） | 定稿 |
| [EP05](episodes/ep05-reef-chart/) | 撞礁是遲早的，會不會沉才是問題（帳單三部曲 3/3） | 定稿 |
| [EP06](episodes/ep06-ghost-five-faces/) | 同一隻鬼，換了五張臉（股市怪談） | 定稿；白話稿重做一次 |
| [EP07](episodes/ep07-taiwan-money-again/) | 台灣錢淹腳目，這次淹在別人腳下 | 定稿 |

- 一集怎麼做：[`docs/recipe.md`](docs/recipe.md)
- 節目怎麼營運（選題、審稿、跟 imitator 整合、上架平台）：[`PIPELINE.md`](PIPELINE.md)
- 主持人 Ping 的命名與人設：[`HOST.md`](HOST.md)
- EP00 自介稿與節目文案：[`episodes/ep00-intro/script.md`](episodes/ep00-intro/script.md)
- 固定開場：[`show/ident/`](show/ident/)
- 前身 POC：[`clarencechien/ttspoc`](https://github.com/clarencechien/ttspoc) 的 `podcast/`（工具與 EP01 從 `799872e` 搬來）

## 上架狀態
- 網站與 feed：<https://podcast.ai-apps.work>，feed `https://podcast.ai-apps.work/feed.xml`（GitHub Pages，見 `PIPELINE.md` §5 的過渡方案）
- 擁有者信箱：`podcast@ai-apps.work`（Cloudflare Email Routing 轉寄）
- 還沒送審 Apple Podcasts、Spotify 等平台
- 下載數據：SoundOn Prefix（`show.json` 的 `enclosure_prefix`），feed 裡的音檔網址先經過 SoundOn 再 302 回我們的檔案；網站播放器不經過
- 贊助連結：<https://portaly.cc/clarencech/support>（`show.json` 的 `support_url`），見下面的「Portaly 現況」

## 收入方式（2026-11-04 調查；目前只做了贊助連結）

先講結論：**現在先不賺錢，先累積聽眾；但從第一天就把會影響以後選擇的事情做對。**
多數「平台幫你賺」的方式都要求把節目託管在那個平台，跟我們現在自架 feed 的做法衝突，而且都有聽眾數門檻。

### 有哪些方式

| 方式 | 怎麼運作 | 要的條件 | 跟我們現況合不合 |
|---|---|---|---|
| **口播贊助（業配）** | 廠商付錢，Ping 在節目裡念一段贊助內容 | 有聽眾數可以談；要標示是贊助 | **自架就能做**。但 AI 聲音念業配，廠商不一定接受；要在說明與口播都標「本集由 ○○ 贊助」 |
| **SoundOn 動態廣告** | 平台自動在節目裡插廣告，跟創作者分潤 | 2022 年推出時的報導沒寫分潤比例與門檻；插廣告要由託管平台做，**應該要託管在 SoundOn**（未確認） | 衝突：要搬離自架 |
| **Spotify Partner Program** | Spotify 依 Premium 用戶收聽時間分潤 | 託管在 Spotify for Creators、至少 3 集、近 30 天 2,000 小時收聽、1,000 位不重複聽眾；2026 年擴大到 35 個以上市場，**沒看到台灣** | 衝突：要託管在 Spotify；門檻遠高於現況 |
| **Apple Podcasts 訂閱** | 聽眾在 Apple Podcasts 付費訂閱，拿到無廣告或加碼內容 | 加入 Apple Podcasters Program（每年約 US$19.99）；Apple 抽成；台灣應該可用（第三方資料，未確認） | 不用搬家，付費內容另外上傳到 Apple；要有值得付費的加碼內容 |
| **Firstory 贊助／會員** | 聽眾單次贊助或按月訂閱，會員可聽專屬單集（也能上 Spotify） | 託管在 Firstory；台灣目前做訂閱最成熟的平台，抽成比例沒查到 | 衝突：要搬離自架 |
| **Patreon** | 聽眾按月支持，會員拿到 Patreon 產生的私人 RSS 收聽加碼內容 | Patreon 抽成；私人 feed 由 Patreon 託管 | **公開節目維持自架，加碼內容放 Patreon**，兩者可以並存 |
| **贊助按鈕**（Buy Me a Coffee、Ko-fi 等） | 網站與 show notes 放一個連結，聽眾自由小額贊助 | 幾乎沒有 | **已上線**，用 Portaly 的 /support（見下面）。收入很小，主要是看有沒有人願意付 |
| **Podcasting 2.0 value-for-value** | feed 加 `podcast:value`，支援的 app 讓聽眾用比特幣閃電網路按分鐘付費 | 要有閃電網路錢包；支援的 app 少 | 技術上加幾行 feed 就好，但台灣聽眾幾乎用不到 |
| **導流到自己的產品** | 節目帶人去看 imitator 報告，再接顧問、課程、企業內訓 | 要先有可賣的東西 | **對工程師向的小眾節目，通常是最實際的收入**；完全不受平台規則限制 |
| **YouTube** | 影音 podcast（封面加音波），YouTube 合作夥伴計畫分潤 | 1,000 訂閱、4,000 小時觀看等門檻；2026 年起大量檢查「量產內容」，AI 配音本身不禁止，但要有真實的製作價值 | 可以多一個曝光管道；分潤門檻高且 AI 內容風險高 |

### 會影響所有選項的四件事
1. **GitHub Pages 不能當商業網站。** 規範寫明不能拿來做線上生意或以商業交易為主的網站。節目裡念贊助、放一個贊助連結應該還好；但要正式做廣告或付費內容，就該先把 host 搬到 imitator 的 Worker 或 podcast 託管平台。feed 網址已經是自己的網域，搬家只改 DNS，不影響聽眾。
2. **AI 合成聲音。** 平台在收緊「量產 AI 內容」（業界叫 podslop）。我們的差別是每集都有真人審稿、改寫自查證過的報告、不量產，這要在節目說明和申請資料裡講清楚。揭露原則（`PIPELINE.md` §6.2）不能因為想過審而拿掉。
3. **內容權利。** 部分集數是別人文章的導讀（例如 EP01 的 Felix Rieseberg），不賺錢時是評論；開始賺錢之後，大量引用別人的內容風險會變高，要更偏向評論與自己的觀點。案例裡的真實人物維持不具名。
4. **TTS 的商業使用條款。** Gemini API 用付費層級、確認生成的音檔可以商用；免費層級的資料可能被拿去訓練，正式營利前要換成付費 key。這點沒查官方條款原文，要再確認。

### Portaly 現況（2026-11-04）

**對外只用 /support。** <https://portaly.cc/clarencech/support> 是 Portaly 個人頁內建的贊助功能，單次和每月都能付，不用寫程式。

- **出現在哪裡**：
  - feed：`tools/feed.py` 的 `with_support()` 把「請 Ping 喝杯咖啡：<網址>」接在節目簡介和每一集說明的最後，SoundOn、Apple、Spotify 讀 feed 時都會顯示。
  - 網站：訂閱區塊下面和頁尾。
- **文案只能在 Portaly 後台手改。** Portaly MCP 和開放 API 都沒有個人頁或 /support 的端點。

**Payment 方案先不用。** 用 MCP 建了一個「請 Ping 喝杯咖啡」，id `jsVGziLeKoNCoamvEKzW`，一次性、自由金額、TWD，目前是**下架**狀態。不用的原因：

- **沒有固定的購買頁。** 要由伺服器拿 API key 呼叫 `POST /api/creator-subscription/checkout-sessions`，拿到 `checkoutUrl` 再把人轉過去。
  - 這個網址 30 分鐘就過期，所以不能直接貼進 feed 或說明。
  - key 只能放在伺服器端，GitHub Pages 是靜態站，放不了。
- **live key 有三個條件**：
  - 通過金流審核（KYC）
  - 有 Portaly 付費會員或 Vibe 訂閱
  - 第二個商品起，每個商品要另外審核

  在那之前只能用 test key 測試。
- **要用的時候**：架一支 Cloudflare Worker，提供一個固定網址。它負責建 session、轉址，並接付款完成的 callback（驗 `x-portaly-signature`）。key 和 callback secret 放在 Worker 的 secret。
  - 適合的時機是做付費加碼內容（例如「Ping 的延伸筆記」），因為那時要知道誰付了錢。
  - 單純贊助用 /support 就夠了。
- **重新上架前要先在後台調整方案**：
  - 「收集手機」目前是開的：API 改得到，MCP 改不到。
  - 「使用條款」開著但內容是空的：只能在後台改。

**開放 API 能自動化什麼**（`portaly.ai/llms.txt` 是索引，完整規格在 `portaly.ai/openapi.json`）：

| 範圍 | 能做的事 | 限制 |
|---|---|---|
| Payment（訂閱與單次付款） | 建立與修改方案、上下架；建結帳 session；查訂單、退款、查發票；取消或恢復訂閱；產生訂閱者的自助管理頁 | 結帳都要經過伺服器端建 session；live key 要通過 KYC 加付費會員 |
| 折扣碼 | 新增、修改、停用、查詢 | 只能用在 Payment 方案 |
| 數位商品 | 列出 Portaly 上的商品、建單品或組合包的結帳、上下架、查訂單 | 不能用 API 新增商品，要先在後台建好 |
| 推廣分潤 | 開關、設定分潤比例 | 只限單次、固定價格的方案，也只限台灣帳號 |
| Webhook | 12 種付款與訂閱事件（成交、續扣、退款、取消等），都有簽章可以驗證 | 要有伺服器接收 |
| Email（beta） | 從自己的網域寄信：單封、批次、排程；查寄送狀態與額度 | 只開放受邀帳號，還要 Premium 方案；用另一種 key（`pem_*`） |
| 發信 MCP（beta） | AI 擬電子報、寄測試信給你；你在後台按「確認上線」後才會寄出 | 要有 Email beta 資格、Premium Plus，並在 <https://portaly.cc/admin/email/mcp> 開通 |
| 評價徽章 | 用 iframe 嵌入已購買者的評分 | 要先有真實訂單 |
| 結帳頁品牌 | 結帳頁顯示的商家名稱和 logo（目前是空的） | |

做不到的：
- 個人頁和 /support 的內容
- 方案的「使用條款」開關
- 用 API 建數位商品

另外，/support 收到的贊助很可能不在訂單 API 的範圍裡，因為訂單 API 只涵蓋 Payment 和數位商品。這點還沒驗證過。

**跟這個節目有關的**（都還沒做）：
1. **新集數上架時自動發電子報**：最貼近現在的產線，也不用架伺服器。`feed.py` 跑完後，用 `episode.json` 的說明加上 breakpoint 擬一封信，寄測試信給自己，在 Portaly 按確認才寄出。
   - 前提：帳號有 Email beta 資格加 Premium Plus，而且 Portaly 上要有訂閱名單。
   - **下一步就是確認這兩件事。**
2. **付費加碼內容（「Ping 的延伸筆記」）**：Payment 月繳方案，加上 Worker 建結帳和接 webhook，再加自助管理頁讓聽眾自己取消。等有固定聽眾再做（見下面「建議的順序」第 2 步）。
3. **賣數位商品**：例如逐字稿加延伸閱讀的組合包。商品要先在後台手動建，API 只負責結帳。目前沒有適合賣的東西。
4. **收入月報**：用訂單和發票 API 自動整理收入。要等 Payment 或數位商品真的有交易才有意義。

現在不用做的有三項：折扣碼、推廣分潤、評價徽章。原因是都要先有付費方案和真實訂單。

**key 的規矩**：只放在環境變數或 Worker secret，不進 repo，也不貼進對話；用完或外流就到 <https://portaly.cc/admin/creator-subscription> 撤銷重建。test key 也讀得到、改得到正式的方案，不能因為是 test 就放鬆。

### 建議的順序
1. **現在**：不賺錢。用 SoundOn Prefix 看下載數；網站和 show notes 放一個贊助連結（已做，Portaly /support）。
2. **每月有固定聽眾（約 1,000 人）之後**：試一則口播贊助，固定放在 breakpoint 之前；同時評估要不要開 Apple Podcasts 訂閱或 Patreon 的加碼內容（例如「Ping 的延伸筆記」）。
3. **要做平台分潤（動態廣告、Spotify）時**：才決定要不要把 host 搬到那個平台。不要太早被單一平台綁住：一搬過去，feed、數據和加碼內容都在別人手上。

### 參考資料
- Spotify：[Monetizing your show with Spotify for Creators](https://support.spotify.com/us/creators/article/spotify-for-creators-monetization-options/)、[Partner Program 擴大到 35 個以上市場](https://routenote.com/radar/spotify-partner-program-expands-to-more-than-35-new-countries-how-creators-can-make-money/)
- Apple：[Set up a channel subscription](https://podcasters.apple.com/support/set-up-a-subscription)、[Apple Podcasts Subscriptions 全球上線](https://www.iclarified.com/81402/apple-podcasts-subscriptions-and-channels-now-available-worldwide)
- SoundOn：[推出動態廣告（INSIDE）](https://www.inside.com.tw/article/27810-soundon-dynamic-ad-insertion)、[動態廣告發出百萬廣告金（T 客邦）](https://www.techbang.com/posts/98767-soundon-dynamic-ads-earns-podcaster-millions-of-dollars)、[Prefix 數據追蹤碼](https://support.soundon.fm/articles/4529054)
- Firstory：[訂閱贊助一年破 600 萬](https://www.inside.com.tw/article/27427-podcast-subscription)、[2025 趨勢預測](https://www.inside.com.tw/article/37526-fistory-2025-podcast)
- Patreon：[Enable audio RSS feeds for my members](https://support.patreon.com/hc/articles/213557023)、[Pocket Casts 加入私人 feed](https://support.pocketcasts.com/knowledge-base/private-or-members-only-feeds/)
- AI 內容與分潤：[The Audio Industry Is Grappling With the Rise of 'Podslop'](https://www.pulse.bot/entertainment/news/the-audio-industry-is-grappling-with-the-rise-of-podslop-be7d9d8d-8133-4614-a223-58d27a740607/)、[Can You Monetize AI-Generated Videos on YouTube in 2026?](https://fluxnote.io/guides/monetize-ai-generated-videos-youtube-2026)
- Portaly：[Portaly Payment 教學](https://portaly.cc/blog/portaly-payment-tutorial)、[官方 agent skills（portaly-ai/portaly-skills）](https://github.com/portaly-ai/portaly-skills)、[API 文件](https://portaly.ai/docs)、[OpenAPI 規格](https://portaly.ai/openapi.json)
- GitHub Pages：[GitHub Pages limits（禁止的用途）](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)
