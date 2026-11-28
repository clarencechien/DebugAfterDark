# 一集的費用

2026-11-26 用實際用量算的。圖解：<https://claude.ai/artifact/JcZ21ADGUqAknXx5eSFTba>（private）。
之前的推算在 [`recipe.md`「時間與費用」](recipe.md#時間與費用一集約-7-到-9-分鐘)，那張表沒算重生成。

## 目前的發現

數字是 Gemini 的估算（`tools/usage_log.py`：回應的 token 數 × 價目表，寫在 `/mnt/project-files/factory/usage.jsonl`），
不是帳單；帳單看 AI Studio。2026 年底前是優惠價，2027-01-01 起 Gemini 約翻倍。

| 每集（美元） | 改寫 | TTS | 驗收 | 挑選（Colab） | 合計 |
|---|---|---|---|---|---|
| EP52/53 平均（11/25，順） | 0.25（28%） | 0.50（56%） | 0.07（7%） | 0.08（9%） | **0.90** |
| EP54/55 平均（11/26） | 0.47（27%） | 1.07（60%） | 0.15（8%） | 0.08（5%） | **1.77** |
| recipe.md 推算（11 月初） | 0.35 | 0.35 | 0.06 | 未計 | 0.76 |

- **TTS 一直是最大塊**，兩批的比例幾乎一樣。原因是輸出是音訊 token（每秒約 25 個，每百萬 9 美元），
  而且一集實際生成約 36 分鐘的聲音才挑出 8 分鐘（每段 3 次再加補生成）。
- 改寫和驗收佔比小是因為它們是文字 token，不是做得少。驗收只檢查挑中的那一次。
- EP54/55 貴一倍的原因是重生成回合多：TTS 呼叫 180 次對 94 次、改寫 72 次對 41 次；成品也長約兩成。
  **省錢最有效的是減少重生成回合。**
- EP40–51 只補記了 TTS：平均每集 0.42（0.35–0.58）。
- Colab（跑 Breeze 挑選和驗收轉寫）：11/25 到 11/26 四集用了 3.21 CU，每集約 0.8 CU。
  CU 是 Google AI Pro 每月附送的額度（Clarence 11/26 確認），邊際成本 0；照付費價（100 CU 約 US$9.99）換算才是 0.08。
  一個月 60 集約 48 CU，在 200 CU 額度內。
- **GPU 池（11/26）**：Colab（AI Pro 附送 CU）和 Modal（每月 US$30 額度）都是免費額度，`--asr breeze-cloud` 依序用 Colab L4 → Modal → 本機 CPU。
  有設定 Modal 時 Colab 只要 L4、不再退到 A100（A100 每小時 6.73 CU，L4 是 1.94；兩集同時挑選時 Colab 本來就不給第二台 L4），
  直接交給 Modal。Modal 的 GPU 秒數現在也寫進 `usage.jsonl`（`service: modal`，不含閒置等待關機的 10 分鐘）。
  `requirements.txt` 加了 `modal`，新容器不會再因為沒裝套件而跳過 Modal。
- 不算進每集的：Claude（寫稿、核對、thread）走訂閱；GitHub Pages、Actions、Cloudflare cron Worker 免費；
  imitator 的 Workers Paid 5 美元／月是報告站的。來源若是當天新跑的自動研究報告，另加約 10 美元（`research/runs/cost.log`）。
- 一天兩集，Gemini 一個月約 55–105 美元。11/21 和 11/26 撞到花費上限，跟這個量級吻合。

### 記錄的缺口

- `usage.jsonl` 沒有標集數，上面是照時間分批算的（EP52/53 = 11/25 01:30–02:20 UTC，EP54/55 = 11/26 03:30–05:55 UTC）。
  11/25 07:20–07:50 另有 0.39 美元對不上任何一集。`log_gemini()` 現在收得下額外欄位，之後可以補 `episode=`。

## 可選的 API（以 EP52/53 的 token 量推算，每集）

| 步驟 | 選項 | 每集 | 備註 |
|---|---|---|---|
| 改寫 | Gemini 3.8 Flash（現行） | 0.25 | |
| | Claude Haiku 5.5（$0.10／$0.50） | 0.03 | 品質沒測過；假設 token 量相同 |
| | Claude Sonnet 5.5（$2／$10） | 0.67 | 同上 |
| | 寫稿的 agent 自己改（訂閱） | 0 | thread 跑比較久 |
| TTS | Gemini 3.8 Flash TTS（現行，$9／M 音訊） | 0.50 | |
| | Gemini 3.8 Flash-Lite TTS（$6／M） | 0.33 | 11/26 實測可以用 D1 聲音 |
| | Gemini 2.5 Flash TTS preview（$10／M） | 0.55 | 舊模型、比較貴 |
| | Gemini 2.5 Pro TTS preview（$20／M） | 1.10 | |
| | 同模型走 Batch API | 0.25 | **11/28 帳單確認半價**（見下方「Batch 對帳」） |
| | ElevenLabs Flash／v3（$0.05／$0.10 每千字元） | 0.52／1.04 | 重生成照字元收；不是 D1 的聲音 |
| 驗收 | 評審換 Claude Haiku 5.5 | 0.05 | 現行 0.07 |
| | 轉寫只用 Breeze（EP42/43 先例） | 0.02 | |

### 驗收的 Gemini 能不能改抽測（11/26 查）

`stt_check.py` 的判定是「Breeze 和 Gemini **都**聽錯的地方才標記」，Gemini 的角色是過濾 Breeze 的誤報。
45 集用 Breeze 的資料（排除 Gemini 撞上限、CER=1.0 的集數）：

| 每集平均 | Breeze | Gemini |
|---|---|---|
| CER | 0.030 | 0.019 |
| 只有這邊聽錯的地方 | 約 26 處 | 約 7 處 |
| 兩邊都錯（現在的標記） | 約 5 處 | |

- Breeze 的轉寫準確度還沒有追上 Gemini，「Breeze ≥ Gemini 就改抽測」的條件目前不成立。
- 只用 Breeze 不會漏掉現在的任何標記（那些本來就包含 Breeze 聽錯的地方），但每集要看的地方會從約 5 處變成約 31 處。
- 驗收的 Gemini 一集只花約 0.05 美元（約 5%），改抽測省不多。換模型的實測見下一節：最划算的是同模型關思考。

組合：最省（Haiku 改寫＋Flash-Lite TTS）約 0.51；改寫升級（Sonnet）約 1.32；TTS 換 ElevenLabs v3 約 1.44。
Native Audio（Live）是即時串流對話用的，不適合做 podcast。

## 驗收換模型實測（11/26）

整集 mp3 盲聽寫，對整份稿子算 CER（EP52、EP53，同一個 prompt）：

| 模型 | EP52 CER | EP53 CER | 思考 token | 秒 | 每集一次的估算 |
|---|---|---|---|---|---|
| 3.8 Flash（現行） | 0.042 | 0.027 | 約 3,300 | 37 | 0.027 |
| **3.8 Flash，關思考**（thinking_budget=0） | **0.033** | **0.027** | 0 | 14 | **0.015** |
| 3.5 Transcribe（只在 v1beta） | 0.045 | 0.038 | 0 | 8 | 單價查不到 |
| 3.5 Flash-Lite | 0.080 | 0.067 | 0 | 7 | 0.009 |

- **3.5 Flash-Lite 不能用**：錯字率是現行的兩倍多，比 Breeze（約 0.03）還差，當不了過濾器。
- **3.5 Transcribe 勉強**：整集的數字接近，但小段試聽把「上一集是鏡子篇的上集」聽成「上瘾机制是镜子片的商品」，輸出也是簡體。
- **最好的是同一個 3.8 Flash 把思考關掉**：錯字率一樣或更低，費用約少 45%（現行的錢大多花在思考 token），還快 2.5 倍。
  `stt_check.py --gemini-thinking 0`。

## 實驗：TTS 和驗收降本，改寫不動（Clarence 11/26 決定）

**問題**：同一份稿子、同一個 D1 聲音，TTS 換 Flash-Lite 或走 Batch、驗收的 Gemini 關思考，品質掉多少、錢省多少？

**目標**：改寫維持現行，TTS 和驗收降本、品質不變。以順的那集（0.90）推算：

| 組合 | 改寫 | TTS | 驗收 | 挑選 | 合計 | 省 |
|---|---|---|---|---|---|---|
| 現行 | 0.25 | 0.50 | 0.07 | 0.08 | 0.90 | |
| Flash-Lite＋驗收關思考 | 0.25 | 0.33 | 0.04 | 0.08 | 0.70 | 23% |
| Batch（若半價）＋驗收關思考 | 0.25 | 0.25 | 0.04 | 0.08 | 0.62 | 31% |
| Flash-Lite 走 Batch（若半價）＋驗收關思考 | 0.25 | 0.17 | 0.04 | 0.08 | 0.54 | 40% |
| 同上，Colab 照實算 0（AI Pro 附送額度） | 0.25 | 0.17 | 0.04 | 0 | **0.46** | **49%** |

Colab 是 AI Pro 附送的額度，所以只動 TTS 和驗收，Flash-Lite 走 Batch 加驗收關思考就約降一半；這是本實驗的目標組合。
改寫 0.25 不動，它就佔了半價目標的一半以上。另一個大槓桿是重生成：EP54/55 那種多回合的集數一集 1.77，回合數本身就能差一倍。

**做法**（下一集；上架的仍是對照組，除非 Clarence 聽完改選）：

```bash
# 對照組（照 recipe）
python3 tools/make_podcast.py episode --voice D1 --script episodes/<ep>/script.json --tag <ep> --takes 3
# A：Flash-Lite
python3 tools/make_podcast.py episode --voice D1 --script episodes/<ep>/script.json --tag <ep>_lite --takes 3 --model gemini-3.8-flash-lite-tts
# B：Batch（同模型，非同步；11/26 試 4 段 109 秒）
python3 tools/make_podcast.py episode --voice D1 --script episodes/<ep>/script.json --tag <ep>_batch --takes 3 --batch
# C：Flash-Lite 走 Batch（可選，若 A 的聲音過關）
python3 tools/make_podcast.py episode --voice D1 --script episodes/<ep>/script.json --tag <ep>_litebatch --takes 3 --model gemini-3.8-flash-lite-tts --batch
# 驗收：對照組的 stt_check 多跑一次關思考版，比兩份報告的標記
python3 tools/stt_check.py ... --gemini-thinking 0 --out <ep>-stt-nothink.json
```

各組各自跑挑選和後製，出完整 mp3。`--batch` 失敗的段會改用一般呼叫重做，那幾段要記下來。

**比什麼**

| 項目 | 怎麼量 |
|---|---|
| 費用 | `usage.jsonl` 各組的列（Batch 的列有 `batch: true`）；Batch 的實際折扣隔天對 AI Studio 帳單 |
| 重生成 | 需要補生成的段數、`--add-takes` 回合數 |
| 聲音漂移 | `match_voice.py`，對 D1 參考的相似度（基準中位數 0.894，低 0.03 以上算漂） |
| 清晰度 | `stt_check.py` 的 Breeze CER |
| 停頓 | 每分鐘 ≥0.6 秒的長停頓 |
| 驗收關思考 | 兩份 stt_check 的「兩邊都錯」標記是否一致、Gemini CER |
| 耳朵 | Clarence 盲聽同兩三段的各組版本 |

額外成本約 1 美元（多生成兩到三組 TTS）。

### 結果（EP57，2026-11-27）

同一份稿子（`ep57-which-wire`）、同一個 D1 聲音，各錄 33 次（11 段 × 3），各自挑選和後製。Lite＋Batch 沒做。

| | 對照（Flash） | Flash-Lite | Batch（Flash） | Lite＋Batch |
|---|---|---|---|---|
| 集數 | EP57 | EP57 | EP57 | — |
| TTS 費用（估，33 次） | 約 0.44 美元 | 約 0.28 美元（−37%） | 帳單 NT$6.86（約 0.21 美元，半價） | — |
| 重生成段數 | 0 | 0 | 0（33 次 207 秒回來，一般呼叫約 1 分鐘） | — |
| 漂移相似度 | 0.897 | 0.899 | 0.895 | — |
| CER（Breeze／Gemini） | 3.0%／1.3% | 3.5%／1.6% | 4.0%／1.9% | — |
| 音高跳動（整集） | 0.228 | 0.232 | 0.225 | — |
| 長停頓／分 | 11.1 | 11.1 | 11.8 | — |
| 盲聽（Clarence，s02＋s05） | 「有點弱、不太穩」 | 「最接近目前的聲音，比較穩」 | 「比較小聲、比較悶，但可能最穩」 | — |

EP57 上架的是 Flash-Lite 版（Clarence 選 B）。另外 EP56 用 Flash-Lite 重錄 s01、s11 跟 Flash 版對聽，
Clarence 的評語是「Flash 的品質跟味道比較濃，Flash-Lite 有時會太淡」：s11 換成 Lite，s01 留 Flash。
盲聽和對聽方向不完全一致，每次生成本來就是抽籤，一集的樣本不夠下定論。

驗收關思考（`--gemini-thinking 0`）：11 段裡 2 段 Gemini 回空白（CER 1.0），「兩邊都錯」從 7 處變 12 處。這次不可靠，先不換。

**結論（暫定）**：Flash-Lite 便宜約 37%，數字和盲聽都沒有明顯變差，但有時語氣偏淡。
**下一集起整集改用 Flash-Lite 試做**（Clarence 11/27）：`make_podcast.py episode ... --model gemini-3.8-flash-lite-tts`，
補錄也用 Flash-Lite；試聽時特別注意「太淡」。Batch 的半價 11/28 已對帳確認（下一節），要不要改走 Batch 還沒決定。
「太淡」「太激動」這類差別現在的挑選指標量不到，另一個 thread 在查能不能自動量。

### Batch 對帳（11/28，Clarence 的 Cloud Billing 截圖）

帳單以**新台幣**計（價目表和 `usage.jsonl` 是美元）。11/26–27 的 Batch 只有 EP57 Batch 組 33 次和 11/26 的 4 次試跑：

| 帳單 SKU | 用量 | 金額 |
|---|---|---|
| gemini 3.8 flash tts audio batch（輸出） | 46,630 token | NT$13.61 |
| flash tts text batch（輸入） | 6,421 token | NT$0.10 |
| 折扣 | | −NT$6.86 |
| **淨額** | | **NT$6.86（約 0.21 美元），額度全額抵掉** |

- token 數和 `usage.jsonl` 對得上（33 次 45,755＋試跑約 875 = 46,630）。
- 原價 NT$13.61 ÷ 46,630 token = 每百萬 NT$292，等於 9 美元 × 約 32.4 元匯率，就是一般價；折扣剛好 50%。
- `usage.jsonl` 的 Batch 列記的是原價，算費用時要再乘 0.5。
- Flash-Lite 走 Batch 還沒跑過，它的批次價沒在帳單上看到，先假設也是半價。

## 每集成本：舊做法 vs 新做法（11/28）

以順的那集的 token 量算（EP52/53）。挑選的 Colab／Modal 都在免費額度內，算 0。匯率約 32.4。

| 做法 | 改寫 | TTS | 驗收 | 合計（美元） | 合計（台幣） | 比舊做法 |
|---|---|---|---|---|---|---|
| 舊：Flash TTS（11/26 以前） | 0.25 | 0.50 | 0.07 | **0.82** | 約 NT$27 | |
| **現行：Flash-Lite TTS（11/27 起）** | 0.25 | 0.33 | 0.07 | **0.65** | 約 NT$21 | −0.17（約 NT$5.5），−21% |
| Flash TTS 走 Batch | 0.25 | 0.25 | 0.07 | 0.57 | 約 NT$18 | −0.25（約 NT$8），−30% |
| Flash-Lite 走 Batch | 0.25 | 0.17 | 0.07 | 0.48 | 約 NT$16 | −0.33（約 NT$11），−41% |

- 2027-01-01 起 Gemini 約漲一倍，各列也跟著約翻倍。
- 重生成多的集數（像 EP54/55）TTS 會翻倍，省下的金額也跟著放大。
- 驗收關思考那條不算進去：EP57 試了不可靠，沒換。
