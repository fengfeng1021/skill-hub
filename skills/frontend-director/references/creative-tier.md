# Creative Tier — 創意等級矩陣

v6.1 的缺陷是「防禦式設計」：全部 Gate 檢查都是非劣檢查，沒有卓越檢查；動效階段語義是「確認合理」而非「做出記憶點」。本檔案為每個專案在 contract 階段標記創意等級，等級決定設計、動效、審查的下限，**不允許等級以下的保守輸出**。

## 判定方式（contract 階段必填）

依產品類型與受眾期望判定：

| Tier | 名稱 | 適用 | 判斷訊號 |
|---|---|---|---|
| Tier 1 | 保守・信賴型 | 金融、醫療、法務、政府、企業工具 | 受眾要求可信與穩定，視覺創意是次要 |
| Tier 2 | 進取・品牌型（預設） | 一般消費品牌、SaaS、內容站 | 需要記憶點但不能喧賓奪主 |
| Tier 3 | 大膽・創意型 | 創意機構、作品集、藝術、時尚、娛樂、行銷活動 | 動態與視覺本身是產品；「安全」是失敗 |

判定訊號舉例：要求「令人印象深刻」「大膽」「震撼」「wow」「創意機構作品集」「落地頁行銷」→ Tier 3。不確定時取較高等級，contract 的變更紀錄必須記錄判定理由。

## Tier 下限（不可違反的生產標準）

### Tier 1
- 動效：M1（微互動，CSS）即可；不得為了動效犧牲可信感。
- 簽章視覺：嚴格事實規則（sourced／procedural-validated）。
- 視覺要求：完整編輯級排版、狀態齊全。

### Tier 2
- 動效：至少 M2（敘事型，使用 GSAP 時間軸；載入 gsap-timeline，捲動驅動再加 gsap-scrolltrigger）。
- 簽章視覺：至少一項達到「創意構成」等級（EX-1..EX-5 全過）。
- 必做：每頁至少一個 signature moment（見下）。

### Tier 3
- 動效：至少 M2，預設 M3（沉浸式：ScrollTrigger 敘事、stagger、時間軸編排、倒帶與中斷控制）。**必須載入對應 GSAP skills**（gsap-timeline、gsap-scrolltrigger、gsap-performance 依序）。
- 簽章視覺：EX-1..EX-5 全過，且至少一個視覺採用非保守構成（不對稱、粗獷、超比例字型、破壞性排版、動態視覺等）。
- 必做：
  1. 每個主要頁面至少一個 **signature moment**——一進場或捲動中讓人停下來的互動時刻（全視窗動畫、cursor 互動、scroll-driven 場景轉換、影片式敘事等）。
  2. **bolder 對照審查**：ui Gate 前，與 3 個同類頂尖站（真實網址）書面比較——列出每頁 1–2 句「我們比它多做了什麼」；找不到超越點就回設計階段。
  3. 動效不得只當裝飾：至少一段動效必須**傳遞資訊**（如 scroll-driven 案例進場、時間軸對照、數據動畫）。
- 防禦式設計禁令：不得以「合規」「對比度 OK」「reduced-motion 有支援」當作設計完成的理由；Tier 3 的驗收基準是「印象與記憶點」，不是「沒有缺陷」。

## Signature Moment 定義與檢查

signature moment = 使用者第一次到達某頁面時，在 3 秒內發生的、讓其停頓並記住的互動或視覺事件。

檢查清單（每頁至少一項為真）：
- SM-1｜進場編排：首屏元素有時間軸編排的進場（非同時淡入）。
- SM-2｜動態主視覺：主視覺會動（scroll 驅動、視差、形變、循環動畫），不是靜態圖。
- SM-3｜互動驚喜：cursor、hover、拖曳、過場中有超出預期的即時回應。
- SM-4｜敘事結構：捲動即故事（章節轉場、場景轉換、進度敘事）。

## 與真實性規則的關係
- Tier 3 的創意自由只適用於**非事實性**視覺（藝術、品牌、抽象構成）。
- 事實性畫面（科學、地理、金融、歷史、產品辨識、人物照）仍然只能 `sourced`／`procedural-validated`；創意機構站的「案例研究截圖」屬產品辨識 → sourced；其抽象背景、字型構成、動態場景 → 可自由。
- 這套分級解決 visual-truth 語感過度保守的問題：同一套規則，Tier 1 嚴格、Tier 3 把抽象與生成視覺放行到「誠實抽象」即可。

## Gate 對應
- contract：記錄 tier（contract gate 檢查項目 `creative-tier`）。
- ui：Tier ≥2 的專案，EX 檢查全部適用；Tier 3 另加 signature-moment-plan 與 bolder-comparison。
- motion：Tier 決定動效檔位（M1/M2/M3）與 GSAP skill 載入義務；Tier 3 不得 skip 動效。
- integration：signature moment 在真實瀏覽器實測（觸發、中斷、reduce 降級）；Tier 3 的 bolder 對照成果列入視覺證據。
