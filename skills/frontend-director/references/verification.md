# 整合驗證與交付證據

逐任務通過不代表整體一定正確。整合階段要從驗收契約反向證明產品，而不是只列出執行過哪些命令。

## 驗證層級

1. **靜態**：格式、lint、typecheck、生成檔一致性。
2. **單元／元件**：核心邏輯、邊界、狀態與錯誤分支。
3. **整合**：模組、資料流、路由、API 與持久化協作。
4. **瀏覽器／端到端**：真實主要、替代、錯誤與恢復流程。
5. **品質屬性**：手機與桌面、鍵盤、焦點、無障礙、效能、reduced motion、console error。

## 語意 Oracle

不要只斷言元素存在或文字出現。對每個跨元件需求寫出「輸入 → 所有依賴輸出」的不變量，並至少驗證邊界值與一個失敗／重設路徑。例如：

- slider 值改變後，統計、環境、圖表 marker 與文字替代都對應同一數值；marker 座標仍在圖表 domain 內。
- 「清除篩選」要重設所有會造成空結果的條件，不只重設其中一個欄位。
- 警告訊息要出現在對應的數據卡與可存取名稱中，不能只檢查頁面上某處有警告文字。
- localStorage 損壞、拒絕或寫入失敗時，恢復行為與使用者回饋符合契約。

把這些不變量存成 `semantic-oracles` Gate 證據。DOM snapshot、截圖與單一 `getByText` 都不能單獨證明跨元件同步正確。

只執行專案真實存在且適用的命令。缺少某層時，用可重複人工步驟或其他證據替代並明確標示限制。

## Adversarial visual and interaction checks

If UI passed, create `.agent/evidence/visual-evidence.json`, run `workflowctl validate-visual-evidence`, and record it as automated `visual-fidelity`. Review actual desktop, mobile, and largest detail screenshots against source material. Prefer a blind independent agent or human; when unavailable, disclose degraded self-review. Any false binary check returns the workflow to UI or the owning implementation task.

If UX passed, `interaction-stress` must be automated. Exercise sequences, not isolated clicks: play then drag then pause/reset; rapid tab or filter changes with focus tracking; repeated modal open/close and focus return; reload/storage denial/error recovery; interrupted animations and cleanup; reduced-motion functional equivalence. Assert state and output invariants after every transition.

## 證據要求

每份證據包含需求／任務範圍、時間、版本或工作樹指紋、實際命令或步驟、退出碼、關鍵結果和有效狀態。截圖只能證明可見狀態，不能代替資料、安全或鍵盤行為測試。

## 追蹤矩陣

```markdown
| Requirement | Tasks | Implementation | Verification | Fresh evidence | Status |
|---|---|---|---|---|---|
| FR-001 | T-001 | src/... | unit + browser | .agent/evidence/... | pass |
```

## Gate

- 所有 `FR/NFR` 都映射到已完成任務與最新證據。
- 適用的 build、typecheck、lint、測試與瀏覽器流程已實際執行。
- 桌面、手機、鍵盤、焦點、錯誤恢復和 reduced motion 已按需求驗證。
- `semantic-oracles` 已驗證跨元件同步、幾何 domain、reset 完整性與警告歸屬等適用不變量。
- console、網路和測試輸出沒有未解釋錯誤。
- 未驗證項目和既有失敗沒有被寫成通過。
