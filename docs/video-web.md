# 影片版：做一頁網頁，再逐格錄成影片

狀態：**11/27 決定做**。非 AI 的舊集（錢＋其他）照 EP36 的做法做影片版，RSS 版改私人，開場 A/B 一起跑，12/5 起上架。
排程和集數見下面「開場 A/B 實驗」，每集的流程圖見 [`video-version-flow.svg`](video-version-flow.svg)。

現行的影片做法見 [`video.md`](video.md)（`tools/make_video.py`），這份只寫另一條路，跟它的差別。
比較頁（六種畫面風格示意、成本表）：<https://claude.ai/artifact/XmMBuTwUxBknyUrdPBtb6Q>。

## 每集的配方（11/28 定，EP41、EP30 樣片做法）

長片一律走這條路（`opening` 或 `opening-b`，照「開場 A/B 實驗」的排法）。一集約 30–40 分鐘，錄製本身約 4 分鐘（每分鐘影片約 22 秒）。
產出先放專案資料夾 `video/old-nonai/<epNN>/`（新集放 `video/<epNN>/`），Clarence 看過才 commit、上傳。

0. **環境**（雲端容器每次都要）：`apt-get install -y fonts-noto-cjk fonts-noto-cjk-extra`；LXGW WenKai TC 放
   `~/.cache/dad-fonts/LXGWWenKaiTC-Bold.ttf`（用 `User-Agent: Wget/1.0` 讀 `fonts.googleapis.com/css2?family=LXGW+WenKai+TC:wght@700`
   會拿到完整的 ttf，不是切片的 woff2）。
1. **字卡**：`make_video.py episodes/<ep> --skeleton` 產 `video/visuals.json`，照 `script.json` 一段一段寫數字卡
   （`anchor` 是腳本裡的原句，`top`、`value`、`label`、`source`）。
   - 數字只能用腳本講過的。腳本用中文數字（「三萬五」）就照寫中文，寫成「3.5 萬」會被 `number_cards` 檢查擋下。
   - `source` 寫真正的出處（主計總處、勞動部、研究名稱）；只有報告自己算的、推論的才寫 `report`。
   - **開場的 root cause**：trace 開場把 cold open 裡**第一張 `source` 是 `report` 的卡**標成 ERROR（`◀ root cause?`）。
     這張要是這集要追的問題（EP41 是「巷口的店生意慘」，不是「成交金額 2.6 倍」）；不對就把前面的卡標成它真正的出處。
   - 沒有 `youtube` 欄位的舊集（例如 EP30），補 `title` 和兩組 `thumbnail`（照 `hooks.md`），`--thumbnail-only` 出縮圖。
2. **抓報告的圖表**：`make_video.py --capture-figures` 會截報告的 figure 和 table。報告有藏起來的元素時會逾時失敗，
   這時直接讀報告 HTML 的 `<figure>`、`<table>` 和「看數字」表，把數字抄出來。
3. **圖表重新配色**：報告的圖是淺色頁面畫的，放在深色畫面裡很刺眼，**一律用報告的數字重畫**，不直接貼截圖。
   - 寫 `video/charts.json`（格式見 `tools/webvideo/make_charts.py` 開頭；每張寫 `from` 註明數字取自報告哪一節），
     跑 `python3 tools/webvideo/make_charts.py episodes/<ep>`，產 `video/visuals/chart-*.png`（1600×440，背景就是畫面的底色）。
   - 配色：重點用橘（`acc`），這張圖要講的那一根用紅（`red`），其他灰（`dim`）。橫條圖從 0 開始。
   - 在 `visuals.json` 對應的段落加 `{"type": "figure", "anchor": "…", "image": "visuals/chart-x.png", "caption": "…", "source": "…"}`，
     anchor 選旁白講到那張圖的句子，不要跟數字卡同一句。一集 2–4 張就好，表格太長的挑 5–6 列改成短句。
   - 播放器看到檔名 `chart-*` 就不加白框；舊的截圖（`fig*.png`）照舊有白框。
4. **時間、字幕、檢查**：`make_video.py episodes/<ep> --no-video`，六項檢查都要 PASS（boundaries、subtitle_sync、subtitle_text、
   chapters、number_cards、figures）。
5. **錄製**：`build_timeline.py episodes/<ep> -o tl.json`，`render.js tl.json <ep>-A.mp4 --theme opening --variant pulse`（B 版 `--theme opening-b`）。
   先用 `--still <秒>` 看幾張：開場的 trace、每張圖出現的那一刻、最後的 breakpoint。
6. **給 Clarence 看**：mp4、預覽總表、縮圖，加上要他決定的事（root cause 對不對、新擬的標題縮圖、旁白跟報告不一致的地方）。
   他說好之後再 commit（`visuals.json`、`charts.json`、`visuals/chart-*.png`、srt、chapters、縮圖、`render_log.json`），上傳照 `publish.md`。

## 這條路是什麼

AI SDLC 課程 A1 的 demo 重播（專案資料夾 `ai-sdlc-course/a1-runs/replay-src/`）用了這個做法：

1. 一頁 HTML 提供 `seek(t)`：給一個秒數，就把畫面畫成那一刻的樣子。畫面只由資料和 `t` 決定，沒有計時器。
2. Playwright 打開這頁，逐格呼叫 `seek(i / fps)` 再截圖，PNG 直接餵給 ffmpeg，接上 mp3 成為 mp4。

它不是錄螢幕：同一份資料每次輸出一樣的影片，要改字只要改資料再重算。

跟現行的 `make_video.py`（Pillow 畫卡片、ffmpeg 合成）比：

| | make_video.py（現行） | 網頁錄製 |
|---|---|---|
| 換風格 | 改 Python 畫圖的程式 | 換一份 CSS |
| 報告的圖表 | 從報告截圖，整張出現 | 可以重畫成 SVG，跟著旁白逐條出現、標重點 |
| 動態 | 淡入、推近、進度條（ffmpeg 濾鏡） | 網頁能做的都能做，仍然可以只用低調的動態 |
| Shorts | `make_short.py` 另外一套 | 同一份資料換直式版面 |
| 時間、字幕、驗收 | 已經做好 | 先沿用 make_video.py 的產出 |

## 原型（這個 PR）

`tools/webvideo/`，沿用 make_video.py 已經算好的時間，所以不用重新對時：

- `build_timeline.py episodes/<ep>`：讀 `video/<ep>.srt`（字幕）、`video/render_log.json`（卡片時間、章節、段落起點）、
  `video/visuals.json`（卡片文字、每段背景），寫成一份 `timeline.json`。
- `player.html`：播放器，三種風格。沒有第三方 script、沒有 storage API（照 imitator `style/STYLE.md`），字型用系統的 Noto CJK。
  - `slide`：現行 make_video.py 的版面搬到網頁。**留給 Shorts 用**（使用者 11/27），長片不用。
  - `paper`：資料新聞風，**深色**（深夜的調性；使用者 11/27 確認可以）。
  - 兩種開場都先放**開機封面**：開機訊息（掛載這集的報告、載入幾個 finding 和章節、啟動 ping@debugafterdark），
    接著打出 EP 編號和這集的標題。標題打完後至少停留到能慢慢念完的時間（每秒 4.5 字，最少 4 秒；
    EP36 的 23 字標題停約 5 秒，封面總長約 6.8 秒）。封面疊在 cold open 的聲音上，不加長影片，字幕照常顯示。
  - `opening`（**A 版，11/27 定稿**：開機封面 → trace 開場（pulse）→ 深色 paper）：**建議的長片組合**（使用者 11/27）。cold open 用 trace 畫面，之後整集接 `paper`。整集都是終端機會太多，
    所以 debug 感只放在開場。trace 畫面是可觀測性工具的樣子：終端機的使用者是 `ping`（節目主持人），跑
    `trace tail --episode <ep> --follow`，cold open 的每張卡片變成一個 span（瀑布圖跟著旁白長出來），下方是結構化 log
    （INFO／WARN／ERROR）。報告自己提出的第一個論點標成 ERROR 和「root cause?」，就是這集要追的問題。
    span 名稱、數值、出處都是卡片本身的內容；trace id 由集數算出來，固定不變。
    長條的動法有四種，用 `render.js --variant` 選，版面都一樣（11/27 使用者覺得第一版一路慢慢爬有點毛躁）：
    `step`（第一版）、`ease`（0.8 秒衝到最終長度，時間數字往上跳）、`scan`（一條掃描線掃過時間軸，長條跟著填）、
    `pulse`（ease 加上進行中的 span 輕微呼吸，**預設**，使用者 11/27 選定）。
    trace 在開機封面結束後才開始：指令一個鍵一個鍵打出來（間隔不均勻但固定），按 Enter 後，
    已經發生的 span 依序補上，第一條也有動畫；新 span 那一列整列亮一下（ERROR 是紅色）。後三種在新 span 出現時，那一列和對應的 log 會亮 0.6 秒。
    樣片在 `video/web-video-options/ep36-sample/trace-motion/`。
  - `opening-b`（**B 版**）：同一個開機封面，cold open 直接用深色 paper 的大數字卡，整集都是 paper。跟 A 只差 cold open 那約 40 秒。
  - `terminal`：有 debug 代入感的終端機。每張數字卡變成一道指令（提示字元是 `ping@debugafterdark`）：前後對比的數字用 SQL 查詢，結果是表格加長條；
    單一數字用 SQL 回傳一列；其他用 `trace grep`、`trace plot`，結果是 TUI 方框。指令會先打字、
    「查詢中」一下再出結果，結果剛好落在旁白講到那句的時候。底部是 tmux 式的狀態列（集數、章節、進度、出處），換章就清畫面。
    **介於真實與 mock 之間**：指令、資料表名、`trace` 這個工具是佈景；畫面上的每個數字、說明和出處都是那張卡片本身的內容，
    不另外編。CJK 等寬字型的框線字是全形，對不齊，所以方框和表格用 CSS 邊框畫。
- `render.js timeline.json out.mp4 --theme paper --from 0 --to 30`：逐格錄製。`seek()` 回傳一個 key，
  key 沒變的格子直接重用上一張截圖，所以畫面靜止的時候幾乎不花時間。`--still 15.5 x.png` 只出一張預覽。

```bash
apt-get install -y fonts-noto-cjk fonts-noto-cjk-extra    # 雲端容器要先裝
python3 tools/webvideo/build_timeline.py episodes/ep36-credit-line -o /tmp/tl.json
node tools/webvideo/render.js /tmp/tl.json /tmp/paper.mp4 --theme paper --from 0 --to 30
```

### 2026-11-27 實測（EP36 前 30 秒，4 核雲端容器）

| 風格 | 30 秒裡真的截圖的格數（共 900 格） | 花的時間 | 換算每分鐘影片 |
|---|---|---|---|
| slide（背景一直慢慢推近） | 133 | 26.5 秒 | 53 秒 |
| paper | 93 | 11.4 秒 | 23 秒 |
| terminal（有打字效果） | 173 | 12.6 秒 | 25 秒 |

11/27 第二版（terminal 改成 SQL／CLI，paper 改深色）：paper 每分鐘 21 秒，terminal 每分鐘 28 到 29 秒。
第三版 `opening`（前 60 秒，其中 43 秒是 trace，瀑布圖一直在長）：每分鐘 38 秒。

照這個速度，9 分鐘的 EP36 整集約 3.5 到 8 分鐘，跟現行 make_video.py（約 9 分鐘）差不多或更快。
樣片和截圖在專案資料夾 `video/web-video-options/ep36-sample/`（第二版在 `v2/`，opening 在 `v3/`），只在本機產出，沒有上傳。

原型還沒做的：數字卡和字幕的驗收（目前直接沿用 make_video.py 的檢查結果）、slide 的 Shorts 直式版面、
資料新聞風的「圖表重畫成 SVG」（目前只放報告截圖）、報告導讀風格。

## 如果要做，接進流程的方式

```
imitator 報告 HTML ─┐
script.json、mp3 ───┼─> 分鏡（新）：scenes.json ─> player.html + 風格 CSS ─> render.js ─> 驗收 ─> 使用者看 ─> 9c、9d（不變）
每句的時間 ─────────┘
```

- **分鏡**：先沿用 `visuals.json`（已經有 anchor、數字卡、出處）。之後要做圖表重畫時，再讓模型從報告抽出圖表資料寫進 scenes，
  數字一律跟報告或 `script.json` 比對，比不到就不出現（跟現在 `numbers_not_in_script` 的檢查一樣）。
- **風格**：同一份 scenes 可以換 CSS，也可以混用（例如平常資料新聞風，AI 題的段落插終端機）。
- 9b 確認、9c commit、9d 上傳都不變。mp4 一樣放 Release、比對 sha256。

## 等數字出來要決定的事

1. EP36 影片版第 7 天跟 EP28–EP39（RSS 版）比，自然流量有沒有比較好。沒有的話，先查是畫面還是包裝的問題，再決定要不要換畫面風格。
2. 要不要做風格的 A/B：同一集只能上一支影片，所以比較的方式是「連續幾集輪流用不同風格」，每集看第 7 天的點閱率、30 秒和 1 分鐘留存，只看自然流量。
   上架時間實驗（到 12/4，檢討 12/10）還在跑，風格測試要排在它之後，或至少不要跟它用同一批集數。
3. 主風格。11/27 使用者的方向：長片用 `opening`（trace 開場 + 深色 paper），slide 只做 Shorts。

## 開場 A/B 實驗（11/27 定：用非 AI 的舊集跑）

問題：cold open 用 trace 畫面（A，`opening`）還是直接用大數字卡（B，`opening-b`），觀眾比較會留下來？
A 和 B 只差 cold open 那約 40 秒，開機封面、標題、縮圖版型、後面的 paper 都一樣，所以差別可以算在開場上。

- **用哪些集（使用者 11/27）**：非 AI 的舊集，照 EP36 的做法：影片版公開，那集 RSS 匯入的版本改私人
  （videoId 加進 `tools/yt_autofix.py` 的 `KEEP_PRIVATE`）。分類照 `strategy.md`「選題比例」；EP38 和之後的新集算 AI。
  不另做「純音訊、自己上傳」的對照組（使用者選少做一個實驗），所以影片版跟 RSS 版的差別分不出是畫面還是不走 RSS 匯入。
- **怎麼分組**：「測試與比較」不能換影片內容，所以用集數輪流，**在類型裡面輪流**：錢和其他各自照 ABBA 排。
  - 錢（11 集）：EP41 A、45 B、34 B、35 A、28 A、29 B、24 B、25 A、26 A、12 B、20 B
  - 其他（9 集）：EP30 A、27 B、22 B、23 A、14 A、18 B、19 B、32 A、40 A
  - 先不翻：EP06、07、13、15、16（RSS 版還有真流量，或還在實驗裡），EP37（等 12/7 改標題結果）。第一批結果出來再決定。
- **什麼時候**：12/4 舊集改標題和 EP07 A/B 結束、上架時間實驗的晚上組也跑完之後。**12/5 起每天 12:00（台北）一支**，
  錢和其他輪流（避開 20:00 的新集），12/24 上完。上傳用 `yt_upload.py`，`private` + `publishAt` 排程。
- **同一個時段、都不下廣告、縮圖同一個版型**（12/4 EP07 A/B 的贏家），「測試與比較」兩組都不做。
- **看什麼**：只看自然流量（排除廣告），每集第 7 天的數字。
  - 主要：**30 秒留存**（開場剛結束的時候還剩幾成人）。
  - 次要：1 分鐘留存、平均觀看百分比。
  - 點閱率不看：觀眾點進來之前看不到開場，點閱率差異只會來自題目。
- **怎麼判斷**（事先定好，免得看到數字再改標準）：A 的 30 秒留存中位數比 B 高 5 個百分點以上，而且兩類各自的前 4 集裡
  至少 3 組（相鄰的 A、B 配成一組）方向一樣，就用 A；B 比 A 高同樣幅度就用 B；其他情況算平手，用 B（錄製快一半，畫面也比較單純）。
  也分開看錢和其他：如果真的是一類適合 A、一類適合 B，再改成按類型固定。
- **檢查點**：12/19 第一次看（兩類各前 4 集到第 7 天），12/31 全部 20 集到第 7 天後定案。
- **舊集的限制**：題目可能過時（例如 EP45 講台股跌 28%），所以不跟 EP36 這種新集直接比，只比同一批的 A 和 B。
- **要人工的**：EP24–27 的 Short「相關影片」要在工作室改連到新的影片版。字幕用 API（`captions.insert`）上傳：
  11/27 重新授權加了 `youtube.force-ssl`，雲端環境驗證通過（repo secret 給 Action 用的那份還沒驗）。
- 實驗記錄在 `youtube/experiments.json` 的 `video-version-old-nonai`，上傳後把 videoId 填進 `videos`。

樣片（EP36 前 60 秒，只在本機）：專案資料夾 `video/web-video-options/ep36-sample/ab/` 的 `A-0-60.mp4`、`B-0-60.mp4`。
