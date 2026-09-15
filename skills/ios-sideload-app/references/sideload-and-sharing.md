# 側載安裝與資料共享

對象是 SideStore / AltStore 這類自簽側載環境。

---

## 1. App Group 在側載後會被改寫

側載工具簽名前會：

1. 向 Apple 後台註冊 App Group，識別碼**尾端加上 Team ID**
2. 把 App ID 指派到這個群組
3. 把「真正可用的群組清單」寫進**每個 bundle**（主程式與每個擴展各自一份）
   Info.plist 的 `ALTAppGroups` 鍵

```
你寫的：            group.com.example.app
側載後真正可用的：   group.com.example.app.<TEAMID>
```

### 執行期解析器（照抄即可）

```swift
public enum SharedAppGroup {
    public static let defaultGroupID = "group.com.example.app"

    /// 側載工具注入的清單（= 簽章實際授權的群組）
    public static var declaredGroupIDs: [String] {
        var ids: [String] = []
        if let injected = Bundle.main.object(forInfoDictionaryKey: "ALTAppGroups") as? [String] {
            ids.append(contentsOf: injected)
        }
        if let declared = Bundle.main.object(forInfoDictionaryKey: "YourAppGroups") as? [String] {
            ids.append(contentsOf: declared)
        }
        var seen = Set<String>()
        return ids.filter { !$0.isEmpty && seen.insert($0).inserted }
    }

    /// 只探測「簽章授權過的」群組；完全沒有授權資訊時才退回預設值
    public static var candidates: [String] {
        let declared = declaredGroupIDs
        return declared.isEmpty ? [defaultGroupID] : declared
    }

    public static var resolvedGroupID: String? {
        candidates.first { FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: $0) != nil }
    }

    public static var containerURL: URL? {
        resolvedGroupID.flatMap { FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: $0) }
    }

    public static var sharedDefaults: UserDefaults? {
        resolvedGroupID.flatMap { UserDefaults(suiteName: $0) }
    }
}
```

### 三個必須知道的細節

1. **不能寫死 group id**，一定要讀 `ALTAppGroups`。
2. **不能用 `UserDefaults(suiteName:) != nil` 判斷授權** —— 沒授權時它照樣回傳物件，
   只是讀寫失敗。要用 `containerURL(...) != nil`。
3. **只探測簽章授權過的群組**。對未授權的 group 呼叫 `containerURL` 會被
   `containermanagerd` 拒絕（訊息類似
   `Group containers identifiers should be prefixed by requestor's team ID`），
   **在小工具程序裡這個拒絕可能直接讓程序被終止**，於是 WidgetKit 拿不到 descriptor，
   小工具就永遠不會出現在小工具庫。
   所以候選清單**不要**在授權群組後面接一個未授權的預設值當後備。

> 若要做到萬無一失，可以在解析後做一次「寫入探測」：寫一個值、立刻讀回來確認。

---

## 2. 安裝時的那個對話框（最容易踩）

App 含擴展時，SideStore 會跳出標題為 **「App Contains Extensions」** 的對話框：

| 選項 | 後果 |
|---|---|
| `Keep App Extensions (Use Main Profile)` | ❌ 擴展沿用主程式的 provisioning profile，`application-identifier` 沒涵蓋擴展自己的 bundle ID，`installd` **拒絕註冊**該擴展 |
| **`Keep App Extensions (Register App ID for Each Extension)`** | ✅ 為擴展建立專屬 App ID 與 profile |
| `Remove App Extensions` | ❌ 刪除擴展 |
| `Choose App Extensions` | 手動勾選要保留哪些 |

### 原始碼層級的證據（SideStore）

```
// FetchProvisioningProfilesOperation
guard !context.useMainProfile, !targetAppBundle.appExtensions.isEmpty else { return profiles }
// ← useMainProfile 為真時，完全不為擴展建立 App ID 與 profile

// ResignAppOperation
guard let profile = context.useMainProfile ? profiles.values.first : profiles[identifier] else { ... }
// ← 擴展因此拿到 profiles.values.first（主程式的 profile）

// SideSign 簽章時會把 profile 中「App 沒宣告」的授權整批過濾掉，
// 但 application-identifier 是例外、不會被過濾
// → 擴展被簽成主程式的 App ID
```

### 怎麼確認中了這一條

讀擴展的 `embedded.mobileprovision`，比對：

```
✅ 83RUT3JH8N.com.example.app.widget    ← <TeamID>.<擴展自己的 bundle ID>
❌ 83RUT3JH8N.com.example.app           ← 主程式的（中了 Use Main Profile）
```

**App Group 清單正確也沒用** —— 這一條壞的是擴展本身的註冊資格。

---

## 3. 更新時擴展會被剔除（而且幾乎是必然）

側載工具在安裝時會比對「新版本的擴展」與「裝置上已安裝版本的擴展」，
**只保留兩邊都有的**，多的視為 excess 直接刪除；如果是全新安裝（資料庫沒有這個 App）
則全部保留。

### 為什麼「幾乎是必然」

比對用的是**完整 bundle ID 字串相等**，但兩邊的 ID 根本不會相等：

| 來源 | 擴展 bundle ID |
|---|---|
| 下載的 IPA（側載前的原始狀態） | `com.example.app.widget` |
| 裝置上已安裝的版本 | `com.example.app.<TEAMID>.widget` |

（側載工具在簽名時會把 App 的 bundle ID 改成帶 Team ID 的版本，
擴展的 ID 也跟著被改寫，所以裝置上的那個永遠多一層 Team ID。）

判定結果：新版本的擴展在裝置上「找不到相同 ID」→ **一律視為 excess → 刪除**。
這不是偶發，是每次更新都會發生。

### 處理方式

1. **先打開開關**：側載工具「設定 → User Customizations → GENERAL →
   開啟 `Customize App Extensions`」。
   沒打開時，更新流程是「不詢問、直接刪」；打開後才會跳出對話框讓你選。
2. 安裝時選 **`Keep App Extensions (Register App ID for Each Extension)`**（就會跳過移除）。
3. 如果已經被刪掉（小工具突然消失）→ **刪除 App 後重新安裝**即可恢復。
4. 安裝完**開啟 App 至少一次**（系統才會向 WidgetKit 註冊擴展）。
5. 免費帳號的 App ID 有數量上限（例如 3 個），小工具會額外佔用 1 個；
   額度用完時擴展相關流程會失敗，可在側載工具的 App IDs / DIAGNOSTICS 頁面清理。

---

## 4. 交付給別人時要附的安裝說明

> 安裝時若跳出「App Contains Extensions」：
>
> - ✅ 選 **Keep App Extensions (Register App ID for Each Extension)**
> - ❌ 不要選 **Keep App Extensions (Use Main Profile)**
>
> 這是小工具能不能被系統註冊的關鍵。選錯的話 App 完全正常，但小工具永遠不會出現。
>
> 另外請先確認「設定 → User Customizations → `Customize App Extensions`」是開著的，
> 而且這次是**刪除後重新安裝**（不是按更新）。安裝完要開啟 App 一次。

---

## 5. 側載後才看得到的資訊

| 資訊 | 哪裡看 |
|---|---|
| 擴展的 bundle ID 與檔案 | 安裝後的 `PlugIns/*.appex`（App 內診斷或側載工具的 bundle 瀏覽器） |
| 實際生效的授權 | 各 bundle 的 `embedded.mobileprovision` → `Entitlements` |
| 實際可用的 App Group | Info.plist 的 `ALTAppGroups`（或 `SharedAppGroup.resolvedGroupID`） |

**注意**：CI 產出的原始 IPA 裡的 `embedded.mobileprovision` 是「側載前」的狀態，
`application-identifier` 可能還不存在 —— 那是正常的。
要確認鐵則 4，必須看**安裝到裝置之後**的版本。
