# imitator 2026 報告對照表

更新：2026-11-16。共 139 份 2026 年的報告：已做 37、推薦 11、可做 42、不做 49。

- **來源**：imitator 的 `archive/report/`，加上只用 curl 推、不在 archive 的公開報告（`GET /v1/a` 列出，要 `IMITATOR_TOKEN`）。日期是報告的發佈或最後更新日；10-02 那一批是搬家日。
- **狀態**：已做（集數）、推薦（下一批）、可做、不做（工具、mockup、旅遊、私人、自家產品、轉載、內部筆記、教材）。
- **連結**：slug 一律用連字號，imitator 會把檔名的底線換成連字號。雲端容器抓得到公開報告的 `/r/<slug>`。
- **選題時**：先看推薦表的鉤子方向，再照 [`docs/hooks.md`](hooks.md) 定標題和第一段。收聽數據看，財經和台灣生活題材聽的人比較多。

## 推薦的下一批

依建議順序。標題是方向，不是定稿。

| # | 報告 | 標題方向 | 鉤子 |
|---|---|---|---|
| 1 | [玩法好改，也就好抄 — Slotbound 案卷](https://imitator.ai-apps.work/r/slotbound-case)（11-16） | 還沒上市，手機版就先被抄了 | 具體數字＋反轉：48 小時號稱 4.7 億韓元；正式版還沒上，討論區就有人問手機版是不是官方的 |
| 2 | [一句話的遊戲，八小時的帳單 — Slotbound 案卷 · 下](https://imitator.ai-apps.work/r/slotbound-case-2)（11-16） | 一句話做一個遊戲，帳單五百五十美元 | 「你已經在用了」：Fable 5.2 上市那週的洗版；一句指令、八小時、四億多 token |
| 3 | [貨到哪，票開給誰，誰在用 — 分層讀法番外](https://imitator.ai-apps.work/r/who-is-using)（11-16） | 六十萬顆晶片，卡在香港 | 時事：H200 停在香港、Claude 改使用資格；可以當分層讀法系列的開場，再接上篇 |
| 4 | [不是誰追上誰，而是哪一層 — 2026 年美中 AI 與半導體的分層讀法](https://imitator.ai-apps.work/r/layers-of-llm)（07-28） | 美中 AI 誰追上誰？先問是哪一層 | 流行說法對上資料：每一則新聞都是真的，誤讀出在把不同的層壓成同一層；跟番外 who-is-using 合成兩集 |
| 5 | [平均數幫不了單店：11% 成長底下的服務業對帳](https://imitator.ai-apps.work/r/gdp-service-ledger)（10-02） | GDP 破一成一，巷口的店為什麼說很慘？ | 流行說法對上資料：成長在廠房和港口，成本和缺工在店面 |
| 6 | [Meta 詐騙廣告醜聞完整解析 ／ 聖塔克拉拉郡 vs Meta 訴訟 2026.5.11](https://imitator.ai-apps.work/r/meta-lawsuit)（05-20） | 你每天滑到的詐騙廣告，一年替 Meta 賺七十億美元 | 聽眾自己的處境＋具體數字；起訴書內容，訴訟還沒開庭，講法要中性 |
| 7 | [Uncle Bob 為何不讀 AI 寫的程式碼？｜完整研究](https://imitator.ai-apps.work/r/uncle-bob)（07-25） | 寫《Clean Code》的人，不讀 AI 寫的程式碼 | 反差：他移動的是人該讀什麼，不是不在乎品質；工程師會點 |
| 8 | [同一句話，換成簡體，答案就翻面](https://imitator.ai-apps.work/r/jevlike-tw-script)（10-12） | 同一句台灣是一個國家，繁體說對，簡體說錯 | 反差＋你已經在用了；八十四題裡三十五題翻面。題材敏感，只講測到的事 |
| 9 | [國家給保險公司補錢，等於要爆炸嗎？](https://imitator.ai-apps.work/r/japan-insurer-bailout-report-1)（09-08） | 國家給保險公司補錢，是要爆炸了嗎？ | 時事問句，答案是「不是，墊子變薄了先加厚」；要先確認注資新聞還新不新 |
| 10 | [一個指標個案，和一條隔離線 — Qwen3.8 沙箱事件查核報告](https://imitator.ai-apps.work/r/qwen-index-case)（10-27） | AI 在沙箱裡，做了一件它說不會做的事 | 真實個案＋懸念；通報者是競爭對手，網路摘要少講了幾件事 |
| 11 | [熄燈的窗 · 台灣少子化與房價](https://imitator.ai-apps.work/r/birthrate-vs-housing)（08-17） | 生的人變少了，房價為什麼還在漲？ | 流行說法對上資料；原文是八頁投影片，內容要先讀過確認夠不夠撐一集 |

## 系列與成對

| 系列 | 報告 | 怎麼做 |
|---|---|---|
| Slotbound 案卷 | `slotbound-case`、`slotbound-case-2` | 上下集：上集講被抄，下集講一句話做遊戲的帳單 |
| 分層讀法 | `who-is-using`、`layers-of-llm`、`no-exchange-rate` | 兩集：番外的時事當開場接上篇，下篇的三本帳併進第二集 |
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
| EP30 | 一天修好人生？兩億人讀過，只有三樣有效 | [`dankoe-one-day`](https://imitator.ai-apps.work/r/dankoe-one-day) | 試聽中 |
| EP31 | AI 幫你做完了，你知道它做對了嗎？ | [`knowing-is-dear`](https://imitator.ai-apps.work/r/knowing-is-dear) | 試聽中 |

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
| 2026-11-05 | [帳單上印著誰的名字 — AI 平台地形 下篇](https://imitator.ai-apps.work/r/ai-platform-2026-11) | AI 平台地形 下篇 |
| 2026-10-30 | [Eric Elliott：從年薪五十萬到住車](https://imitator.ai-apps.work/r/eric-elliott-report) | 真人故事（AI 讓我無家可歸），要小心處理 |
| 2026-10-17 | [每一層，都要能說不 — Zeabur 之後的 AI 平台地形](https://imitator.ai-apps.work/r/ai-platform-2026-10) | AI 平台地形 上篇 |
| 2026-10-16 | [jevlike 懶人包 — 不寫一個字，只讀一個字母](https://imitator.ai-apps.work/r/jevlike-primer) | 自家實驗：只讀一個字母的決策 API，偏技術 |
| 2026-10-06 | [它很會分，但它不會想 — Jev 在 agent workflow 裡的位置](https://imitator.ai-apps.work/r/agent-arch-4) | 架構系列 4 |
| 2026-10-05 | [人人都是建築師，那誰來簽證 — AI 時代的程式設計師](https://imitator.ai-apps.work/r/everyone-an-architect) | AI 時代的程式設計師 |
| 2026-10-04 | [劍客、小孩，與一面歪掉的鏡子 — 2026H2 Agent 生存指南](https://imitator.ai-apps.work/r/agent-survival-2026h2) | 與 EP11 主題接近 |
| 2026-10-02 | [一天一萬顆神經元能買到什麼 — Workers AI 番外](https://imitator.ai-apps.work/r/workers-ai-appendix) | Workers AI 番外，小眾 |
| 2026-10-02 | [你連的是什麼線 — 從一百萬則通知的假議題，到 AI 時代的架構師](https://imitator.ai-apps.work/r/which-wire) | AI 時代的架構師 |
| 2026-10-02 | [帽子可以借，印章借不走：一人公司裡的 AI-native SDLC](https://imitator.ai-apps.work/r/sdlc-seal) | 一人公司的 AI-native SDLC |
| 2026-10-02 | [62% 同意，是兩個答案 — 拆解 Pocket Polis](https://imitator.ai-apps.work/r/pocket-polis-case-study) | 公民審議工具，小眾 |
| 2026-10-02 | [同事換了職業：從定理、pattern 到數位同事的九十年](https://imitator.ai-apps.work/r/pattern-story) | 從定理、pattern 到數位同事的九十年 |
| 2026-10-02 | [沒有匯率：三個分母、四種單位、一頁字典](https://imitator.ai-apps.work/r/no-exchange-rate) | 分層讀法下篇：AI 支出的三本帳，較抽象，跟上篇或番外合成一集 |
| 2026-10-02 | [分層融化：四個詞、兩根軸、一個迴圈](https://imitator.ai-apps.work/r/layers-melting) | 分層融化 |
| 2026-10-02 | [工作比紀錄大：Incumbent 往上爬的一年](https://imitator.ai-apps.work/r/incumbents-are-coming) | Incumbent 往上爬 |
| 2026-10-02 | [Mod 到底是什麼 · Claude Code 改裝手冊](https://imitator.ai-apps.work/r/claude-code-mods) | Claude Code 改裝手冊，小眾 |
| 2026-10-02 | [持有 VT 幾歲能退休](https://imitator.ai-apps.work/r/bysq-report-twvt) | 持有 VT 幾歲能退休，財經 |
| 2026-10-02 | [你早就在用 harness 了 — 買哪一層、刻哪一層](https://imitator.ai-apps.work/r/agent-arch-3) | 架構系列 3 |
| 2026-10-02 | [演員登台:從 Actor 模型到 Durable Objects 的五十年](https://imitator.ai-apps.work/r/actor-to-durable-objects-public) | 同上 |
| 2026-09-03 | [先看有沒有 Ultra：2026 Intel 筆電處理器對照](https://imitator.ai-apps.work/r/intel-core-ultra-2026-guide) | 筆電處理器對照，購物指南 |
| 2026-08-22 | [演員登台:從 Actor 模型到 Durable Objects 的五十年](https://imitator.ai-apps.work/r/actor) | Actor 模型到 Durable Objects（有三個版本） |
| 2026-08-20 | [迴圈工程](https://imitator.ai-apps.work/r/loop-engineering) | 迴圈工程，EP22 提過 |
| 2026-08-20 | [第一百次,要比第一次聰明 — Agent 系統的演進設計](https://imitator.ai-apps.work/r/agent-arch-2) | 架構系列 2 |
| 2026-08-18 | [40 歲開始，退休金該怎麼算？｜個人財務逆向工程](https://imitator.ai-apps.work/r/forties) | 40 歲退休金怎麼算，財經 |
| 2026-08-11 | [一個 agent loop,還是一條有界的流程?](https://imitator.ai-apps.work/r/test-agent-arch) | 架構 |
| 2026-08-11 | [它們不會報錯,它們會成功 — 兩個 AI 系統的架構選型](https://imitator.ai-apps.work/r/agent-arch) | 架構系列 1 |
| 2026-07-26 | [Elon Musk 深度訪談解析：近乎無限的經濟與星際文明](https://imitator.ai-apps.work/r/elon-interview) | 與 EP19 重疊 |
| 2026-07-24 | [測試在測什麼?— 可測的、不可測的、與兩者之間的搬運(第三篇)](https://imitator.ai-apps.work/r/llm-testing-essence) | 測試在測什麼，系列 3/3 |
| 2026-07-23 | [工具在手,怎麼用才算數?— Claude Code 使用指南(下篇)](https://imitator.ai-apps.work/r/ai-amp-or-mirror-2) | Claude Code 使用指南，系列 2/3 |
| 2026-07-23 | [同一個工具,為什麼結果差這麼多?— LLM 使用者差異研究綜述](https://imitator.ai-apps.work/r/ai-amp-or-mir) | 使用者差異研究，系列 1/3 |
| 2026-06-16 | [前沿與生態之間，藏著一條沒人標出來的曲線](https://imitator.ai-apps.work/r/frontier-vs-ecosystem) | AI 產業分析 |
| 2026-06-09 | [智慧的經濟學 · Cursor Developer Habits Report 重點一頁](https://imitator.ai-apps.work/r/ai-economics) | Cursor 開發習慣報告，一頁重點 |
| 2026-03-24 | [xAI 將會獲勝：Elon Musk 的生態系戰略與時間軸圖表](https://imitator.ai-apps.work/r/xai-will-win) | 3 月寫的，與 EP19 重疊 |
| 2026-02-23 | [Tesla Comet：基於 ClickHouse 的千兆級觀測平台技術解析](https://imitator.ai-apps.work/r/tesla-with-clickhouse) | 工程師向、小眾 |
| 2026-02-16 | [巨變前夕：AI 生存指南](https://imitator.ai-apps.work/r/ai-shift-2026) | 2 月寫的，可能過時 |
| 2026-01-08 | [2026-2030 AI 時代財富生存指南](https://imitator.ai-apps.work/r/ai-weath-survival) | 財經，1 月寫的，內容可能過時 |

## 不做

| 日期 | 報告 | 備註 |
|---|---|---|
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
