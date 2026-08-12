# 跨 Agent／跨模型評測

用相同任務、程式庫快照、模型參數、權限和時間限制比較 control 與 skill。不要讓評測模型看到預期修正或先前結論。

## 實驗組

- `control`：不載入 frontend-director。
- `skill`：只要求使用 frontend-director，不額外口述其內容。
- 可選 `ablation`：逐一移除設計、Coding Loop、控制器或平台 adapter，判斷真正有效的部分。

## 最低任務集

涵蓋新介面、既有頁面改版、表單與錯誤恢復、資料儀表板、bug 修復、重構、動畫、API／安全和效能退化。固定加入單位格式、可感知進度、Modal 焦點返回、reduced motion、手機觸控區和圖表 fallback 等回歸案例。

## Adversarial visual cases

Include factual signature-image tasks in which a generic gradient object can superficially satisfy DOM and performance checks. Score provenance, recognizability without labels, entity distinction, factual truth, source/model match, and full-size craft as primary metrics. Also include impossible scale/camera bounds, duplicated textures across entities, broken-asset fallback, and interaction sequences such as play→drag→reset. A single false factual claim or placeholder core visual is a critical regression regardless of aggregate aesthetics.

## 評分

先使用確定性指標：build、typecheck、lint、unit、integration、E2E、console error、無障礙、效能預算和安全掃描。再做不知道組別的人工／模型審查：需求覆蓋、產品特異性、互動完整性、模組邊界、重複、錯誤處理和可維護性。

每次 run 依 `evals/result.schema.json` 產生 JSON；用 `scripts/evaluate_runs.py` 比較同一 agent、model、task 的 control 與 skill。只有預先定義的主要指標改善、沒有關鍵回歸，才宣稱品質提升。
