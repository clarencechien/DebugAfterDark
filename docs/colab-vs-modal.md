# Breeze ASR：Colab 對 Modal（2026-11-18）

挑選與驗收（`docs/recipe.md` 第 5、7 步）的 Breeze-ASR-25 轉寫目前在 Modal 上跑。這次拿 EP34、EP35 的同一批生成，
在 Colab 上再跑一次，比時間、成本和挑選結果。只跑了一次，數字是單次讀數。

做法參考 [clarencechien/colabpoc](https://github.com/clarencechien/colabpoc)（Colab CLI v0.8.0、`--auth=adc`、憑證在環境變數
`COLAB_ADC_JSON`，不印出來）。Colab 端的腳本是 `tools/colab_breeze.py`，原始轉寫在
[`colab-vs-modal/colab_breeze_ep34_ep35.json`](colab-vs-modal/colab_breeze_ep34_ep35.json)。

## 兩邊的設定

| | Modal（`tools/modal_breeze.py`） | Colab（`tools/colab_breeze.py`） |
|---|---|---|
| GPU | A10（這次拿到的；設定是 L4 → A10G → T4 依序退） | T4（帳號沒有付費運算單元，L4 會被拒，見 colabpoc） |
| 模型 | Breeze-ASR-25 轉 CTranslate2 int8，在 image 裡轉好 | 同一個轉法，每台新 VM 自己下載、轉一次 |
| 解碼 | zh、beam 5、VAD、時間戳超出時重試，int8_float16 | 完全相同 |
| 平行 | 每批 12 檔，三批同時送，可能落在不同容器 | 一張卡，逐檔 |
| 音檔 | 同一批 57 個 wav（EP34 27 個、EP35 30 個，共 44.6 分鐘），沒有轉檔 | 同左，tar 之後上傳，兩邊 md5 相同 |

## 時間

| 步驟 | Modal | Colab |
|---|---|---|
| 開機 | TTS 時就用 `warm_remote()` 叫醒，挑選時已經在跑 | `colab new` 4 秒拿到 T4 |
| 準備模型 | 0（在 image 裡） | pip 8 秒、下載加轉檔 76 秒 |
| 上傳 | 跟著呼叫送出 | 123 MB 一次上傳回 HTTP 500；切成 4 個 40 MB 共 23 秒 |
| 轉寫 | EP34 63 秒、EP35 60 秒（牆鐘；GPU 合計 207 秒） | 57 檔 283 秒（RTF 0.108） |
| 一集挑選的總牆鐘 | 86–114 秒（含本機的聲紋、抖動） | 只轉寫就約 5 分鐘，另加上傳與準備 |

Modal 快的原因是三批平行。Colab 單張 T4 逐檔，即使不算準備時間，轉寫也是 Modal 的四到五倍。

## 結果一不一樣

| 項目 | 數字 |
|---|---|
| 轉寫文字完全相同 | 30／57 |
| 對稿子的平均錯誤率 | Modal 3.64%、Colab 3.43% |
| 同一個生成兩邊錯誤率的差 | 平均 0.39 個百分點，最大 3.8 |
| 「一樣清楚」的生成集合相同（容忍 0.012） | 9／19 段 |
| Modal 選中的那次，落在 Colab 的「一樣清楚」集合外 | 3 段（EP34 s00、EP35 s02、EP35 s05） |

不同的地方多是一兩個字：它／他、喔、單押／單壓、部位／不會。錯誤率的平均差不多，但挑選規則的容忍值只有
0.012，一兩個字就會讓集合改變，所以換到 Colab，至少有 3 段會選到不同的生成。
差異是 GPU（T4 對 A10）造成的，還是別的原因：沒查，只記現象。2026-11-07 曾在 Modal L4 與本機 CPU 比過 EP10，十段選中的相同。

## 成本（推算）

| | 推算 | 依據 |
|---|---|---|
| Modal | GPU 207 秒，加上容器閒置到關閉的 10 分鐘 | 實際金額看 Modal 後台帳單，這裡沒有核對 |
| Colab | VM 存活約 15 分鐘（00:50–01:05 UTC，含一次因檔名重複重跑），約 0.3 運算單元 | `usage` 顯示的 1.15 單元／小時乘上存活時間；帳戶餘額全程 0.00，沒有看到實際扣點 |

## 踩到的事

- Colab 的 image 是 CUDA 13，ctranslate2 4.8.5 要 `libcublas.so.12`：把 pip 的 CUDA 12 cublas、cudnn 放進 `LD_LIBRARY_PATH`
  （`colab_breeze.py` 的 `cuda12_libs()`，同 colabpoc 的作法）。
- `colab exec` 預設 30 秒沒輸出就斷線，轉檔和轉寫要加 `--timeout`；斷線時 VM 上的指令照常跑完。
- 單檔上傳 123 MB 會 500，切成 40 MB 一塊就過。錯誤訊息的網址裡帶有 runtime 的 token，不要貼出去。
- 兩集的檔名都是 `s00_open.take0`，結果要用「集數／檔名」當 key。
- 結束一定 `colab stop`；這次 `stop` 之後 `sessions` 立刻是空的，`usage` 的 Active assignments 仍顯示 1 一陣子（colabpoc 記過同樣現象）。

## 結論

- **挑選照舊用 Modal。** 快四到五倍，不用每次轉模型、上傳，而且 0.012 的容忍值是在 Modal 和 CPU 上定的。
- **Colab 可以當 Modal 掛掉時的備案**，管線是通的。用的話要知道：約 3/19 段會選到不同的生成，得重新看那幾段；
  一集多花約 5 分鐘。
- 要比得公平，需要 Colab 拿得到 L4（付費運算單元），並且多跑幾集。這次沒做。

## 2026-11-22 更新：改成 Colab L4 優先

- 帳號餘額從 0 變成 200 運算單元（來源沒查，可能是 Google AI Pro 每月額度）。實測：L4 可開（1.94 單元／小時），
  A100 40GB 可開（6.73，第一次沒貨、重試拿到），G4 沒貨，H100 帳號沒權限。
- Modal 11/20、11/22 都撞到花費上限，所以 `--asr breeze-cloud` 改成 Colab L4 → Modal → 本機 CPU，`tools/colab_remote.py` 從本機驅動整個流程。
- `colab_breeze.py` 加 `--workers`：一張 L4 上 3 條執行緒，EP46 的 32 段轉寫 47 秒 → 30 秒，文字 32/32 相同。
- 新開的 session 第一個 `exec` 曾卡 7 分鐘，現在先送一個空指令等 kernel 回應再做事。
- L4 對 Modal 的挑選結果還沒並排比過（Modal 這兩天沒額度）；Modal 有額度時拿同一集兩邊各跑一次再補。
