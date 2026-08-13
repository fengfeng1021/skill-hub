# 動效基線（調度層 — 不承載設計取捨）

動效的「風格與大膽度」由 [creative-tier.md](creative-tier.md) 與 GSAP 子 skill 決定，本檔案只規定調度規則與不可違反的底線（無障礙與資源清理）。本檔案不含「動效只准引導注意」等克制語義；敘事、沉浸、實驗性動效在 Tier 2／3 是被要求的，不是被容忍的。

## 調度規則

1. 依 [creative-tier.md](creative-tier.md) 判定動效檔位（M1 微互動／M2 敘事／M3 沉浸），檔位決定技術與最低工作量。
2. M1 可用 CSS transition；M2／M3 必須使用 GSAP 並載入對應子 skill（gsap-timeline、gsap-scrolltrigger、gsap-performance 依場景），不得以 CSS 簡化替代 GSAP 可達成的敘事效果。
3. 動畫狀態必須從產品狀態推導，不建立第二套互相競爭的狀態來源。
4. Tier 3 動效至少一處傳遞資訊（scroll 驅動資料、時間軸對照、進度敘事），且至少一個 signature moment（見 creative-tier.md）。

## 不可違反的底線（無障礙／品質，任何檔位適用）

- 優先 `transform`／`opacity`，避免每幀 layout；GSAP 用 transform aliases。
- 動畫可重複觸發、中斷、快速切換、元件卸載，不殘留 timer、listener、timeline；GSAP 用 `gsap.context()`／`matchMedia()` 清理，resize 時 `ScrollTrigger.refresh()`。
- `prefers-reduced-motion` 下保留完整功能與必要狀態回饋，動效降級為靜態最終狀態；使用 `gsap.matchMedia()` 的 reduceMotion 條件。
- 動畫不延遲主操作、不遮擋控件、不讓焦點與視覺位置分離。
- duration／ease／stagger 使用一致 tokens。
- 低階裝置、頁籤切換與 resize 需檢查。

Motion Gate 記錄：檔位判定與理由、動效清單與目的、reduced-motion 等價、GSAP 使用與清理策略。integration 在一般與 reduce 兩種模式實測，快速重複操作確認狀態收斂。
