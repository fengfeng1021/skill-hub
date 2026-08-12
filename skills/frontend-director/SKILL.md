---
name: frontend-director
description: 以單一入口完成長篇前端任務的工作流總指揮。用於建立或大幅改版網站、Web App、互動頁面與前端功能時，自動依序執行需求契約、檔案級實作藍圖、UI、UX、動效、持續程式碼品質與最終安全審查；也會依小型任務裁剪不需要的階段。使用者不必逐輪指定子 skill，除非出現無法安全假設且會改變範圍、安全或核心體驗的重大歧義。
---

# 前端工作流總指揮

接管一個前端任務直到可驗證交付。只負責路由、狀態、階段交接與 Gate；專業判斷交給當前階段的子 skill。

## 不可違反的規則

1. 使用者只需啟動本 skill 一次。宣告工作流後立即繼續，不在階段之間要求使用者再次指定 skill 或例行批准。
2. 先建立需求契約，再設計或寫程式。不得依照後來的實作或測試降低原始需求。
3. 一次只載入當前階段需要的子 skill；不要在開場讀完所有已安裝 skill，也不要複製它們的完整內容到本上下文。
4. 程式碼品質是全程 overlay，不是最後才執行的階段。每次有意義的修改後都要取得新證據。
5. 每階段必須更新工作流狀態、留下產物並通過 Gate；失敗時回到負責修正的階段，不得帶病向後推進。
   下游發現若改變檔案範圍、元件／模組邊界、資料流、公開介面或任務依賴，必須先更新實作藍圖並重跑 Plan Gate，再重驗受影響階段。
6. 除非缺少會實質改變範圍、安全／隱私或核心體驗的決策，否則採用合理預設並記錄假設後自主前進。
7. 使用 Agent 原生 skill 發現／調用機制按名稱定位子 skill，不猜固定路徑。需求契約、實作藍圖、品質驗證或高風險安全入口屬必要能力，缺失時不得宣稱 production-ready；可選設計輔助缺失時才可記錄降級並以 Gate 繼續。不得假裝已使用不存在的 skill。

## 啟動與續跑

建立或讀取 `.agent/frontend-workflow.md`。若長任務被中斷、壓縮或換回合，先從此檔恢復，不重做已通過且證據仍有效的階段。

```markdown
# Frontend Workflow
- Mode: full | targeted
- Current phase: contract | plan | ui | ux | motion | integration | security | done
- Contract: <path>
- Implementation plan: <path>
- Selected skills: <phase → skill names>
- Evidence directory: .agent/evidence/
- Completed gates: <gate + evidence id/path/time + valid/invalid>
- Pending requirements: <FR/NFR IDs>
- Assumptions/risks: <items>
- Next action: <one concrete action>
```

先把任務分類：

- 新網站、新 Web App、跨多個畫面的功能或重大改版：`full`，執行完整鏈路。
- 小型視覺調整、單一互動、單一動效或局部修正：`targeted`，只跑契約、必要的輕量實作計畫、相關專業階段、品質 overlay 與按風險決定的安全收尾。
- 純 bug／重構且不改變畫面：跳過 UI／UX／動效，保留契約、品質與安全。

## Phase 0：需求契約

載入 `define-acceptance-contract`，產生可追蹤的 `FR-###`／`NFR-###`、範圍、排除、假設、情境與成功條件。

Gate：

- 沒有重大未決歧義、矛盾或不可測量條目。
- 所有使用者明確要求都有需求 ID。
- 契約路徑已寫入工作流狀態。

## Phase 0.5：實作藍圖

載入 `plan-implementation`。先探索現有架構與測試，再保存使用者要求保持相容的 API、資料格式、事件與行為基線；把每個需求 ID 拆成 `T-###` 檔案級任務、元件／模組邊界、依賴、驗證順序與回滾方式。

Gate：每個 `FR`／`NFR` 都被任務覆蓋；路徑真實或明確標為待建立；每項任務有驗證證據；公開介面與「必須保留」行為有修改前基線。計畫路徑已寫入工作流狀態。若規劃發現需求衝突，回到契約，不自行改寫。

## Phase 1：UI

按需求選擇，不要全部載入：

| 條件 | 主 skill | 可選輔助 |
|---|---|---|
| 新介面、整體視覺、現有畫面打磨 | `impeccable` | `ui-ux-pro-max` |
| 使用者提供要模仿的網站／截圖 | `taste` | `impeccable` |
| 明確要求品牌系統或跨頁一致性 | `hue` | `ui-ux-pro-max` |

先產生設計方向、tokens、元件層級與響應式策略，再實作 UI。完成後以實際渲染結果檢查，不只讀程式碼。

Gate：契約中的視覺／內容需求有對應畫面；主要與次要層級清楚；桌機與手機沒有溢出；文字可讀、焦點可見；沒有用通用檢查表取代產品特異性。

## Phase 2：UX

載入 `interaction-experience-design`，只讀與本任務類型對應的 references。以契約和實際渲染頁面檢查主要流程、替代／錯誤／空狀態、導覽、返回、鍵盤、焦點與操作回饋。

Gate：核心任務可以走完；每個互動有狀態與回饋；錯誤可恢復；鍵盤與觸控有可用路徑。若 UX 修正會改變畫面，回到 UI 更新並重新通過 UI Gate。

## Phase 3：動效

先檢查專案既有動畫方案；若它能通過本階段 Gate，沿用現有技術，不為了使用 GSAP 替換動畫棧。需要 GSAP 時只載入對應 skill：

- 基本 tween：`gsap-core`
- React：加 `gsap-react`；Vue／Svelte：加 `gsap-frameworks`
- 多段編排：加 `gsap-timeline`
- 捲動驅動：加 `gsap-scrolltrigger`
- 特殊外掛：確定用到才加 `gsap-plugins`
- 出現卡頓或大量動畫：加 `gsap-performance`

Gate：動效服務引導、回饋或空間連續性；不遮擋操作；中斷／重入狀態正確；`prefers-reduced-motion` 保留功能；優先使用 transform／opacity。若動效暴露 UX 問題，回到 UX。

## 全程 Quality Overlay

首次寫碼前啟動 `delivery-quality-gate` 的持續品質模式：

- 從需求 ID 先建立驗證策略，不能按錯誤實作倒推測試標準。
- 每次有意義的修改後跑最小相關測試；每個階段結束跑適用的 lint、typecheck、build 與瀏覽器驗證。
- 每個里程碑檢查 diff、檔案責任、重複、耦合、錯誤處理與需求覆蓋；有審查能力時使用 `requesting-code-review`，再用 `receiving-code-review` 驗證意見。
- 把指令、結果、截圖或報告路徑寫入工作流狀態；舊證據在程式變更後不得沿用。

證據統一放在 `.agent/evidence/` 或專案既有證據目錄。預設一份證據一個 Markdown 檔，ID／檔名用 `E-YYYYMMDD-HHMMSS-<scope>.md`；每筆至少記錄需求／任務範圍、指令或人工步驟、時間、相關版本／commit、結果與 `valid` 狀態。後續修改影響該範圍時標成 `invalid` 並寫下失效原因，再重新取得證據。

## Phase 4：整合驗證

從需求契約建立追蹤矩陣：

| 需求 ID | 實作位置 | 驗證方式 | 最新證據 | 狀態 |
|---|---|---|---|---|

Gate：每個 `FR`／`NFR` 都有實作與最新證據；瀏覽器實測核心流程與雙尺寸；測試數量、README 與實際輸出一致；控制台錯誤和殘留風險已記錄。

## Phase 5：安全與交付

讓 `delivery-quality-gate` 進入最終安全模式。先做風險分級，再由 Mantis 入口選擇需要的安全 skill；不要預先載入全部 Mantis。高風險認證、權限、金流、個資或外部輸入變更必須做威脅建模與深入審查，純靜態低風險變更至少檢查秘密、依賴、XSS／注入面與外部資源。

未解決的 Critical／High 安全問題會阻擋交付；Medium 必須有已驗證緩解措施或使用者明確接受風險；Low 可以在最終報告揭露。只有需求追蹤矩陣全數通過、品質證據有效、安全門檻符合時，才能把 Current phase 標為 `done` 並交付。

## 最終回報

用一份精簡報告列出：完成範圍、使用過的子 skill、各 Gate 證據、需求覆蓋、測試／build 結果、安全結果與殘留風險。不要只回報「已完成」。
