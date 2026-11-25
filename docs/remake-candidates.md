# imitator 2025 報告重製清單（冷飯熱炒）

更新：2026-11-22。imitator 公開報告 378 篇，2026 年的 161 篇在 [`report-candidates.md`](report-candidates.md)；這份只看 **2025 年的 217 篇**，挑出值得**重新寫成現在 imitator 格式**（重查資料、更新數字、照 [`hooks.md`](hooks.md) 定鉤子）再拿來做 podcast 的。

**這是備選池，不是推薦表。** 重製好的新報告會有新的 slug，那時再照平常的流程放進 `report-candidates.md` 的推薦表；這裡不排集數，也不影響推薦表的順序。

- **來源**：`GET /v1/a`（要 `IMITATOR_TOKEN`）列出 `updatedAt` 在 2025 年的 217 篇，每篇抓 `/r/<slug>` 的網頁文字判斷。2025 年的報告多半是互動頁和儀表板，網頁文字只抓得到骨架，判斷主要靠標題、章節和開頭段落，重製前要再讀一次原頁。
- **為什麼要重製，不能直接做**：數字都過了一年以上，很多是轉述別人的訪談或書，沒有自己的問題。重製時要換成「一個聽眾會問的問題，用資料回答」。
- **分類**：照 [`strategy.md`](strategy.md)「選題比例」：**錢**放錢日（五天兩集），**AI** 和**硬**（產業、科技、社會，非 AI）放另外四天。
- **優先**：AI 那邊推薦表約 12/10 見底，比錢（12/16 起要新報告）早，所以首選先排 AI。
- **一年後對帳**：很多 2025 年的報告是預言（Dario、Karpathy、Altman、Musk、金價）。重製的鉤子最好用「一年前他說……，現在呢？」，EP10 Huntley 對帳就是這種做法。

統計：首選 13 組（33 篇）、次選 22 組（42 篇）、內容已含在已做集數或 2026 報告的 34 篇、不做 108 篇。

**11-22 第二輪**：拿 2026 年 161 篇報告全文和已做集數的稿子逐組對照，內容已經講過的（不一定同標題）移到「已有對應」，例如 METR 慢 19%（推薦 #5、#9）、AI 寫作業（EP46）、4% 與 GK 提領（EP25）、《致富的特權》（EP07）。

## 首選：AI 與硬題目（排在前面）

| # | 類別 | 原報告 | 標題方向 | 鉤子 | 要更新什麼 |
|---|---|---|---|---|---|
| 1 | AI | [互動式報告：強納森·布洛論軟體知識的崩潰 (最終整合版)](https://imitator.ai-apps.work/r/jonathan-blow)（06-11）<br>[Kent Beck：52 年的程式碼與未來](https://imitator.ai-apps.work/r/kent-back)（08-27） | 沒人會寫底層了，軟體知識會失傳嗎？ | 流行說法對上歷史：Blow 說知識在慢慢崩潰，Kent Beck 說 TDD 在 AI 時代更重要 | 2026 年的實例（AI 寫的程式出事、沒人看得懂的系統）；推薦 #7 llm-testing-essence 已講測試在測什麼，這篇要放在「知識怎麼傳下去」，不要再講測試 |
| 2 | AI | [架構師與哨兵：Fowler vs. Willison AI 觀點互動式分析](https://imitator.ai-apps.work/r/fowler-vs-willison)（08-29） | AI 助理能讀你的信、能上網、能碰私人資料，三件湊齊就會出事 | 具體案例：Willison 的「致命三要素」，配 2025–26 真的發生的提示注入事件 | 補 2025–26 事件清單（瀏覽器 agent、MCP、郵件 agent），原文是觀點比較，要改成案例帶 |
| 3 | 硬 | [互動式AI伺服器電源供應商分析報告](https://imitator.ai-apps.work/r/ai-power)（07-09）<br>[互動式報告：AI 的電力革命 - 為何高壓直流電是未來](https://imitator.ai-apps.work/r/ai-power-revolution)（07-14）<br>[特斯拉 Megapack vs. 台達電 BESS: 極速安裝的秘密](https://imitator.ai-apps.work/r/megapack-vs-bess)（09-10）<br>[台達電子：引領產業趨勢，共創市場價值](https://imitator.ai-apps.work/r/delta)（05-26） | AI 機房缺的不是晶片，是電：台達電為什麼變成 AI 股 | 台灣公司＋具體數字：800V 直流、儲能，從一顆 GPU 的耗電算到變電所 | NVIDIA 800V 路線進度、台達電 2025–26 營收結構、各家電源廠市占；四篇合成上下篇 |
| 4 | 硬 | [互動敘事：瑞士鐘錶業的危機與重生 (增強版)](https://imitator.ai-apps.work/r/quartz-crisis)（06-12）<br>[互動式報告：典範轉移與贏家的詛咒 (增強版)](https://imitator.ai-apps.work/r/paradigm-shifts)（08-12） | 石英錶差點打死瑞士錶，三十年後瑞士賺更多 | 歷史比喻：被新技術打敗的產業怎麼活回來，套到 AI 和工程師 | 2025–26 瑞士錶出口與美國關稅、Apple Watch 出貨；比喻要落到 AI 的具體對照 |
| 5 | 硬 | [互動式報告：Apple 的中國故事](https://imitator.ai-apps.work/r/apple-in-china)（06-17）<br>[中國製造業崛起：互動式報告](https://imitator.ai-apps.work/r/apple-at-cn)（05-27） | Apple 教會中國做手機，然後呢？ | 反差：最會分散風險的公司，把自己綁得最深 | 《Apple in China》之後的關稅、印度產能比例、2026 年 iPhone 產地數字；EP18 已講深圳代工的「自研光譜」，這篇講 Apple 怎麼把製造知識教出去，角度要分開 |
| 6 | AI | [互動式報告：溫和的奇點](https://imitator.ai-apps.work/r/gentle-singularity)（06-13）<br>[互動式報告 v2：專訪 OpenAI 執行長 Sam Altman](https://imitator.ai-apps.work/r/openai-next)（10-11）<br>[互動式報告：剖析 AI 世代的 ChatGPT 用戶光譜](https://imitator.ai-apps.work/r/ai-generation-with-openai)（06-12） | Altman 說奇點會很溫和，一年後他自己承認低估了普及要多久 | 預言對帳：2025-06〈溫和的奇點〉的時間表，對上他 2026 年的改口（ani-by-ben 轉載的 Senra 訪談） | 〈溫和的奇點〉逐條預測對 2026 現況、OpenAI 產品與用量數字；三篇合成一篇 |
| 7 | AI | [伊隆·馬斯克 CNBC 專訪互動解析](https://imitator.ai-apps.work/r/elonmusk)（05-26）<br>[伊隆·馬斯克訪談精華](https://imitator.ai-apps.work/r/elon-on-allin-podcast)（09-10）<br>[特斯拉 vs. Waymo：互動式對比分析](https://imitator.ai-apps.work/r/tesla-vs-waymo)（06-11）<br>[互動式網頁報告：特斯拉 RoboTaxi 深度解析](https://imitator.ai-apps.work/r/ray-on-robotaxi)（08-16） | 特斯拉說 Robotaxi 穩了，一年後街上跑的是誰的車 | 預言對帳＋具體數字：2025 年的承諾對上 2026 年 Waymo 與特斯拉的城市數、車隊數、事故報告 | 2026 年兩家的營運城市、每週載客數、NHTSA 調查；EP19 也是馬斯克，這篇只講自駕，不講財富 |

## 首選：錢（12/16 起的錢日用）

| # | 類別 | 原報告 | 標題方向 | 鉤子 | 要更新什麼 |
|---|---|---|---|---|---|
| 8 | **錢** | [「以房養老」互動解析：透視繼承風暴與隱藏陷阱](https://imitator.ai-apps.work/r/reverse-mortgage)（07-01） | 以房養老：爸爸走了，銀行說欠 90 萬，三個月後變 340 萬 | 聽眾自己的處境＋真實個案：繼承前查到的數字為什麼不準 | 個案後續、銀行與金管會之後改的規則、2026 年以房養老件數與利率、限定繼承怎麼用 |
| 9 | **錢** | [海外投資與財富傳承決策儀表板](https://imitator.ai-apps.work/r/inheritance)（10-03） | 海外券商的帳戶，人走了錢拿得回來嗎？ | 聽眾自己的處境：美股開戶容易，傳承很難；美國遺產稅對外國人只免 6 萬美元 | 2026 年美國遺產稅與台灣規定、各券商的繼承流程、複委託的對照數字；EP25 實戰篇只用一句帶過 6 萬美元門檻，這篇講整個流程 |
| 10 | **錢** | [失能險深度解析資訊圖](https://imitator.ai-apps.work/r/disability-ins)（06-07） | 失能險和長照險，差在用哪一把尺 | 聽眾自己的處境：同一場病，一張賠一張不賠；接保險課系列 | 2026 年保單條款、長照 3.0 的政府給付、保費範例；推薦 #15 保險課番外講了「長照在台灣靠稅收」，這篇只講兩張保單的差別 |
| 11 | **錢** | [周冠男教授的ETF投資心法圖表](https://imitator.ai-apps.work/r/prof0050)（06-02）<br>[周冠男教授的被動投資心法](https://imitator.ai-apps.work/r/dr0050)（09-12）<br>[互動資訊圖：約翰·柏格的再平衡智慧](https://imitator.ai-apps.work/r/rebalance)（06-12）<br>[綠角投資智慧互動導覽](https://imitator.ai-apps.work/r/greenhorn)（05-26）<br>[智慧投資儀表板 ｜ 大人學 x 綠角 (增強版)](https://imitator.ai-apps.work/r/greenhorn-daren)（06-02）<br>[小資YP理財智慧互動指南](https://imitator.ai-apps.work/r/5m1y)（05-27）<br>[小資YP投資理財視覺化指南](https://imitator.ai-apps.work/r/5m1y-info)（05-27）<br>[小資YP的千萬之路：互動式財務策略儀表板](https://imitator.ai-apps.work/r/yp-intro)（06-05） | 單筆投入 68% 會贏，為什麼 74% 的人還是分批買？ | 研究對上心理：先鋒研究和網路調查剛好相反；下篇接再平衡（柏格說不一定要做） | 用台股與 VT 重跑單筆對分批、再平衡到 2026；原文是轉述名人理財觀，重製要改成用資料回答一個問題 |
| 12 | **錢** | [互動式報告：穩定幣戰爭與金融的未來](https://imitator.ai-apps.work/r/stable)（06-02）<br>[穩定幣戰場：互動式分析儀表板](https://imitator.ai-apps.work/r/stable-coin)（07-16）<br>[產業趨勢與市場研究：比特幣與泰達幣深度報告](https://imitator.ai-apps.work/r/tether)（05-31） | 穩定幣是數位美元，還是下一場擠兌？ | 時事：美國 2025-07 通過穩定幣法案之後，台灣也要開放 | GENIUS 法案之後的市值與發行商、台灣金管會的規範進度；三篇合成一篇 |
| 13 | **錢** | [瘋狂的黃金：互動式市場分析報告](https://imitator.ai-apps.work/r/bloomberg-324)（06-14） | 金價 3500 美元時大家說瘋了，後來呢？ | 預言對帳：一年前的「瘋狂」對上現在的價格，誰在買 | 2025–26 金價、各國央行買金數字、台灣人買金管道 |

## 次選

有題目，但鉤子弱、跟已做的重疊，或真人、真實公司要特別小心。首選用完或有新聞剛好接上時再看。

| 類別 | 原報告 | 方向與備註 |
|---|---|---|
| AI | [`revenge`](https://imitator.ai-apps.work/r/revenge)、[`revenge-ori`](https://imitator.ai-apps.work/r/revenge-ori)、[`horseless-carriages`](https://imitator.ai-apps.work/r/horseless-carriages) | Yegge「菜鳥開發者的復仇」與「無馬馬車」：2025 的預測哪些成真 |
| AI | [`mckinsey`](https://imitator.ai-apps.work/r/mckinsey)、[`shawn-k-case`](https://imitator.ai-apps.work/r/shawn-k-case) | 顧問業裁員、被裁的資深工程師；跟可做的 Eric Elliott 同一類，要小心真人 |
| AI | [`ai-at-work-2025`](https://imitator.ai-apps.work/r/ai-at-work-2025)、[`bond2025`](https://imitator.ai-apps.work/r/bond2025)、[`core-skill-2030`](https://imitator.ai-apps.work/r/core-skill-2030) | BCG、Mary Meeker、WEF 年度報告：用 2026 新版重寫，舊版數字對照 |
| AI | [`ai-agent`](https://imitator.ai-apps.work/r/ai-agent)、[`dev-ai-era`](https://imitator.ai-apps.work/r/dev-ai-era)、[`ai-enablement`](https://imitator.ai-apps.work/r/ai-enablement) | 垂直 agent 市場、a16z 九種開發模式：推薦 #3–4 AI 平台地形已講 agent 生態，只剩預測對帳的角度 |
| AI | [`illusion-of-thinking`](https://imitator.ai-apps.work/r/illusion-of-thinking) | Apple《思考的幻覺》之爭：推理模型一年後還卡在同一題嗎 |
| AI | [`rene-turcios`](https://imitator.ai-apps.work/r/rene-turcios) | 不會寫程式的黑客松之王：炒作與真相，真人題材要小心 |
| AI | [`tech-debt`](https://imitator.ai-apps.work/r/tech-debt)、[`ai-writing-trend`](https://imitator.ai-apps.work/r/ai-writing-trend)、[`ilya-sutskever`](https://imitator.ai-apps.work/r/ilya-sutskever)、[`apple-retreats`](https://imitator.ai-apps.work/r/apple-retreats)、[`psych-safety`](https://imitator.ai-apps.work/r/psych-safety) | 單篇觀點，有新角度再做 |
| 硬 | [`chunghwa`](https://imitator.ai-apps.work/r/chunghwa) | 中華電信憑證被 Chrome 不信任：一年後的影響 |
| 硬 | [`eggs-events`](https://imitator.ai-apps.work/r/eggs-events) | 毒蛋事件與溯源系統：2025 的第一次實戰 |
| 硬 | [`tsunami-at-taiwan`](https://imitator.ai-apps.work/r/tsunami-at-taiwan)、[`tsunami-at-taiwan-v2`](https://imitator.ai-apps.work/r/tsunami-at-taiwan-v2) | 人口海嘯：可跟推薦 #17 少子化與房價合併 |
| 硬 | [`din-tai-fung-us`](https://imitator.ai-apps.work/r/din-tai-fung-us)、[`cost-of-perfume`](https://imitator.ai-apps.work/r/cost-of-perfume) | 商業故事：鼎泰豐美國單店營收第一、茉莉花供應鏈 |
| 硬 | [`china-deps`](https://imitator.ai-apps.work/r/china-deps)、[`ethane`](https://imitator.ai-apps.work/r/ethane)、[`china-odi`](https://imitator.ai-apps.work/r/china-odi) | 中美供應鏈互相卡脖子：用 2025–26 關稅戰重寫 |
| 硬 | [`neuralink`](https://imitator.ai-apps.work/r/neuralink) | Neuralink 一年後的進度對帳 |
| **錢** | [`tw-factor`](https://imitator.ai-apps.work/r/tw-factor) | 台股因子 ETF：資料多了一年，回測能不能做了 |
| **錢** | [`algebra-of-wealth`](https://imitator.ai-apps.work/r/algebra-of-wealth) | 《財富的代數》：書摘要改成一個能算的問題才做 |
| **錢** | [`house`](https://imitator.ai-apps.work/r/house)、[`chunghe-yonghe-story`](https://imitator.ai-apps.work/r/chunghe-yonghe-story) | 房市量縮價撐、雙北抗跌：EP24 已做租或買，2026 也有 house-dashboard 儀表板；要有新的問題才做 |
| **錢** | [`jko-event`](https://imitator.ai-apps.work/r/jko-event) | 街口 36 億風暴的後續：處分與訴訟進度，涉及真實公司要逐句核對 |
| **錢** | [`cathie-wood`](https://imitator.ai-apps.work/r/cathie-wood)、[`cathie-wood-q3`](https://imitator.ai-apps.work/r/cathie-wood-q3) | 木頭姐的預測對帳 |
| **錢** | [`the-big-short`](https://imitator.ai-apps.work/r/the-big-short)、[`the-big-short2`](https://imitator.ai-apps.work/r/the-big-short2) | 2008 次貸：沒有新數字，要找現在的對照才有鉤子 |
| **錢** | [`broken-money`](https://imitator.ai-apps.work/r/broken-money)、[`bank-locked`](https://imitator.ai-apps.work/r/bank-locked) | Lyn Alden 貨幣史；銀行靜止戶條件（可併入 Meta 詐騙系列講警示帳戶） |
| **錢** | [`us-dollar`](https://imitator.ai-apps.work/r/us-dollar) | 長輩手上的美金存款怎麼辦：EP07 講了匯率的大帳，這篇只講個人手上的美金，用 2025–26 匯率重寫 |
| **錢** | [`am-income-growth-fund`](https://imitator.ai-apps.work/r/am-income-growth-fund)、[`covered-call`](https://imitator.ai-apps.work/r/covered-call) | 配息 8% 的基金、掩護性買權 ETF：論點跟 EP35「股息不是多出來的錢」相同，只有產品不同；有新聞（如基金配本金爭議）再做 |

## 已有對應（不重製）

內容已經在已做的集數或 2026 年的報告裡講過（不一定同標題），重製也只會重複。右欄寫是哪一集或哪一篇、講到哪裡。

| 報告 | 對應 |
|---|---|
| [剖析 Geoffrey Huntley 的 Vibe Coding](https://imitator.ai-apps.work/r/vibe-coding)（05-26） | EP10 huntley-18-months 已做 Huntley 對帳 |
| [剖析 Geoffrey Huntley 的 AI 驅動軟體開發願景](https://imitator.ai-apps.work/r/gh-vibe-coding)（06-06） | 同上 |
| [AI 驅動軟體開發趨勢資訊圖表](https://imitator.ai-apps.work/r/vibe-coding-info)（05-26） | 同上（頁面是空的） |
| [軟體架構的哲學探索 - Eskil Steenberg](https://imitator.ai-apps.work/r/arch-large-sf-projects)（09-09） | 2026 版 agent-arch-5（Steenberg 架構課） |
| [四騎士與七巨頭：互動式分析](https://imitator.ai-apps.work/r/4r-m7)（06-12） | EP34 七巨頭 |
| [M觀點科技股互動分析儀表板](https://imitator.ai-apps.work/r/mulia-view-point)（07-15） | EP34 七巨頭 |
| [元大台灣50 (0050) 投資績效解析 - 智慧投資風格 (v4)](https://imitator.ai-apps.work/r/0050)（06-06） | EP29 0050 五年 |
| [買房 vs. 租房 財務對決模擬器](https://imitator.ai-apps.work/r/rent-or-buy)（10-09） | EP24 租或買 |
| [互動式報告：新程式碼即規格文件](https://imitator.ai-apps.work/r/the-new-code)（08-04） | EP42–44 不讀之後（規格） |
| [互動式 Vibe Coding 深度解析](https://imitator.ai-apps.work/r/claude-in-prd)（08-04） | EP42–44 不讀之後 |
| [AI 時代的極速競賽](https://imitator.ai-apps.work/r/base-in-ai-gen)（09-12） | 推薦 #5 ai-mirror-1（放大器） |
| [互動式報告：AI 時代的生存策略](https://imitator.ai-apps.work/r/time-to-vibe-coding)（08-27） | 推薦 #5 ai-mirror-1 |
| [代理網路趨勢與未來展望 - 互動資訊圖表](https://imitator.ai-apps.work/r/sin)（05-26） | 推薦 #4 ai-platform-2026-11（agent 付款） |
| [Cursor 收費方案詳解](https://imitator.ai-apps.work/r/cursor-pricing)（05-26） | EP47 AI 月費買到多少 |
| [AI就業風暴：幕後真相與未來警示](https://imitator.ai-apps.work/r/white-collar)（05-29） | 推薦 #9 everyone-an-architect 已講 22–25 歲 AI 高曝險職業就業 −19%（Brynjolfsson） |
| [AI就業風暴：幕後真相與未來警示](https://imitator.ai-apps.work/r/white-collar-info)（05-29） | 同上 |
| [Claude 創辦人 Dario Amodei AI 未來展望](https://imitator.ai-apps.work/r/anthropic)（05-26） | 同上（Dario 訪談，就業預言是主軸） |
| [AI 產業趨勢與市場研究資訊圖表 - Dario Amodei 洞察](https://imitator.ai-apps.work/r/anthropic-info)（05-26） | 同上 |
| [AI 趨勢與市場研究資訊圖表](https://imitator.ai-apps.work/r/claude4)（05-26） | 同上（Anthropic 訪談，內容跟 Dario 篇重疊） |
| [AI 程式設計助理效益互動式分析報告](https://imitator.ai-apps.work/r/ai-roi)（07-16） | 推薦 #5 ai-mirror-1 以 METR「感覺快 20%、實測慢 19%」為主軸；#9 還補了 METR 重測（−18%） |
| [互動式報告：Anthropic 團隊如何使用 Claude Code](https://imitator.ai-apps.work/r/anthropic-team)（06-08） | 同上（AI 寫程式的生產力數字） |
| [互動式報告：Andrej Karpathy - AI 時代的軟體](https://imitator.ai-apps.work/r/andrej-karpathy)（06-19） | 推薦 #9 everyone-an-architect 已講 Karpathy 收回 vibe coding、改叫 agentic engineering；推薦 #8 番外篇講他的四個載體 |
| [互動式分析：AI對教育的真正威脅](https://imitator.ai-apps.work/r/myth-auto-learning)（06-10） | EP46 practice-on-purpose 已講賓州大學土耳其高中實驗（練習 +48%、閉卷 −17%） |
| [互動式報告：AI、學習與第一性原理](https://imitator.ai-apps.work/r/ai-learning-fpt)（06-11） | 同上 |
| [互動式退休提領計畫模擬器](https://imitator.ai-apps.work/r/four-percent-rule)（06-07） | EP25 地板（retire-floor-playbook：3.5% 規劃線、4% 上限）與 bysq-report-tw-case（固定 4%、GK 護欄、VPW 破產率） |
| [GK 動態提領策略互動模擬器](https://imitator.ai-apps.work/r/gk-method)（07-11） | 同上（GK 護欄） |
| [FIRE 動態提領引擎 (FDE-60)](https://imitator.ai-apps.work/r/fire-dashboard)（11-19） | 同上（動態提領） |
| [視覺化回測：0050 vs 0056 退休提領策略 (2008-2025)](https://imitator.ai-apps.work/r/0050vs0056)（06-18） | EP35 not-extra-money 已用 2008 起 1,000 萬比 0050 與 0056 的提領 |
| [五年從零到五百萬：投資心態與策略互動報告](https://imitator.ai-apps.work/r/mr-waterdrop)（06-15） | EP35（高股息對大盤） |
| [央行政策互動解析平台](https://imitator.ai-apps.work/r/privilege)（05-26） | EP07 taiwan-money-again 已講《致富的特權》與「利率低，房價就漲」 |
| [台灣央行政策互動解析](https://imitator.ai-apps.work/r/privilege2)（05-26） | 同上 |
| [台灣央行政策影響資訊圖表](https://imitator.ai-apps.work/r/privilege-info)（05-26） | 同上 |
| [TISA 0050 連結基金 vs. 直購 0050 ETF 互動分析](https://imitator.ai-apps.work/r/tisa-0050)（08-15） | 推薦 #15 保險課番外已講 TISA 的制度與免稅條件 |
| [小資族 SpaceX 投資可行性分析 (進階版)](https://imitator.ai-apps.work/r/small-money-on-spacex)（09-02） | EP19 ownership-token 從一股 SpaceX 倒推產能 |

## 不做

| 理由 | 報告 |
|---|---|
| 旅遊、行程、個人生活（18） | [`vietnam`](https://imitator.ai-apps.work/r/vietnam)、[`tokyo`](https://imitator.ai-apps.work/r/tokyo)、[`yunlin`](https://imitator.ai-apps.work/r/yunlin)、[`eva-gold`](https://imitator.ai-apps.work/r/eva-gold)、[`honeymoon`](https://imitator.ai-apps.work/r/honeymoon)、[`nz-step-0`](https://imitator.ai-apps.work/r/nz-step-0)、[`nz-step-1`](https://imitator.ai-apps.work/r/nz-step-1)、[`nz-step-2`](https://imitator.ai-apps.work/r/nz-step-2)、[`nz-step-3`](https://imitator.ai-apps.work/r/nz-step-3)、[`nz-step-4`](https://imitator.ai-apps.work/r/nz-step-4)、[`nz-comp`](https://imitator.ai-apps.work/r/nz-comp)、[`nz-a-vs-b`](https://imitator.ai-apps.work/r/nz-a-vs-b)、[`d-day`](https://imitator.ai-apps.work/r/d-day)、[`old-restaurant`](https://imitator.ai-apps.work/r/old-restaurant)、[`breakfast-with-konbini`](https://imitator.ai-apps.work/r/breakfast-with-konbini)、[`checklist`](https://imitator.ai-apps.work/r/checklist)、[`gym-pricing`](https://imitator.ai-apps.work/r/gym-pricing)、[`case-study`](https://imitator.ai-apps.work/r/case-study) |
| 小工具、空頁（5） | [`cal`](https://imitator.ai-apps.work/r/cal)、[`line-gen`](https://imitator.ai-apps.work/r/line-gen)、[`player`](https://imitator.ai-apps.work/r/player)、[`intuition-challenge`](https://imitator.ai-apps.work/r/intuition-challenge)、[`alpha-tracker`](https://imitator.ai-apps.work/r/alpha-tracker) |
| 購物指南（規格一年就過期）（7） | [`macbook-global-buy`](https://imitator.ai-apps.work/r/macbook-global-buy)、[`pixel-10-fold-guide`](https://imitator.ai-apps.work/r/pixel-10-fold-guide)、[`ipad-mini-guide`](https://imitator.ai-apps.work/r/ipad-mini-guide)、[`macbook-air-guide`](https://imitator.ai-apps.work/r/macbook-air-guide)、[`ryzen-ai`](https://imitator.ai-apps.work/r/ryzen-ai)、[`gcp-dev-prog`](https://imitator.ai-apps.work/r/gcp-dev-prog)、[`mtb`](https://imitator.ai-apps.work/r/mtb) |
| 技術教學、工具文件（28） | [`agent`](https://imitator.ai-apps.work/r/agent)、[`prompt-tutorial`](https://imitator.ai-apps.work/r/prompt-tutorial)、[`anthropic-courses`](https://imitator.ai-apps.work/r/anthropic-courses)、[`ai-fluency`](https://imitator.ai-apps.work/r/ai-fluency)、[`docker-plugin`](https://imitator.ai-apps.work/r/docker-plugin)、[`docker-o11y`](https://imitator.ai-apps.work/r/docker-o11y)、[`distr-tracing`](https://imitator.ai-apps.work/r/distr-tracing)、[`grafana-12-oac`](https://imitator.ai-apps.work/r/grafana-12-oac)、[`grafana101`](https://imitator.ai-apps.work/r/grafana101)、[`apple-container`](https://imitator.ai-apps.work/r/apple-container)、[`dotnet-strategy`](https://imitator.ai-apps.work/r/dotnet-strategy)、[`nplus1`](https://imitator.ai-apps.work/r/nplus1)、[`nplus1exp`](https://imitator.ai-apps.work/r/nplus1exp)、[`headscale`](https://imitator.ai-apps.work/r/headscale)、[`duckdb`](https://imitator.ai-apps.work/r/duckdb)、[`gemini-cli`](https://imitator.ai-apps.work/r/gemini-cli)、[`gen-ai-guide-v1`](https://imitator.ai-apps.work/r/gen-ai-guide-v1)、[`gen-ai-guide-v2`](https://imitator.ai-apps.work/r/gen-ai-guide-v2)、[`copilot`](https://imitator.ai-apps.work/r/copilot)、[`gemini-inside`](https://imitator.ai-apps.work/r/gemini-inside)、[`sub-agent`](https://imitator.ai-apps.work/r/sub-agent)、[`sub-agent-cont`](https://imitator.ai-apps.work/r/sub-agent-cont)、[`multi-agent-obs`](https://imitator.ai-apps.work/r/multi-agent-obs)、[`12-factor-agents`](https://imitator.ai-apps.work/r/12-factor-agents)、[`slidev-vs-marp`](https://imitator.ai-apps.work/r/slidev-vs-marp)、[`gpo-cheatsheet`](https://imitator.ai-apps.work/r/gpo-cheatsheet)、[`custom-data-flow`](https://imitator.ai-apps.work/r/custom-data-flow)、[`vibe-coding-flow`](https://imitator.ai-apps.work/r/vibe-coding-flow) |
| 泛泛的 AI 勵志、行銷（6） | [`gtm`](https://imitator.ai-apps.work/r/gtm)、[`vibegtm`](https://imitator.ai-apps.work/r/vibegtm)、[`the-path-to-ai`](https://imitator.ai-apps.work/r/the-path-to-ai)、[`dev-reinvented`](https://imitator.ai-apps.work/r/dev-reinvented)、[`value-today`](https://imitator.ai-apps.work/r/value-today)、[`cursor`](https://imitator.ai-apps.work/r/cursor) |
| 政治、軍事、選舉（9） | [`china`](https://imitator.ai-apps.work/r/china)、[`pearl-harbor-redux`](https://imitator.ai-apps.work/r/pearl-harbor-redux)、[`australia`](https://imitator.ai-apps.work/r/australia)、[`ko`](https://imitator.ai-apps.work/r/ko)、[`ko-prosecution`](https://imitator.ai-apps.work/r/ko-prosecution)、[`lindefu`](https://imitator.ai-apps.work/r/lindefu)、[`typhoon-morakot`](https://imitator.ai-apps.work/r/typhoon-morakot)、[`daetongnyeong`](https://imitator.ai-apps.work/r/daetongnyeong)、[`harvard`](https://imitator.ai-apps.work/r/harvard) |
| 書摘、自我成長、名人故事（轉述他人）（18） | [`algebra-of-happiness`](https://imitator.ai-apps.work/r/algebra-of-happiness)、[`not-giving-a-fk`](https://imitator.ai-apps.work/r/not-giving-a-fk)、[`want-it-all`](https://imitator.ai-apps.work/r/want-it-all)、[`pm-in-life`](https://imitator.ai-apps.work/r/pm-in-life)、[`katie-ledecky`](https://imitator.ai-apps.work/r/katie-ledecky)、[`generation`](https://imitator.ai-apps.work/r/generation)、[`neijuan`](https://imitator.ai-apps.work/r/neijuan)、[`dont-gen`](https://imitator.ai-apps.work/r/dont-gen)、[`trust`](https://imitator.ai-apps.work/r/trust)、[`nicolas-cole`](https://imitator.ai-apps.work/r/nicolas-cole)、[`lovart`](https://imitator.ai-apps.work/r/lovart)、[`palmer-luckey`](https://imitator.ai-apps.work/r/palmer-luckey)、[`john-stockton`](https://imitator.ai-apps.work/r/john-stockton)、[`fox-hsiao`](https://imitator.ai-apps.work/r/fox-hsiao)、[`bruces-story`](https://imitator.ai-apps.work/r/bruces-story)、[`high-school`](https://imitator.ai-apps.work/r/high-school)、[`7-fruits`](https://imitator.ai-apps.work/r/7-fruits)、[`harry-8`](https://imitator.ai-apps.work/r/harry-8) |
| 真人財富八卦、個人戰績（3） | [`hook-vs-joeman`](https://imitator.ai-apps.work/r/hook-vs-joeman)、[`terry-vs-gooaye`](https://imitator.ai-apps.work/r/terry-vs-gooaye)、[`tesla-story`](https://imitator.ai-apps.work/r/tesla-story) |
| 加密貨幣個別項目、演講（5） | [`crypto`](https://imitator.ai-apps.work/r/crypto)、[`crypto-info`](https://imitator.ai-apps.work/r/crypto-info)、[`ether-fi`](https://imitator.ai-apps.work/r/ether-fi)、[`bitcoin-vs-sp500`](https://imitator.ai-apps.work/r/bitcoin-vs-sp500)、[`house-vs-btc`](https://imitator.ai-apps.work/r/house-vs-btc) |
| 題目太窄或沒有鉤子（9） | [`magna`](https://imitator.ai-apps.work/r/magna)、[`shaleoil`](https://imitator.ai-apps.work/r/shaleoil)、[`rocket`](https://imitator.ai-apps.work/r/rocket)、[`from-oceans-to-orbits`](https://imitator.ai-apps.work/r/from-oceans-to-orbits)、[`tdoc-vs-hims`](https://imitator.ai-apps.work/r/tdoc-vs-hims)、[`blue-line-event`](https://imitator.ai-apps.work/r/blue-line-event)、[`taiwan-vacation`](https://imitator.ai-apps.work/r/taiwan-vacation)、[`tsmc-sh-2025`](https://imitator.ai-apps.work/r/tsmc-sh-2025)、[`taiwan-luxury-market`](https://imitator.ai-apps.work/r/taiwan-luxury-market) |

## 重製之後

1. 重製的報告用新 slug 發佈（不要覆蓋 2025 原頁，舊連結還在別處被引用）。
2. 在 `report-candidates.md` 推薦表加一列，備註寫「重製自 `<2025 slug>`」，再把這裡那一列標成已重製。
3. 每集的 PR 照 [`recipe.md`](recipe.md) 只動 `episodes/<ep>/`，不改這份。

