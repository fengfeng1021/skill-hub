# 雙軌建置：Swift Playgrounds 與 Xcode 並存

這個檔案回答：**怎麼同時保留「在 iPad 上用 Swift Playgrounds 直接跑」與「CI 打包出含小工具的 IPA」，而且不寫兩份程式碼。**

---

## 為什麼需要雙軌

| 需求 | 用什麼 |
|---|---|
| 在 iPad 上開 Swift Playgrounds 直接跑、即時預覽 | `.swiftpm`（SwiftPM App，`AppleProductTypes`） |
| 有 WidgetKit 小工具擴展 | `Package.swift` **無法**定義 App Extension，只能用 Xcode target |

推論：

- **不要**為了小工具放棄 `.swiftpm`（使用者就沒辦法在裝置上直接跑了）
- **也不要**手工用 `swiftc` 拼 `.appex`（會缺 `Metadata.appintents`，見 `packaging-and-signing.md`）

**正解**：主 App 走 `.swiftpm`，另外用 XcodeGen 生一個**只有擴展**的 Xcode 專案，
兩邊指向同一份原始碼。

---

## 目錄配置

```
repo/
├── App.swiftpm/                    ← 主 App（Swift Playgrounds 可開）
│   ├── Package.swift
│   ├── AppInfo.plist               ← additionalInfoPlistContentFilePath
│   └── Sources/AppModule/
│       ├── App.swift
│       ├── Models/                 ← 共用模型（擴展也會編到這些）
│       │   ├── Course.swift
│       │   └── SharedAppGroup.swift
│       ├── Services/
│       └── Views/
├── App.swiftpm/WidgetExtension/    ← 擴展原始碼（不屬於 SwiftPM target）
│   ├── AppWidgetBundle.swift
│   ├── AppWidgetView.swift
│   ├── WidgetDataStorage.swift
│   ├── Info.plist
│   ├── WidgetExtension.entitlements
│   └── Assets.xcassets/
├── App.entitlements                ← 主 App 的授權
├── project.yml                     ← XcodeGen：只定義擴展 target
└── .github/workflows/build-ios.yml
```

### 關鍵觀念：`WidgetExtension/` 不在 SwiftPM 的 target 裡

```swift
// App.swiftpm/Package.swift
targets: [
    .executableTarget(name: "AppModule", path: "Sources/AppModule")   // 只有它
]
```

所以：

- 放在 `App.swiftpm/WidgetExtension/` 的檔案（含 `Assets.xcassets`）**SwiftPM 完全看不到**，
  不會產生「unhandled resource」警告，也不會被編進主 App
- Xcode 那邊用 `sources:` 把 `WidgetExtension/` 與共用的 `Models/` 一起編進擴展

---

## SwiftPM 這邊的地雷

| 地雷 | 說明 |
|---|---|
| `UILaunchScreen` 被合併成巢狀字典 | SwiftPM 產生的 plist 與 `AppInfo.plist` 合併時可能變巢狀。CI 要 `Delete` 後重新 `Add :UILaunchScreen dict` |
| 沒有 `CFBundleDisplayName` 可用 | `additionalInfoPlistContentFilePath` 可以塞，但 SwiftPM 不一定會照你想要的位置合併；CI 用 `PlistBuddy` 明確覆寫最保險 |
| 資源不能放在 target 目錄 | 想加資源（Asset Catalog 等）要放**別的目錄**，否則 SwiftPM 會抓它當 target 資源 |
| `DT*` 平台鍵 | 由 Xcode／SwiftPM 自動處理，但手工組裝擴展時要自己想辦法 |

### 版本號同步

主 App 的版本由 `Package.swift` 決定，擴展由 CI 覆寫成同一組：

```bash
VERSION=$(grep 'displayVersion:' App.swiftpm/Package.swift | head -n1 | sed -E 's/.*"([^"]+)".*/\1/')
BUILD=$(grep 'bundleVersion:'  App.swiftpm/Package.swift | head -n1 | sed -E 's/.*"([^"]+)".*/\1/')
```

**提醒**：發布後不要在同一個版本號上重複發 Release。
側載工具與系統都以版本號判斷新舊；改東西就往上跳一號。

---

## 建置順序

```
1. xcodebuild 主 App（SwiftPM scheme，derivedDataPath ./build）
2. xcodegen generate → xcodebuild 擴展（SYMROOT/OBJROOT，注意不能用 -derivedDataPath）
3. 把擴展 cp -R 進 build/Build/Products/*-iphoneos/App.app/PlugIns/
4. 先簽擴展、再簽 App
5. 逐項驗證（見 	roubleshooting.md 第 5 節）
6. zip 成 IPA
```

**順序不能顛倒**：先簽 App 的話，App 的 `CodeResources` 不會涵蓋稍後才放入的擴展。

---

## 驗收：兩軌都要能跑

| 情境 | 驗收方式 |
|---|---|
| Playgrounds | 在 iPad 上開 `.swiftpm` → 執行 → 外觀與功能正常（順帶作為外觀基準） |
| CI / 側載 | 下載 Release IPA → 安裝 → 小工具庫搜尋 → 檢查診斷面板 |

**兩軌都要記得測**。只測 Playgrounds 不會發現擴展的問題；
只測 IPA 不會發現舊工具鏈的相容性（`#if compiler` 那條路徑）壞掉。
