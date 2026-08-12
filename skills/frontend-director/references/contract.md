# 需求契約基線

在設計或寫碼前，把使用者要求固定成 `.agent/acceptance-contract.md`。若已載入 `define-acceptance-contract`，使用其完整方法；否則執行本基線。

## 步驟

1. 保留使用者明確要求的原意，整理目標使用者、主要情境、輸入輸出、限制、必須保留與排除範圍。
2. 用 `FR-001` 起編功能需求，用 `NFR-001` 起編效能、無障礙、相容性、安全與品質限制。
3. 每項只描述一個可觀察結果，並補上主要、空白、載入、錯誤、恢復和邊界情境中適用的條件。
4. 把可逆細節列為假設；只有會改變範圍、安全、隱私或核心體驗的缺口才詢問使用者。
5. 不得用「漂亮、快速、直覺、完整、適當」作為唯一驗收條件；改寫成可觀察或可測量結果。

## 最小格式

```markdown
# Acceptance Contract

## Goal
## Scope / Out of scope
## Assumptions

| ID | Requirement | Acceptance | Source |
|---|---|---|---|
| FR-001 | ... | Given/When/Then 或可觀察結果 | user/project/assumption |
| NFR-001 | ... | 數值、標準或明確檢查 | user/project/assumption |

## Edge and failure states
## Compatibility and must-preserve baseline
## Change log
```

## Gate

- 所有明確要求都有 ID，沒有互相矛盾或不可驗證的條目。
- 沒有為了現有程式或測試容易通過而降低要求。
- 每項假設都可逆且沒有擴大安全風險。
- 將需求加入控制器後才推進：

  ```text
  workflowctl add-requirement FR-001 --text "..." --kind functional
  workflowctl pass-gate contract --evidence .agent/acceptance-contract.md --summary "需求完整且可測"
  ```
