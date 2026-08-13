---
name: frontend-director
description: 以單一入口完成高品質前端長任務。用於建立或大幅改版網站、Web App、互動頁面、設計系統或跨檔案前端功能，以及同時要求設計、UX、動效、程式品質、測試與安全交付時；會建立可恢復的需求與任務狀態，按任務執行理解、測試、實作、驗證、差異審查與證據閉環，並在 Claude Code、Codex、OpenCode、Hermes 或其他支援 Agent Skills 的環境使用同一套核心。也用於中小型前端修改，但會裁剪不適用階段。使用者只需啟動本 skill 一次。
---

# 前端總指揮

接管前端任務直到可驗證交付。使用本檔作為唯一入口；每到一個階段，先用宿主原生機制發現並載入該階段的子 Skill，再執行工作。完整組合包內的子 Skill 是必須實際使用的能力，不是只安裝備用。只有 discovery 證據確認能力不存在或不可讀時，才使用內建 reference fallback；不得跳過載入後仍宣稱用了 Skills。

## 定位聲明：本 skill 是調度器，不是設計標準

frontend-director 只做四件事：
1. 階段路由（contract → plan → ui → ux → motion → implementation → integration → security）
2. 子 Skill 的發現與載入協議
3. 狀態、任務與證據的管理（workflowctl）
4. Gate 的記錄與通過機制（骨架，不承載具體設計標準）

**本 skill 不持有具體設計限制**：設計標準的分工為——`impeccable`（craft 與大膽導向）、`ui-ux-pro-max`（設計模式資料庫，一般創意專案默認）、`taste`（僅在使用者提供參考網站時，逆向工程該站品味）、`hue`（僅在使用者要求模仿品牌或建立可重用設計語言時）、`interaction-experience-design`（交互邏輯）、`gsap-*`（動效實作）、`delivery-quality-gate`（程式品質與安全）。references/ 內的非劣檢查清單若與子 skill 的標準衝突，以子 skill 與 [創意等級](references/creative-tier.md) 為準。設計創意度的下限由 [creative-tier.md](references/creative-tier.md) 決定，本 skill 的 Gate 只驗證「該階段該有的工作與證據存在」，不驗證「設計是否夠克制」。


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
   若狀態來自 v5／policy v1 或 v6／policy v2，先執行 `upgrade-policy`；舊狀態仍可讀，但不得沿用舊 Gate 證據完成 v6.1。
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

4. 不得在子 Skill 可用時選 fallback。UI 階段的載入規則：`impeccable`、`ui-ux-pro-max` 必載並分工（一般創意專案默認）；`taste` 僅在使用者提供參考網站時載入；`hue` 僅在明確要求模仿品牌或建立設計語言時載入（見階段路由表）；implementation 起讓 `delivery-quality-gate` 全程作為品質 overlay；security 階段再依風險讓它路由 Mantis 或同等能力。

## 階段路由

| 階段 | 必讀 | 階段能力（依序實際載入） | Gate |
|---|---|---|---|
| contract | [需求契約](references/contract.md)＋[創意等級](references/creative-tier.md) | 必載 `define-acceptance-contract`，判定並記錄 Creative Tier（Tier 3 必填） | 所有明確要求已有可測 `FR/NFR`；Tier 已判定 |
| plan | [實作規劃](references/implementation-plan.md) | 必載 `plan-implementation` | 每項需求映射到檔案級 `T-###` 與驗證 |
| ui | [創意等級](references/creative-tier.md) | 必載 `impeccable` → `ui-ux-pro-max`（一般創意專案默認組合）；`taste` **只在**使用者提供參考網站時載入；`hue` **只在**使用者明確要求模仿某品牌網站或建立可重用設計語言時載入 | signature visual 計畫與雙尺寸規格完整（標準依子 skill 與 tier） |
| ux | [UX 互動](references/ux-interaction.md) | 必載 `interaction-experience-design`（交互邏輯先行；創意互動不受其扣分制限制） | 主要、錯誤、空白、載入與恢復流程可完成 |
| ux | [UX 互動](references/ux-interaction.md) | 必載 `interaction-experience-design`（交互邏輯先行；創意互動不受其扣分制限制） | 主要、錯誤、空白、載入與恢復流程可完成 |
| motion | [動效](references/motion.md)＋[創意等級](references/creative-tier.md) | Tier ≥2 必載 GSAP 對應 skill（timeline／scrolltrigger／performance 依檔位）；用其審查與實作敘事動效 | 動效達檔位（M2/M3）、可中斷且支援 reduced motion；Tier 3 有 signature moment |
| implementation | [Coding Loop](references/coding-loop.md) | 必載 `delivery-quality-gate`，並保持品質 overlay | 每個任務都有最新驗證、format 與 diff 審查 |
| integration | [整合驗證](references/verification.md) + [視覺真實性](references/visual-truth.md) | 再載 `delivery-quality-gate`，使用真實瀏覽器、語意 oracle 與證據 manifest | 每個需求、signature visual 與互動壓力路徑都有最新證據 |
| security | [安全交付](references/security.md) | 再載 `delivery-quality-gate`；高風險必載 Mantis／同等 specialist | Critical/High 為零，其他風險已處理 |

純 bug、重構或不改可見介面的任務可以跳過 `ui`、`ux`、`motion`，但必須記錄理由。新增或修改可見介面時不得跳過 `ui`；含狀態或互動時不得跳過 `ux`。`contract`、`plan`、`implementation`、`integration`、`security` 不可跳過。

## 逐任務執行

進入 `implementation` 後，依計畫順序處理每個任務：

1. 用控制器 `start-task T-###`，只讀該任務需要的程式、契約和 references。
2. 建立修改前基線；可行時先建立會因缺陷而失敗的測試或重現步驟。
3. 實作最小但完整的修改，不把無關重構混進同一任務。
4. 執行最小相關測試；用 `record-check` 記錄真實指令、退出碼與證據。實作 Gate 另要求 tests、typecheck、lint、format 與 diff-review；若專案已有 formatter 必須實際執行，不存在的命令只能以具體理由記為 not-applicable，不能靜默省略。
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

## v6.1 核心視覺真實性硬閘門

任何新增或修改可見 UI 的任務，都必須讀取並執行 [Signature Visual Truth](references/visual-truth.md)。先找出承載產品識別或事實主張的 signature visuals，再為每一項選擇 `sourced`、`procedural-validated`、`generated-illustration` 或 `intentional-abstraction`。科學、醫療、地理、金融、歷史、博物館與產品辨識等事實性畫面，只能使用前兩種。

不得以 CSS 漸層圓球、無紋理幾何體、emoji、任意線條、假地圖、假資料、共用貼圖或小尺寸遮掩缺陷來冒充核心視覺。沒有可信資產時，改採明確標示的誠實抽象或改變視覺方向，不得偽造寫實感。

UI Gate 必須記錄 `signature-visual-plan`。若 UI 階段通過，integration Gate 必須以 `.agent/evidence/visual-evidence.json` 記錄自動化 `visual-fidelity`，並執行：

```text
workflowctl validate-visual-evidence --manifest .agent/evidence/visual-evidence.json
```

同時執行 `interaction-stress`，覆蓋播放中拖曳、快速切換、重設、重複開關、焦點返回、動畫清理與 reduced-motion。implementation Gate 另外固定要求 `format`；若專案已有 formatter，必須實際執行並通過。核心視覺任何一項二元審查為 false，都要回到最早負責任務修正，不能用 Lighthouse、detector 分數、build 成功或自述報告抵銷。

## 最終回報

列出完成範圍、`skillsUsed` 與 fallbacks、需求覆蓋、實際 format／lint／typecheck／測試／build／桌面與手機瀏覽器結果、visual-fidelity、interaction-stress、語意 oracle、安全分級、未驗證項目及殘留風險。不得只回報「已完成」，也不得把未執行的檢查寫成已通過。
