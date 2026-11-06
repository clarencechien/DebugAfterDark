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
| [EP08](episodes/ep08-unlimited-tokens/) | 無限的是 token，有限的是驗收（驗收筆記 1/2） | 定稿 |
| [EP09](episodes/ep09-million-cores/) | 一百萬顆 CPU，是用來驗的（驗收筆記 2/2） | 定稿 |

- 一集怎麼做：[`docs/recipe.md`](docs/recipe.md)
- 節目怎麼營運（選題、審稿、跟 imitator 整合、上架平台）：[`PIPELINE.md`](PIPELINE.md)
- 主持人 Ping 的命名與人設：[`HOST.md`](HOST.md)
- EP00 自介稿與節目文案：[`episodes/ep00-intro/script.md`](episodes/ep00-intro/script.md)
- 固定開場：[`show/ident/`](show/ident/)
- 前身 POC：[`clarencechien/ttspoc`](https://github.com/clarencechien/ttspoc) 的 `podcast/`（工具與 EP01 從 `799872e` 搬來）

## 上架狀態
- 網站與 feed：<https://podcast.ai-apps.work>，feed `https://podcast.ai-apps.work/feed.xml`（GitHub Pages，見 `PIPELINE.md` §5 的過渡方案）
- 擁有者信箱：`podcast@ai-apps.work`（Cloudflare Email Routing 轉寄）
- **Spotify**：已上架（2026-11-06），<https://open.spotify.com/show/56y20c8Jscmnjajo8vUIzw>
- **Apple Podcasts**：已上架（2026-11-06），<https://podcasts.apple.com/tw/podcast/id6831404475>（節目 ID `6831404475`；網址中間的名稱 Apple 不看，只認 ID）
- 其他平台：KKBOX、Podcast Index 還沒送；YouTube 品牌頻道已建好，新頻道要滿 24 小時才能送 RSS（2026-11-06 試過，顯示「Your account is too new」；選項有出現，代表台灣可以用 RSS 匯入）
- Apple Podcasts Connect 帳號：Account Name 用品牌名「Debug After Dark」、類型 Individual（以後若開付費訂閱，個人帳號可能會顯示真實姓名，要再確認）。Podcasts Connect 的 API key 是給託管平台發佈付費內容（Delegated Delivery）用的，不能拿來送審免費節目
- 網站功能：每集一頁（`/ep05/` 這種短網址，有各自的分享預覽）、每集「分享這一集」按鈕；在 LINE、Facebook、Instagram 等 app 內建瀏覽器打開時提示改用瀏覽器（LINE 另有一鍵 `openExternalBrowser=1`）；Media Session 讓鎖定畫面顯示集名與封面，可倒退 15 秒、快轉 30 秒（`tools/build_site.py`）
- 數據：各平台**各算各的**，數的東西也不一樣（下載、播放、瀏覽），不能直接相加（2026-11-06 整理）

  | 收聽或造訪管道 | 誰統計 | 數的是什麼 |
  |---|---|---|
  | Apple Podcasts | SoundOn Prefix（app 照 feed 網址下載，經過 Prefix）＋ Podcasts Connect 的 Analytics | 下載；播放、聽眾、追蹤、聽到哪裡 |
  | 其他 podcast app、手動貼 feed 的人、SoundOn 播放頁 | SoundOn Prefix（`show.json` 的 `enclosure_prefix`，先經過 SoundOn 再 302 回我們的檔案） | 下載 |
  | Spotify | Spotify for Creators 後台（Spotify 從自己的伺服器播，SoundOn 大多看不到） | 播放、聽眾 |
  | 我們的網站（首頁、單集頁） | **Cloudflare Web Analytics**（2026-11-06 加上，`show.json` 的 `cf_web_analytics_token`） | 網頁瀏覽、來源（例如 LINE、Facebook）、國家、裝置；不用 cookie。**不數播放**，網站播放器不經過 Prefix |
  | YouTube（之後） | YouTube Studio | 觀看 |

  - Apple 的收聽會同時出現在 SoundOn（下載）和 Podcasts Connect（播放），兩邊不能相加。
  - Cloudflare Web Analytics 在 Cloudflare 後台的「Analytics & Logs → Web Analytics」，站點 `podcast.ai-apps.work`。因為這個子網域的 DNS 是 DNS only（灰雲），Cloudflare 沒辦法自動插入，改由 `tools/build_site.py` 的 `beacon()` 在每一頁放統計程式；token 本來就放在公開網頁裡，不是密鑰。
- 贊助連結：<https://portaly.cc/clarencech/support>（`show.json` 的 `support_url`），見下面的「Portaly 現況」

## 上架平台（2026-11-05 整理）

### 建議的順序（Apple、Spotify 已上架，2026-11-06）
| 順序 | 平台 | 怎麼上 | 費用 | 審核 | 備註 |
|---|---|---|---|---|---|
| 1 | Apple Podcasts | 用 Apple 帳號登入 Podcasts Connect，貼 feed 網址 | 免費（付費訂閱方案另計，非必要） | 通常幾天 | 很多第三方 app（Overcast、Pocket Casts 等）也從 Apple 目錄找節目。內容規範要求 AI 合成聲音在**內容與資料裡都要明顯揭露** |
| 2 | Spotify | creators.spotify.com →「Find an existing show → Somewhere else」，貼 feed；8 位數驗證碼寄到 feed 的信箱 | 免費 | 通常幾小時 | 驗證碼寄到 `podcast@ai-apps.work` |
| 3 | KKBOX | 用 KKBOX 帳號綁 feed（一個帳號只能綁一個節目） | 免費 | 約 1–3 個工作天 | 台灣本地平台；找到的資料多是 2020–2023 年，以 KKBOX 官方頁為準 |
| 4 | Podcast Index | podcastindex.org 貼 feed | 免費 | 幾分鐘 | 開放目錄，Podcast Addict、Fountain 等從這裡抓 |
| 5 | YouTube | YouTube Studio：建立 → 新增 Podcast → 提交 RSS feed，驗證碼寄到 feed 的信箱 | 免費 | 不一定 | RSS 匯入只開放部分國家，**台灣在不在名單上還沒確認**；YouTube 對量產 AI 內容最嚴，放最後 |
| 可選 | Amazon Music | Amazon Music for Podcasters 提交 feed | 免費 | 幾天 | 台灣用的人少 |

SoundOn 已經有我們的播放頁，不用另外申請。送審都要登入節目擁有者自己的帳號，由人操作。

### feed 裡的節目說明格式（2026-11-06）
- **問題**：說明原本是純文字加換行。Apple、Spotify 會把說明當 HTML 顯示，換行被吃掉，整段黏在一起；只有 SoundOn 照原樣保留換行。
- **第一次改（只用 HTML）**：段落用 `<p>`，breakpoint 用 `<ol>` 編號清單，網址變成連結。Apple 顯示正確。但 Spotify 網頁版會把標籤全部拿掉、拿掉處不留空格，結果編號不見、字黏在一起。
- **現在的做法**（`tools/feed.py` 的 `notes_html`）：
  - `<content:encoded>`：Apple 優先讀這個，保留完整 HTML 和編號清單。
  - `<description>`：Spotify 讀這個。編號直接寫成文字「1. …」，每個 `<br>`、`</p>` 後面都加真正的換行。會顯示 HTML 的平台照段落顯示，會拿掉標籤的平台也還留著編號和換行。
- **檢查結果**：
  - feed 結構逐集都正常：8 集都有兩種說明，HTML 標籤都有關好，guid 不重複，音檔大小跟伺服器上的檔案完全一致。
  - W3C 驗證器判定有效、0 錯誤。2 個警告不影響：一個是自訂的 `imitator:` 命名空間，另一個是 description 含 HTML，Apple 的規格允許。
- **平台更新是一集一集來的**：Apple、Spotify 不會一次把所有集數換成新格式，同一時間有的集新、有的集舊是正常的。2026-11-06 檢查時，Apple 的 EP05、EP06 已經換成新格式，EP04、EP07 還是舊的。想快一點，可以在 Podcasts Connect 按 RSS Feed 旁的 **Refresh**。Apple 平常也會自己定期重抓，頻率不固定。
- **SoundOn**：重抓後也會換成新格式，要確認沒有把 `<p>` 這種標籤直接顯示出來。
- **Apple 網頁版不顯示說明裡的連結**：說明裡的網址只顯示成文字，不能點。能點的只有說明下方的「單集網頁」按鈕，它來自每集的 `<link>`。目前 `<link>` 連到 imitator 的原始報告，2026-11-06 決定維持這樣，不改成我們的單集頁。iPhone 的 Podcasts app 通常會把說明裡的網址變成可以點的連結，待用手機確認。
- **Apple 各集的更新進度**（2026-11-06，跳過快取直接查，回應是 `x-cache: MISS`，所以不是快取）：EP01、EP03、EP05、EP06 已是新格式，EP02、EP04、EP07 還是舊的，EP00 看不出差別。feed 裡這幾集的內容跟已更新的集數一樣，只是 Apple 還沒處理到。超過兩天還沒更新，就去 Episodes 頁看狀態，或聯絡 Apple 客服。

### 送審前要決定的
- **`itunes:author`**：目前是「深夜 Debug」，會在 Apple、Spotify 公開顯示成創作者。feed 的 owner 名稱與 copyright 也都是「深夜 Debug」，沒有本人名字。
- **每集口播 AI 揭露**：節目層與每集說明都有，EP00 有口播；其他集要不要在片尾加一句，待決定。
- **下載數會分散**：Spotify、YouTube 會自己存一份音檔，從那裡播的不經過 SoundOn Prefix，要到各平台後台看；只有 Apple 與直接讀 feed 的 app 會被 SoundOn 統計。
- **流量**：GitHub Pages 建議每月 100 GB，一集約 8–10 MB，約一萬次下載內都夠；超過就把 mp3 搬到 Cloudflare R2。

### 不想被連到本人
三個平台的公開頁都只顯示 feed 或頻道設定裡的名稱，帳號本人不公開（營利時要給平台真實資料，但不公開）。YouTube 用**品牌帳號頻道**，和個人頻道分開：觀看紀錄、訂閱、留言各自獨立，切換用右上角頭像的「切換帳戶」；用節目身分留言前先確認頭像。
目前還會連到本人的地方：
- 贊助網址 `portaly.cc/clarencech/support`（feed 和網站都有）
- 這個 repo 是公開的
- 部分 imitator 報告有署名

EP02 說明裡的個人 GitHub 連結已在 2026-11-05 拿掉。

### YouTube 不能當其他平台的來源
YouTube 用 RSS 匯入時，是把我們 feed 裡的音檔**複製一份**放在 YouTube／YouTube Music，只給它自己的聽眾用。它不提供 RSS，也沒有可以直接下載的音檔網址，所以 Apple、Spotify、KKBOX 這些讀 RSS 的平台**不能反過來引用 YouTube**；而且 YouTube 是持續從我們的 feed 抓新集數，我們的 feed 不在，它也收不到新的一集。
要離開 GitHub Pages 時，可以選：
- **Cloudflare R2 放音檔，加上 Pages 或 Workers 放網站和 feed**：產線不用改，用量小時接近免費。這是建議的做法。
- **SoundOn 託管**
- **Spotify for Creators 託管**

feed 網址在自己的網域上，搬家只改指向，聽眾與各平台不受影響。

### 多語版在各平台怎麼放
各平台都是「一份 feed＝一個節目」，同一個節目不能匯入多份 feed。所以每種語言一份 feed：
- feed 路徑：`/feed.xml`（中文）、`/en/feed.xml`、`/ja/feed.xml`。
- Apple、Spotify：同一個帳號送三份 feed，就是三個獨立節目。Apple 的「頻道」可以把幾個節目放在一起，但它跟付費訂閱方案一起設定，要做時再確認條件。
- YouTube：同一個品牌頻道裡分別匯入三份 feed，成為三個 Podcast 播放清單。另一條路是 YouTube 的「多語言音軌」，一支影片放三種語言的音軌，但只能用上傳影片的方式，RSS 匯入做不到。
- KKBOX：一個帳號只能綁一份 feed。
- 每份 feed 的身分要分開：`podcast:guid`、標題、語言（`zh-tw`、`en`、`ja`）、封面文字各自設定；擁有者信箱可以共用。
- 各版在說明與網站上互相連結。試作與決定見 `PIPELINE.md` §8 第 8 項。

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
- 上架平台：[YouTube：Deliver podcasts using an RSS feed](https://support.google.com/youtube/answer/13525207)、[YouTube RSS 可用地區](https://support.google.com/youtube/answer/14106258)、[Spotify：Adding a new show](https://support.spotify.com/us/creators/article/adding-a-new-show)、[Apple Podcasts Content Requirements](https://podcasters.apple.com/support/891-content-and-subscription-guidelines)、[KKBOX for Podcasters（INSIDE）](https://www.inside.com.tw/article/20511-kkbox-for-podcasters)、[Firstory：上架到各個收聽平台](https://intercom.help/firstory/zh-TW/articles/12000138-%E4%B8%8A%E6%9E%B6%E5%88%B0%E5%90%84%E5%80%8B%E6%94%B6%E8%81%BD%E5%B9%B3%E5%8F%B0)
- GitHub Pages：[GitHub Pages limits（禁止的用途）](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)
