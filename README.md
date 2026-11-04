# DebugAfterDark — 深夜 Debug｜Debug After Dark

把 [imitator](https://imitator.ai-apps.work/) 上的報告改寫成給人聽的 podcast：台灣華語、單人主持、AI 語音合成，
目的是讓還沒讀過報告的人也聽得懂、聽完想去看全文。主持人是 AI 角色 **Ping**。

| 集數 | 內容 | 狀態 |
|---|---|---|
| [EP00](episodes/ep00-intro/) | 嘿，還醒著嗎？（預告集，節目自介） | 定稿 |
| [EP01](episodes/ep01-fifth-move/) | 記住了第一招，漏掉了第五招 | 定稿；用新產線重做（ttspoc 的 POC 版在 `poc/`） |
| [EP02](episodes/ep02-harness-probe/) | 第五招的實驗：跑從來不是問題，看才是 | 定稿（s01 補上回顧上一集） |
| [EP03](episodes/ep03-one-point-cost/) | 每加一分，就扣一分（帳單三部曲 1/3） | 定稿 |

- 一集怎麼做：[`docs/recipe.md`](docs/recipe.md)
- 節目怎麼營運（選題、審稿、跟 imitator 整合、上架平台）：[`PIPELINE.md`](PIPELINE.md)
- 主持人 Ping 的命名與人設：[`HOST.md`](HOST.md)
- EP00 自介稿與節目文案：[`episodes/ep00-intro/script.md`](episodes/ep00-intro/script.md)
- 固定開場：[`show/ident/`](show/ident/)
- 前身 POC：[`clarencechien/ttspoc`](https://github.com/clarencechien/ttspoc) 的 `podcast/`（工具與 EP01 從 `799872e` 搬來）

## 上架狀態
- 網站與 feed：<https://podcast.ai-apps.work>，feed `https://podcast.ai-apps.work/feed.xml`（GitHub Pages，見 `PIPELINE.md` §5 的過渡方案）
- 擁有者信箱：`podcast@ai-apps.work`（Cloudflare Email Routing 轉寄）
- 還沒送審 Apple Podcasts、Spotify 等平台；SoundOn Prefix 數據追蹤碼在申請中

## 收入方式（2026-11-04 調查，還沒做任何一項）

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
| **贊助按鈕**（Buy Me a Coffee、Ko-fi 等） | 網站與 show notes 放一個連結，聽眾自由小額贊助 | 幾乎沒有 | **現在就能做**，收入很小，主要是看有沒有人願意付 |
| **Podcasting 2.0 value-for-value** | feed 加 `podcast:value`，支援的 app 讓聽眾用比特幣閃電網路按分鐘付費 | 要有閃電網路錢包；支援的 app 少 | 技術上加幾行 feed 就好，但台灣聽眾幾乎用不到 |
| **導流到自己的產品** | 節目帶人去看 imitator 報告，再接顧問、課程、企業內訓 | 要先有可賣的東西 | **對工程師向的小眾節目，通常是最實際的收入**；完全不受平台規則限制 |
| **YouTube** | 影音 podcast（封面加音波），YouTube 合作夥伴計畫分潤 | 1,000 訂閱、4,000 小時觀看等門檻；2026 年起大量檢查「量產內容」，AI 配音本身不禁止，但要有真實的製作價值 | 可以多一個曝光管道；分潤門檻高且 AI 內容風險高 |

### 會影響所有選項的四件事
1. **GitHub Pages 不能當商業網站。** 規範寫明不能拿來做線上生意或以商業交易為主的網站。節目裡念贊助、放一個贊助連結應該還好；但要正式做廣告或付費內容，就該先把 host 搬到 imitator 的 Worker 或 podcast 託管平台。feed 網址已經是自己的網域，搬家只改 DNS，不影響聽眾。
2. **AI 合成聲音。** 平台在收緊「量產 AI 內容」（業界叫 podslop）。我們的差別是每集都有真人審稿、改寫自查證過的報告、不量產，這要在節目說明和申請資料裡講清楚。揭露原則（`PIPELINE.md` §6.2）不能因為想過審而拿掉。
3. **內容權利。** 部分集數是別人文章的導讀（例如 EP01 的 Felix Rieseberg），不賺錢時是評論；開始賺錢之後，大量引用別人的內容風險會變高，要更偏向評論與自己的觀點。案例裡的真實人物維持不具名。
4. **TTS 的商業使用條款。** Gemini API 用付費層級、確認生成的音檔可以商用；免費層級的資料可能被拿去訓練，正式營利前要換成付費 key。這點沒查官方條款原文，要再確認。

### 建議的順序
1. **現在**：不賺錢。用 SoundOn Prefix 看下載數；網站和 show notes 放一個贊助連結（可選）。
2. **每月有固定聽眾（約 1,000 人）之後**：試一則口播贊助，固定放在 breakpoint 之前；同時評估要不要開 Apple Podcasts 訂閱或 Patreon 的加碼內容（例如「Ping 的延伸筆記」）。
3. **要做平台分潤（動態廣告、Spotify）時**：才決定要不要把 host 搬到那個平台。不要太早被單一平台綁住：一搬過去，feed、數據和加碼內容都在別人手上。

### 參考資料
- Spotify：[Monetizing your show with Spotify for Creators](https://support.spotify.com/us/creators/article/spotify-for-creators-monetization-options/)、[Partner Program 擴大到 35 個以上市場](https://routenote.com/radar/spotify-partner-program-expands-to-more-than-35-new-countries-how-creators-can-make-money/)
- Apple：[Set up a channel subscription](https://podcasters.apple.com/support/set-up-a-subscription)、[Apple Podcasts Subscriptions 全球上線](https://www.iclarified.com/81402/apple-podcasts-subscriptions-and-channels-now-available-worldwide)
- SoundOn：[推出動態廣告（INSIDE）](https://www.inside.com.tw/article/27810-soundon-dynamic-ad-insertion)、[動態廣告發出百萬廣告金（T 客邦）](https://www.techbang.com/posts/98767-soundon-dynamic-ads-earns-podcaster-millions-of-dollars)、[Prefix 數據追蹤碼](https://support.soundon.fm/articles/4529054)
- Firstory：[訂閱贊助一年破 600 萬](https://www.inside.com.tw/article/27427-podcast-subscription)、[2025 趨勢預測](https://www.inside.com.tw/article/37526-fistory-2025-podcast)
- Patreon：[Enable audio RSS feeds for my members](https://support.patreon.com/hc/articles/213557023)、[Pocket Casts 加入私人 feed](https://support.pocketcasts.com/knowledge-base/private-or-members-only-feeds/)
- AI 內容與分潤：[The Audio Industry Is Grappling With the Rise of 'Podslop'](https://www.pulse.bot/entertainment/news/the-audio-industry-is-grappling-with-the-rise-of-podslop-be7d9d8d-8133-4614-a223-58d27a740607/)、[Can You Monetize AI-Generated Videos on YouTube in 2026?](https://fluxnote.io/guides/monetize-ai-generated-videos-youtube-2026)
- GitHub Pages：[GitHub Pages limits（禁止的用途）](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)
