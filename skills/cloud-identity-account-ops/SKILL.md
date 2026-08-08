---
name: cloud-identity-account-ops
description: 批量建立與管理 Google Cloud Identity 租戶 example.com 的員工帳號 — 批量建帳號（a01-a50 命名體系）、批量改密碼（Directory API）、關閉登入時變更密碼。適用於「建立 N 個帳號」「新增員工 mail」「把所有帳號密碼改成 X」「重設密碼」等需求。
---

# Cloud Identity (example.com) 帳號批量操作

## 觸發情境
- 「建立/新增 N 個帳號」「新增員工 mail」「新增到上限為止」
- 「把帳號密碼改成 X」「重設密碼」
- 關閉/開啟「要求登入時變更密碼」

## ⛔ 安全規則（違反會出大事！）
1. **絕對不要修改管理員帳號**（任何租戶的管理員：不改密碼、不重設、不刪除）。管理員密碼由用戶自己管理。批量操作前先確認「使用者清單」中哪個是管理員（通常是列表中的第一個或帳號尾碼不同），操作時只針對員工帳號。
   - 過往教訓：批量重設時誤點到管理員行，導致管理員密碼被改為隨機值，需走 Google 帳戶救援流程才能恢復（且救援流程強制新密碼含符號）。
2. **員工密碼固定為 `REDACTED_SECRET`**（除非用戶明確要求其他值）。建帳號後一律用流程 B 統一設定，並關閉「要求登入時變更密碼」。

## 每次操作前必須確認的參數（不要假設上次的值！）
用戶會更換管理員帳號、網域、密碼。開始前先確認（或用對話紀錄中的最新值）：
1. **管理員帳號**（如 admin-user@example.com）
2. **管理員密碼**（如 REDACTED_SECRET）
3. **員工帳號網域**（如 example.com）
4. **命名規則**（如 a01-a50 每 50 換字母；或不指定用預設）
5. **員工顯示名**（中性英文名 or 其他）
6. **員工密碼**（如 REDACTED_SECRET）
7. **數量 / 上限**（Cloud Identity Free 上限 51 人含管理員）

上次使用環境（僅供參考，勿直接套用）：管理員 admin-user@example.com / REDACTED_SECRET；網域 example.com；員工密碼 REDACTED_SECRET。

## 環境與前置
- 本機 Chrome 啟動指令（CDP）：
  `"/c/Program Files/Google/Chrome/Application/chrome.exe" --remote-debugging-port=9222 --user-data-dir="D:\hermes-cdp-profile" --no-first-run --no-default-browser-check --disable-gpu --start-maximized`
  **必須加 `--disable-gpu`**（本機 ASTER 多工作站軟體與 Chrome GPU 加速衝突會黑屏/輸入事件失效）。
- Admin Console 使用者清單 URL：`https://admin.google.com/u/1/ac/users`（登入後會重定向到 /u/0/）
- 命名慣例預設：a01-a50、b01-b50（每 50 個換字母）；顯示名用不重複的中性英文名（`scripts/gen_names.py` 生成）

## 流程 A：批量建帳號（UI 混合流程）
**特性：必須「Hermes browser_click 開表單 + Python CDP 填表」混合**（「新增使用者」按鈕只有 Hermes 能點到，CDP 找不到）。

1. 確認 Chrome 運行 + 已登入（導航 /ac/users 能顯示清單；若跳登入頁，用 REDACTED_SECRET 登入）
2. 用 Hermes `browser_navigate` 到 `https://admin.google.com/u/1/ac/users`（完整載入，勿用 JS location.href 導航 — 會污染 Angular 狀態）
3. 等 5 秒，`browser_click` 點「新增使用者」→ 驗證 URL 變 `/ac/user/bulkadd`（否則重試）
4. 跑 `scripts/make_batch.py <起始index>`（如 `python scripts/make_batch.py 0`）：自動加行到 10 → 填名/姓/郵件 → 點繼續 → 等建立 → 關閉。帳號會自動生成密碼（後續用流程 B 統一改）
5. 每批完成後重新導航回 /ac/users，重複直到數量達標或出現「已達上限」對話框
6. **注意**：達到 51 人上限時 Google 會彈「新使用者沒有可用的授權」對話框 — 即為上限，停止

## 流程 B：批量改密碼（Directory API — 唯一可靠批量方式）
**UI 沒有批量重設密碼功能**（「更多選項」只有刪除）。用 API：

1. **取得 OAuth token**（OAuth Playground，Google 官方 public client）：
   - 導航 `https://developers.google.com/oauthplayground/`
   - 在 scopes 輸入框填 `https://www.googleapis.com/auth/admin.directory.user`，點 Authorize APIs
   - 選管理員帳號 → 同意（「繼續」）→ Exchange authorization code for tokens
   - token 在 `document.getElementById('access_token_field').value`（CDP 讀取）
2. 跑 `scripts/batch_password_api.py`：對每個帳號 PUT `https://admin.googleapis.com/admin/directory/v1/users/{email}`，body `{"password": "REDACTED_SECRET", "changePasswordAtNextLogin": false}`
   - `changePasswordAtNextLogin: false` = 關閉「要求登入時變更密碼」（用戶要求）
   - HTTP 200 = 成功；400「Reused Password Not Allowed」= 密碼已是目標值（也算成功）
3. 帳號清單預設 a01-a50；可改腳本內 users 產生式

## 驗證
- 建帳號：導航 /ac/users 確認帳號出現在清單（每頁 20 個，需翻頁）
- 改密碼：API 回應 200；或登出後用新密碼實際登入一次

## 踩坑清單（必讀！）
1. **Chrome 黑屏/輸入失效**：ASTER 環境 + Chrome GPU 加速 → 視窗黑屏、CDP 輸入事件被吞（點擊無效但 DOM 正常）。解法：`--disable-gpu` 啟動；若已發生，重啟 Chrome。另外 Windows 電源計劃「關閉顯示器」計時器也會造成閒置黑屏（powercfg /change monitor-timeout-ac/dc 0）
2. **admin console 是 Angular SPA**：
   - 「新增使用者」「重設密碼」等按鈕需真實滑鼠事件（Hermes browser_click 或 CDP Input.dispatchMouseEvent 帶 hover）；JS `.click()` 對部分按鈕無效
   - **JS `location.href` 導航會污染 Angular** → 後續按鈕全失效；用 Hermes browser_navigate 完整載入
   - 每行操作按鈕（重設密碼）在「勾選模式」下隱藏；行尾按鈕 hover 才渲染（CDP 點擊前先 mouseMoved 到行）
3. **郵件欄位只填 local part**（a01），網域自動帶 @example.com；填完整格式會變 a01@example.com@example.com 報錯
4. **名字/姓氏欄位**：中文（CJK）經 insertText 輸入 Angular 收不到（IME 繞過）→ 用 ASCII（英文名）
5. **CDP 開的彈窗 vs Hermes 開的彈窗**：Hermes browser_click 開的重設密碼彈窗，其密碼框主 frame 可訪問；CDP 點擊開的彈窗內容不可訪問 → 開彈窗用 Hermes、填彈窗用 CDP
6. **eval_js 的 expression 必須 IIFE 包裝** `(function(){...})()`，裸 `var x; return x;` 是 SyntaxError 返回 None
7. **session 過期症狀**：點擊全部無效（Hermes 回報成功但頁面不動）→ 檢查是否跳登入頁；重新登入即可。管理員密碼錯誤時用「帳戶救援」流程（輸入最後記得的密碼可過）
8. **重設密碼彈窗的 checkbox**「要求使用者在登入時變更密碼」是 Material 自訂元素（非 input[type=checkbox]），JS 找不到；用 API 的 changePasswordAtNextLogin 控制最可靠
9. **Google 密碼規則**（myaccount 變更）：無符號短密碼被拒（強度弱）；近期用過的密碼不能重複用 → 變更時需全新密碼
10. **分頁**：清單每頁 20 行；「前往下一頁」按鈕在底部（aria-label=前往下一頁，CDP 可點）

## 腳本
- `scripts/gen_names.py [輸出路徑] [前綴] [起始號] [數量]` — 生成帳號名單（中性英文名不重複），例：`python gen_names.py names.json a 1 50`
- `scripts/make_batch.py <起始index> [names.json路徑]` — 建帳號批次（需 Hermes 先開表單；每批 10 個）
- `scripts/batch_password_api.py [網域] [密碼] [數量] [起始號]` — Directory API 批量改密碼 + 關閉變更要求（需 OAuth token），例：`python batch_password_api.py example.com REDACTED_SECRET 50 1`

## 常用參數
- 員工密碼：**固定 REDACTED_SECRET**（用戶明確指定，除非用戶要求更改）
- 管理員帳號/密碼：**由用戶自行管理，不碰**
- 顯示名：中性英文名（first + last，如 Alex Chen）
- Cloud Identity Free 上限 51 人（含管理員）；超過需申請提高（cloud_id_increase 表單 2026 年失效，會重定向到支援頁）
