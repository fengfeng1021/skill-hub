# 登入、裝置與企業 SSO runbook

## 目錄

1. [正式企業 SSO 是什麼](#正式企業-sso-是什麼)
2. [選擇登入策略](#選擇登入策略)
3. [判斷登入阻擋類型](#判斷登入阻擋類型)
4. [官方單一帳號救援](#官方單一帳號救援)
5. [部署正式 SSO](#部署正式-sso)
6. [受控臨時 SSO](#受控臨時-sso)
7. [新裝置與瀏覽器 profile](#新裝置與瀏覽器-profile)
8. [測試矩陣](#測試矩陣)
9. [回滾與維運](#回滾與維運)
10. [官方資料](#官方資料)

## 正式企業 SSO 是什麼

SSO（Single Sign-On）讓公司自己的 Identity Provider（IdP）負責驗證身份，Google 則是 Service Provider（SP）。使用者輸入公司郵件後，Google 把登入導向 IdP；IdP 完成密碼、MFA 或 passkey 驗證後，以簽名的 SAML assertion 或 OIDC token 告訴 Google「這個人是誰」，Google 再建立自己的 session。

```text
裝置／瀏覽器 → Google（SP）→ 公司 IdP → 簽名的 SAML／OIDC 回應 → Google session
```

「正式」代表 IdP 不是臨時 tunnel 或一次性腳本，而是有：

- 穩定 HTTPS 網域與高可用服務
- 使用者生命週期與停權同步
- MFA／passkey、安全政策與稽核日誌
- SAML／OIDC 金鑰和憑證輪替
- 監控、備份、擁有者和故障處理
- 獨立 break-glass 超級管理員
- pilot、分批 rollout 和可驗證回滾

SSO 不會把舊裝置的 Cookie 複製到新裝置，也不等於永久取消 Google 所有風險檢查。

## 選擇登入策略

| 策略 | 使用情況 | 限制 |
|---|---|---|
| `native` | 少量帳號、Google 原生密碼和 challenge 可接受 | Login Challenge 的 10 分鐘關閉是逐一使用者；Employee ID 不保證顯示 |
| `permanent-sso` | 多裝置、持續新增帳號、已有或願意維運正式 IdP | 需要 IdP、MFA、憑證輪替、稽核和 break-glass 設計 |
| `temporary-sso` | 只為一批受控帳號建立一次本機 session，且使用者明確批准例外流程 | 高風險、必須短期、專用 OU、一次性授權和完整 teardown；不是 Google 官方救援功能 |

選 IdP：

- 已使用 Microsoft Entra：優先評估 Google 預先設定的 Entra OIDC profile。
- 已使用 Okta、JumpCloud 或其他企業 IdP：使用該供應商官方 Google Workspace 整合。
- 有自架維運與資安能力：可評估 Keycloak 等 SAML／OIDC IdP。
- 完全沒有 IdP，只想處理一次登入：不要為了繞過 challenge 倉促建立永久 SSO；先用官方單一救援或受控臨時流程。

不要替使用者默選會產生成本或長期維運責任的 IdP。先說明選項並取得決定。

## 判斷登入阻擋類型

記錄不含秘密的畫面文字、Google／IdP 網域、帳號與時間：

1. **密碼錯誤**：Google 明確回報密碼錯誤。
2. **Login Challenge**：密碼通過後要求手機、Employee ID、已登入裝置、QR 或復原資訊。
3. **2-Step Verification**：組織要求的第二步；使用備用碼、安全金鑰或管理員復原流程。
4. **Too many failed attempts**：停止反覆提交，只保留一個 pilot，等待風險狀態冷卻再測。
5. **首次登入**：身份確認、服務條款或授權頁可能在其他分頁；完成後回到目標服務。
6. **SSO 錯誤**：核對 ACS、Entity ID、NameID、簽章、憑證時間、OU 指派與 IdP 允許名單。
7. **帳號選擇器**：已登入其他帳號不代表目標帳號成功；核對右上角主身份。

## 官方單一帳號救援

Login Challenge 阻擋一個使用者時：

1. 開啟 Admin Console 的 `Directory > Users`。
2. 選取目標非管理員使用者。
3. 進入 `Security > Login challenge`。
4. 選擇 `Turn Off For 10 Minutes`。
5. 等數分鐘生效，只測這一個 pilot。
6. 在 10 分鐘內登入並核對目標服務。
7. 成功後加入適當復原方式／passkey／安全金鑰。

這是單一使用者、臨時 10 分鐘的救援。Google 明確說明：若阻擋原因是 Login Challenge，只重設密碼不足以恢復登入。

Employee ID 可由 CSV、Directory API 或目錄同步批量填入，但 Google 依風險選擇實際 challenge。啟用 SSO 或 2SV 時不會顯示 Employee ID challenge。

## 部署正式 SSO

### A. 變更前

1. 建立至少兩個 break-glass 超級管理員，使用強 MFA／安全金鑰，放在獨立 OU。
2. 確認 break-glass OU 的 SSO 指派為 `None`；實際測試 Google 原生登入。
3. 建立專用 pilot OU，只放一個非管理員。
4. 導出目前 OU 成員、SSO 指派和 post-SSO verification，保存不含秘密的回滾基線。
5. 指定 IdP 擁有者、變更窗口、停止條件和回滾人員。

### B. 建立 SAML profile

若選 SAML：

1. 在 Admin Console 前往 `Security > Authentication > SSO with third party IdP`。
2. 選擇 `Add SAML profile`，輸入不含秘密的 profile 名稱。
3. 從 IdP 取得 Entity ID、HTTPS Sign-in URL、Sign-out URL、Change password URL 和 X.509 公開憑證。
4. 上傳公開憑證並儲存。絕不把 IdP 私鑰上傳到 Google、Git 或 skill。
5. 從 Google 的 SP Details 複製該 profile 專用的 ACS URL 和 Entity ID。
6. 回到 IdP 建立 Google 應用，填入 ACS／Entity ID，把 NameID／subject 精確映射為 Google 使用者的 primary email。
7. 要求 IdP 簽名回應或 assertion，檢查 audience、recipient、時間窗與時鐘同步。

若選 OIDC：使用 Google 的自訂 OIDC profile 或預先設定 Entra OIDC profile；從 IdP 取得 issuer、client ID 和 client secret。把 client secret 放在 IdP／Google 的安全設定中，不寫入任何本機文件或回覆。

### C. 指派與 post-SSO verification

1. 開啟 `Manage SSO profile assignments`。
2. 只對 pilot OU／群組選擇 `Another SSO profile`；不要指派根 OU。
3. 選擇使用者直接前往 Google 服務時的行為：輸入 Google username 後導向 IdP，或仍要求 Google 密碼。記錄選擇。
4. 到 `Security > Authentication > Login challenges > Post-SSO verification` 讀取 pilot OU 的目前值。
5. 現代 SSO profile 預設會套用額外 Login Challenge 與 2SV。只有使用者明確批准、pilot OU 受控且回滾就緒時才調整；不要對整個組織一律關閉。

### D. Pilot 測試

依序測試：

1. SP-initiated：從 Google Maps／Drive 等服務輸入 pilot 郵件，確認導向正確 IdP。
2. IdP-initiated：從 IdP 應用啟動 Google（若供應商支援）。
3. NameID：登入後右上角必須是 pilot primary email。
4. 新 profile：全新瀏覽器 profile 可以完成登入。
5. 重開：關閉整個瀏覽器，重開相同 profile 後 session 仍存在。
6. 登出：Google 與 IdP 的登出行為符合設計。
7. 停權：在 IdP 停權測試帳號後不能重新取得 Google session。
8. IdP 故障：break-glass 管理員仍可使用 Google 原生登入。

### E. 分批 rollout

pilot 全部通過後，按 OU／群組分批指派。Google 的現代 SSO profile 可指派 OU 或群組，不能逐一使用者指派。每批完成都重新測試一個舊使用者、一個新使用者和 break-glass 管理員。

## 受控臨時 SSO

只有使用者明確要求並批准外部登入路由變更時執行。不得把它稱為 Google 官方救援方式。

必要條件：

- 專用非管理員 OU 和硬性帳號允許名單
- 全新短期 HTTPS IdP 端點
- 專用 SAML 簽章私鑰，私鑰只存在受限本機／祕密管理器
- 短時效 assertion、一次性授權、禁止重放、預設失敗關閉
- IdP 不收集、不記錄、不轉送 Google 密碼
- pilot、並行度 1、明確結束時間和 teardown 清單

流程：

1. 保存 SSO 指派與 post-SSO verification 基線。
2. 建立臨時 SAML profile，只指派 pilot OU。
3. 為 pilot 發放一次性 grant；完成首次登入、身份確認、條款和目標服務驗證。
4. 逐一處理 manifest；每個帳號使用獨立 grant。
5. 身份錯配、允許名單外登入、assertion 重放或管理員被導向 IdP 時立即停止並回滾。
6. 全部完成後執行「回滾與維運」中的臨時 teardown。

## 新裝置與瀏覽器 profile

Google 把每個裝置、瀏覽器、App、無痕視窗或重新驗證視為不同 session。已保存的 Chrome profile 只對該電腦的 user-data 目錄有效。

每個帳號使用獨立持久化 profile：

1. 啟動目標 profile，開啟指定 Google 服務。
2. 核對右上角主帳號，不只看帳號選擇器。
3. 處理身份確認、條款與授權分頁。
4. 關閉整個瀏覽器，再用相同 profile 重開。
5. 只保存 profile 路徑、帳號和驗證時間；不要讀取或複製 Cookie 資料庫。

換設備時仍要建立新 session；正式 SSO讓流程一致，但不會搬移舊 Cookie。

## 測試矩陣

| 測試 | 必須結果 |
|---|---|
| pilot Google 服務啟動 | 導向正確 IdP／原生流程，登入正確帳號 |
| 新瀏覽器 profile | 可完成身份驗證 |
| 關閉重開相同 profile | session 仍有效或按組織政策重新驗證 |
| 允許名單外帳號 | 臨時 IdP 必須拒絕 |
| assertion 重放 | 必須拒絕 |
| IdP 停權 | 不能建立新 Google session |
| break-glass 管理員 | 始終可使用 Google 原生登入 |
| 回滾 | pilot OU 恢復原 SSO 指派和驗證政策 |

## 回滾與維運

永久 SSO：

- 設定 MFA、稽核、告警、停權同步和 session 政策。
- 上傳第二張公開憑證進行輪替；Google 建議至少在到期前 24 小時開始。
- 每季實測 break-glass 登入和 IdP 故障流程。
- IdP 或 OU 變更先進 pilot，再分批 rollout。

臨時 SSO teardown：

1. 將目標 OU／群組的 SSO 指派恢復原值或 `None`。
2. 恢復 post-SSO verification 原值。
3. 停止 tunnel、reverse proxy 和 IdP 程序，確認沒有孤兒程序。
4. 移除臨時 hosts／DNS／本機轉送。
5. 刪除短期私鑰、runtime token／URL 和一次性授權。
6. 刪除臨時 SSO profile；若因稽核保留，必須未指派、端點不可用且私鑰已銷毀。
7. 唯讀核對員工 OU、break-glass OU 和目標本機 profiles。

## 官方資料

- [Google：設定 SSO](https://knowledge.workspace.google.com/admin/apps/setting-up-sso)
- [Google：SSO 可選設定、post-SSO verification 與憑證輪替](https://knowledge.workspace.google.com/admin/apps/optional-sso-settings-and-maintenance)
- [Google：Login Challenge 與登入故障](https://knowledge.workspace.google.com/admin/support/troubleshooting/troubleshoot-login-challenges-2-step-verification-and-sign-in-issues)
- [Google：Employee ID Login Challenge](https://knowledge.workspace.google.com/admin/security/add-employee-id-as-a-login-challenge)
- [Google：裝置與 sessions](https://support.google.com/accounts/answer/3067630)
