# 聲音：保存、監測、重現

節目的聲音是 Gemini 3.8 Flash TTS 的設計聲線 D1（`voice_b3c8x0jsntqc`），加上 `prompts/styles.json` 的 v5 語氣。這份文件寫三件事：哪些事會讓聲音變掉、平常怎麼發現、模型停用時怎麼盡量重現。

## 會讓聲音變掉的事

| 情況 | 會不會報錯 | 現況（2026-11-20） |
|---|---|---|
| TTS 模型停用 | 停用後請求直接失敗 | `gemini-3.8-flash-tts` 沒有公布停用日。停用通知可能只提早幾週（這次 TTS 預覽版的通知信在 11 月，12-18 就停用），要留意 Google 的通知信和[停用頁](https://ai.google.dev/gemini-api/docs/deprecations) |
| 同一個模型名稱被自動轉到別的模型，或在原名稱下更新 | 不會 | 其他模型已經發生過，例如 `gemini-2.5-flash` 在 12-01 會轉到 Flash-Lite。聲音會變，程式不會報錯 |
| 設計聲線過期 | 過期後請求失敗 | 聲線閒置一年就過期，每合成一次就把效期推到一年後。實測 11-20 合成一次後，D1 的效期變成 2027-11-20。D2、D1M1、D1M2 沒在用，2027-11-03 到期 |
| 自己改了設定 | 不會 | 語氣（`prompts/styles.json`、各段 `mood`）、母帶的 `--match-eq` |
| API 或 SDK 改變 | 看情況 | google-genai 3.x 預設走 `v1`，但 3.8 TTS 和 voices 端點只在 `v1beta`，在 `v1` 會回 404。`make_podcast.py` 的 `client()` 已經明確指定 `v1beta` |

## 保存了什麼

| 東西 | 位置 | 用途 |
|---|---|---|
| 聲線的設計提示詞、ID、效期、設計時用的模型 | `voices/registry.json` | 重新設計或延伸聲線時用 |
| 語氣提示詞 | `prompts/styles.json`（v5），每段的 `mood` 在 `script.json` | 重現時要用同一套語氣 |
| 參考錄音 | `voices/references/`：同一句試聽稿，無損 flac，加上聲紋、音高和 sha256 | `match_voice.py` 比對候選聲線 |
| 每一集的成品 | `episodes/*/*.mp3`，40 集約 6.5 小時 | 最完整的「原本的聲音」，比參考錄音長得多 |
| 每一集用的模型 | `episode.json` 的 `voice.model`，以及新增的 `voice.model_served`（實際回應的模型） | 事後查是哪一集開始變的 |
| 每個 take 的請求與回應 | `out/segments/<voice>_<ep>/*.meta.json`（不進 git），交付時 `log.json` 複製成 `qa/tts_log.json` | 實際回應的模型、interaction id、文字、語氣 |
| 聲紋走勢 | 每集的 `episodes/<ep>/qa/voice_drift.json`，`match_voice.py drift` 印出全部 | 每集跟參考錄音的相似度 |

`voices/references/` 和各集的 mp3 不能遺失。

## 平常怎麼發現

1. **合成時**：`make_podcast.py episode` 最後會印 `TTS model served`。如果跟 `gemini-3.8-flash-tts` 不一樣，先不要做母帶。
2. **交付時**：`package_episode.py` 把 `qa/tts_log.json` 裡實際回應的模型寫進 `episode.json`，跟 `voice.model` 不一樣就警告。
3. **交付後**：跑 `python3 tools/match_voice.py track episodes/<ep>`。它會量這集 mp3 跟參考錄音的聲紋相似度，寫進 `episodes/<ep>/qa/voice_drift.json`（每集一個檔，兩集平行做不會衝突；`python3 tools/match_voice.py drift` 看全部的走勢）。如果比前 10 集的中位數低 0.03 以上，就會標出來。
   - 基準線（2026-11-20 量 EP00–EP39）：0.885 到 0.910，中位數 0.894。EP00 是試作期，0.874。
   - 當時的量測尺度：同模型同聲線約 0.93，同聲線但隔一代模型約 0.87–0.90，不同聲線約 0.79–0.81（`match_voice.py` 開頭）。所以跟參考錄音比，0.03 的落差就值得去聽。這是排名用的訊號，最後還是要人耳判斷。
4. **每季**：跑 `python3 tools/make_podcast.py voices`，更新 `registry.json` 裡的效期和模型。

其他文字類工具（改寫、轉寫、評審、出圖）的輸出也開始記錄 `model_version`。

## 語氣太淡、太激動（只記錄，2026-11-27）

`select_takes.py` 的清楚、穩定、語速、聲紋都量不到 Clarence 聽得出的「太淡」「太激動」。EP56 他比過的兩段：
s01 Flash 勝過 Lite take2（太激動），s11 Lite take2 勝過 take0（太淡）。下面三樣都**只記錄、不改變挑選結果**，
等他的標註累積到夠多再決定要不要用。

| 判斷 | 工具 | EP56 那兩段 | 花費 |
|---|---|---|---|
| 音高範圍（p90−p10 半音）高出整集中位數 2 半音以上 → `excited?` | `select_takes.py` 每個 take 的 `affect`、`affect_flag`；`measures.py affect` | 太激動的 take 9.8，其他 6.3–7.9：抓到。太淡的 take0 7.9 反而比他選的 7.3 大：抓不到 | 0 |
| Gemini 聽參考錄音（D1）加同段幾次生成，標太淡／剛好／太激動並選最像參考的；正序、倒序各問一次 | `affect_judge.py judge` → `<segments>/affect_judge.json` | 兩段選的都跟他一樣；標籤正倒序不一致的記「不確定」 | 每段約 US$0.014（2 次呼叫，每段 3 次生成、約 40 秒），十來段一集約 0.15–0.45 |
| 他的標註 | `take_review.py` 產生 `epNN-takes.html`，結果 JSON 貼回對話存成 `takes-tags.json` | — | 0 |

```bash
python3 tools/take_review.py out/segments/D1_<ep> /mnt/project-files/episodes/epNN/ --script episodes/<ep>/script.json
python3 tools/affect_judge.py judge out/segments/D1_<ep> --script episodes/<ep>/script.json   # Gemini 額度滿時跳過
python3 tools/affect_judge.py compare out/segments/D1_<ep> --tags /mnt/project-files/episodes/epNN/takes-tags.json
```

做法參考 EmergentTTS-Eval（NeurIPS 2025, arXiv 2505.23009）：直接拿 Gemini 做兩兩比較，跟人的偏好高度相關。
沒用的：UTMOS、DNSMOS、NISQA 只量音質和自然度；emotion2vec 拿來比激動程度接近亂猜（arXiv 2604.26347）。

**什麼時候改成參與挑選**：累積兩集左右（約 60 個標註），`compare` 的吻合率 75% 以上，而且他選的那次 Gemini 也選的比例
高過 `select_takes.py` 現在的選擇，才把它接成篩選條件，接之前先問他。

## 停用公告之後：重現的順序

1. **公告一出，先在停用前用舊模型多錄一套參考**。這是最後一次能拿到原聲的機會：D1 加 v5，念試聽稿、一段英文術語多的、一段情緒起伏大的，各 3 個 take，用無損格式存進 `voices/references/`，再跑 `match_voice.py build`。
2. **先試同一個 voice ID 搭新模型**。API 文件寫設計聲線「可以在任何支援的 TTS 模型上合成」。用同一句試聽稿錄 3 個 take，跑 `match_voice.py match`，再人耳聽。
3. **不夠像的話，用舊聲線當底，在新模型上衍生新聲線**：建立新的 prompted voice，把 `base_voice` 設成舊的 D1。D1M1、D1M2 就是這樣做出來的。提示詞寫「保持同一個人、同樣的台灣口音」，多做幾個候選，用 `match_voice.py` 排名。
4. **再不行**：用 `registry.json` 裡的原提示詞重新設計，或試內建聲線，一樣用 `match_voice.py` 排名，最後由人耳決定。
5. **最後手段是聲音複製**：API 有 replicated voice，用一段錄音複製聲線，需要附同意錄音。2026-11 已經決定不走聲音複製（PIPELINE.md §9），如果要用，要節目擁有者重新決定。
6. **換聲之後**：舊集不重錄，因為 mp3 和 sha256 已經在 RSS 裡。把新聲線的參考錄音加進 `voices/references/`，在這份文件註明從哪一集開始換（`voice_drift.json` 的 `voice_id` 會跟著變，前 10 集的中位數只比同一個聲線）。

自動評審判斷口音不可靠（recipe 第 7 步），所以最後要不要換、換成哪個，都由台灣母語者用耳朵聽了再決定。
