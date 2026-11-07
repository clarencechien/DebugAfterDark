# 深夜 Debug podcast pipeline 計劃

**狀態**：計劃（2026-11-04），還沒有實作。
**前身**：[`clarencechien/ttspoc`](https://github.com/clarencechien/ttspoc) 的 `podcast/`（POC，2026-09-25 到 2026-11-03，
對照到 `main` 的 `799872e`）。ttspoc 最後兩個 commit 已經寫好一份逐步的製作流程 `podcast/PIPELINE.md`，
工具也改成不綁 EP01、可以做任何一集。**那份是「一集怎麼做」的配方，這份是「整個節目怎麼營運」**：
選題、審稿、發佈、跟 imitator 的整合、上架平台。配方搬過來之後放在 `docs/recipe.md`，兩份不重複寫。
主持人的命名與人設在 [`HOST.md`](HOST.md)，EP00 自介與節目文案在 [`episodes/ep00-intro/script.md`](episodes/ep00-intro/script.md)。
**分工**：

| repo | 放什麼 |
|---|---|
| **DebugAfterDark**（這裡） | podcast 的一切：節目設定、聲線、寫稿 prompt、讀音表、逐集稿子、產線程式、成品 mp3、RSS feed 的產生器 |
| **imitator** | report（HTML）與它的 agent 版本（markdown）；Worker 多擔一份 podcast 檔案的 host 工作 |
| **ttspoc** | 凍結，當研究紀錄。README 加一行指到這裡 |

---

## 1. 目標：一份 report，三種讀法

| | 給誰 | 形式 | 網址 | 誰產生 |
|---|---|---|---|---|
| **report** | 人，用看的 | 單檔 HTML | `/r/{slug}`（現有，不動） | 寫報告的 agent |
| **podcast** | 人，用聽的；**門檻比 report 低** | mp3 + RSS | `/podcast/{show}/…` | 這個 repo 的產線 |
| **llm.txt** | agent | markdown | `/llms.txt`（全站索引）、`/r/{slug}.md`（單篇） | 寫報告的 agent，舊報告用腳本回填 |

- **不是每份 report 都有 podcast。** llm.txt 則每份都該有，而且它是 podcast 產線的輸入：
  `report.html → {slug}.md → podcast 稿 → mp3`。一次萃取，兩邊用。
- 單篇的路徑用 `/r/{slug}.md` 而不是 `/r/{slug}/llm.txt`，是照 [llms.txt 提案](https://llmstxt.org/)
  的慣例（同一個網址加 `.md`）。slug 只允許 `[a-z0-9-]`，所以 `.md` 後綴不會跟任何 slug 撞。
- **上架路徑跟 report 一樣只有 GitHub 與 CLI**，沒有網頁後台。
- 要能上 Apple Podcasts，也要能上 Spotify、YouTube、KKBOX、Pocket Casts 等吃 RSS 的平台
  —— 做好一份合規的公開 RSS，其他平台都是一次性的送審。

### 非目標
- 不做群組（group）可見度的 podcast。podcast app 不會帶 cookie，Apple 也要求 feed 公開；
  私密 feed 得用秘密網址，那是另一套憑證，等真的有需求再說。**v1 只替 public report 做 podcast。**
- 不做下載統計。imitator 的 spec 明確不做分析（§1 非目標），各平台後台自己有數字。
- 不做網頁播放器或後台。單集頁就是一份普通的 imitator report（見 §5.3）。

---

## 2. POC 學到什麼（產線的設計依據）

全部出自 `ttspoc/podcast/RESULTS.md`，這裡只留會改變做法的結論。

### 寫稿
1. **原文直接念不行。** 改寫成口語稿後盲測四次都勝出：每句 ≤ 20 字、每段 ≤ 1 個精確數字、不條列、
   不用書面詞、要有主持人反應與反問。規則在 `prompts/spoken_script_zh-TW.md`，用 `script_lint.py` 量化。
2. **每段分開改寫會長出口頭禪**（「你猜」8 段、「醬」8 段）。要有**整集口頭禪額度**，用完的詞列入後面段落的禁用清單；
   prompt 裡不能放可照抄的範例句。
3. **模型會自己加事實**（「蓋住一部分」寫成「蓋住一半」）。需要一道事實關卡，人工修改要記在 `manual_edits`。
4. **大陸用語要明列禁用**（更狠的是、坑、盲猜…），lint 抓、多候選挑。
5. **同音、易混詞要改稿，不是改念法**：季度檢討→公司每一季的檢討會、忙人→一群很忙的人、正本→原文、時間戳→時間戳記。
6. **稿子不要一句一行**，TTS 會在每個換行停下來。寫成段落，用標點控制停頓。

### 聲音
7. **每段 ≤ 350 字分段生成**，第一次就全部通過音長檢查。整集 2,698 字一次送也成功了，但音色仍漂 727 Hz，
   而且單次上限約 10.9 分鐘，所以**分段是預設**。
8. **語氣指示比聲線更影響口音與節奏。** v2 解決畏縮卻變播音腔；v4 台灣味最重但四聲被拉平、清晰度下降；
   **v5 = v4 + 「四聲要確實降下來」** 是目前的平衡點。
9. **沒有種子，同設定每次差很多**（同一段長停頓 4 次對 15 次）。每段念 3 次再挑。
10. **前後一致性要後製補**：逐段 -20 LUFS、音色匹配等化（往整集中位數拉 80%、每頻帶 ±6 dB），最後整集 -16 LUFS。
11. **不要加重壓縮**，會把氣音、齒音拉亮。溫和 EQ（eqA）就好。

### 品質檢查
12. **給評審看稿子的校對沒用**：它照著稿子「聽出」字，吻合度永遠 0.98 以上。**必須盲聽**：
    STT 不給稿子，轉寫後逐字比對，比對要**連聲調一起比**（季度 jì dù 對 基督 jī dū）。
13. **Breeze-ASR-25** 最懂台灣華語與中英夾雜（錯誤率 3.6% 對 Whisper 6.3%）。Whisper 會在停頓處幻覺，要偵測後重轉。
14. **Gemini 評審分不出台灣腔與大陸腔**，跟台灣母語者的判斷相反；磁性也排不出穩定名次。
    **口音與磁性只能人耳判斷**，自動分數只拿來挑「清楚、一致、停頓少」。
15. 挑選順序：清晰度（差 0.012 以內視為同級）→ 一致性（聲紋差 ≤ 0.015、音色重心差 ≤ 300 Hz）→ 長停頓最少。
    最後再做一輪**相鄰段比對**（`select_takes.py --neighbour`）：某次生成跟前後段的相似度高出 0.01 以上就換掉。
    EP01 的結尾段靠這一步從 0.917 拉到 0.955。

### 最後兩個 commit 定下來的事（`87d6a2e`、`29ace11`）
16. **正式製作的預設是 D1 + v5**：設計聲線 `voice_b3c8x0jsntqc`、`styles.json` 的 v5、每段 3 次、Breeze 挑選、
    逐段 -20 LUFS、音色匹配。ElevenLabs Hardy 降為替代方案：最清楚，但長停頓是 D1 的兩倍。
17. **驗收門檻有數字了**：Breeze 盲聽 CER 各段平均 ≤ 3.5%（EP01 是 3.0%）、兩套辨識都聽錯的內容詞 0 處、
    `consistency_check.py` 全部段落在範圍內。不合格的段用 `--only <段> --add-takes 3` 補生成，只新增不覆蓋。
18. **自動檢查抓不到歸屬錯誤。** `ep00_smoke` 這個兩段的測試集在人工核對時抓到兩個事實錯誤：
    「其他評論者說的」被寫成「Felix 說的」、「三處不符」被誇大成「根本對不上」。這兩種錯的數字和人名都對，
    比對數字與專有名詞的關卡會放行，**只有逐段對照素材讀過一遍才抓得到**。所以人工關卡 A 不能省。
19. **容器重啟會砍掉執行中的工作**。改寫要加 `--resume`、生成檔已存在就不重做；長的步驟都要能中斷續跑。
20. **Breeze 很重**：每個新容器要下載約 3 GB 權重並轉成 CTranslate2（約 1.5 GB），CPU 上轉寫 30 次生成約 20 分鐘。
    所以 Breeze 不放進發佈 Action，在製作端跑（見 §7）。
21. **音色匹配管不到語速和語調**（2026-11-04 EP00 試作）：三段通過一致性檢查、音色重心只差 127 Hz，
    聽起來仍然「接起來不太一樣」，因為最後一段每秒快了一個字、停頓少了一截，而且三段的 mood 各不相同。
22. **一次生成沒有接縫，但不一定比較好**：EP00 整集一次生成聽起來比較連貫，但咬字抖、口音偏大陸。
    量出來音高跳動比分段版多 29%（0.259 對 0.201 半音），6 次一次生成的中位數也比分段高；mood 裡「整集前後一致」
    這類控制型句子可能把口音推向播音腔。所以**分段是預設**，一次生成只當候選；全集同一個 mood、不寫控制型句子；
    挑選加上音高跳動、語速、接縫亮度三條。見 `episodes/ep00-intro/review/README.md` §3、§4。

23. **集與集的關係要講出來**（2026-11-04）：EP02 是 EP01 第五招的下集，但兩集的稿子都沒提到彼此，聽起來只像
    「機翼尖端在閃」又講了一次。原因是寫稿 prompt 有「事實只能來自素材」，草稿裡的「上一集聊過」被當成多餘的話刪掉。
    現在 `draft.json` 可以寫 `previously` 和 `recap`，改寫會要求那一段回顧上一集；節目說明寫「上一集：」「延伸收聽：」。
24. **Breeze 不能用 beam 1 加速**：只快 30%，但會改變挑選結果（docs/recipe.md 第 5 步）。真的要快，要減少每段的生成次數或換有 GPU 的環境。
25. **`pkill -f` 和 `pgrep -f` 會找到自己**：要找的字串也在背景指令自己的命令列裡，EP01 的串接流程因此空等了 20 分鐘，
26. **書面詞和長段落會讓聲音變差**（2026-11-05 EP06）：第一版段落近 400 字、滿是財經書面詞與 edge、alpha 這類英文術語，還有改口；數字上錯誤率 2.8%、音高跳動 0.242，看起來跟前幾集差不多，但試聽是「前五分鐘不穩、偏大陸腔、咬字聽不出詞」。改成白話、拿掉改口、每段 300 字內、每句平均 16 到 18 字後整集重生成：錯誤率 2.1%、音高跳動 0.238，試聽通過。數字抓不到口音，**稿子的用字本身就是聲音品質的一部分**（寫稿規則第 18 條、`script_lint.py` 的 `jargon`、`self_corrections`）。
27. **稿子也要過一次繁中 AI 味檢查**（2026-11-07）：`tools/twtone_check.py` 呼叫 [twtonepoc](https://github.com/clarencechien/twtonepoc) 的 twtone，零 token、一集不到一秒。它抓的是配對研究證實有效的表層訊號（「不是…而是」對舉的密度台灣 2015–2022 的文章只有每千字 0.08）和 zhtw-mcp 的台灣用詞；只報告不改寫，「要改」的句子由 agent 逐句最小改動。改寫模型寫出來的稿子最常超標的是對舉句。
    手動停流程時也停掉了自己的指令。等待和停止都改用 PID。

### 還沒決定的事（產線的前置條件，見 §7 M0）
- **D1 是預設，但還沒有經過台灣母語者盲聽確認。** RESULTS.md 的下一步第 1、2 項仍然是「人耳挑聲線」「人耳盲聽三集」，
  口音一直標著「待台灣母語者確認」。M0 要做的是確認 D1，不是從頭三選一；不通過才回頭比 Hardy 與 Enceladus。
- **主持人的名字**（見 `HOST.md`）。

### 成本
照配方正式做一集（約 9 分鐘、2,400 字）：改寫 0.36 + 語音 0.40（三次生成，含一成補生成）+ 盲聽 0.06 =
**約 US$0.82，2027-01-01 起 Gemini 漲一倍約 US$1.63**。精簡做法（1 個候選稿、每段念 2 次）約 0.45，2027 起約 0.89。
Breeze 與一致性檢查在本機跑，不花錢。時間約 50 分鐘，加上 agent 寫稿和核對。都不是決策因素。
（2026-11-03 整天的實驗花了約 3.7 美元，大多是試錯。）

---

## 3. 產線總覽

```
imitator                          DebugAfterDark                                   imitator
─────────                         ───────────────────────────────────────────────  ─────────────────────
/r/{slug}.md ──▶ 0 選題 ──▶ 1 素材 ──▶ 2 大綱 ──▶ 3 改寫 ──▶ 4 lint+事實 ──┐
                                                                           ▼
                                                              ◆ 人工關卡 A：稿子（PR review）
                                                                           │
                 5 TTS×3 ──▶ 6 挑選 ──▶ 7 後製 ──▶ 8 盲聽 QA ──▶ 9 逐字稿 ◀─┘
                                                                           │
                                                              ◆ 人工關卡 B：聽一次（PR review）
                                                                           │
                                                   10 打包 ──▶ merge 到 main ──▶ 11 發佈 ──▶ /podcast/{show}/audio/*.mp3
                                                                                          /podcast/{show}/feed.xml
                                                                                          /r/dad-ep{NN}（單集頁）
                                                                                          portal 與 /llms.txt 出現 🎧
```

**一集 = 一個 PR。** 兩道人工關卡都是 PR review，merge 就是核准；merge 到 `main` 觸發發佈。
這跟 imitator 的 `inbox/` 一樣：GitHub 上的動作就是上架動作，不用另外的後台。

### 各階段

| # | 階段 | 輸入 → 輸出 | 自動檢查 | 來自 POC 的哪裡 |
|---|---|---|---|---|
| 0 | 選題 | `/llms.txt` → `episodes/{id}/episode.json`（report slug、目標長度） | report 必須是 public | — |
| 1 | 素材 | `/r/{slug}.md` → `source.md`（凍結一份，記 sha256） | 抓不到 `.md` 時退回 HTML 萃取 | `script/sources/` |
| 2 | 大綱 | `source.md` → 8–10 段，每段一個重點、≤ 350 字預算 | 總字數對應 6–10 分鐘（每秒約 4.2 字） | `ep01.json` 的段落表 |
| 3 | 改寫 | 大綱 + 素材 + 上段結尾 → 每段 3 個候選 | 口頭禪額度、禁用詞 | `rewrite_episode.py` |
| 4 | lint + 事實 | 候選 → `script.json` | `mainland_words` 為空、`precise_numbers` ≤ 1；句長、條列、語助詞密度；**稿中每個數字與專有名詞都要能在素材裡找到**；讀音表與易混詞表比對。之後 agent 逐段對照素材讀一遍，專抓**歸屬（誰說的）與程度（誇大）**，見 §2 第 18 點 | `script_lint.py`、配方第 3 步的核對表、`manual_edits` |
| 5 | TTS | 每段 × 3 次，全集同一個 mood；一次生成只當候選（§2 第 22 點） | 音長 ÷ 預期音長在 0.6–1.6 之內，否則重試 ≤ 2 次 | `make_podcast.py episode --takes` |
| 6 | 挑選 | 3 個 take → 1 個 | Breeze 盲聽 CER → 專有名詞念法（Ping）→ 穩定度（音高跳動）→ 語速（各段字／秒離中位數 ≤ 10%）→ 一致性與接縫亮度 → 長停頓 | `select_takes.py --consistency` |
| 7 | 後製 | 選中的段 → `master.mp3` | 逐段 -20 LUFS、match-EQ、eqA、段間 0.6 s、整集 -16 LUFS / true peak ≤ -1 dBTP。順序是片頭音效 → cold open（當集的鉤子）→ 固定開場（`show/ident/`，每集同一個音檔）→ 正文 → 片尾 | `make_podcast.py master --match-eq` |
| 8 | 盲聽 QA | `master.mp3` → `qa.json`（標記點 + 時間） | 整集 Breeze CER ≤ 3%，兩套 ASR 都錯的點要處理 | `stt_check.py` |
| 9 | 逐字稿 | 稿子（文字真值）+ STT 時間戳 → `transcript.vtt` | 每個 cue 都對得回稿子 | 新增 |
| 10 | 打包 | 上面全部 → `episode.json` 補齊長度、bytes、sha256、模型與聲線紀錄、成本 | schema 驗證 | `cost_estimate.py` |
| 11 | 發佈 | `main` 上的 `episodes/*` → imitator | 見 §5 | 新增 |

### 「降低入門門檻」寫進寫稿規則
report 是寫給已經有興趣的人看的；podcast 的工作是讓還沒興趣的人聽完覺得「我懂了，想去看全文」。
所以 `prompts/` 在 POC 的 15 條之外加一份 `beginner_rules.md`：

1. **假設聽眾沒看過 report。** 第一段先講「這跟你有什麼關係」，再講內容。
2. **術語第一次出現就用一句話解釋**，之後不再解釋；整集術語上限 5 個，其餘換白話。
3. **每個概念配一個生活比喻**（POC 的「帳單先付」「複寫單的第二聯」就是這種）。
4. **只講 report 的 2–3 個重點**，其餘明說「細節在文章裡」。不追求完整，追求聽得懂。
5. **結尾給一個下一步**：一件今天就能做的事，加上「全文在我們的報告網站上，標題是〈…〉」（口播不念 imitator，見 §4）。
   網址不用念，放在 show notes。
6. 財經類 report 要加「不構成投資建議」的口頭與 show notes 聲明；摘譯類 report 要明說原作者與原文，
   podcast 是導讀與評論，**不逐句念譯文**。

---

## 4. 這個 repo 的結構

**現況（2026-11-04）**：M2 的第一步做完了 —— ttspoc 的工具原樣搬進 `tools/`，路徑改成下面的結構，修了段間停頓的 bug，
挑選加了穩定度與語速；EP00 定稿、EP01 從 ttspoc 搬來、EP02 是第一集照新產線做的。整理成 Python 套件與 `dad` CLI 是之後的事。

```
README.md
PIPELINE.md                     ← 這份：節目怎麼營運
HOST.md                         主持人 Ping 的命名與人設
docs/recipe.md                  一集怎麼做（ttspoc podcast/PIPELINE.md 搬來改寫），照著做就能出一集
show/
  ident/                        固定開場（ident.flac，每集共用），見 show/ident/README.md
  show.json, cover-3000.jpg     節目設定與封面（M0，未做）
voices/
  registry.json                 Gemini 設計聲線 ID（D1、D2、remix）與描述、到期日
  elevenlabs.json               ElevenLabs 聲線（替代方案）
  references/                   每個聲線的參考錄音 + references.json（聲紋、音高、sha256），聲線消失時用 match_voice.py 找替代
prompts/
  spoken_script_zh-TW.md        寫稿 prompt（Ping、cold open、breakpoint、降低門檻）
  styles.json                   TTS 語氣 v1–v5，v5 是預設
  taiwan_mandarin_features.md   台灣華語發音特色
tools/
  rewrite_episode.py            第 2 步：口語改寫
  script_lint.py                第 3 步：口語程度與大陸用語
  make_podcast.py               第 4、6 步：生成與後製（episode / master）
  select_takes.py               第 5 步：挑選（清晰度 → 專有名詞 → 穩定度 → 語速 → 一致性 → 停頓）
  stt_check.py                  第 7 步：Breeze 盲聽校對
  consistency_check.py          第 7 步：段與段一致性（含接縫亮度、語速）
  measures.py                   音高跳動、語速、漂移、接縫的量測
  gemini_check.py               Gemini 盲聽錯誤率與 Ping 念法（粗篩）
  package_episode.py            第 8 步：episode.json 的長度、bytes、sha256
  match_voice.py, compare_voices.py, elevenlabs_tts.py   聲線比對與替代方案
tests/
  smoke/                        兩段的回歸測試集（ttspoc 的 ep00_smoke），不上架
episodes/<ep>/
  episode.json                  guid、標題、說明、report slug、聲線、製作方式、長度、bytes、sha256
  draft.json, sources/          第 1 步：草稿與原文摘錄
  script.json, rewrites/        第 2、3 步：定稿與每段的候選、manual_edits
  qa/                           挑選、盲聽、一致性、響度、音色匹配的紀錄
  <ep>.mp3                      成品
out/                            中間檔（take、正規化後的段落），不進 git
```

### 從 ttspoc 搬了什麼（2026-11-04，來源 `799872e`）
- **工具**：`make_podcast`、`rewrite_episode`、`script_lint`、`select_takes`、`stt_check`、`consistency_check`、`compare_voices`、
  `match_voice`、`elevenlabs_tts`。第一個 commit 是原樣複製，之後的 commit 才改，diff 看得出改了什麼。
- **改了什麼**：路徑；`make_podcast.py master` 的段間停頓 bug（插停頓的兩行縮排在 `--match-eq` 的區塊裡，從來沒插進去，EP01 的成品因此沒有段間停頓）；
  `--ident`、`--out`、預設 v5、ID3 揭露；`select_takes.py` 加專有名詞、穩定度、語速三關；`consistency_check.py` 加接縫亮度與語速；
  `rewrite_episode.py` 改讀 `episodes/<ep>/`；寫稿 prompt 改成 Ping 與新的每集結構。
- **資料**：prompts、styles、聲線登記與參考錄音、EP01 的稿子與 QA、`ep00_smoke` → `tests/smoke`。
- **沒搬**：聲線比較、ElevenLabs 對照、語氣 A/B 等實驗，它們是 ttspoc 的研究紀錄。
- 還沒做：`smoke` 與 EP01 用新工具從頭重跑一次。EP02 從頭跑完，當作新工具可用的證明。

### 成品 mp3 放 git
一集 128 kbps 單聲道約 8–10 MB。放 git 的理由：發佈 Action 需要拿得到檔案；這個 repo 是 podcast 的 source of truth，
R2 上的那份壞掉或被刪可以從這裡重推。**這是 podcast 產線本身的輸出，不是 imitator 的 artifact 備份機制** ——
imitator「不做 artifact 備份」的決定不受影響。repo 超過 1 GB（約 100 集）時再評估改 Git LFS 或 GitHub Release asset。

---

## 5. 跟 imitator 的整合

> **過渡方案（2026-11-04 起）：先用這個 repo 的 GitHub Pages 當 podcast host。** `tools/build_site.py` 把 final 的集數組成
> `feed.xml`、封面、音檔（檔名帶 sha256 前 8 碼）和收聽頁，`.github/workflows/pages.yml` 部署。Release 不適合放音檔：
> 實測會 302 到一小時就過期的簽名網址、Content-Type 是 `application/octet-stream` 加 `attachment`；Pages 回 `audio/mpeg`、支援 Range。
> 限制：站台 1 GB（約 100 集）、每月流量軟上限 100 GB。**feed 網址送審後就改不掉**，Pages 不能做伺服器端 301，
> 所以建議在送審前就設自己的子網域（`show.json` 的 `custom_domain`），之後要搬到 imitator 的 Worker 只改 DNS。
> 下面是原本規劃的 imitator 整合，搬過去時照這份做。

原則沿用 imitator 的 spec：**source 留 git，artifact 去 R2；Worker 盡量維持 dumb host。**
所以 RSS 由這個 repo 產生（feed 的歷史就是 git 歷史），Worker 只負責收、驗、吐，再多維護一個「哪份 report 有 podcast」的衍生索引。

### 5.1 URL 與 R2 key

| 網址 | 內容 | 可見度 | R2 key |
|---|---|---|---|
| `/r/{slug}` | report HTML（現有） | public / group | `artifacts/{slug}.html` |
| `/r/{slug}.md` | report 的 agent 版 | 跟著 report | `artifacts/{slug}.md` |
| `/llms.txt` | 全站索引，Worker 從 KV 即時組出來 | 只列 public | — |
| `/podcast/{show}/feed.xml` | RSS | public | `podcasts/{show}/feed.xml` |
| `/podcast/{show}/audio/{file}.mp3` | 音檔，**不可覆寫** | public | `podcasts/{show}/audio/{file}.mp3` |
| `/podcast/{show}/transcripts/{file}.vtt` | 逐字稿 | public | `podcasts/{show}/transcripts/{file}.vtt` |
| `/podcast/{show}/cover.jpg` | 封面 | public | `podcasts/{show}/cover.jpg` |
| `/r/dad-ep{NN}` | 單集頁（普通的 report artifact） | public | `artifacts/dad-ep{NN}.html` |

**feed 網址一旦送審就是永久的**：`https://imitator.ai-apps.work/podcast/debug-after-dark/feed.xml`。
要搬家只能靠 301 加 `<itunes:new-feed-url>`，所以 M3 之前要定案（§8 的問題 1）。

### 5.2 寫入 API（新增）

| | 請求 | 授權 | 規則 |
|---|---|---|---|
| agent 版 | `PUT /v1/a/{slug}.md`，`text/markdown` | report 的 owner | report 必須已存在；可見度跟 report；Worker 取第一個 `> ` 段落當摘要寫進 `idx:{slug}`，給 `/llms.txt` 用 |
| 音檔 | `PUT /v1/p/{show}/audio/{file}.mp3`，`audio/mpeg` | show 的 owner | **key 已存在就 409**；檔名帶 sha256 前 8 碼（`ep01-3f9a2c1d.mp3`），Worker 驗 body 的雜湊跟檔名相符 |
| 逐字稿、封面 | `PUT /v1/p/{show}/transcripts/{file}.vtt`、`/cover.jpg` | show 的 owner | 只收 `text/vtt`、`image/jpeg`、`image/png`；**不收 SVG**（SVG 能帶 script） |
| feed | `PUT /v1/p/{show}/feed.xml`，`application/rss+xml` | show 的 owner | **發佈的那一刻**：驗證通過才寫入，見下 |
| 刪除 | `DELETE` 同上路徑 | owner | 目前 feed 還引用的音檔回 409 |

**show 的擁有權**沿用 artifact 的規則：第一個寫入 `/v1/p/{show}/` 的 group 擁有它，不轉手。
建議開一個專用的 group（例如 `podcast`），GitHub secret 用它的 token —— 這個 repo 的 Action 就只能動 podcast，
碰不到任何 report。write token 90 天到期，跟 inbox 那把一樣要輪替。

**音檔不可覆寫**是這份計劃最重要的一條。R2 沒有 versioning，覆寫就是永久消失；
而 podcast app 會快取音檔，同網址換內容的結果不可預期。改成「新內容 = 新檔名，feed 指過去，guid 不變」，
兩個問題一起消失，而且音檔可以 `Cache-Control: immutable`。

**feed PUT 的驗證**（失敗回 400、什麼都不寫，錯誤訊息照 `publishing-rules.md` 的格式用英文寫 error / reason / fix）：
1. 有 XML 宣告、`<rss` 與 itunes namespace；大小 ≤ 1 MB。
2. 每個 `<enclosure url>` 都在 `/podcast/{show}/audio/` 底下，**R2 裡真的有那個物件，而且 `length` 等於物件大小**。
   壞掉的 enclosure 到了 Apple 那邊才發現，要好幾天才修得回來；在這裡擋最便宜。
3. 每個 `<imitator:report>` 指到的 slug 存在且是 public。
4. 通過後寫入 feed，並重建這個 show 的 `pod:{reportSlug}` KV（刪掉 feed 裡已經沒有的）。

Worker 環境沒有 DOMParser，所以第 2–3 步是對 `<item>…</item>` 區塊做字串比對。這只有在 feed 是我們自己產生的格式時才可靠 ——
看不懂的 feed 就拒絕，不要猜。

### 5.3 report 怎麼「有 podcast link」
**不改 report 的 HTML。** report 的 owner 和 show 的 owner 可能是不同 group；而且 imitator 的 Worker 不改 body。做法：

- feed 每個 `<item>` 帶自訂 namespace 的 `<imitator:report>fifth-move</imitator:report>`，feed 寫入時 Worker 由它建
  `pod:fifth-move → {show, guid, title, episodePage, audio, duration}`。**連結是 podcast 這邊宣告的**，不需要 report 的 owner 動手。
- **portal**：有 `pod:` 的 report 旁邊顯示 🎧，連到單集頁。
- **`/llms.txt`**：該 report 那行後面加 `[podcast](單集頁)`，另有一節列 feed 與各集。
- **`/r/{slug}` 與 `/r/{slug}.md` 的回應 header**：加 `Link: </r/dad-ep01>; rel="alternate"; type="text/html"; title="podcast"`，
  有 `.md` 的話再加 `Link: </r/{slug}.md>; rel="alternate"; type="text/markdown"`。只加 header，body 一個 byte 都不動。
- **單集頁 `/r/dad-ep{NN}`** 是產線產生的普通 public report：用 imitator 的 `report.css` 底盤，內容是 `<audio controls preload="none">`、
  show notes、逐字稿全文、回到原 report 的連結、各平台訂閱連結。它照樣跑在 sandbox 裡（`<audio>` 不需要 CORS），
  照樣過 imitator 的發佈規則（不載入第三方 script、不用 storage API）。它也有自己的 `.md`（就是逐字稿），agent 可以讀。
- report 作者**想要**在文章裡放播放器也可以，自己重推 HTML 加一個 `<audio>`；這是選項，不是產線的一部分。

### 5.4 讀取端的 header

| 路徑 | Content-Type | 其他 |
|---|---|---|
| `*.mp3` | `audio/mpeg` | **支援 `Range` 回 206 與 `HEAD`**（Apple 明文要求）；`Accept-Ranges: bytes`；`Cache-Control: public, max-age=31536000, immutable`；`Access-Control-Allow-Origin: *` |
| `feed.xml` | `application/rss+xml; charset=utf-8` | `public, max-age=300`；ACAO `*`（網頁版 podcast app 在前端抓 feed） |
| `.md`、`llms.txt`、`.vtt` | `text/markdown` / `text/plain` / `text/vtt`，皆 `charset=utf-8` | 跟著可見度決定快取 |
| 以上全部 | — | `X-Content-Type-Options: nosniff` |
| feed、`.md`、`llms.txt`、`.vtt` | — | 另加 `Content-Security-Policy: sandbox; default-src 'none'` —— XML 被瀏覽器直接打開時可以靠 XHTML namespace 執行 script，這行把那條路關掉。音檔與圖片不加：它們本身不能執行程式碼，加了反而可能影響瀏覽器直接播放 |

R2 的 `get(key, { range: request.headers })` 直接吃 Range header。ACAO `*` 只給 public 的 podcast 檔案，`/r/` 與任何 group 內容都不給。

### 5.5 imitator 那邊要改的東西（清單）

1. `worker/src/index.js`：新路由 `/llms.txt`、`/r/{slug}.md`、`/podcast/…`、`/v1/a/{slug}.md`、`/v1/p/…`，早退順序照 spec §8.3。
2. 新模組 `podcast.js`（音檔、feed 驗證、`pod:` 索引）、`llms.js`（索引組裝）；`portal.js` 加 🎧 與 feed 的 `<link rel="alternate">`。
3. **Cloudflare WAF custom rule 要先改**：加上 `/llms.txt`、`starts_with "/podcast/"`、`starts_with "/v1/p"`。
   spec §8.3 寫過：不改的話新路由會在邊緣被擋掉，而且 Worker log 裡什麼都看不到。**部署前做，不是部署後。**
4. Body 上限：音檔沿用 25 MB（128 kbps 單聲道約 26 分鐘），目標每集 ≤ 15 分鐘，暫時不用調。
5. `docs/spec.md` 加一節 podcast 與 llms.txt；`docs/publishing-rules.md` 加音檔與 feed 的規則；`CLAUDE.md` 與
   `docs/claude-md-snippet.md` 加「發佈 report 時一併推 `.md`」。
6. `style/STYLE.md` 加「agent 版」一節：寫 report 時一起寫 `{slug}.md`，固定開頭格式（`# 標題`、`> 一段摘要`、網址、日期、
   重點、正文、來源）。
7. `inbox/` 收 `{slug}.md`，`publish-inbox.mjs` 先推 HTML 再推 `.md`；workflow 的 `paths` 加 `inbox/**.md`。
8. `scripts/extract-md.mjs`（Node 內建模組，跟 `inline-cdn.mjs` 一樣零相依）：把 `archive/report/*.html` 萃取成 markdown 回填。
   用 curl 直接推、沒進 git 的 report，public 的從 `/r/{slug}` 抓，group 的由 owner 自己處理。
9. `worker/test/`：Range（含 `bytes=0-1`、尾段、超界 416）、HEAD、音檔 409、雜湊不符、feed 各種驗證失敗、
   `pod:` 重建、`.md` 可見度跟著 report、`/llms.txt` 不漏 group 標題。

---

## 6. 上架 podcast 平台

### 6.1 feed 要有的東西
依 Apple 的 [Podcast requirements](https://podcasters.apple.com/support/823-podcast-requirements)
與 [RSS 指南](https://help.apple.com/itc/podcasts_connect/en.lproj/itcb54353390.html)（2026-11-04 查閱，送審前再對一次）：

- RSS 2.0、公開可讀、XML 宣告、itunes namespace；伺服器支援 HEAD 與 byte-range。
- 節目層：`title`、`description`、`language`（`zh-tw`）、`itunes:image`（1400–3000 px 正方形 JPEG/PNG、RGB、無 alpha）、
  `itunes:category`（Technology，大小寫要跟 Apple 一致）、`itunes:explicit`、`itunes:author`、`itunes:owner`/`itunes:email`、
  `itunes:type`（episodic）、`link`。
- 每集：`title`、`enclosure`（url、length、type）、**永遠不變的 `guid`**（用 `debug-after-dark:ep01` 這種，不用網址）、
  `pubDate`（RFC 2822）、`description`（show notes，含原 report 網址）、`itunes:duration`、`itunes:episode`、`link`（單集頁）。
- Podcasting 2.0：`podcast:transcript`（指到 `.vtt`）、`podcast:locked`（防止別人把 feed 匯入其他 host）、`podcast:guid`。
- 檔名與網址只用 ASCII 英數（加連字號）。
- `feed.py` 是純函式：同樣的 `show.json` 與 `episodes/` 一定產生 byte-for-byte 相同的 feed，測試直接比對快照。

### 6.2 AI 聲音的揭露
這個節目的主持人是合成聲音。各平台規定還在變動，搜尋到的說法互相矛盾，Apple 官方頁面沒找到明確條文。
不論規定怎麼寫都照這樣做：
- 節目描述第一句、每集 show notes 結尾都寫「本節目的聲音由 AI 語音合成，內容改寫自 imitator 上的文章」；
- 片頭用一句話講一次；
- 不複製、不模仿任何真人的聲音（POC 已經這樣做，`voices/registry.json` 記錄每個聲線的來源）。
- Gemini 的輸出都帶 SynthID 浮水印。
- 送審前到 Apple 與 Spotify 的內容規範頁再確認一次，把結果記進 `show/README.md`。

### 6.3 送審（一次性，人做）

| 平台 | 方式 | 注意 |
|---|---|---|
| Apple Podcasts | Podcasts Connect → 新增節目 → 貼 feed 網址 → 驗證 → 送審 | 需要 Apple ID；審核要幾天；Overcast、Castro、Pocket Casts 等多數 app 會跟著 Apple 目錄 |
| Spotify | Spotify for Creators → Add a new show → Find an existing show → Somewhere else → 貼 feed | **驗證碼寄到 feed 裡的 `itunes:email`**，所以那個信箱要收得到信（§8 問題 3） |
| YouTube | YouTube Studio 的 RSS 匯入 | 台灣是否開放要確認 |
| KKBOX | KKBOX podcast 的 RSS 投稿 | 台灣聽眾的大宗之一，流程要確認 |
| Podcast Index | podcastindex.org 提交 | 開放目錄，很多獨立 app 用它 |

建議**上線時至少有 2–3 集**再送審，第一印象比較完整。送審前用 Apple 的 validator 跑一次。

---

## 7. 里程碑

| 階段 | 內容 | 完成的定義 |
|---|---|---|
| **M0 決策**（人） | 台灣母語者盲聽確認 D1 + v5（不通過才比 Hardy、Enceladus）；**主持人名字**（`HOST.md` 的試念測試）；節目名稱與 show slug；封面；feed 用的公開信箱；podcast 用的 group | `show/show.json` 與 `voices/registry.json` 定案 |
| **M1 llm.txt**（imitator） | `.md` 寫入/讀取、`/llms.txt`、`Link` header、`extract-md.mjs` 回填、STYLE.md/CLAUDE.md/inbox 更新 | 所有 public report 都有 `/r/{slug}.md`；`/llms.txt` 列得出全部；**跟 podcast 無關，可以先上** |
| **M2 產線搬家**（這裡） | 先原樣搬 ttspoc 的工具與配方（**2026-11-04 完成**）；EP00 定稿、固定開場（完成）；EP02 照新配方做一集（見 `episodes/ep02-harness-probe/`）；之後再整理成套件與 `dad` CLI、讀音表 | EP02 的 CER ≤ 3.5%、一致性全過 |
| **M3 podcast host**（imitator） | §5.5 的 1–5、9；WAF 規則先改 | 測試全過；手動推一份測試 feed 到一個測試 show，用 curl 驗 Range/HEAD，用 Apple validator 驗 feed |
| **M4 發佈自動化**（這裡） | `feed.py`、`episode_page.py`、`scripts/publish.py`、`.github/workflows/publish.yml` | merge 一個 EP 的 PR 後，音檔、逐字稿、feed、單集頁都上線，portal 出現 🎧 |
| **M5 開台** | 做 EP02、EP03；送 Apple、Spotify、其他平台 | 三個平台都搜得到 |
| **M6 穩定** | 每週一集的節奏；聲線健康檢查 | 連續四週準時，沒有人工救火 |

M1 跟 M2 可以同時做，互不相依。

### 發佈 Action 的安全
照抄 imitator `publish-inbox.yml` 的守則：
- trigger 只有 push 到 `main`，**不用 `pull_request_target`**（fork 的 PR 拿不到 secret 的前提）。
- 只用 `actions/checkout` 並釘 commit SHA；runner 內建 Python，`publish.py` 只用標準函式庫，不 `pip install`。
- 發佈順序固定：**音檔 → 逐字稿 → 單集頁 → feed 最後**。feed 是 commit point，前面任何一步失敗就不推 feed，
  平台看到的永遠是一致的狀態。音檔不可覆寫，所以重跑整個 Action 是安全的（已存在且雜湊相同就略過）。
- 產生音檔的步驟（呼叫 TTS、跑 Breeze）**不在 Action 裡跑**，在 Claude Code session 或本機跑，結果 commit 進 PR。
  Action 只有發佈權限，沒有 TTS 的 key。

CLI 路徑就是在本機跑同一支 `python3 scripts/publish.py episodes/ep02-xxx`，`IMITATOR_TOKEN` 讀環境變數，規矩跟 imitator 的 `CLAUDE.md` 一樣。

---

## 8. 待決定的問題

1. **節目名稱與 feed 網址**：已決定（2026-11-04）。節目「深夜 Debug｜Debug After Dark」，feed `https://podcast.ai-apps.work/feed.xml`：Cloudflare DNS 一筆 DNS only 的 CNAME 指向 `clarencechien.github.io`，GitHub Pages 設 custom domain 並 Enforce HTTPS，舊的 github.io 網址 301 過來。以後搬到 imitator 的 Worker 只改 DNS，Worker 要在這個子網域的根目錄提供 `/feed.xml` 與 `/audio/...`。
2. **主持聲線**：預設 D1 + v5，待台灣母語者確認。**已決定不走聲音複製**（2026-11-04）：主持人是 AI 角色，不代表任何真人。
3. **主持人名字**：建議 Ping，收尾單元叫「今晚的 breakpoint」（已決定保留）。理由與試念測試在 `HOST.md`。
4. **feed 的公開信箱**：Spotify 驗證碼寄到這裡，而且它公開在 feed 裡、會被爬。建議開一個專用 alias，不用個人信箱。
5. **頻率**：每週一集？依 report 產出量決定。
6. **哪些 report 適合**：public、不會很快過時、有故事可講。`HOST.md` 的節目定位把範圍從 code、Agent 擴大到「人生與 Mindset」，
   所以財經、移居這類 report 也在範圍內；數字密集的財經表格類要先試一集，看門檻降不降得下來，並加上不構成投資建議的聲明。
7. **單集頁的 slug 前綴** `dad-ep{NN}` 會出現在 portal 列表裡，要不要之後讓 portal 把它們分成一區。
8. **多語版**：做得到，先不做（2026-11-04）。英文版與日文版 EP00 已試作，稿子與成品留在 `episodes/ep00-intro/en/`、`ja/`，結果在 `episodes/ep00-intro/review/multilingual-pilot.md`，逐句對照在 `multilingual-scripts.md`，節目擁有者聽過，稿子沒問題。
   要做的時候：每種語言一個獨立節目與 feed（`/en/feed.xml`、`/ja/feed.xml`）；英文由節目擁有者審；日文在音檔開頭與說明揭露「沒有經過母語者確認」，第一集最好仍找一位母語者聽過再決定；音檔量變大前先把 mp3 搬到 Cloudflare R2。工具：`make_podcast.py` 讀 script.json 的 `chars_per_sec`、`mood_joiner`、`base_style_v5`，挑選與檢查用 `tools/lang_check.py`。

---

## 9. 風險

| 風險 | 影響 | 對策 |
|---|---|---|
| **聲線消失**：Gemini 設計聲線閒置一年過期；換模型後同名聲線會漂移；ElevenLabs 聲音庫的聲音由配音員控制，可能下架或改條款 | 節目換了一個人 | 釘死模型版本；定期使用保持效期（ttspoc 的配方寫「使用會延長效期」，但 11-03 當天實測效期沒有立即更新，M2 要驗）；保留參考錄音並用 `match_voice.py` 找最接近的替代；用聲音庫的聲音前讀清楚商業授權。已決定不走聲音複製，所以**參考錄音加 `match_voice.py` 是唯一的備援**，`voices/references/` 不能遺失 |
| Gemini 2027-01-01 漲一倍 | 一集約 US$1.34 | 可接受；必要時語音改 Flash-Lite 或 ElevenLabs |
| 自動評審對口音無效 | 大陸腔混進去沒人發現 | 關卡 B 必須是台灣母語者 |
| 模型加事實 | 節目講了 report 沒講的事 | §3 第 4 階段的數字與專有名詞比對 + 人工關卡 A |
| feed 寫壞 | 各平台顯示錯誤或下架單集 | Worker 端驗證（§5.2）；feed 可從 git 重新產生 |
| R2 物件被刪 | 音檔 404 | 這個 repo 有成品，重推即可；音檔不可覆寫、被 feed 引用的不可刪 |
| 摘譯類 report 的著作權 | 平台下架 | 只做導讀與評論，註明原作者與原文，不逐句念譯文 |
| 新路由忘了改 WAF | 上線後全部被邊緣擋掉、log 是空的 | §5.5 第 3 項放在部署前 |
