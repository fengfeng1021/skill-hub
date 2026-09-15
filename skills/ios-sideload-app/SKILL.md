---
name: ios-sideload-app
description: 把 iPhone/iPad App 打包成可自簽側載安裝的 IPA，並確保 WidgetKit 桌面小工具真的會出現在小工具庫、主程式與小工具能共享資料、外觀使用 iOS 26 原生液態玻璃。當任務涉及 iOS App 打包、GitHub Actions 建置 IPA、SideStore/AltStore 側載安裝、小工具不出現在小工具庫、App Group 共享資料、Swift Playgrounds 專案要出 IPA、或液態玻璃外觀不一致時使用。內含七條硬性規則、發佈前檢查清單、症狀對照表與 IPA 體檢工具。
---

# iPhone App 打包出貨

一份「從沒有 Mac 到手機上能跑」的實戰規則集。

每一條規則都對應一個真實踩過的坑：**看起來全部正常、卻什麼都不會動，而且沒有任何錯誤訊息**。
先讀完七條鐵則再動手，可以省下好幾輪「改了又沒用」的來回。

---

## 什麼時候用

- 要把 Swift Playgrounds（`.swiftpm`）或原生 Xcode 專案做成可側載的 IPA
- 要在沒有 Mac 的環境下用 GitHub Actions 出 IPA
- 小工具「裝了卻在小工具庫找不到」
- 主程式改了資料，小工具還顯示舊的
- 同樣的程式碼在 Swift Playgrounds 很漂亮，裝成 IPA 就「少一味」

## 七條鐵則

> 這七條是整個流程唯一不能出錯的地方。**先逐條核對，再開始寫程式或除錯。**

### 鐵則 1：小工具擴展一定要用**真正的 Xcode app-extension target** 建置

不要用 `swiftc` 把 `WidgetExtension/*.swift` 編成執行檔、再手工塞進 `PlugIns/`。

手工組裝的 `.appex` 會缺少 Xcode 才會產生的 **App Intents 中介資料**
（`Metadata.appintents/extract.actionsdata` 與 `version.json`）。
iOS 26 的 WidgetKit 在列舉擴展能力時會讀這份資料 ——
缺了它的症狀是「檔案都在、簽章也對、Mach-O 完全正常，但小工具庫就是找不到，且沒有任何錯誤」。

做法：用 **XcodeGen**（`project.yml`）產生一個只包含擴展 target 的 Xcode 專案來編譯。
詳見 `references/widget-extension.md`。

### 鐵則 2：擴展點只宣告 `NSExtension`

```xml
<key>NSExtension</key>
<dict>
    <key>NSExtensionPointIdentifier</key>
    <string>com.apple.widgetkit-extension</string>
</dict>
```

**不要**再加 `EXAppExtensionAttributes`。那是 ExtensionKit 擴展點的路徑，
iOS 的 WidgetKit 屬於傳統 NSExtension（`com.apple.widgetkit-extension`），
兩者混用會讓系統走錯註冊路徑。也不要加 `NSExtensionPrincipalClass`。

### 鐵則 3：App 與擴展都要宣告**同一個 App Group**，而且執行期要讀 `ALTAppGroups`

1. `App.entitlements` 與擴展的 `.entitlements` 都要有
   `com.apple.security.application-groups`，值為同一個 group id。
   沒有它，側載工具會直接跳過 App Group 指派，而且不會報錯。
2. 側載工具簽名前會把 group 改寫成 `group.<原始 id>.<TeamID>`，
   並把「真正可用的清單」寫進每個 bundle 的 Info.plist 的 **`ALTAppGroups`** 鍵。
   **執行期一定要先讀這個鍵，不能寫死 group id。**

順帶兩個必需的小細節：
- 判斷授權不能用 `UserDefaults(suiteName:) != nil`（沒授權也會回傳物件），
  要用 `FileManager.containerURL(forSecurityApplicationGroupIdentifier:) != nil`
- **只探測簽章實際授權的 group**：對未授權的 group 呼叫 `containerURL` 會被
  `containermanagerd` 拒絕，在小工具程序裡甚至可能導致程序被終止，
  於是小工具永遠不會出現在小工具庫

### 鐵則 4：側載安裝時選「**Register App ID for Each Extension**」

安裝含擴展的 App 時，SideStore 會跳出「App Contains Extensions」對話框：

| 選項 | 後果 |
|---|---|
| Keep App Extensions (Use Main Profile) | ❌ 擴展沿用主程式的簽章，`application-identifier` 沒涵蓋擴展自己的 bundle ID，`installd` **拒絕註冊**這個擴展 |
| **Keep App Extensions (Register App ID for Each Extension)** | ✅ 為擴展建立專屬 App ID 與 profile，系統才會註冊 |
| Remove App Extensions | ❌ 直接刪掉擴展 |

選錯的症狀極具欺騙性：**App 完全正常、擴展檔案也在，只有小工具永遠不出現**。
判斷方法：讀擴展的 `embedded.mobileprovision`，看 `application-identifier`
是否為 `<TeamID>.<擴展自己的 bundle ID>`。

### 鐵則 5：要用 Xcode 26 / iOS 26 SDK 建置，才有液態玻璃

Liquid Glass 只在**以 iOS 26 SDK 建置**時才會被系統啟用。
用舊 SDK 建置的 App 裝在 iOS 26/27 上會被系統以「相容模式」渲染：
工具列不會有玻璃圓盤、彈窗與分頁切換器不會用新材質。

Swift Playgrounds 是用**裝置自身的 SDK** 建置，所以在那邊一定看得到新外觀 ——
這就是「同一份程式碼、兩邊不一樣」的根本原因。CI 請用 `macos-26` + Xcode 26，
並在 SDK 版本小於 26 時直接讓建置失敗。

同時：**不要用半透明純色去「模仿」玻璃**，要用系統的
`glassEffect` / `GlassEffectContainer` / `.buttonStyle(.glassProminent)`，
並用 `if #available(iOS 26.0, *)` 加 `#if compiler(>=6.2)` 雙重防護保留舊系統後備。

### 鐵則 6：動過擴展之後，要**刪除 App 再重新安裝**

側載工具在「更新」時會比對新舊版本的擴展，**自動移除新版有、但已安裝版本沒有的擴展**。
若某一版沒帶上擴展，之後每次更新都會被再刪一次，使用者會覺得「我明明每次都選保留」。

做法：
1. 到側載工具「設定 → User Customizations → GENERAL → 開啟 `Customize App Extensions`」
   （沒開啟時，更新會不詢問就刪除）
2. 刪除 App 後**重新安裝**
3. 安裝完**開啟 App 至少一次**（系統才會向 WidgetKit 註冊擴展）
4. 必要時重開機，或切換一次系統語言，強制重建小工具索引

### 鐵則 7：小工具沒出現時，**先做對照實驗再改程式**

問一句話就能定位問題在誰身上：

> 「這台裝置上，**其他側載 App** 的小工具看得到嗎？」（最快：側載工具自己的小工具）

- 看得到 → 裝置與側載機制正常，問題在你的擴展 → 往鐵則 1～4 查
- 看不到 → 平台或側載工具層級的限制，**改你的 App 也沒用**，不要繼續瞎改

## 標準流程

1. **確認目標**：iOS 最低版本、側載工具、是否需要小工具與共享資料。
2. **專案結構**：主程式保持 `.swiftpm`（可在 Swift Playgrounds 直接跑），
   另外用 `project.yml` 讓擴展以真正的 Xcode target 建置。
3. **寫 entitlements**：App 與擴展各一份，內容相同的 App Group。
4. **寫 CI**：`macos-26` → 選 Xcode 26 → 建主 App → 建擴展 → 嵌入 `PlugIns/`
   → 簽章（先擴展、後 App）→ 驗證 → 打包 IPA → 發 Release。
   **驗證是硬性關卡**：缺少 `Metadata.appintents`、缺少 App Group 授權、
   擴展 Info.plist 出現 `EXAppExtensionAttributes`，一律讓建置失敗。
5. **在 App 內建診斷面板**：顯示擴展有沒有被安裝、bundle ID、
   以及 `embedded.mobileprovision` 裡實際生效的 `application-identifier` 與 App Group，
   並提供「複製報告」按鈕。使用者不必接電腦就能回報精準資訊。
6. **交付前跑檢查清單**：`references/troubleshooting.md` 的檢查清單。
7. **交付時附上安裝說明**：明確寫出要選「Register App ID for Each Extension」，
   以及必須刪除後重新安裝。

## 小工具內容邏輯（常見的第二類 bug）

小工具「顯示早上的課／顯示上一個行程」通常**不是同步壞了**，而是挑選邏輯缺少時間判斷。

```swift
// ❌ 行程全部結束後會退回「今天最早的那一筆」，晚上 9 點顯示早上的課
let target = current ?? next?.course ?? todayList.first ?? courses.first

// ✅ 只有「正在進行」或「還有下一筆」時才以行程為主角，其餘顯示狀態
let target: Course? = current ?? next?.course     // 沒有就 nil，交給畫面顯示「今日已結束」
```

配套：小工具時間軸要在「今天已結束／今天沒有行程」時只留單一狀態，
並在**跨日零點**重新調度；今日清單則只列「還沒結束」的項目。

## 症狀對照表

| 症狀 | 最可能的原因 | 看哪一條 |
|---|---|---|
| 小工具庫完全找不到（但其他側載 App 的小工具正常） | 擴展缺 `Metadata.appintents`（手工組裝） | 鐵則 1 |
| 同上，但 `Metadata.appintents` 有 | 安裝時選了 Use Main Profile | 鐵則 4 |
| 小工具顯示範例資料、不會變 | App Group 未授權，或寫死 group id | 鐵則 3 |
| 小工具時好時壞、偶爾消失 | 更新時擴展被剔除，或程序被終止 | 鐵則 6 / 3 |
| Playgrounds 有質感、IPA 沒有 | 用舊 SDK 建置 | 鐵則 5 |
| 工具列按鈕變成雙層外框 | 手動套了舊版的 `.bordered` 與自畫外框 | 鐵則 5 |
| 小工具顯示已結束的行程 | 挑選邏輯缺少時間判斷 | 上面的「小工具內容邏輯」 |
| 小工具庫搜尋不到中文名 | 主 App 缺 `CFBundleDisplayName` | `references/troubleshooting.md` |
| 側載後 App 開不起來、擴展驗證失敗 | 擴展沒有可用的 provisioning profile | 鐵則 4 |

## 參考檔案

| 檔案 | 什麼時候讀 |
|---|---|
| `references/build-pipeline.md` | 要寫 GitHub Actions、`project.yml`、entitlements、簽章流程與 CI 驗證關卡 |
| `references/widget-extension.md` | 要建立或修擴展的 target、Info.plist、時間軸與內容邏輯 |
| `references/sideload-and-sharing.md` | 要處理側載安裝、App Group 共享、`ALTAppGroups`、更新被剔除的問題 |
| `references/native-look.md` | 要處理液態玻璃、ProMotion、SDK 版本造成的外觀落差 |
| `references/dual-track-build.md` | 要同時保留「Swift Playgrounds 可直接跑」與「CI 出 IPA」兩條路 |
| `references/troubleshooting.md` | 出問題要查表、要寫 App 內診斷面板、要跑交付前檢查清單 |
| `scripts/inspect_ipa.py` | 任何時候：一鍵體檢 IPA 的擴展、簽章與中介資料（純 Python，不需 Xcode） |
