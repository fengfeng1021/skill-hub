# 疑難排解、App 內診斷、交付前檢查清單

---

## 1. 先做對照實驗（最省時間的一步）

> 「這台裝置上，**其他側載 App** 的小工具看得到嗎？」

最好的對照對象是**側載工具自己的小工具**（例如 SideStore 的 Widget）。

| 結果 | 結論 |
|---|---|
| 看得到 | 裝置與側載機制正常 → 問題在你的擴展 → 往第 2 節查 |
| 看不到 | 平台或側載工具層級的限制 → **改你的 App 也沒用**，先確認裝置與工具相容性 |

跳過這一步，很容易花好幾輪在「改了又沒用」上。

---

## 2. 決策樹

```
Q1. 安裝後的 App bundle 裡真的有 PlugIns/*.appex 嗎？
    ├─ 沒有 → 側載工具在簽名時剔除了它
    │          → 設定 → User Customizations → 開啟 Customize App Extensions
    │          → 刪除 App 後重新安裝（不要用更新）
    └─ 有 → Q2

Q2. 擴展的 embedded.mobileprovision 裡，application-identifier
    有沒有涵蓋擴展自己的 bundle ID？
    ├─ 沒有 → 安裝時選了 Use Main Profile
    │          → 重裝並改選 Register App ID for Each Extension
    └─ 有 → Q3

Q3. 擴展產物裡有 Metadata.appintents/ 嗎？
    ├─ 沒有 → 用 swiftc 手工組裝的
    │          → 改用 XcodeGen 產生真正的 Xcode app-extension target
    └─ 有 → Q4

Q4. App Group 授權有沒有生效？
    ├─ 沒有 → App 或擴展的 entitlements 缺 com.apple.security.application-groups
    │          → 兩份都要補，並確認執行期讀 ALTAppGroups
    └─ 有 → Q5

Q5. 使用者的操作順序對嗎？
    → 刪除後重新安裝 → 選 Register App ID → 開啟 App 一次
    → 重開機或切換一次系統語言重建索引
```

`python scripts/inspect_ipa.py App.ipa` 會把 Q1～Q4 一次印出來。

---

## 3. 症狀對照表

| 症狀 | 最可能的原因 | 對應規則 |
|---|---|---|
| 小工具庫完全找不到，其他側載 App 的小工具正常 | 擴展缺 `Metadata.appintents`（手工組裝 `.appex`） | 鐵則 1 |
| 同上，但 `Metadata.appintents` 存在 | 安裝時選了 Use Main Profile | 鐵則 4 |
| 小工具顯示範例資料、永遠不變 | App Group 未授權，或寫死 group id | 鐵則 3 |
| 小工具前幾天正常，更新後消失 | 更新時擴展被剔除 | 鐵則 6 |
| 小工具時好時壞 | 程序被終止（存取未授權的 App Group） | 鐵則 3 |
| Playgrounds 有質感、IPA 沒有 | 用舊 SDK 建置 | 鐵則 5 |
| 工具列按鈕變雙層外框 | 手動套了舊版 `.bordered` + 自畫外框 | 鐵則 5 |
| 小工具顯示已結束的行程 | 挑選邏輯缺少時間判斷 | `references/widget-extension.md` 第 4 節 |
| 小工具庫搜尋不到中文名 | 主程式缺 `CFBundleDisplayName` | `references/widget-extension.md` 第 6 節 |
| 側載後 App 開不起來 | 擴展沒有可用的 provisioning profile | 鐵則 4 |
| 內容被 letterbox | `UILaunchScreen` 巢狀 | `references/native-look.md` 第 4 節 |
| 分頁切換器像自己畫的 | 用純色模仿玻璃 | `references/native-look.md` 第 2 節 |

---

## 4. App 內診斷面板（強烈建議內建）

使用者不一定能接電腦。讓 App 讀「自己 bundle 內的實際狀態」，
產生可複製的報告，一則訊息就能定位問題。全部使用公開 API。

```swift
import Foundation

enum WidgetDiagnostics {

    // 1. App Group：授權到的實際容器
    static func groupStatus() -> String {
        SharedAppGroup.resolvedGroupID.map { "已取得授權：\($0)" }
            ?? "未授權；候選：\(SharedAppGroup.candidates.joined(separator: ", "))"
    }

    // 2. 擴展：有沒有被安裝、bundle ID、擴展點、執行檔在不在
    static func extensionProbes() -> [(folder: String, id: String, point: String, exe: Bool, profile: String?)] {
        guard let dir = Bundle.main.builtInPlugInsURL,
              let items = try? FileManager.default.contentsOfDirectory(at: dir, includingPropertiesForKeys: nil)
        else { return [] }

        return items.filter { $0.pathExtension.lowercased() == "appex" }.map { url in
            let bundle = Bundle(url: url)
            let info = bundle?.infoDictionary ?? [:]
            let executable = info["CFBundleExecutable"] as? String ?? ""
            let extensionPoint = (info["NSExtension"] as? [String: Any])?["NSExtensionPointIdentifier"] as? String
            return (url.lastPathComponent,
                    bundle?.bundleIdentifier ?? "unknown",
                    extensionPoint ?? "未宣告",
                    !executable.isEmpty
                        && FileManager.default.fileExists(atPath: url.appendingPathComponent(executable).path),
                    provisioning(at: url))
        }
    }

    // 3. 簽章：讀 bundle 內的 embedded.mobileprovision，取出實際生效的授權
    static func provisioning(at bundleURL: URL) -> String? {
        let url = bundleURL.appendingPathComponent("embedded.mobileprovision")
        guard let data = try? Data(contentsOf: url),
              let start = data.range(of: Data("<?xml".utf8)),
              let end = data.range(of: Data("</plist>".utf8), in: start.lowerBound..<data.endIndex),
              let plist = try? PropertyListSerialization.propertyList(
                  from: data.subdata(in: start.lowerBound..<end.upperBound),
                  options: [], format: nil) as? [String: Any]
        else { return nil }

        let entitlements = plist["Entitlements"] as? [String: Any] ?? [:]
        let appID = entitlements["application-identifier"] as? String ?? "未提供"
        let groups = entitlements["com.apple.security.application-groups"] as? [String] ?? []
        return "App ID = \(appID)，App Group = \(groups.isEmpty ? "無 ✗" : groups.joined(separator: ", "))"
    }

    // 4. 交叉比對：application-identifier 有沒有涵蓋擴展自己的 bundle ID
    static func covers(_ appID: String, bundleIdentifier: String) -> Bool {
        guard let dot = appID.firstIndex(of: ".") else { return false }
        let identifier = String(appID[appID.index(after: dot)...])
        if identifier == "*" { return true }
        if identifier.hasSuffix(".*") { return bundleIdentifier.hasPrefix(String(identifier.dropLast(2)) + ".") }
        return identifier == bundleIdentifier
    }

    // 5. 報告（照著印，使用者直接複製貼上）
    static func report() -> String {
        var lines: [String] = []
        lines.append("=== 小工具診斷 ===")
        lines.append("系統版本: \(ProcessInfo.processInfo.operatingSystemVersionString)")
        lines.append("App bundle ID: \(Bundle.main.bundleIdentifier ?? "?")")
        lines.append("")
        lines.append("[1] App Group 授權\n    \(groupStatus())")
        lines.append("")
        lines.append("[2] 主程式簽章\n    \(provisioning(at: Bundle.main.bundleURL) ?? "無")")
        lines.append("")
        lines.append("[3] 擴展")
        for probe in extensionProbes() {
            lines.append("    ✓ \(probe.folder)")
            lines.append("      bundle ID: \(probe.id)")
            lines.append("      擴展點: \(probe.point)")
            lines.append("      執行檔: \(probe.exe ? "存在" : "遺失")")
            lines.append("      簽章授權: \(probe.profile ?? "無")")
        }
        return lines.joined(separator: "\n")
    }
}
```

在面板上放一顆「複製報告」按鈕：

```swift
UIPasteboard.general.string = WidgetDiagnostics.report()
```

使用者的回報成本就從「描述症狀」降到「貼上一段文字」。

---

## 5. 交付前檢查清單

### A. 建置

- [ ] CI runner 是 `macos-26`，且明確選取 Xcode 26
- [ ] 有硬性檢查：iOS SDK < 26 就讓建置失敗
- [ ] 主程式沒有 `UIDesignRequiresCompatibility = true`
- [ ] 主程式的 `UILaunchScreen` 是扁平的空字典
- [ ] 主程式有 `CFBundleDisplayName`
- [ ] `CADisableMinimumFrameDurationOnPhone` / `CADisableMinimumFrameDuration` = `true`
- [ ] 沒有常駐 `CADisplayLink` 之類「強迫刷新率」的程式碼

### B. 擴展

- [ ] 由 `project.yml` 產生的 Xcode app-extension target 建置（不是 `swiftc`）
- [ ] target 有放至少一個 `AppIntent`（否則不會產生中介資料）
- [ ] 連結 `WidgetKit` / `SwiftUI` / `AppIntents`
- [ ] 有 `Assets.xcassets`（含 `WidgetBackground`、`AccentColor`）

### C. 產物（用 `scripts/inspect_ipa.py` 核對）

- [ ] `Metadata.appintents/extract.actionsdata` 存在
- [ ] `Metadata.appintents/version.json` 存在
- [ ] `Assets.car` 存在
- [ ] `PkgInfo` 存在且內容 `XPC!`
- [ ] `CFBundlePackageType = XPC!`
- [ ] `NSExtensionPointIdentifier = com.apple.widgetkit-extension`
- [ ] **沒有** `EXAppExtensionAttributes`、**沒有** `NSExtensionPrincipalClass`
- [ ] `DT*` / `DTSDKName` 是 26.x
- [ ] Mach-O：`LC_MAIN` 存在、`platform=iOS`、`sdk=26.x`
- [ ] 擴展版本與主程式一致

### D. 簽章與授權

- [ ] `App.entitlements` 與擴展的 `.entitlements` 有同一個 App Group
- [ ] 兩者的簽章 entitlements 都真的含 App Group（`codesign -d --entitlements :-`）
- [ ] 簽章順序：先擴展、後主程式
- [ ] entitlements 檔內沒有註解

### E. 執行期

- [ ] 共享容器用 `ALTAppGroups` 解析，沒有寫死
- [ ] 候選清單只含簽章授權過的群組
- [ ] 用 `containerURL(...) != nil` 判斷授權
- [ ] 小工具庫預覽（`context.isPreview`）用範例資料
- [ ] 每次存檔呼叫 `WidgetCenter.shared.reloadAllTimelines()`
- [ ] 行程全部結束後不會顯示「今天最早那一筆」，有「今日已結束」狀態

### F. CI 驗證關卡

- [ ] 缺 `Metadata.appintents` → 建置失敗
- [ ] 缺 `Assets.car` → 建置失敗
- [ ] 擴展簽章缺 App Group → 建置失敗
- [ ] 擴展 Info.plist 出現 `EXAppExtensionAttributes` → 建置失敗
- [ ] 擴展執行檔缺 `LC_MAIN` → 建置失敗
- [ ] 打包後 `unzip -l` 確認 `PlugIns/*.appex` 在 IPA 裡

> `check` 函式的語意：`test -f X; check $? "..."` 中 **`$?` = 0 代表成功**。
> 寫成「等於 1 才成功」會讓所有驗證反向誤判、產物正常卻中止打包。

### G. 實機驗收

- [ ] 先做對照：這台裝置上側載工具自己的小工具看得到嗎？
- [ ] 側載工具已開啟 `Customize App Extensions`
- [ ] 刪除 App 後重新安裝（不是更新）
- [ ] 安裝對話框選 **Register App ID for Each Extension**
- [ ] 安裝完開啟 App 至少一次
- [ ] 重開機或切換一次系統語言
- [ ] 小工具庫搜尋**顯示名稱**（不是英文 bundle 名）
- [ ] 小工具顯示的資料與 App 內一致
- [ ] 隔一段時間回看，內容有跟著時間變

### H. 交付文件

- [ ] Release notes 寫明「安裝要選哪個選項、要刪除後重裝」
- [ ] 版本號有往上跳（不要同號重發）
- [ ] 側載來源（如 `apps.json`）的 `version` / `downloadURL` 已同步
