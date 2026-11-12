# 深夜 Debug 製作配方：一集怎麼做

給要做新一集的 agent：照這份從一篇 imitator 報告做出一集 mp3。每一步都有指令、產出和通過條件。
為什麼這樣做、試過哪些不行：POC 在 ttspoc 的 `podcast/RESULTS.md`，搬家後的發現在 `PIPELINE.md` §2 和
`episodes/ep00-intro/review/README.md`。節目怎麼營運（選題、審稿、發佈、上架）在 `PIPELINE.md`。

來源：ttspoc `podcast/PIPELINE.md`（`799872e`），2026-11-04 搬過來時改了路徑，並加上 EP00 試作學到的規則：
主持人 Ping 與每集結構、全集同一個 mood、挑選加穩定度與語速、段落間停頓的 bug 修正。EP02 是第一集照這份做的。

## 總覽

| 步驟 | 誰做 | 指令或工具 | 產出（都在 `episodes/<ep>/`） |
|---|---|---|---|
| 0. 環境 | 一次性 | pip、轉換 Breeze | 套件、`/home/user/models/breeze-asr-25-ct2-int8` |
| 1. 選題、草稿與素材 | agent 自己寫 | — | `draft.json`、`sources/<段>.txt`、`episode.json` |
| 2. 台灣口語改寫 | Gemini 3.8 Flash | `tools/rewrite_episode.py` | `script.json`、`rewrites/<段>.json` |
| 3. 檢查稿子 | 工具加 agent 逐段核對 | `tools/script_lint.py`、`tools/twtone_check.py` | 修正後的 `script.json`，修正紀錄在 `manual_edits` |
| 4. 生成語音 | Gemini 3.8 Flash TTS | `tools/make_podcast.py episode` | `out/segments/D1_<ep>/` 每段三次 |
| 5. 挑選 | Breeze-ASR-25（Modal GPU，或本機 CPU）、Resemblyzer | `tools/select_takes.py` | 每段一個 `<段>.wav`、`select_log.json` |
| 6. 後製 | ffmpeg | `tools/make_podcast.py master` | `<ep>.mp3` |
| 7. 驗收 | Breeze、Resemblyzer、Gemini | `stt_check.py`、`consistency_check.py`、`measures.py`、`gemini_check.py` | `qa/`，不合格回第 4 或第 3 步 |
| 8. 交付 | — | `tools/package_episode.py` | `episode.json` 補上長度、bytes、sha256 |

`<ep>` 是這一集的資料夾名，例如 `ep02-harness-probe`。指令都在 repo 根目錄執行。中間檔都在 `out/`（不進 git）。

## 0. 環境（每個新容器做一次）

環境變數：`gemini_key`（或 `GEMINI_API_KEY`）。

```bash
python3 -m pip install -r requirements.txt
git clone --depth 1 https://github.com/clarencechien/twtonepoc /home/user/twtonepoc && /home/user/twtonepoc/setup.sh   # twtone（第 3 步），會下載 zhtw-mcp 並驗 SHA256
python3 -m pip install --index-url https://download.pytorch.org/whl/cpu torch
python3 -m pip install -r requirements-qa.txt
python3 -m pip install --ignore-installed pillow      # 系統的 Pillow 跟 python3.11 不相容時
python3 -m pip install "av<14"                        # faster-whisper 1.2 跟 PyAV 15 以上不相容（open() 不收 metadata_errors）
mkdir -p /home/user/models
ct2-transformers-converter --model MediaTek-Research/Breeze-ASR-25 \
  --output_dir /home/user/models/breeze-asr-25-ct2-int8 --quantization int8 \
  --copy_files tokenizer.json preprocessor_config.json   # 約 3 GB 下載、1.5 GB 結果、幾分鐘
```

- 一定用 `python3 -m pip`。模型放在別的路徑時設 `BREEZE_CT2=<路徑>`。
- **Modal（第 5、7 步的 Breeze 改在雲端 GPU 跑）**：環境變數 `modal`、`modal_secret` 是 Modal 的 token（不要印出來）。
  雲端容器要經過 HTTPS proxy 才連得到 Modal，所以要裝 proxy 支援；app 只要部署一次，改了 `tools/modal_breeze.py` 才重新部署：

  ```bash
  python3 -m pip install 'modal[api-proxy-support]'      # 少了 python-socks 會連不上
  MODAL_TOKEN_ID="$modal" MODAL_TOKEN_SECRET="$modal_secret" SSL_CERT_FILE=/root/.ccr/ca-bundle.crt \
    modal deploy tools/modal_breeze.py                    # 第一次會建 image、在 image 裡轉好 Breeze int8
  ```

  之後的指令都要帶 `SSL_CERT_FILE=/root/.ccr/ca-bundle.crt`；`transcribe_remote()` 會自己把 `modal`／`modal_secret` 對應成 Modal 要的變數。
  本機的 Breeze 轉換（上面的 `ct2-transformers-converter`）仍然要做：Modal 失敗時會退回本機跑。
- D1 的聲線 ID 在 `voices/registry.json`，語氣在 `prompts/styles.json`，`make_podcast.py` 會自動讀。
- 雲端容器抓不到 imitator 網站（Cloudflare 挑戰頁擋資料中心 IP），報告原文從 imitator repo 的 `archive/report/<slug>.html` 拿。

## 1. 選題、草稿與素材（agent 自己寫）

**選題**：public 的報告，不會很快過時，有故事可講。先讀完全文，只挑 **2 到 3 個重點**（降低門檻：聽眾沒看過原文，
不追求完整），其他明說「細節在原文」或直接略過。

切成 8 到 10 段，每段 150 到 350 字；財經、學術題材每段 300 字內（EP06：超過 350 字的段落念得最不穩）。**結構固定**：

| 位置 | 內容 |
|---|---|
| 第一段 | **cold open**：一個鉤子直接切進痛點，不打招呼、不自我介紹（固定開場會接在後面） |
| 中間 | 正文，每段一個重點或一個例子 |
| 最後一段 | **今晚的 breakpoint**：三個帶走的重點，每個一句、只能是前面講過的；接片尾「原文連結在節目資訊欄。我是 Ping，有收到的話，回我一個 pong。下次見。」 |

### `draft.json`

```json
{
 "show": "深夜 Debug",
 "episode": "EP02 標題",
 "source": "https://imitator.ai-apps.work/r/<slug>",
 "audience": "工程師、想搞懂 AI 的人",
 "segments": [
  {"id": "s00_open",  "mood": "<全集同一個 mood>", "text": "這一段要講的內容（草稿，事實要對）"},
  {"id": "s08_outro", "mood": "<全集同一個 mood>", "text": "…"}
 ]
}
```

- **`text`** 只決定這段講什麼，不必口語；事實、人名、數字要對，因為改寫只會改說法。**誰說的要寫清楚**
  （「報告的作者做了實驗」，不是「我做了實驗」：Ping 沒有個人經歷）。
- **`mood` 全集用同一個**（EP00 試作：三段各用不同 mood，語速差了 27%，接起來像換人）。目前的版本：
  > 像深夜跟朋友聊天，有點感性但不畏縮。英文詞（Ping、pong、Claude Code、Three.js、prompt 這些）用台灣工程師平常講英文的念法自然帶過，就像台灣人講 double check 那樣
  - 不要寫「慵懶」「壓低聲音」「語速偏慢」：念得畏縮、停頓多。
  - 不要寫「篤定」「句尾俐落」「整集前後一致」這類控制型的句子：推向播音腔，台灣人聽起來偏大陸腔。
  - 「慢一點」會讓語速明顯變慢。

### 系列與上一集：`previously`、`recap`
接著上一集的話，在 `draft.json` 加：

```json
"series": "第五招 2/2（上：EP01）",
"previously": {"episode": "EP01", "title": "記住了第一招，漏掉了第五招", "summary": "一兩句：上一集講了什麼，這集跟它的關係"},
```

並在第一個正文段（cold open 之後那段）加 `"recap": true`。改寫時只有那一段會被要求開頭用「上一集……」接回去，
沒說「上一集」的候選會排最後。**用聽的，集與集的關係只能靠主持人講出來**：EP02 草稿原本寫了「上一集聊過」，
改寫時被當成多餘的話刪掉，聽眾完全聽不出 EP02 是 EP01 第五招的下集（2026-11-04）。
只回顧上一集，不預告下一集：上架順序可能會變，預告不一定成立。節目說明也寫「上一集：」「延伸收聽：」。

### `sources/<段落 id>.txt`
每段一個檔，放這段對應的原文摘錄。改寫時事實只能來自這裡，所以要涵蓋這段要講的全部事實。

### `episode.json`
先寫好 `id`、`number`、`type`（`full`）、`guid`（`debug-after-dark:ep02`，永遠不變）、`title`、`description`（show notes 格板見
`episodes/ep00-intro/script.md`）、`report_slug`、`source_url`、`voice`、`audio.file`。其餘第 8 步補。

範例：`episodes/ep02-harness-probe/`。

## 2. 台灣口語改寫

```bash
python3 tools/rewrite_episode.py --episode episodes/<ep> --n 3 --resume
```

- 寫稿 prompt 在 `prompts/spoken_script_zh-TW.md`：每句 ≤ 20 字、每段 ≤ 1 個精確數字、不條列、素人感、台灣用字、避開大陸用語、
  Ping 不講自己的經歷、cold open 不打招呼、最後一段是 breakpoint、術語第一次出現就解釋。
- 每段三個候選，自動挑沒有大陸用語、口頭禪沒超額、數字少、句子短的那個。整集口頭禪額度在 `rewrite_episode.py` 的 `PHRASE_CAPS`。
- `--resume`：容器重啟會砍掉執行中的工作，加這個會沿用已完成的段落。
- 有自我更正（呃、我是說、應該說、啊不對、刪節號）或 cold open 打招呼的候選排最後；三個都有就再要三個，最多再兩輪（`--extra-rounds`）。2026-11-12 起 prompt 第 12、14 條不再鼓勵改口和「嘿，還醒著嗎？」，並加第 20 條；用 EP23 前 5 段實測，15 個候選的自我更正都是 0（舊版同段 3 個裡有 2 個有）。
- 每段的三個候選同時送出，各自最多重試 3 次（proxy 偶爾斷線）。一段約 25 秒，EP11 十段 261 秒（以前一段約 70 秒）。

## 3. 檢查稿子（不能省）

```bash
python3 tools/script_lint.py episodes/<ep>/script.json
```

通過條件：每段 `mainland_words` 是空的，`precise_numbers` 最多一個。

再跑 twtone（[`clarencechien/twtonepoc`](https://github.com/clarencechien/twtonepoc)，零 token 的繁中檢查：表層 AI 味訊號加上 zhtw-mcp 的台灣用詞與翻譯腔，門檻來自 2015–2022 的台灣同類文章）：

```bash
python3 tools/twtone_check.py episodes/<ep>/script.json      # 報告存到 episodes/<ep>/qa/twtone.md，每行標出是哪一段
```

- 「要改」區（超過台灣基準語料任何一篇，最常見的是「不是…而是」對舉）：一句一句最小改動，保留事實與限定詞，記進 `manual_edits`；在澄清誤讀的句子可以留，但同一段別連用。
- 用詞區（zhtw-mcp）：只是建議，不自動套用。像「數據→資料」「沙箱→沙盒」是教育部立場，口語節目照聽眾習慣決定。
- 翻譯腔 warning、「略過」區：不主動改。twtone 是給文章用的，Ping 的反問和「對」「嘛」這類口語是刻意的。
- 2026-11-07 回頭跑已上架的集數：EP05、EP08 各有 2 處對舉超過門檻，EP09 沒有。

接著 agent 逐段對照 `sources/<段>.txt` 讀一遍。這些錯自動檢查抓不到，都實際發生過：

| 問題 | 實例 | 怎麼改 |
|---|---|---|
| 歸屬錯 | 「其他評論者說的」寫成「Felix 說的」；作者做的實驗寫成「我做了」 | 照素材改回；Ping 用「作者」「報告」 |
| 誇大或自己加數量 | 「三處不符」寫成「根本對不上」；「遮住部分資料」寫成「蓋住一半」 | 照素材改回、刪掉數量 |
| 改口、口頭禪太多 | 十段裡九段有「我是說」「呃不對」 | 全集留 3 到 4 處 |
| 同音或聽起來像別的詞 | 季度→基督、忙人→盲人、正本→這本、時間戳→時間出；句首的「報告說」→「包括說」（EP06、EP09） | 換說法：每一季的檢討會、一群很忙的人、原文、時間戳記；「這份報告說」「報告裡說」（`script_lint.py` 的 `bare_report`） |
| 偏大陸的用語 | 更狠的是、盲猜、坑 | 更扯的是、用猜的、要注意的地方 |
| 書面專業詞、英文術語、改口、段落太長 | EP06 第一版：段落近 400 字，超額報酬、過擬合、樣本外、edge、alpha，加上「呃我是說」；前五分鐘念得不穩、偏大陸腔、咬字聽不出詞 | 換成白話（多賺的部分、太貼合過去、沒看過的新資料），拿掉改口，每段 300 字內、每句平均 18 字內（寫稿規則第 18 條） |
| 書面詞 | 季度、推估、處方 | 換成聊天的說法 |
| 結構走樣 | cold open 打了招呼；breakpoint 加了前面沒講的事；片尾句不對 | 照第 1 步的結構改 |
| 回顧不見或講錯 | 有 `previously` 卻沒有「上一集」；EP02 的回顧寫成「Felix 漏掉的第五招」（漏掉的是轉傳的人） | 補上或照上一集的稿子改正 |
| 對真實的人語氣不當 | 「你猜他怎麼做？結果只開給一個帳號」「你猜贊助拿了多少」 | 照素材的框架敘述，不讓聽眾看笑話；當事人要求匿名就不寫名字 |

每處修改記在 `rewrites/<段>.json` 的 `manual_edits`（`{"from", "to", "reason"}`），再存回 `script.json`。

## 4. 生成語音

```bash
python3 tools/make_podcast.py episode --voice D1 --script episodes/<ep>/script.json --tag <ep> --takes 3
```

- **D1** 是設計聲線 `voice_b3c8x0jsntqc`，閒置一年才會刪除。**語氣預設 v5**（`prompts/styles.json`）。
- **每段念三次**：沒有種子，每次差很多。每次都自動檢查時長，太短或太長就重念，最多重試 2 次。
- **全部的生成同時送**（`--parallel`，預設 6 個同時進行），每次各自做時長檢查和最多 3 次網路重試。EP11 的 30 次生成 70 秒（EP10 逐一生成約 8 分鐘）。
- 中斷後重下同一指令即可，已存在的生成檔不會重做。
- **一定要帶 `--tag <ep>`**：漏了會寫進 `out/segments/D1/`，兩集先後漏帶就會互相蓋掉同名的 take（2026-11-07 EP10、EP11 一起重錄時發生過）。
- **不要整集一次生成**當正式版：EP00 試作的一次生成比較連貫，但音高跳動多 29%、聽起來咬字抖、口音偏大陸。

## 5. 挑選

```bash
python3 tools/select_takes.py --script episodes/<ep>/script.json --segments out/segments/D1_<ep> \
  --asr breeze-modal --consistency --neighbour
```

`--asr breeze-modal` 把轉寫送到 Modal 的 L4 GPU（`tools/modal_breeze.py`）：同一個 Breeze int8 模型、同樣的解碼設定（zh、beam 5、VAD、
時間戳超出音檔時的重試），只有裝置不同。EP10 的 30 次生成在 GPU 上重挑，10 段選中的版本跟 CPU 完全相同；挑選 79 秒，本機 22 分鐘。
每批 12 個檔同時送出，每批最多等 600 秒、失敗重試一次，還是失敗就在本機 CPU 轉寫那一批，所以網路斷了也不會丟掉整次執行。
沒有 Modal 時改用 `--asr breeze`（本機）。

**Modal 等開機（2026-11-10）**：EP16 挑選 9 分鐘，第一批在開始後 412 秒才回來，GPU 實際只算了 37 秒，其餘是在排 L4；
本機的聲紋、抖動、亮度合計約 30–44 秒，不是瓶頸，所以聲紋不搬上 Modal。現在 `gpu=["L4", "A10G", "T4"]`（排不到 L4 就用別的），
`make_podcast.py episode` 開始生成時就先 `warm_remote()` 叫醒容器，容器閒置 10 分鐘才關。EP17 挑選 1 分 16 秒，
補錄後重選 40 秒（Modal 8 秒）。`transcribe_remote` 每批會印「開始後幾秒回來、GPU 算了幾秒」，差很多就是在等開機。

依序篩選：
1. **清楚**：Breeze 盲聽錯誤率跟最好的那次差 0.012 以內。
2. **專有名詞**（`--terms`）：盲聽稿要出現同樣次數。**Breeze 會把 Ping 寫成「pin」**，所以 Ping 不要放進 `--terms`，
   改用第 7 步的 `gemini_check.py terms`。
3. **穩定**：音高跳動（`measures.py`）比最穩的那次多 0.02 半音以內。EP00：0.20 聽起來穩，0.26 聽起來抖。
4. **語速**：字／秒離整集中位數一成以內。
5. **像同一個人**：聲紋接近整集平均（差 0.015 以內）、音色重心離中位數最近的那次再加 300 Hz 以內。
6. **停頓**：長停頓最少。

最後一輪相鄰段比對（`--neighbour`）：有一次生成跟前後段更像（相似度高出 0.01 以上）就換。
選擇紀錄在 `out/segments/D1_<ep>/select_log.json`，每次生成的轉寫文字和時間戳也存在裡面（第 7 步會沿用）。
Breeze 在 CPU 上轉寫 30 次生成約 20 到 25 分鐘；用 Modal 時整個挑選 1.5 到 4 分鐘（含 GPU 開機，聲紋仍在本機算）。只改規則或只補了幾次生成時加 `--reuse`，只轉寫新的檔。

- **`--reuse` 是用檔名對轉寫**：改了稿子重新生成的段落，檔名還是 `take0`～`take2`，會拿到舊稿的轉寫。
  改稿的段落要先刪掉它的 `*.take*.wav`，並把那段從 `select_log.json` 拿掉，再生成、挑選。
- **音高不在篩選條件裡**：挑完看一下各段選中那次的中位音高，離整集中位數超過 ±6 Hz 就補生成再挑（第 7 步的 `consistency_check.py` 也會標）。
- **手動指定**：自動挑的那次有問題（例如語速慢兩成），把想要的 take 複製成 `<段>.wav`，在 `select_log.json` 那段改 `chosen`
  並寫 `manual_override` 說明原因。之後再跑 `select_takes.py` 會蓋掉，要重做一次。

**不要用 `--beam 1` 省時間**（2026-11-04 用 EP02 的 27 次生成實測）：只快 30%（832 秒對 1,182 秒；CPU 上時間主要花在編碼器，
beam 只影響解碼），但 9 段裡有 3 段選中的不同，單次錯誤率最多差 0.04，比「一樣清楚」的容忍值 0.012 大三倍。
**只重做幾段時**，用第 7 步最後的 `--only <段> --add-takes 3` 加 `--reuse`：新生成接在舊的後面，其他段的選擇和轉寫不變
（`--neighbour` 可能讓鄰段換一次，看一下輸出）。

## 6. 後製

```bash
python3 tools/make_podcast.py master --voice D1 --tag <ep> --script episodes/<ep>/script.json --match-eq \
  --ident show/ident/ident.flac --out episodes/<ep>/<ep>.mp3
```

1. 每段調到 -20 LUFS（各段音量會差 4 到 6 dB）。
2. `--match-eq` 音色匹配：每段頻譜往整集中位數拉 80%，每頻帶最多 ±6 dB，再調回 -20 LUFS。
3. 順序：片頭音效 → 第一段（cold open）→ **固定開場**（`show/ident/ident.flac`，每集同一個音檔，不做音色匹配）→ 其餘各段 → 片尾音效，
   段與段之間 0.6 秒（ttspoc 版的這個停頓從來沒插進去，這裡已修）。
4. 整集：高通、輕壓縮、-16 LUFS、128 kbps 單聲道 mp3，ID3 寫上 AI 合成聲音的揭露。

## 7. 驗收

```bash
python3 tools/stt_check.py --asr breeze-modal --from-select --script episodes/<ep>/script.json \
  --segments out/segments/D1_<ep> --out episodes/<ep>/qa/stt_check.json
python3 tools/consistency_check.py --script episodes/<ep>/script.json \
  --segments out/master/norm_D1_<ep> --out episodes/<ep>/qa/consistency.json
python3 tools/measures.py wobble episodes/<ep>/<ep>.mp3 --skip 3.6 --tail 3.6
python3 tools/gemini_check.py terms --segments out/segments/D1_<ep> --script episodes/<ep>/script.json --terms Ping,pong
```

- `--from-select`：Breeze 那一半直接沿用第 5 步存下的選中那次的轉寫，不再轉寫一次；只有 Gemini 那一半要跑。
  Gemini 轉寫各段同時送（6 個），每段最多重試 3 次，回空白就記成 `"empty": true` 繼續（EP10 的 oh F moment 那段三次都回空白），不會讓整個檢查中斷。
- 四個檢查彼此獨立，可以同時跑。EP11 的驗收 85 秒（EP10 本機約 9 分鐘）。

| 檢查 | 通過 |
|---|---|
| Breeze 盲聽錯誤率，各段平均 | 3.5% 以下（EP01 3.0%） |
| 兩套辨識都聽錯的內容詞 | 0 處 |
| `consistency_check.py` | 全部段落在範圍內：相鄰段聲紋 ≥ 0.93、音高 ±6 Hz、音色重心 ±350 Hz、響度 ±1 dB、**接縫亮度 ±400 Hz、語速 ±10%** |
| 整集音高跳動 | 0.23 半音以下（EP00 定稿 0.20；聽起來抖的那版 0.26） |
| Ping／pong | `gemini_check.py terms` 判為英文念法（粗篩，人耳為準） |

- **兩邊都錯**：念不清楚或用字有問題，回第 3 步改稿或第 4 步重念。
- **只有 Breeze 標**：常是英文詞拼錯（Claude、Three.js、Ping→pin）；中文內容詞到標註時間點聽一下。
- **只有 Gemini 標**：Gemini 常把「二零二六」聽成「二零二四」。

不合格的段補生成，再挑選和後製：

```bash
python3 tools/make_podcast.py episode --voice D1 --script episodes/<ep>/script.json --tag <ep> --only <段> --add-takes 3
python3 tools/select_takes.py --script episodes/<ep>/script.json --segments out/segments/D1_<ep> --asr breeze-modal --consistency --neighbour --reuse
```

**自動檢查都不能判斷口音**：Gemini 評審判斷台灣腔與大陸腔跟台灣母語者相反。口音、磁性、整體感覺只能人耳。

## 8. 交付

把 `select_log.json`、`out/master/norm_D1_<ep>/levels.json`、`match_eq.json` 複製到 `episodes/<ep>/qa/`，然後：

```bash
python3 tools/package_episode.py episodes/<ep>
```

補上 `episode.json` 的長度、bytes、sha256、響度（RSS 的 `<enclosure length>` 要跟檔案完全一致）。開 PR 給人審：稿子（關卡 A）與成品（關卡 B）。

## 不要做的事

- 不要讓 Gemini 評審判斷台灣口音。
- 不要複製或模仿真人的聲音。
- 不要把稿子寫成一句一行：TTS 會在每個換行停頓。
- 不要只看清晰度挑選：會挑到停頓多、或聽起來抖的那次（EP00 第二版就是這樣挑錯的）。
- 不要加重壓縮：氣音和齒音會變亮。
- 不要每段用不同的 mood：語速和語調會在接縫換檔，音色匹配救不回來。

## 時間與費用（一集約 7 到 9 分鐘）

| 步驟 | 以前（EP10，逐一、本機） | 現在（EP11，同時送、Modal） | 費用（2026 年底前） |
|---|---|---|---|
| 2. 改寫，10 段各 3 候選 | 約 10 分鐘 | 261 秒 | 約 0.35 美元 |
| 4. 生成，30 次 | 約 8 分鐘 | 70 秒 | 約 0.35 美元 |
| 5. 挑選，Breeze | 22 分鐘（CPU） | 93 秒（L4 GPU） | Modal 按秒計費，每集 GPU 只開一兩分鐘 |
| 6. 後製 | 約 1 分鐘 | 36 秒 | 0 |
| 7. 驗收 | 約 9 分鐘 | 85 秒 | 約 0.06 美元 |
| 合計 | 約 50 分鐘 | 約 9 分鐘 | 約 0.8 美元，2027 年起約 1.6 美元，加 Modal |

加上第 1、3 步 agent 自己的寫稿和核對時間，以及補生成、重挑的回合（每回合約 2 到 4 分鐘）。
以前慢在三件事：生成和改寫一個一個等、Breeze 在 4 核 CPU 上轉寫、驗收又把選中的那次轉寫一遍。
Modal 費用以 Modal 後台帳單為準。EP02 的實際數字見 `episodes/ep02-harness-probe/README.md`。

## 替代方案

- **整集一次生成**：沒有接縫，但 EP00 試作偏抖、口音偏掉，只當候選。
- **ElevenLabs Hardy**：最清楚，但長停頓是 D1 的兩倍。`tools/elevenlabs_tts.py episode --voice HARDY`。
