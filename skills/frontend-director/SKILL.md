---
name: frontend-director
description: 以單一入口完成高品質前端長任務。用於建立或大幅改版網站、Web App、互動頁面、設計系統或跨檔案前端功能，以及同時要求設計、UX、動效、程式品質、測試與安全交付時；會建立可恢復的需求與任務狀態，按任務執行理解、測試、實作、驗證、差異審查與證據閉環，並在 Claude Code、Codex、OpenCode、Hermes 或其他支援 Agent Skills 的環境使用同一套核心。也用於中小型前端修改，但會裁剪不適用階段。使用者只需啟動本 skill 一次。
---

# 前端總指揮

接管前端任務直到可驗證交付。使用本檔作為唯一入口；每到一個階段，先用宿主原生機制發現並載入該階段的子 Skill，再執行工作。完整組合包內的子 Skill 是必須實際使用的能力，不是只安裝備用。只有 discovery 證據確認能力不存在或不可讀時，才使用內建 reference fallback；不得跳過載入後仍宣稱用了 Skills。

## 不可違反的規則

1. 先固定需求，再設計或寫碼。不得為了配合現有實作或測試而降低需求。
2. 使用者只需啟動本 skill 一次。除非決策會改變範圍、安全、隱私或核心體驗，否則採取合理可逆假設並繼續。
3. 一次只載入目前階段需要的 reference 或外部 skill；不要在任務開始時讀完全部內容。
4. 寫碼時一次只處理一個 `T-###`，完整跑完 Coding Loop 才進入下一項。
5. 任何影響已驗證範圍的修改都會使舊證據失效；沒有新證據不得宣稱通過。
6. 優先遵守專案既有架構、命令與規範。不要猜測不存在的檔案、工具或測試指令。
7. 外部增強 skill 不得改寫本工作流的需求、任務、狀態與 Gate；有衝突時以使用者要求和驗收契約為準。
8. Gate 不能只靠一份自述 Markdown 通過；必須先記錄該階段要求的具名檢查、證據 hash 與工作區指紋。
9. `skillsUsed` 不得為空完成 full workflow；每次載入子 Skill 都要記錄 `SKILL.md`，缺失時改記有 discovery 證據的 fallback。

## 啟動或恢復

把本 `SKILL.md` 所在資料夾記為 `<skill-root>`，不要假設 `.codex`、`.claude`、`.opencode` 或 `.hermes` 等固定安裝路徑。

1. 讀取專案指示、使用者要求、現有程式與測試入口。
2. 若 `.agent/workflow-state.json` 存在，執行：

   ```text
   python <skill-root>/scripts/workflowctl.py --root <project-root> status
   ```

   從 `currentPhase`、`currentTask` 和 `nextAction` 繼續；不要重做仍有效的工作。
   若狀態來自 v5／policy v1，先執行 `upgrade-policy`；舊狀態仍可讀，但不得沿用空子 Skill 與舊 Gate 證據完成 v6。
3. 若狀態不存在，依任務選擇 `full` 或 `targeted`，執行：

   ```text
   python <skill-root>/scripts/workflowctl.py --root <project-root> init --mode full
   ```

4. 若環境不能執行 Python，依 [狀態與控制器](references/workflow-state.md) 維持相同 JSON；可繼續工作，但最終報告必須標示控制器未自動驗證。

## 子 Skill 載入協議

進入每個階段後先做以下動作，完成前不可執行 `pass-gate`：

1. 用宿主原生 Skill 工具找出表格所列能力並完整讀取其 `SKILL.md`；沒有原生工具時使用 `scripts/agent_skill_bridge.py list/load`。
2. 每載入一個 Skill 就記錄：

   ```text
   workflowctl log-skill <name> --skill-file <absolute-path-to-SKILL.md> --resources SKILL.md --source native
   ```

3. 找不到時保存真實 discovery 輸出，再記錄 fallback：

   ```text
   workflowctl log-fallback --missing-skills <name> --reason "..." \
     --reference <表格中的必讀 reference> --discovery-evidence .agent/evidence/<phase>-skill-discovery.txt
   ```

4. 不得在子 Skill 可用時選 fallback。UI 階段的 `impeccable`、`taste`、`hue` 要依序載入並分工；implementation 起讓 `delivery-quality-gate` 全程作為品質 overlay；security 階段再依風險讓它路由 Mantis 或同等能力。

## 階段路由

| 階段 | 必讀 | 階段能力（依序實際載入） | Gate |
|---|---|---|---|
| contract | [需求契約](references/contract.md) | 必載 `define-acceptance-contract` | 所有明確要求已有可測 `FR/NFR` |
| plan | [實作規劃](references/implementation-plan.md) | 必載 `plan-implementation` | 每項需求映射到檔案級 `T-###` 與驗證 |
| ui | [UI 品質](references/ui-quality.md) | 必載 `impeccable` → `taste` → `hue`；按需 `ui-ux-pro-max` | 設計方向具產品特異性且雙尺寸可用 |
| ux | [UX 互動](references/ux-interaction.md) | 必載 `interaction-experience-design` | 主要、錯誤、空白、載入與恢復流程可完成 |
| motion | [動效](references/motion.md) | 通過時至少載入一個對應 GSAP Skill；即使用純 CSS 也用它審查目的、性能與降級；確實不需動效才 skip | 動效有目的、可中斷且支援 reduced motion |
| implementation | [Coding Loop](references/coding-loop.md) | 必載 `delivery-quality-gate`，並保持品質 overlay | 每個任務都有最新驗證與 diff 審查 |
| integration | [整合驗證](references/verification.md) | 再載 `delivery-quality-gate`，使用真實瀏覽器與語意 oracle | 每個需求都有實作與最新證據 |
| security | [安全交付](references/security.md) | 再載 `delivery-quality-gate`；高風險必載 Mantis／同等 specialist | Critical/High 為零，其他風險已處理 |

純 bug、重構或不改可見介面的任務可以跳過 `ui`、`ux`、`motion`，但必須記錄理由。新增或修改可見介面時不得跳過 `ui`；含狀態或互動時不得跳過 `ux`。`contract`、`plan`、`implementation`、`integration`、`security` 不可跳過。

## 逐任務執行

進入 `implementation` 後，依計畫順序處理每個任務：

1. 用控制器 `start-task T-###`，只讀該任務需要的程式、契約和 references。
2. 建立修改前基線；可行時先建立會因缺陷而失敗的測試或重現步驟。
3. 實作最小但完整的修改，不把無關重構混進同一任務。
4. 執行最小相關測試；用 `record-check` 記錄真實指令、退出碼與證據。實作 Gate 另要求 tests、typecheck、lint 與 diff-review；不存在的命令只能以具體理由記為 not-applicable，不能靜默省略。
5. 檢查 diff 的需求範圍、模組邊界、重複、錯誤處理、型別、無障礙、效能與安全。
6. 只有控制器允許 `complete-task` 時才開始下一個任務。失敗就留在同一任務修正。

完整命令與失效規則見 [Coding Loop](references/coding-loop.md) 和 [狀態與控制器](references/workflow-state.md)。

## Gate 與回退

- 先依 [狀態與控制器](references/workflow-state.md) 用 `record-gate-check` 記錄該階段所有必要檢查，再用 `pass-gate <phase> --evidence <path> --summary <text>` 通過；用 `skip-phase` 記錄不適用的可選階段。
- Gate 失敗時回到造成問題的最早階段。UX 修正若改變視覺結構，回到 UI；實作發現契約衝突，回到 contract；安全修補後回到 implementation 與 integration 重驗。
- 需求、公開介面、元件邊界、資料流或任務依賴被修改時，執行 `invalidate`，不可沿用舊證據。
- 只有 `workflowctl finish` 成功後，才可把狀態標為 `done`。
- security Gate 前必須用 `classify-security` 明確分為 low／medium／high；空 `risks` 陣列不再等於完成安全審查。

## 跨 Agent 行為

核心只依賴開放的 `SKILL.md`、相對 references、JSON 和 Python 標準函式庫。各宿主的 hooks、plugins 或 tool events 只用於自動啟動、恢復與阻止提前完成，不得成為核心正確性的唯一來源。接入 Claude Code、Codex、OpenCode、Hermes 或自研 Agent 時讀 [平台轉接](references/platform-adapters.md)。模型容易漏步驟、工具結果判斷不穩或長上下文表現下降時，再讀 [較弱模型護欄](references/model-robustness.md)，每次只提供一張任務工作卡。

## 最終回報

列出完成範圍、`skillsUsed` 與 fallbacks、需求覆蓋、實際 lint／typecheck／測試／build／桌面與手機瀏覽器結果、語意 oracle、安全分級、未驗證項目及殘留風險。不得只回報「已完成」，也不得把未執行的檢查寫成已通過。
