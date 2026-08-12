# 實作藍圖方法與範本

## 基線清單

先記錄受影響的現況，尤其是使用者要求保持相容的部分：

- 公開 API：URL、method、headers、request／response schema、錯誤語意、認證與副作用
- UI／UX：主要流程、返回、焦點、錯誤、載入、成功與資料保留
- 資料：schema、遷移、持久化格式、分析事件與隱私邊界
- 工程：框架、相依版本、設計 tokens、測試／lint／typecheck／build 指令
- 證據：契約測試、快照、fixture、命令輸出或人工觀察

## 範本

```markdown
# Implementation Plan: <任務名稱>

## 輸入
- Acceptance contract: <path>
- Workflow state: <path>

## 現況與修改前基線
- B-001｜<必須保留的行為／介面>｜證據：<測試、fixture、輸出或檔案>

## 架構與資料流
- 元件／模組責任：<邊界>
- 資料流：<來源 → 轉換 → 狀態 → 輸出>
- 公開介面：<保留／新增／明確變更>
- 新相依：<無，或理由、替代方案與影響>

## 任務

### T-001｜<單一可驗證責任>
- Covers: FR-001, NFR-002
- Depends on: 無
- Modify: `src/existing.ts`
- Create: `tests/new.test.ts`
- Change: <具體要改的責任與邊界>
- Verify: `<最小相關指令或人工檢查>`
- Evidence: <預期輸出／截圖／報告>
- Risks/Rollback: <風險與回退方式>

## 執行順序
1. T-001：<為何先做>
2. T-002：<依賴什麼>

## 覆蓋矩陣
| 需求 ID | 任務 ID | 驗證 | 狀態 |
|---|---|---|---|

## 計畫變更紀錄
| 時間 | 任務／需求 ID | 變更 | 理由與證據 |
|---|---|---|---|
```

## 任務品質檢查

- 路徑真實存在，或已明確標為待建立。
- 變更描述能讓另一個 Agent 不重新設計也能開始做。
- 測試對應需求，不是只驗證內部實作細節。
- 任務邊界避免同一檔案被多個平行步驟互相覆寫。
- 先做高風險基線與契約驗證，再做大範圍視覺或結構變更。
- 每個步驟完成後都有局部驗證；最終另有整合驗證。

## 方法來源

本方法以兩個 MIT 開源專案重新整理：

- [GitHub Spec Kit](https://github.com/github/spec-kit)：由規格建立計畫與任務、保持需求／計畫／任務一致，並在實作前做跨產物分析。
- [Superpowers writing-plans](https://github.com/obra/superpowers/tree/main/skills/writing-plans)：以精確檔案、依賴順序、測試與可執行小任務降低實作歧義。
