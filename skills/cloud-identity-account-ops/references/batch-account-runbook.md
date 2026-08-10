# 批量帳號 runbook

## 目錄

1. [完成標準](#完成標準)
2. [建立 tenant plan](#建立-tenant-plan)
3. [唯讀盤點](#唯讀盤點)
4. [產生與核對 manifest](#產生與核對-manifest)
5. [建立或更新帳號](#建立或更新帳號)
6. [批量設定 Employee ID](#批量設定-employee-id)
7. [密碼策略](#密碼策略)
8. [Pilot 與批量驗證](#pilot-與批量驗證)
9. [故障處理](#故障處理)
10. [官方資料](#官方資料)

## 完成標準

只有同時滿足以下條件才算完成：

- manifest 的帳號數與 Directory 實際結果相同。
- 管理員排除名單沒有任何寫入。
- 每個帳號位於正確 OU，Employee ID 符合規則。
- pilot 可登入指定 Google 服務。
- 成功、失敗與跳過清單不含秘密。
- 已說明新裝置仍會建立新的 Google session。

## 建立 tenant plan

從 `assets/tenant-plan.example.json` 複製一份到 Git 以外的暫存目錄。逐欄確認：

- `primary_domain`：目前任務的已驗證網域，不沿用範例。
- `target_ou`：專用非根 OU。若不存在，先規劃建立。
- `account_pattern`：前綴、起始號、數量和補零位數。例如 `a`、1、50、2 會產生 `a01` 到 `a50`。
- `profile`：可稽核的顯示名規則，不使用隨機姓名假裝真實員工。
- `employee_id_strategy`：`local-part` 或 `none`。
- `pilot`：必須屬於生成範圍，且不是管理員。
- `admin_exclusions`：至少兩個已確認的管理員／break-glass 帳號；若租戶實際只有一個，停止並要求先建立第二個安全管理員。
- `target_services`：只放 HTTPS 服務 URL。
- `login_strategy`：`native`、`permanent-sso` 或 `temporary-sso`。

tenant plan 禁止出現 `password`、`token`、`secret`、`private_key`、`cookie`、`certificate` 等欄位。

## 唯讀盤點

在任何寫入前取得：

1. 已驗證網域與別名。
2. 目前使用者和主郵件地址。
3. 超級管理員、委派管理員與 break-glass 帳號。
4. 目標 OU 是否存在及其繼承設定。
5. 可用 Cloud Identity／Workspace 授權。不要假設固定免費上限。
6. 現有 SSO profile、OU／群組指派和 post-SSO verification。
7. 可能與新帳號 local part 衝突的使用者、群組與別名。

只記錄必要欄位。不要匯出或檢查 Cookie、已存密碼、復原碼或 OAuth token。

## 產生與核對 manifest

執行：

```text
python scripts/plan_accounts.py <tenant-plan.json> --manifest <account-manifest.csv>
```

腳本會拒絕秘密欄位、根 OU、無效網域、超出位數的帳號範圍、pilot 不在範圍、pilot 被列為管理員，以及不安全的服務 URL。

核對：

1. 顯示的網域、OU、策略和總數。
2. 首筆、pilot 和末筆帳號。
3. manifest 每列的 `primary_email`、`employee_id`、`target_ou`。
4. 與唯讀盤點的衝突清單。

manifest 已存在時，腳本預設拒絕覆蓋。只有確認舊檔可取代時才加 `--force`。

## 建立或更新帳號

優先順序：

1. **Admin Console CSV**：先從目前 Admin Console 下載最新 CSV 範本，再把 manifest 欄位映射到範本。不要硬編碼可能改版或本地化的欄名。
2. **Admin SDK Directory API**：已有安全 OAuth／service account 流程時使用；先列出請求 payload，pilot 成功才批量。
3. **逐一 UI**：只有數量少且 CSV／API 不可用時使用。

建立前逐列分類：

- `create`：不存在，且授權與 OU 就緒。
- `update`：已存在，只修改使用者批准的欄位。
- `skip`：已符合目標或屬於排除範圍。
- `conflict`：郵件、別名、群組或管理員身份衝突；停止處理該列。

不要把 API 400／409 一律當成功。讀取錯誤類型並重新唯讀檢查該帳號。

## 批量設定 Employee ID

若策略為 `local-part`，把 `user03@example.com` 的 Employee ID 設為 `user03`。先檢查跨網域是否會重複；若多個網域共用同一 OU，可改成組織內唯一值。

可用方式：

- Admin Console CSV 上傳。
- Admin SDK Directory API：寫入 `externalIds[].type: organization`。
- Google Cloud Directory Sync：已有正式目錄來源時使用。

完成後抽查首筆、pilot、中間與末筆。再到 `Security > Authentication > Login challenges` 對指定 OU 啟用 Employee ID challenge。

Employee ID 只是 Google 可能選用的 challenge；Google 依風險決定實際顯示方式。啟用 SSO 或 2SV 時不會顯示 Employee ID challenge。

## 密碼策略

優先使用以下順序：

1. 正式 SSO + IdP MFA，避免日常共享 Google 密碼。
2. 每位使用者唯一的初始密碼，安全交付並要求首次登入變更。
3. 只有明確的受控測試帳號且使用者批准風險時，才使用共用初始密碼。

禁止把密碼放在 tenant plan、manifest 或命令列。

若批准使用 `batch_password_api.py`：

1. 讓使用者在安全環境設定短效 `GOOGLE_DIRECTORY_ACCESS_TOKEN`，scope 至少包含 `admin.directory.user`。
2. 先乾跑：`python scripts/batch_password_api.py <tenant-plan.json>`。
3. 核對目標範圍。
4. 寫入時加 `--apply --shared-password-approved --confirm-domain <domain>`。
5. 在隱藏提示中輸入和確認密碼。
6. 預設要求使用者下次登入變更密碼；只有明確批准時才加 `--no-change-at-next-login`。
7. 完成後清除短效 token 並輪替任何暴露的秘密。

## Pilot 與批量驗證

1. 只建立／更新 pilot。
2. 重新唯讀讀取 pilot 的主郵件、OU、Employee ID 和授權。
3. 依 `login_strategy` 讀取登入與 SSO runbook。
4. 登入指定服務，核對右上角目前帳號。
5. 關閉整個瀏覽器，使用相同持久化 profile 重開並再次核對。
6. pilot 成功後，每批 5–10 個；身份錯配時立即停止。
7. 完成後以 manifest 為基準重新盤點，而不是只相信寫入回應。

## 故障處理

| 症狀 | 動作 |
|---|---|
| 新使用者沒有授權 | 停止建立，核對訂閱與可用授權，不猜固定上限 |
| 郵件已存在 | 檢查使用者、群組、別名與已刪除帳號 |
| API 403 | 核對管理員權限、OAuth scope 和 domain-wide delegation |
| Employee ID 沒出現在登入頁 | 這不是失敗證明；Google 可能選其他 challenge，且 SSO／2SV 會停用此 challenge |
| 密碼重設後仍要求驗證 | 停止改密碼，按登入 runbook 處理 Login Challenge |
| 帳號登入成另一個身份 | 立即停止批次，隔離瀏覽器 profile，核對 SSO NameID 和帳號選擇器 |

## 官方資料

- [Google：批量新增或更新使用者](https://support.google.com/a/answer/40057)
- [Google：Directory API Users](https://developers.google.com/workspace/admin/directory/reference/rest/v1/users)
- [Google：Employee ID Login Challenge](https://knowledge.workspace.google.com/admin/security/add-employee-id-as-a-login-challenge)
- [Google：重設使用者密碼](https://knowledge.workspace.google.com/admin/users/reset-a-users-password)
