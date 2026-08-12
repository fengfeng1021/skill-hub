# UI 品質基線

先決定產品特異的視覺方向，再開始寫元件。可用外部設計 skill 加深探索，但最終選擇必須能說明為何符合本產品、受眾和任務。

## 設計順序

1. **內容與任務**：列出頁面的首要任務、主要資訊、次要資訊與行動優先級。
2. **視覺方向**：用 3–5 個有判別力的詞描述氣質，列出一個應採用與一個應避免的參考方向。
3. **設計 tokens**：定義字體角色、色彩角色、間距節奏、圓角、邊框、陰影和動效節奏；沿用既有系統優先。
4. **元件責任**：先定元件邊界、變體、狀態和響應式行為，再寫 JSX／模板／CSS。
5. **真實渲染**：用實際內容檢查桌面與手機，不用空白方塊或理想化短字串代替。

## 低品質模式防護

- 不要把所有產品做成相同的漸層 hero、三張功能卡和模糊玻璃背景。
- 不要用裝飾取代層級；首要任務必須比品牌裝飾更容易找到。
- 不要任意新增字體、顏色、陰影、圓角和間距值；優先重用 tokens。
- 不要用過多卡片切碎本來可直接閱讀的內容。
- 不要只做正常狀態；載入、空白、錯誤、成功、disabled、focus 和長內容必須有策略。
- 不要以單一桌面截圖宣稱響應式完成。

## Signature visual hard fail

Read [visual-truth.md](visual-truth.md) before approving the UI direction. Record `signature-visual-plan` with each core visual's claim, factual status, truth mode, provenance, detail behavior, and owning task. Reject generic gradient objects, fake textures/data/maps, repeated identities, unviewable scale/camera ranges, and any detail view that merely enlarges a placeholder. Detector or aesthetic scores cannot override this review.

## 必查項目

- 文字層級、閱讀寬度、對比、焦點和觸控目標可用。
- 320–375px 寬度沒有水平溢出；1440px 不因拉寬而失去結構。
- 內容增長、翻譯、慢網路與圖片失敗不會破壞主要流程。
- 表格、圖表和複雜視覺在小螢幕有重排、捲動或等價文字方案。
- 圖示有語意，互動控件使用正確元素，不靠 `div` 模擬按鈕。
- 設計選擇可以追溯到需求，而不是只追求「看起來很 AI」。

UI 規劃 Gate 的證據包含：產品特異設計方向、桌面／手機響應式規格、正常與例外狀態 inventory，以及設計選擇如何回扣任務與受眾。這一階段不能用尚未存在的實作宣稱渲染通過。

實作完成後，integration Gate 必須另以真實瀏覽器驗證桌面與手機渲染、關鍵狀態、長內容、觸控尺寸與無水平溢出；規劃文件不能代替實際畫面。
