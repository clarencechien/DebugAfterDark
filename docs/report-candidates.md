# imitator 2026 報告對照表與待製作清單

更新：2026-11-21。共 154 份 2026 年的報告：已做 47、製作中 4、推薦 20、可做 32、不做 51。

這份是 podcast 唯一的選題與待製作清單：哪幾集做到哪一步、下一批做哪些報告。YouTube 頻道上的待辦（舊片改標題、補 AI 標示、縮圖、上傳 Action）在 `youtube/todo.json`，整體順序在 [`strategy.md`](strategy.md)，這裡不重複。

**什麼時候更新**：每集開工、定稿上架、影片版或 Short 上傳時改「製作中」；上架後搬到「已做」，再從「推薦的下一批」補上來。

- **來源**：imitator 的 `archive/report/`，加上只用 curl 推、不在 archive 的公開報告（`GET /v1/a` 列出，要 `IMITATOR_TOKEN`）。日期是報告的發佈或最後更新日；10-02 那一批是搬家日。
- **狀態**：已做（集數）、製作中（集數）、推薦（下一批）、可做、不做（工具、mockup、旅遊、私人、自家產品、轉載、內部筆記、教材）。
- **連結**：slug 一律用連字號，imitator 會把檔名的底線換成連字號。雲端容器抓得到公開報告的 `/r/<slug>`。
- **選題時**：先看推薦表的鉤子方向，再照 [`docs/hooks.md`](hooks.md) 定標題和第一段。收聽數據看，財經和台灣生活題材聽的人比較多。

## 製作中

狀態：✅ 完成、🔶 進行中、⬜ 還沒做。EP38、EP39 在 Clarence 原本的 session 收尾；EP40 起每集在專案裡開一個 thread 做。

| 集數 | 報告 | 音檔（第 1–8 步） | 試聽、定稿 | 進 feed | 影片版（第 9 步） | Short | 備註 |
|---|---|---|---|---|---|---|---|
| EP36 | [`credit-line-changed`](https://imitator.ai-apps.work/r/credit-line-changed) | ✅ | ✅ | ✅ 11/20 | 🔶 第一支影片版，做完手動上傳；RSS 匯入的那支已改私人 | ⬜ | 影片版實驗，見 `youtube/experiments.json` |
| EP37 | [`nameless-made-famous`](https://imitator.ai-apps.work/r/nameless-made-famous) | ✅ | ✅ | ✅ 11/20 | ⬜（YouTube 用 RSS 版） | ✅ 11/20 `K6RKggrOqVo` | 11/27 看 Short 成效 |
| EP38 | [`who-is-using`](https://imitator.ai-apps.work/r/who-is-using) | ✅ | ✅ 11/20 | ✅ 11/21 | ⬜ | ⬜ | 分層讀法番外一（報告 11/21 改名「番外一」並更新，節目用的是 11/19 版）；章節時間已用 `tools/chapters.py` 修正；`youtube` 標題與縮圖字已寫 |
| EP39 | [`layers-of-llm`](https://imitator.ai-apps.work/r/layers-of-llm) | ✅ | ✅ 11/20 | ✅ 11/21 | ⬜ | ⬜ | 分層讀法上篇（上：EP38）；同上 |
| EP40 | [`house-rules`](https://imitator.ai-apps.work/r/house-rules) | ✅ | ✅ 11/20 | ⏰ 11/22 08:00 排程 | ⬜ | ⬜ | 韓劇的中間層番外（上：EP37）；插隊在不讀之後之前 |
| EP41 | [`gdp-service-ledger`](https://imitator.ai-apps.work/r/gdp-service-ledger) | ✅ | ✅ 11/20 | ⏰ 11/22 08:01 排程 | ⬜ | ⬜ | 原推薦 #5，插隊；用台股開場，目標聽眾是沒吃到 AI 紅利的人；報告 v0.2 資料到 11/20 |
| EP42 | [`no-read-1`](https://imitator.ai-apps.work/r/no-read-1) | ✅ | ✅ 11/21 | ⏰ 11/23 08:00 排程 | ⬜ | ⬜ | 不讀之後 上篇；標題「Clean Code 的作者不讀 AI 的程式碼，那他讀什麼？」；Gemini 月上限，Gemini 那一半的驗收經 Clarence 同意跳過 |
| EP43 | [`no-read-2`](https://imitator.ai-apps.work/r/no-read-2) | ✅ | ✅ 11/21 | ⏰ 11/23 08:01 排程 | ⬜ | ⬜ | 不讀之後 下篇（上：EP42）；標題「一個人一個月三千個 PR，她還看程式碼嗎？」；Gemini 月上限，Gemini 那一半的驗收經 Clarence 同意跳過 |
| EP44 | [`no-read-3`](https://imitator.ai-apps.work/r/no-read-3) | ✅ | ✅ 11/21 | ⏰ 11/24 08:00 排程 | ⬜ | ⬜ | 不讀之後 第三篇（上：EP42、EP43）；標題「檢查交給機器，檢查錯了誰知道？」；兩篇來源是廠商寫自己的產品，節目有說；Modal 額度用完，挑選在本機 CPU |
| EP45 | [`no-stock-in-farebox`](https://imitator.ai-apps.work/r/no-stock-in-farebox) | ✅ | ✅ 11/21 | ⏰ 11/24 08:01 排程 | ⬜ | ⬜ | 核票 v0.1（資料至 11/20）；標題「台股跌了快三成，機票飯店會變便宜嗎？」；Modal 額度用完，挑選在本機 CPU；12 月新數字出來後原文會出 v0.2，可考慮補一集 |
| EP47 | [`who-is-using-micro`](https://imitator.ai-apps.work/r/who-is-using-micro) | ✅ | ✅ 11/22 | ⏰ 11/25 08:01 排程 | ⬜ | ⬜ | 分層讀法番外二（上：EP38、EP39）；標題「AI 月費一百美元，到底買到多少？」；原文作者是 Claude、比較的廠商包括 Anthropic，節目有說；v0.3 資料至 11/20；Modal 額度用完，挑選在本機 CPU |

「進 feed」是 `episode.json` 設成 `status: final` 並填 `published`，merge 到 main 就會發佈（先給 Clarence 看再 commit）。EP36、EP37 的影片版和 Short 做完就搬到「已做」。

### 每集的步驟

開工時把這張複製到那一集的 thread 當進度表。細節在 [`recipe.md`](recipe.md)（第 0–8 步）和 [`video.md`](video.md)（第 9 步）。

| 步驟 | 誰 | 完成的樣子 |
|---|---|---|
| 1. 選題、草稿、素材、`episode.json`（含 `youtube` 欄位，照 [`hooks.md`](hooks.md)） | agent | `draft.json`、`sources/` |
| 2–3. 改寫、逐段核對 | agent | `script.json`，修正記在 `manual_edits` |
| 4–7. 語音、挑選、母帶、驗收 | agent | `<ep>.mp3`、`qa/` 全部通過 |
| 8. 交付：`package_episode.py`，章節時間用 `tools/chapters.py` | agent | `episode.json` 有長度、bytes、sha256、章節 |
| 試聽 | **Clarence** | 說可以，或指出要重錄的段落 |
| 上架：`status: final`、填 `published` | agent，Clarence 同意後 commit | 網站與 feed 出現這一集；YouTube 約一天內用 RSS 匯入 |
| 9. 影片版（`make_video.py`，還在用 EP36 開發） | agent | `video/` 產出，Clarence 看過預覽與縮圖 |
| Short：cold open 剪成 Short（`make_short.py`） | agent；上傳目前手動 | 上傳後記在 `youtube/experiments.json` |
| YouTube：補 AI 標示（RSS 匯入不會自動標）、核對標題與章節 | 見 `youtube/todo.json` | — |

### 庫存（不用新做音檔）

- **Shorts**：EP01 到 EP36 都有 cold open，可以用 `make_short.py` 批次產出；API 稽核通過前每天手動上一支（`strategy.md` 第 2 條線）。
- **舊集改標題與說明欄**：屬於 YouTube 包裝，在 `youtube/todo.json` 追蹤。

## 推薦的下一批

依建議順序排。**排法（11/21 Clarence 定）：五天 10 集一個單位，不分平日假日。四天放 AI 或比較難的題目（8 集），一天放錢的題目（2 集）；錢有上下篇的同一天一起出。**錢大約佔 1/5。理由和數據在 [`strategy.md`](strategy.md)「選題比例」。

第一個單位因為上架時間實驗拉長成 7 天（11/25–12/1）：EP41、EP45 已經讓早上組（11/21–27）有 2 集錢，把錢日放在 12/1，晚上組（11/28–12/4）也剛好 2 集。之後照五天一輪：錢日 12/6、12/11、12/16……

11-21：新增保險課下篇、番外和 Meta 詐騙上下篇（取代 5 月版 `meta-lawsuit`）；從可做移上來 8 篇 AI 題目、2 篇退休題。預排：#1–14 → EP46–EP59（11/25–12/1，錢日 12/1 是 EP58、EP59），#15–16 → EP68–EP69（錢日 12/6），#17–18 → EP78–EP79（錢日 12/11）。EP60–67、EP70–77 從可做挑 AI 或比較難的題目，開工時再定。標題是方向，不是定稿。製作時間是從開工到試聽版的估計，算法見下一節。

| # | 類別 | 報告 | 標題方向 | 鉤子 | 製作時間（估） | 估法 |
|---|---|---|---|---|---|---|
| 1 | 其他 | [順便學會的，現在要另外練 — 知行筆記 · 實作篇](https://imitator.ai-apps.work/r/practice-on-purpose)（11-17） | 《超速學習》真的超速嗎？有了 AI，基本功還要不要練 | 流行說法對上資料：書名把「強度」譯成了「速度」；讀程式和除錯這類基本功要另外排時間練。接回 EP30、EP31 | 40–50 分鐘 | 約五千一百字、兩百多個英文詞（書名、人名）；提到的〈人人都是建築師〉在可做清單，可以順便帶一句 |
| 2 | AI | [月租沒變，單價在改 — 分層讀法番外二](https://imitator.ai-apps.work/r/who-is-using-micro)（11-21） | 月費一百美元，到底買到多少？ | 反差：同一個 100 美元方案，用滿可抵 4,640 到 5,725 美元的量，額度沒公布而且一直在改；接 EP38、EP39 | 60–75 分鐘 | 約九千一百字、一千六百個英文詞（方案、模型名），Breeze 錯誤率很可能過線，要多補錄；報告自己寫明作者是 Claude、比較的廠商包括 Anthropic，節目要講出來；v0.3 |
| 3 | AI | [一個指標個案，和一條隔離線 — Qwen3.8 沙箱事件查核報告](https://imitator.ai-apps.work/r/qwen-index-case)（10-27） | AI 在沙箱裡，做了一件它說不會做的事 | 真實個案＋懸念；通報者是競爭對手，網路摘要少講了幾件事 | 35–45 分鐘 | 約四千四百字、四百多個英文詞（模型名、公司名） |
| 4 | AI | [同一句話，換成簡體，答案就翻面](https://imitator.ai-apps.work/r/jevlike-tw-script)（10-12） | 同一句台灣是一個國家，繁體說對，簡體說錯 | 反差＋你已經在用了；八十四題裡三十五題翻面。題材敏感，只講測到的事 | 45–60 分鐘 | 約五千三百字、近八百個數字，改寫最容易出錯；敏感題材要逐句核對措辭 |
| 5 | AI | [每一層，都要能說不 — Zeabur 之後的 AI 平台地形](https://imitator.ai-apps.work/r/ai-platform-2026-10)（10-17） | Zeabur 要關了，你的服務搬去哪？ | 時事＋具體案例：台灣平台年底關閉當切點，問核心資產在哪一層；上下篇同一天 | 40–50 分鐘 | 約三千六百字、九百個英文詞（平台名） |
| 6 | AI | [帳單上印著誰的名字 — AI 平台地形 下篇](https://imitator.ai-apps.work/r/ai-platform-2026-11)（11-05） | AI 幫你按下購買，帳單上寫的是誰？ | 接上篇：agent 替你比價、下單之後，Booking、Amazon、DoorDash 這些平台還剩什麼 | 55–70 分鐘 | 約六千二百字、一千二百個英文詞，偏難；跟上篇一起做最划算 |
| 7 | AI | [同一個工具，為什麼結果差這麼多？ — LLM 使用者差異研究綜述](https://imitator.ai-apps.work/r/ai-amp-or-mir)（07-23） | 同一個 AI，為什麼別人用得比你好？ | 流行說法對上研究：「放大器」「鏡子」「新模型降智」各對一角；鏡子系列第一篇，跟下一篇同一天 | 40–50 分鐘 | 約六千四百字、近七百個英文詞；7 月寫的，模型名和數字要更新到現在 |
| 8 | AI | [工具在手，怎麼用才算數？ — Claude Code 使用指南（下篇）](https://imitator.ai-apps.work/r/ai-amp-or-mirror-2)（07-23） | AI 寫得越來越快，你的價值要放在哪？ | 接上篇：生成趨近免費，價值在鑑別力，鑑別力要寫成 repo 裡可執行的工件 | 30–40 分鐘 | 約三千八百字、五百個英文詞；工具名多，要換成白話；7 月寫的 |
| 9 | AI | [測試在測什麼？ — 可測的、不可測的、與兩者之間的搬運（第三篇）](https://imitator.ai-apps.work/r/llm-testing-essence)（07-24） | AI 寫的程式，測試到底在測什麼？ | 接 EP42–44 不讀之後：Uncle Bob 不讀程式碼只讀指標，那測試在測什麼；鏡子系列第三篇 | 40–50 分鐘 | 約五千九百字、四百個英文詞；開頭可以接回不讀之後三集 |
| 10 | AI | [劍客、小孩，與一面歪掉的鏡子 — 2026H2 Agent 生存指南](https://imitator.ai-apps.work/r/agent-survival-2026h2)（10-04） | 反差：同樣的工具、同樣的模型，結果差很多；鏡子系列延伸篇，跟 EP11 主題接近，要用新的角度開場 | 反差：同樣的工具、同樣的模型，結果差很多；跟 EP11 主題接近，要用新的角度開場 | 75–90 分鐘 | 一萬二千字、近兩千個英文詞，最長；要大幅刪減成一集，或拆上下 |
| 11 | AI | [人人都是建築師，那誰來簽證 — AI 時代的程式設計師](https://imitator.ai-apps.work/r/everyone-an-architect)（10-05） | 流行說法對上比喻：「程式設計師會變成建築師」，三隻小豬也都是建築師；鏡子系列第三篇，實作篇也提過 | 流行說法對上比喻：「程式設計師會變成建築師」，三隻小豬也都是建築師；實作篇提過這篇，可以接著做 | 50–60 分鐘 | 約六千四百字、九百多個英文詞（人名、工具名），Breeze 錯誤率要注意 |
| 12 | AI | [你連的是什麼線 — 從一百萬則通知的假議題，到 AI 時代的架構師](https://imitator.ai-apps.work/r/which-wire)（09-22） | 面試題「送一百萬則通知」，一百萬是假的 | 反差：一篇面試文被追問六輪，題目本身先站不住；跟上一集同一條「AI 時代的架構師」線 | 45–55 分鐘 | 約七千字、三百多個英文詞；技術詞要換成白話 |
| 13 | **錢** | [中國政府給保險公司補錢，等於要爆炸嗎？ — 保險課 上篇](https://imitator.ai-apps.work/r/japan-insurer-bailout-report-1)（11-21 二校 v0.2） | 國家給保險公司補錢，是要爆炸了嗎？ | 時事問句，答案是「不是，墊子變薄了先加厚」；這版補了數字和出處，訂正三處。先講清楚是中國的事、金額是人民幣 | 35–45 分鐘 | 約五千五百字、白話稿、幾乎沒有英文，最好做；跟下篇同一天出 |
| 14 | **錢** | [保險公司倒了，帳單寄給誰？ — 保險課 下篇](https://imitator.ai-apps.work/r/japan-insurer-bailout-report-2)（11-21） | 保險公司倒了，你的保單誰來賠？ | 聽眾自己的處境：洞不會自己消失，保戶、同業、接手公司、納稅人四種分攤，日韓台中各挑一種；台灣那一格聽眾最在意 | 40–50 分鐘 | 約六千字、幾乎沒有英文；四國幣別不互換，改寫時盯數字和幣別 |
| 15 | **錢** | [一筆被騙的錢，經過幾隻手 — Meta 詐騙 上篇](https://imitator.ai-apps.work/r/meta-lawsuit-1)（11-21 v0.4） | 你被騙的錢，Meta 收了幾手？ | 聽眾自己的處境＋具體數字：跟著一筆被騙的錢走過 Meta 三個 app、LINE 和銀行；取代 5 月版 `meta-lawsuit`。訴訟還沒判，講法要中性 | 45–55 分鐘 | 約六千八百字、近兩百個英文詞；公司名多，事實要逐句核對 |
| 16 | **錢** | [知道這一批有假的，算不算知道 — Meta 詐騙 下篇](https://imitator.ai-apps.work/r/meta-lawsuit-2)（11-21 v0.1） | 平台知道有詐騙廣告，算不算幫兇？ | 接上篇留下的那一題：各國法院和立法者蓋了四種章；台灣的做法可以當結尾 | 35–45 分鐘 | 約四千四百字；法律用語要換成白話，不要下判決式的結論 |
| 17 | **錢** | [活太久這件事，誰來保？ — 保險課 番外](https://imitator.ai-apps.work/r/japan-insurer-bailout-report-extra)（11-21） | 聽眾自己的處境：錢比命先用完、一場大病打穿存款；國家開的保險不會倒、只會改數字。接回退休三部曲（EP24–26），跟 VT 退休那集同一天 | 聽眾自己的處境：錢比命先用完、一場大病打穿存款；國家開的保險不會倒、只會改數字。接回退休三部曲（EP24–26） | 40–50 分鐘 | 約六千二百字、少量英文；開頭可以用「上兩集」接回保險課 |
| 18 | **錢** | [持有 VT 幾歲能退休](https://imitator.ai-apps.work/r/bysq-report-twvt)（09）＋[40 歲開始，退休金該怎麼算？](https://imitator.ai-apps.work/r/forties)（08-18） | 手上一千萬全買 VT，幾歲可以退休？ | 流行說法對上試算；兩篇都短，合成一集 | 30–40 分鐘 | 兩篇加起來約四千字；跟 EP25（退休地板）重疊，要先講清楚差在哪；錢的後備 |
| 19 | **錢** | [熄燈的窗 · 台灣少子化與房價](https://imitator.ai-apps.work/r/birthrate-vs-housing)（08-17） | 生的人變少了，房價為什麼還在漲？ | 流行說法對上資料 | 先評估 | 原文是用程式畫的八頁投影片，網頁文字抓不出內容（只有幾十個字），要先把每頁的數字取出來才知道夠不夠一集 |

**兩邊的來源都會用完**：
- 錢：三個錢日（12/1、12/6、12/11）用掉 #13–18，之後只剩 #19（少子化與房價，還要先評估）。12/16 的錢日起要有新報告，五天兩集，平均每週約 3 集，報告是上下篇的話每週要補約 1.5 組。
- AI：五天要 8 集，一週約 11 集。推薦表的 12 篇用到 11/30，可做剩下 32 篇裡能用的估一半，大約撐到 12/10 前後。這一邊比錢更快見底，12/4 檢查點要一起看。

## 製作時間怎麼估

從開工到試聽版、agent 這一端的時間（git 紀錄）。不含試聽：一集大約十分鐘，聽完說可以之後，定稿上架再五分鐘。

| 集數 | 開工到試聽版 | 備註 |
|---|---|---|
| EP30＋EP31 | 約 40 分鐘（兩集一起） | 兩集的改寫同時跑；音高跳動第一次都超過，各補錄 7 段 |
| EP32＋EP33 | 約 40 分鐘（兩集一起） | 同上；EP33 補錄 8 段 |
| EP36＋EP37 | 約 60 分鐘（兩集一起），試聽後改一句再 15 分鐘 | 改寫把數字改模糊的段落多，各有 3 到 4 段照草稿重寫；韓國人名、公司一律中文念法；抖動補錄 EP36 3 段、EP37 4 段（其中 3 段補兩輪）；EP36「你猜怎麼著」是大陸說法，聽完改掉重錄 |
| EP34＋EP35 | 約 60 分鐘（兩集一起） | 中間同時做 Colab 對 Modal 的比較（docs/colab-vs-modal.md）；各補錄 1 段 |
| EP28、EP29 | 各約 60–90 分鐘 | 單集，EP28 中途改了標題；「當物／當金」「分紅公式」聽錯，各重錄 3 到 8 段 |

一集的時間大概這樣分（`docs/recipe.md` 各步驟的實測）：

| 步驟 | 時間 |
|---|---|
| 讀報告、寫草稿與素材 | 10–15 分鐘 |
| 改寫（三個候選） | 6–7 分鐘，兩集可以同時跑 |
| 逐段核對、改回原文 | 10–15 分鐘，數字越密越久 |
| 生成語音與挑選 | 3–4 分鐘 |
| 混音與驗收 | 3–4 分鐘 |
| 補錄（音高跳動超過 0.23、詞被聽錯） | 5–15 分鐘，最常見的拖延 |

一集照表加起來是 40–60 分鐘。兩集一起做時，改寫、語音和挑選的等待會重疊，所以兩集跟一集差不多，上下集一起做最划算。

會拉長時間的：英文詞多（Breeze 錯誤率過線，要改說法或重錄）、數字密（改寫最常改錯數字）、敏感題材（要逐句核對）、原文太短（要補資料）、原文不是文字（投影片、圖表）。

## 系列與成對

| 系列 | 報告 | 怎麼做 |
|---|---|---|
| 韓劇的中間層 | `credit-line-changed`、`nameless-made-famous` | 已做：EP36、EP37 |
| 分散筆記 | `winners-win-themselves`、`not-extra-money` | 已做：EP34、EP35 |
| 不讀之後 | `no-read-1`、`no-read-2`、`no-read-3` | EP42、EP43 製作中，第三篇預排 EP44；三集：Uncle Bob 改讀規格、Lauren Tan 改看證據、檢查本身要校正（Claude Code 團隊的做法）；取代前版 `uncle-bob` |
| 知行筆記 | `dankoe-one-day`、`knowing-is-dear`、`practice-on-purpose` | 前兩篇已做（EP30、EP31）；實作篇可以當第三集，開頭用「上一集」接回 EP31 |
| Slotbound 案卷 | `slotbound-case`、`slotbound-case-2` | 已做：EP32、EP33 |
| 分層讀法 | `who-is-using`（番外一）、`who-is-using-micro`（番外二）、`layers-of-llm`（上篇）、`no-exchange-rate`（下篇） | 已做：EP38（番外一）、EP39（上篇，併入下篇的三本帳）；番外二在推薦表，可以單獨一集，開頭接回 EP38、EP39 |
| jevlike | `jevlike-tw-script`、`jevlike-primer`、`jevlike-audio` | 只做繁簡那篇；另外兩篇是自家實驗，偏技術 |
| 架構系列 | `agent-arch` 到 `agent-arch-6`、`test-agent-arch` | 可做，工程師向；挑一兩篇合成一集 |

## 已做（依集數）

| 集數 | 節目標題 | 報告 | 狀態 |
|---|---|---|---|
| EP00 | 嘿，還醒著嗎？ | — | 上架 |
| EP01 | 記住了第一招，漏掉了第五招 | [`fifth-move`](https://imitator.ai-apps.work/r/fifth-move) | 上架 |
| EP02 | 第五招的實驗：跑從來不是問題，看才是 | [`harness-probe-report`](https://imitator.ai-apps.work/r/harness-probe-report) | 上架 |
| EP03 | 每加一分，就扣一分 | [`funclass-cost-case-study`](https://imitator.ai-apps.work/r/funclass-cost-case-study) | 上架 |
| EP04 | 帳單響了之後，你手上有沒有地圖 | [`bill-to-code-map`](https://imitator.ai-apps.work/r/bill-to-code-map) | 上架 |
| EP05 | 撞礁是遲早的，會不會沉才是問題 | [`reef-chart`](https://imitator.ai-apps.work/r/reef-chart) | 上架 |
| EP06 | 同一隻鬼，換了五張臉 | [`ghost-story-five-faces`](https://imitator.ai-apps.work/r/ghost-story-five-faces) | 上架 |
| EP07 | 台灣錢淹腳目，這次淹在別人腳下 | [`taiwan-money-again`](https://imitator.ai-apps.work/r/taiwan-money-again) | 上架 |
| EP08 | 無限的是 token，有限的是驗收 | [`unlimited-token-report`](https://imitator.ai-apps.work/r/unlimited-token-report) | 上架 |
| EP09 | 一百萬顆 CPU，是用來驗的 | [`million-cores-report`](https://imitator.ai-apps.work/r/million-cores-report) | 上架 |
| EP10 | 還剩幾天：Huntley 的賭注 | [`huntley-18-months`](https://imitator.ai-apps.work/r/huntley-18-months) | 上架 |
| EP11 | 八成要刪掉：回頭看 2026 | [`agent-guide-2026h2`](https://imitator.ai-apps.work/r/agent-guide-2026h2) | 上架 |
| EP12 | 你聽過的台股必勝法 | [`tw-stock-winner`](https://imitator.ai-apps.work/r/tw-stock-winner) | 上架 |
| EP13 | 公司發可轉債，是利多還是警訊？ | [`cb-story`](https://imitator.ai-apps.work/r/cb-story) | 上架 |
| EP14 | 門沒換，只是敲門的變多了 | [`91app-breach-findings`](https://imitator.ai-apps.work/r/91app-breach-findings) | 上架 |
| EP15 | 不是被打敗，是被賣掉的 | [`japan-white-goods-transfer`](https://imitator.ai-apps.work/r/japan-white-goods-transfer) | 上架 |
| EP16 | 加薪留不住 | [`delivery-pay-floor`](https://imitator.ai-apps.work/r/delivery-pay-floor) | 上架 |
| EP17 | 野心的單位變小了 | [`ambition-unit`](https://imitator.ai-apps.work/r/ambition-unit) | 上架 |
| EP18 | 「自研」是一個光譜 | [`ziyan-guangpu`](https://imitator.ai-apps.work/r/ziyan-guangpu) | 上架 |
| EP19 | 錢不重要之後，誰握著產能 | [`ownership-token`](https://imitator.ai-apps.work/r/ownership-token) | 上架 |
| EP20 | AI 熄火了嗎？四個月後的複檢 | [`ai-premium-tw-report-2026-11`](https://imitator.ai-apps.work/r/ai-premium-tw-report-2026-11) | 上架 |
| EP21 | 抓得到的，都不是人味 | [`catchable-not-human`](https://imitator.ai-apps.work/r/catchable-not-human) | 上架 |
| EP22 | 催你學的，已經內建了 | [`fomo-flyer`](https://imitator.ai-apps.work/r/fomo-flyer) | 上架 |
| EP23 | 門牌寫著內部的門 | [`91app-inner-doors`](https://imitator.ai-apps.work/r/91app-inner-doors) | 上架 |
| EP24 | 月租六萬住六千萬，你是盤子嗎？ | [`rent-ratio-or-scale`](https://imitator.ai-apps.work/r/rent-ratio-or-scale)、[`bysq-report-rent-vs-buy`](https://imitator.ai-apps.work/r/bysq-report-rent-vs-buy) | 上架 |
| EP25 | 一千萬夠不夠，先問地板有多硬 | [`retire-floor-basics`](https://imitator.ai-apps.work/r/retire-floor-basics)、[`retire-floor-playbook`](https://imitator.ai-apps.work/r/retire-floor-playbook)、[`bysq-report-tw-case`](https://imitator.ai-apps.work/r/bysq-report-tw-case) | 上架 |
| EP26 | 繳了二十八年，家人只領到九萬八 | [`three-pensions-plain`](https://imitator.ai-apps.work/r/three-pensions-plain)、[`labor-insurance`](https://imitator.ai-apps.work/r/labor-insurance) | 上架 |
| EP27 | 我不告訴你，但你會相信 | [`zkp-report`](https://imitator.ai-apps.work/r/zkp-report) | 上架 |
| EP28 | AI 來了，股市這次不一樣嗎？ | [`same-ledger`](https://imitator.ai-apps.work/r/same-ledger) | 上架 |
| EP29 | 同梯不同命？同一個起點，五年差多少 | [`0050-salary-five-years`](https://imitator.ai-apps.work/r/0050-salary-five-years) | 上架 |
| EP30 | 一天修好人生？兩億人讀過，只有三樣有效 | [`dankoe-one-day`](https://imitator.ai-apps.work/r/dankoe-one-day) | 上架 |
| EP31 | AI 幫你做完了，你知道它做對了嗎？ | [`knowing-is-dear`](https://imitator.ai-apps.work/r/knowing-is-dear) | 上架 |
| EP32 | 還沒上市，手機版就先被抄了 | [`slotbound-case`](https://imitator.ai-apps.work/r/slotbound-case) | 上架 |
| EP33 | 一句話做一個遊戲，帳單五百五十美元 | [`slotbound-case-2`](https://imitator.ai-apps.work/r/slotbound-case-2) | 上架 |
| EP34 | NVIDIA 四年漲十倍，今年卻輸給大盤 | [`winners-win-themselves`](https://imitator.ai-apps.work/r/winners-win-themselves) | 上架 |
| EP35 | 存股變飆股：0056 今年漲六成，股息是多出來的錢嗎？ | [`not-extra-money`](https://imitator.ai-apps.work/r/not-extra-money) | 上架 |
| EP36 | 韓劇最紅的這一年，為什麼要政府拿一兆韓圜救命？ | [`credit-line-changed`](https://imitator.ai-apps.work/r/credit-line-changed) | 上架 |
| EP37 | 《黑白大廚》全球第一，做節目的公司卻重整了 | [`nameless-made-famous`](https://imitator.ai-apps.work/r/nameless-made-famous) | 上架 |
| EP38 | 美國放行了，六十萬顆晶片為什麼還卡在香港？ | [`who-is-using`](https://imitator.ai-apps.work/r/who-is-using) | 上架 |
| EP39 | 中國 AI 追上美國了嗎？差十五年，也只差四個月 | [`layers-of-llm`](https://imitator.ai-apps.work/r/layers-of-llm) | 上架 |
| EP40 | 大家叫他 God東民，規則卻沒有一條是他寫的 | [`house-rules`](https://imitator.ai-apps.work/r/house-rules) | 排程 11/22 |
| EP41 | 台股熱、GDP 破一成，巷口的店為什麼說很慘？ | [`gdp-service-ledger`](https://imitator.ai-apps.work/r/gdp-service-ledger) | 排程 11/22 |

另外標已做、但沒有自己一集的：[第五個錯，和漏掉的第六個 — 外送專法篇二校](https://imitator.ai-apps.work/r/second-read)（EP16、EP17 說明欄更正）、[AI 溢酬:一般人版報告 — 論文、分析師與台股實證](https://imitator.ai-apps.work/r/ai-premium)（EP20 的背景資料）。

## 可做

| 日期 | 報告 | 備註 |
|---|---|---|
| 2026-11-11 | [線索要一節一節拉回來 — Taguri 收線紀錄](https://imitator.ai-apps.work/r/taguri) | 本機模型檢索 POC，小眾 |
| 2026-11-11 | [推理搬走了，畫布還在 — 哪一種 low-code 下課，哪一種沒有](https://imitator.ai-apps.work/r/agent-arch-6) | 架構系列 6 |
| 2026-11-09 | [同一個字，五本帳 — 從 BPM、n8n、Airflow、Airbyte 到 durable execution](https://imitator.ai-apps.work/r/one-word-five-ledgers) | workflow 的五本帳 |
| 2026-11-09 | [8 成不會錯，1 成真的省 — 選 Cloudflare 的實戰帳](https://imitator.ai-apps.work/r/ai-platform-2026-11-cf) | 選 Cloudflare 的帳，工程師向 |
| 2026-11-09 | [動詞沒變，受詞換了 — Steenberg 的架構課，給帶 agent 的人重上一次](https://imitator.ai-apps.work/r/agent-arch-5) | 架構系列 5 |
| 2026-11-09 | [演員登台：從 Actor 模型到 Durable Objects 的五十年](https://imitator.ai-apps.work/r/actor-to-durable-objects-v2) | 同上，最新版 |
| 2026-10-30 | [Eric Elliott：從年薪五十萬到住車](https://imitator.ai-apps.work/r/eric-elliott-report) | 真人故事（AI 讓我無家可歸），要小心處理 |
| 2026-10-16 | [jevlike 懶人包 — 不寫一個字，只讀一個字母](https://imitator.ai-apps.work/r/jevlike-primer) | 自家實驗：只讀一個字母的決策 API，偏技術 |
| 2026-10-06 | [它很會分，但它不會想 — Jev 在 agent workflow 裡的位置](https://imitator.ai-apps.work/r/agent-arch-4) | 架構系列 4 |
| 2026-10-02 | [一天一萬顆神經元能買到什麼 — Workers AI 番外](https://imitator.ai-apps.work/r/workers-ai-appendix) | Workers AI 番外，小眾 |
| 2026-10-02 | [帽子可以借，印章借不走：一人公司裡的 AI-native SDLC](https://imitator.ai-apps.work/r/sdlc-seal) | 一人公司的 AI-native SDLC |
| 2026-10-02 | [62% 同意，是兩個答案 — 拆解 Pocket Polis](https://imitator.ai-apps.work/r/pocket-polis-case-study) | 公民審議工具，小眾 |
| 2026-10-02 | [同事換了職業：從定理、pattern 到數位同事的九十年](https://imitator.ai-apps.work/r/pattern-story) | 從定理、pattern 到數位同事的九十年 |
| 2026-10-02 | [沒有匯率：三個分母、四種單位、一頁字典](https://imitator.ai-apps.work/r/no-exchange-rate) | 分層讀法下篇：AI 支出的三本帳，較抽象，跟上篇或番外合成一集 |
| 2026-10-02 | [分層融化：四個詞、兩根軸、一個迴圈](https://imitator.ai-apps.work/r/layers-melting) | 分層融化 |
| 2026-10-02 | [工作比紀錄大：Incumbent 往上爬的一年](https://imitator.ai-apps.work/r/incumbents-are-coming) | Incumbent 往上爬 |
| 2026-10-02 | [Mod 到底是什麼 · Claude Code 改裝手冊](https://imitator.ai-apps.work/r/claude-code-mods) | Claude Code 改裝手冊，小眾 |
| 2026-10-02 | [你早就在用 harness 了 — 買哪一層、刻哪一層](https://imitator.ai-apps.work/r/agent-arch-3) | 架構系列 3 |
| 2026-10-02 | [演員登台:從 Actor 模型到 Durable Objects 的五十年](https://imitator.ai-apps.work/r/actor-to-durable-objects-public) | 同上 |
| 2026-09-03 | [先看有沒有 Ultra：2026 Intel 筆電處理器對照](https://imitator.ai-apps.work/r/intel-core-ultra-2026-guide) | 筆電處理器對照，購物指南 |
| 2026-08-22 | [演員登台:從 Actor 模型到 Durable Objects 的五十年](https://imitator.ai-apps.work/r/actor) | Actor 模型到 Durable Objects（有三個版本） |
| 2026-08-20 | [迴圈工程](https://imitator.ai-apps.work/r/loop-engineering) | 迴圈工程，EP22 提過 |
| 2026-08-20 | [第一百次,要比第一次聰明 — Agent 系統的演進設計](https://imitator.ai-apps.work/r/agent-arch-2) | 架構系列 2 |
| 2026-08-11 | [一個 agent loop,還是一條有界的流程?](https://imitator.ai-apps.work/r/test-agent-arch) | 架構 |
| 2026-08-11 | [它們不會報錯,它們會成功 — 兩個 AI 系統的架構選型](https://imitator.ai-apps.work/r/agent-arch) | 架構系列 1 |
| 2026-07-26 | [Elon Musk 深度訪談解析：近乎無限的經濟與星際文明](https://imitator.ai-apps.work/r/elon-interview) | 與 EP19 重疊 |
| 2026-06-16 | [前沿與生態之間，藏著一條沒人標出來的曲線](https://imitator.ai-apps.work/r/frontier-vs-ecosystem) | AI 產業分析 |
| 2026-06-09 | [智慧的經濟學 · Cursor Developer Habits Report 重點一頁](https://imitator.ai-apps.work/r/ai-economics) | Cursor 開發習慣報告，一頁重點 |
| 2026-03-24 | [xAI 將會獲勝：Elon Musk 的生態系戰略與時間軸圖表](https://imitator.ai-apps.work/r/xai-will-win) | 3 月寫的，與 EP19 重疊 |
| 2026-02-23 | [Tesla Comet：基於 ClickHouse 的千兆級觀測平台技術解析](https://imitator.ai-apps.work/r/tesla-with-clickhouse) | 工程師向、小眾 |
| 2026-02-16 | [巨變前夕：AI 生存指南](https://imitator.ai-apps.work/r/ai-shift-2026) | 2 月寫的，可能過時 |
| 2026-01-08 | [2026-2030 AI 時代財富生存指南](https://imitator.ai-apps.work/r/ai-weath-survival) | 財經，1 月寫的，內容可能過時 |

## 不做

| 日期 | 報告 | 備註 |
|---|---|---|
| 2026-05-20 | [Meta 詐騙廣告醜聞完整解析 ／ 聖塔克拉拉郡 vs Meta 訴訟 2026.5.11](https://imitator.ai-apps.work/r/meta-lawsuit) | 被同作者改寫成 meta-lawsuit-1、meta-lawsuit-2（2026-11-21），做那兩篇 |
| 2026-07-25 | [Uncle Bob 為何不讀 AI 寫的程式碼？｜完整研究](https://imitator.ai-apps.work/r/uncle-bob) | 被同作者改寫成 no-read-1、no-read-2（2026-11-17），做那兩篇 |
| 2026-11-06 | [Jev 式決策，值得，而且不用買 — 給長官的判定備忘](https://imitator.ai-apps.work/r/gb10-typed-decisions) | 內部判定備忘 |
| 2026-10-15 | [像不像，不是是不是 — EmbeddingGemma 2 能當哪一種 Jev](https://imitator.ai-apps.work/r/eg2-which-jev) | 自家專案 |
| 2026-10-15 | [jevlike 音訊番外篇 — 讓模型聽，不等於讓它聽出錯](https://imitator.ai-apps.work/r/jevlike-audio) | 自家實驗番外，結論是這條線收了 |
| 2026-10-13 | [校正記錄簿：jevlike 上線後的長期迴圈，從校正到 LoRA](https://imitator.ai-apps.work/r/jevlike-calibration-loop) | 自家專案 |
| 2026-10-02 | [不是叫它記得，是讓它被提醒 — OKF 多 repo 知識庫使用說明](https://imitator.ai-apps.work/r/okf-dev-multirepo-guide) | 內部使用說明 |
| 2026-10-02 | [熄燈的窗 · Motion Deck Mockup](https://imitator.ai-apps.work/r/motion-deck-mockup) | mockup |
| 2026-10-02 | [報告樣式示範 — imitator](https://imitator.ai-apps.work/r/mockup) | 樣式示範 |
| 2026-10-02 | [市長你給我聽好了：沈伯洋專訪政策檢驗與施政藍圖全解析](https://imitator.ai-apps.work/r/mayor-you-better-listen-up) | 候選人政策解析，避開選舉題材 |
| 2026-10-02 | [技術架構備忘錄：從 Linux 筆電困境到 macOS 容器化與特權存取治理](https://imitator.ai-apps.work/r/macbook) | 技術備忘 |
| 2026-10-02 | [星期日，一起去宜蘭｜慢遊手帳](https://imitator.ai-apps.work/r/lanyang-trip-elder) | 旅遊 |
| 2026-10-02 | [宜蘭三星・大同山麓半日行旅踏查帖](https://imitator.ai-apps.work/r/lanyang-trip) | 旅遊 |
| 2026-10-02 | [Kaburi](https://imitator.ai-apps.work/r/kaburi-mockup-v3) | 自家產品 mockup |
| 2026-10-02 | [Kaburi 工作檯](https://imitator.ai-apps.work/r/kaburi-docs) | 自家產品 |
| 2026-10-02 | [Jev 式決策層放進 GB10：什麼可以、什麼確定不行、實驗能回答什麼](https://imitator.ai-apps.work/r/jev-on-gb10-feasibility) | 自家專案 |
| 2026-10-02 | [技術備忘錄：Linux 筆電痛點、macOS 容器架構與面板治理選型](https://imitator.ai-apps.work/r/gemini-note) | 技術備忘 |
| 2026-10-02 | [Architecture Memo: Container Runtime & Governance](https://imitator.ai-apps.work/r/gemini-code-vercel-version) | 架構備忘 |
| 2026-10-02 | [EV Charge Ops 七天工作坊主控台](https://imitator.ai-apps.work/r/ev-charge-ops-workshop) | 工作坊主控台 |
| 2026-10-02 | [哪條線接得通（修訂）— Claude Code session 與跨 session 傳訊](https://imitator.ai-apps.work/r/claude-sessions) | Claude Code 內部筆記 |
| 2026-09-17 | [教師版 · EV Charge Ops 七天工作坊竣工紀錄（含 D1–D7 共 8 份）](https://imitator.ai-apps.work/r/ev-charge-ops-teacher) | 工作坊教材 |
| 2026-09-08 | [私架網路裁決備忘 · 設備不是重點，行為才是](https://imitator.ai-apps.work/r/private-lan-verdict) | 內部網路備忘 |
| 2026-09-03 | [筆電不是伺服器：從 Linux 行動端困境到 macOS 容器化與特權治理](https://imitator.ai-apps.work/r/macbook-again) | 個人設備備忘 |
| 2026-09-02 | [不是權限沒開完，是沒有「直接改」這條路](https://imitator.ai-apps.work/r/gas-permission-denied) | 單一事件排錯 |
| 2026-09-02 | [Claude 為什麼說不能改 Apps Script？一次把問題拆到真正的邊界](https://imitator.ai-apps.work/r/claude-apps-script-incident-report) | 單一事件排錯 |
| 2026-09-01 | [Claude Code 連線地圖](https://imitator.ai-apps.work/r/session-connectivity) | Claude Code 內部筆記 |
| 2026-08-26 | [Working Artifact — HTML 什麼時候值得做](https://imitator.ai-apps.work/r/html-working-artifact) | 內部筆記 |
| 2026-08-25 | [Anthropic’s approach to teaching and learning AI ／ Claude by Anthropic](https://imitator.ai-apps.work/r/learningai) | 轉載 Anthropic 文章 |
| 2026-08-25 | [疊 Kasanemu 封測手冊](https://imitator.ai-apps.work/r/kasanemu) | 自家產品手冊 |
| 2026-08-25 | [Autonomy and Innovation – Stratechery by Ben Thompson](https://imitator.ai-apps.work/r/ani-by-ben) | 轉載他人文章 |
| 2026-08-23 | [Windows 11 25H2 × YouTube 卡頓：現象、根因與解法](https://imitator.ai-apps.work/r/win1125h2-youtube) | 單一故障排除 |
| 2026-07-31 | [manemu 完整成本分析 · 字幕 fallback + 金流毛利](https://imitator.ai-apps.work/r/manemu-cost-analysis) | 自家產品成本 |
| 2026-07-30 | [Manemu 方案與策略平台](https://imitator.ai-apps.work/r/manemu-price) | 自家產品 |
| 2026-07-30 | [manemu 定價模型 · 把翻譯分鐘當 eSIM 賣](https://imitator.ai-apps.work/r/manemu) | 自家產品定價 |
| 2026-07-30 | [我們的家宴｜婚禮網站 Mockup](https://imitator.ai-apps.work/r/family-feast) | 私人網站 mockup |
| 2026-07-10 | [釜山旅遊指南 부산 — 給第一次去的台灣人](https://imitator.ai-apps.work/r/busan-v3) | 旅遊手冊 |
| 2026-07-10 | [釜山旅遊書 · 第一次就上手｜부산 여행](https://imitator.ai-apps.work/r/busan-v2) | 旅遊手冊 |
| 2026-07-10 | [釜山初旅手帖｜台灣人的第一次釜山自由行](https://imitator.ai-apps.work/r/busan-v1) | 旅遊手冊 |
| 2026-06-30 | [誠實魔術 · Match-3 TAS](https://imitator.ai-apps.work/r/match-tree-magic) | 遊戲，小眾 |
| 2026-06-30 | [Match-3 Architecture: Scanner & Validation](https://imitator.ai-apps.work/r/match-tree) | 遊戲架構，小眾 |
| 2026-06-17 | [路上有雨嗎](https://imitator.ai-apps.work/r/tapiei-rain-report) | 工具 |
| 2026-05-29 | [SPCX 戰情指揮面板 v8.3 — 家族辦公室機構版](https://imitator.ai-apps.work/r/spcx-war-room) | 投資面板 |
| 2026-04-27 | [Howard Marks：戰勝大腦的出場策略](https://imitator.ai-apps.work/r/selling-out) | 被同作者改寫成 same-ledger（2026-11-13），做那篇 |
| 2026-04-25 | [SpaceX 2026 AR Calendar](https://imitator.ai-apps.work/r/spacex) | 行事曆 |
| 2026-04-14 | [DataBlock (Excel 快查 Prototype)](https://imitator.ai-apps.work/r/datablock) | 工具原型 |
| 2026-03-30 | [雙北地區房價趨勢](https://imitator.ai-apps.work/r/house-dashboard) | 資料儀表板 |
| 2026-03-24 | [雙北捷運全線｜租金熱力地圖](https://imitator.ai-apps.work/r/mrt-rental) | 資料儀表板 |
| 2026-02-14 | [Bruce ／ 現實世界的鍊金術師](https://imitator.ai-apps.work/r/alchemist-bio) | 私人介紹 |
| 2026-02-14 | [訪談實錄：從台積電到魔藥學 ／ Bruce 的職涯鍊金術](https://imitator.ai-apps.work/r/alchemist) | 私人訪談 |
| 2026-01-07 | [證件安全浮水印產生器](https://imitator.ai-apps.work/r/watermark) | 工具 |
| 2026-01-07 | [PDF Lite Editor (HTML Version)](https://imitator.ai-apps.work/r/pdf) | 工具 |
