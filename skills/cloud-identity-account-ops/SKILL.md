---
name: cloud-identity-account-ops
description: 管理任意 Google Cloud Identity／Google Workspace 租戶的批量帳號與登入問題。用於建立或更新一批使用者、設定 Employee ID、批量密碼、排查 Login Challenge／Too many failed attempts、讓帳號首次登入 Google Maps 等服務、保存每台裝置的登入 profile，以及規劃、部署、驗證或回滾 SAML／OIDC 企業 SSO。遇到「新增 50 個帳號」「換網域重做一批」「帳號要求手機驗證」「新設備無法登入」「部署正式或臨時 SSO」時使用。
---

# Cloud Identity 帳號、登入與 SSO 操作

把每次任務當成新的租戶處理。不要沿用舊對話或舊檔案中的網域、帳號、密碼、憑證、OU 或 SSO 設定。

## 絕對規則

1. 禁止要求使用者把密碼、OAuth token、Cookie、SAML 私鑰、OIDC client secret、一次性授權或復原資料貼進對話。
2. 禁止把秘密寫入 skill、Git、程式碼、命令列、URL、日誌、截圖或帳號 manifest。讓使用者在安全提示中自行輸入，或使用既有祕密管理器／登入 session。
3. 先取得明確的管理員排除名單。禁止以帳號排序、名稱或「第一個使用者」猜測誰是管理員。
4. 禁止對根 OU 批量套用新 SSO。建立專用員工 OU，讓至少兩個 break-glass 超級管理員留在 SSO 指派為 `None` 的獨立 OU。
5. 所有寫入都依序執行：唯讀盤點 → 乾跑 → 單一 pilot → 分批執行 → 唯讀驗證 → 回滾／收尾。不得跳步。
6. 遇到目標不清、管理員可能被包含、IdP 允許名單失效、帳號對錯身份、秘密外洩或無法回滾時，立即停止。

## 固定狀態機

每次只處於一個階段，並在回覆中標明目前階段。

### 0. Intake

取得或唯讀發現以下資料：

- 主網域與所有目標次要網域
- 目標 OU／群組
- 帳號前綴、起始號、位數與數量
- 明確的管理員排除名單
- pilot 帳號
- Employee ID 規則
- 目標 Google 服務
- 登入策略：`native`、`permanent-sso` 或 `temporary-sso`
- 變更窗口、成功條件和回滾條件

複製 [tenant plan 範本](assets/tenant-plan.example.json) 到 skill／Git 以外的暫存位置。只填非秘密資料。

### 1. Read-only discovery

唯讀確認網域已驗證、授權／帳號上限、現有使用者、管理員角色、OU 成員、SSO 指派、post-SSO verification 與 pilot 狀態。輸出差異清單，不做修改。

### 2. Plan and dry run

執行：

```text
python scripts/plan_accounts.py <tenant-plan.json> --manifest <account-manifest.csv>
```

檢查輸出的首筆、末筆、總數、pilot、OU 和管理員排除。把 manifest 視為唯一目標清單。若腳本不可用，手動執行相同檢查，不要自行放寬規則。

### 3. Pilot

只建立或修改 pilot。完成帳號、Employee ID、登入策略和一個目標服務的驗證。關閉並重開相同瀏覽器 profile，再確認仍保持登入。

### 4. Batch

按明確批次執行；預設並行度為 1。每個帳號只記錄 `success`、`failed`、`skipped` 和不含秘密的原因。任何身份錯配立即停止整批。

### 5. Verify

重新唯讀讀取 Directory／SSO 狀態，核對 manifest、管理員未受影響、pilot 與抽樣帳號可進入目標服務。登入狀態只對該裝置與瀏覽器 profile 有效。

### 6. Teardown or handoff

永久 SSO：交付 IdP 擁有者、MFA、稽核、憑證輪替、停權同步和 break-glass 測試。

臨時 SSO：恢復 OU 指派與 post-SSO verification、停止公開端點、移除 tunnel／hosts／DNS、本機程序與一次性授權，刪除短期私鑰和 runtime 秘密，再唯讀驗證沒有殘留。

## 依任務讀取參考文件

- 建立新網域的一批帳號、Employee ID、密碼、CSV／Directory API：完整讀取 [批量帳號 runbook](references/batch-account-runbook.md)。
- Login Challenge、手機驗證、Too many failed attempts、新裝置、Google Maps、SAML／OIDC、正式或臨時 SSO：完整讀取 [登入與 SSO runbook](references/login-and-sso-runbook.md)。
- 同時包含帳號建立和首次登入：兩份都讀，先完成批量帳號 runbook，再執行登入與 SSO runbook。

## 腳本

- `scripts/plan_accounts.py`：驗證 tenant plan，拒絕秘密欄位，產生可審核的帳號 manifest。
- `scripts/batch_password_api.py`：以 Directory API 更新 manifest 內帳號。預設乾跑；必須明確批准共用密碼風險、加 `--apply` 並在隱藏提示中輸入密碼。

不要使用舊版 UI 座標、CDP DOM 選擇器或硬編碼 Admin Console 文字。Google UI 改版時，先從目前頁面辨識元素；能使用官方 CSV 或 Directory API 就不要依賴脆弱的 UI 自動化。

## 每次回報格式

```text
Phase: <0-6>
Tenant: <domain>
Target OU: <ou>
Strategy: <native|permanent-sso|temporary-sso>
Pilot: <email>
Planned / success / failed / skipped: <counts>
Admin exclusions verified: <yes|no>
Rollback ready: <yes|no>
Next action: <one concrete action>
```

不要在回報中附上任何秘密。
