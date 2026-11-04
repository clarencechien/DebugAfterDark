# 固定開場（ident）

> 這裡是深夜 Debug，Debug After Dark。我是 Ping。還醒著的話，我們開始吧。

- `ident.flac`：定稿，約 9 秒。每集後製時用 `make_podcast.py master --ident show/ident/ident.flac` 接在 cold open 後面，
  **不重新生成**，名字每集念法都一樣。後製只調響度，不做音色匹配（它是基準）。
- `ident-preview.mp3`：試聽用，-16 LUFS。
- 2026-11-04 用 D1 + v5 生成 5 次，mood 跟 EP00 定稿的第一段一樣（像深夜跟朋友聊天、台灣英文念法提示），稿子是 `script.json`。

| take | Breeze 錯誤率 | 音高跳動 | 字／秒 | 長停頓／分鐘 | Gemini 判斷 Ping |
|---|---|---|---|---|---|
| 0 | 2.5% | 0.182 | 4.95 | 29.7 | 英文 |
| 1 | 2.5% | 0.180 | 5.21 | 7.8 | 英文 |
| **2（選用）** | 2.5% | **0.103** | 4.39 | 13.2 | 英文 |
| 3 | 5.0% | 0.189 | 5.29 | 15.9 | 英文 |
| 4 | 2.5% | 0.174 | 5.13 | 7.7 | 英文 |

- Breeze 五次都把 Ping 寫成「pin」、把「我是」聽成「或是」一次。Breeze 的拼字習慣讓 `select_takes.py --terms Ping` 在這個詞上
  沒有鑑別力，Ping 的念法改用 `tools/gemini_check.py terms` 檢查（粗篩，最後以人耳為準）。
- 換聲線或換 TTS 模型時才重做。
