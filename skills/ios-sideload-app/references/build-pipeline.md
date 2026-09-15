# 建置流程（GitHub Actions / XcodeGen / 簽章）

---

## 1. 專案結構：雙軌建置

Swift Playgrounds 用 `.swiftpm`（`Package.swift` + `AppleProductTypes`），
但 **`Package.swift` 無法定義 App Extension**。所以：

```
專案/
├── App.swiftpm/                    ← 主程式（Swift Playgrounds 可直接開啟執行）
│   ├── Package.swift
│   └── Sources/AppModule/
├── App.swiftpm/WidgetExtension/    ← 擴展原始碼（不屬於 SwiftPM target）
├── App.entitlements                ← 主程式授權
├── WidgetExtension.entitlements    ← 擴展授權（內容與上面相同）
└── project.yml                     ← XcodeGen：只定義擴展 target
```

在 CI 裡：

1. 用 Xcode 編譯主程式（`-scheme` + `-derivedDataPath`）
2. 用 XcodeGen 產生擴展專案並編譯擴展
3. 把擴展放進主程式的 `PlugIns/`
4. 先簽擴展、再簽主程式
5. 打包 IPA

---

## 2. `project.yml`（XcodeGen）

只定義擴展。關鍵設定與理由：

```yaml
name: AppWidgetExtension

targets:
  AppWidget:
    type: app-extension                 # 不是 extensionkit-extension
    platform: iOS
    deploymentTarget: "16.0"
    sources:
      - path: App.swiftpm/WidgetExtension
        excludes:
          - "Info.plist"                # 由 INFOPLIST_FILE 指定，不要當資源複製
          - "WidgetExtension.entitlements"
      - path: App.swiftpm/Sources/AppModule/Models   # 擴展需要的共用模型
    dependencies:
      - sdk: WidgetKit.framework
      - sdk: SwiftUI.framework
      - sdk: AppIntents.framework       # ← 沒連結就不會產生 App Intents 中介資料
      - sdk: UIKit.framework
      - sdk: Foundation.framework
    settings:
      base:
        PRODUCT_NAME: AppWidget
        PRODUCT_BUNDLE_IDENTIFIER: com.example.app.widget
        INFOPLIST_FILE: App.swiftpm/WidgetExtension/Info.plist
        CODE_SIGN_ENTITLEMENTS: App.swiftpm/WidgetExtension/WidgetExtension.entitlements
        APPLICATION_EXTENSION_API_ONLY: YES
        SKIP_INSTALL: YES
        TARGETED_DEVICE_FAMILY: "1,2"
        GENERATE_INFOPLIST_FILE: NO
        ENABLE_USER_SCRIPT_SANDBOXING: NO
        ASSETCATALOG_COMPILER_GLOBAL_ACCENT_COLOR_NAME: AccentColor
        ASSETCATALOG_COMPILER_WIDGET_BACKGROUND_COLOR_NAME: WidgetBackground
        CODE_SIGNING_ALLOWED: NO
        CODE_SIGNING_REQUIRED: NO
    scheme:
      gatherCoverageData: false
```

### 一定要放一個 App Intent

Xcode 只會在 target 真的有 App Intent 時才產生 `Metadata.appintents`。
一個最小的、iOS 16 就能用的 intent（**不必**提高最低系統版本）：

```swift
import AppIntents
import WidgetKit

public struct RefreshScheduleIntent: AppIntent {
    public static var title: LocalizedStringResource = "重新整理課表小工具"
    public static var description = IntentDescription("立即重新載入時間軸。")
    public static var openAppWhenRun: Bool = false

    public init() {}

    public func perform() async throws -> some IntentResult {
        WidgetCenter.shared.reloadAllTimelines()
        return .result()
    }
}
```

### 一定要有 Asset Catalog

```
App.swiftpm/WidgetExtension/Assets.xcassets/
├── Contents.json
├── WidgetBackground.colorset/Contents.json
└── AccentColor.colorset/Contents.json
```

`Asset Catalog` 會編成 `Assets.car`。
沒有它，Xcode 會把 `NSWidgetBackgroundColorName` / `NSAccentColorName`
指向不存在的顏色。

---

## 3. entitlements

兩份檔案內容相同：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.application-groups</key>
    <array>
        <string>group.com.example.app</string>
    </array>
</dict>
</plist>
```

**不要在 entitlements 裡寫註解。** `codesign --entitlements` 會把整個 plist
內容原封不動寫進簽章的 entitlements blob，註解會一起被嵌進去（可用
`codesign -d --entitlements :-` 看到），白白變大又難讀。

---

## 4. GitHub Actions

```yaml
name: Build iOS IPA

on:
  push:
    branches: [main]

permissions:
  contents: write          # 要發 Release 才需要

jobs:
  build:
    runs-on: macos-26      # macOS 26 映像內建 Xcode 26（iOS 26 SDK）
    steps:
      - uses: actions/checkout@v4

      - name: Select Xcode 26
        run: |
          for c in Xcode_26.6 Xcode_26.5 Xcode_26.4.1 Xcode_26.4 Xcode_26.3 Xcode_26.2 Xcode_26.1.1 Xcode_26.1 Xcode_26.0.1 Xcode_26.0 Xcode; do
            if [ -d "/Applications/${c}.app" ]; then
              sudo xcode-select -s "/Applications/${c}.app/Contents/Developer"
              echo "Selected ${c}"; break
            fi
          done
          sudo xcodebuild -runFirstLaunch || true
          SDK=$(xcrun --sdk iphoneos --show-sdk-version); echo "iOS SDK: ${SDK}"
          [ "${SDK%%.*}" -ge 26 ] || { echo "::error::需要 iOS 26 以上的 SDK"; exit 1; }

      - name: Build app
        run: |
          cd App.swiftpm
          xcodebuild -scheme App -destination 'generic/platform=iOS' -configuration Release \
            -derivedDataPath ./build CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO

      - name: Build widget extension
        run: |
          brew install xcodegen
          xcodegen generate
          # 注意：-derivedDataPath 必須搭配 -scheme；
          # 用 -target 時要改用 SYMROOT／OBJROOT 指定輸出。
          xcodebuild -project AppWidgetExtension.xcodeproj -target AppWidget \
            -configuration Release -sdk iphoneos \
            SYMROOT="$PWD/widgetbuild/Products" OBJROOT="$PWD/widgetbuild/Intermediates" \
            CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO

          A=$(ls -d widgetbuild/Products/Release-iphoneos/*.appex)
          test -f "$A/Metadata.appintents/extract.actionsdata" \
            || { echo "::error::缺 App Intents 中介資料"; exit 1; }
          test -f "$A/Assets.car" || { echo "::error::缺 Assets.car"; exit 1; }

      - name: Embed and sign
        run: |
          cd App.swiftpm
          APP=$(ls -d build/Build/Products/*-iphoneos/*.app)
          A=$(ls -d ../widgetbuild/Products/Release-iphoneos/*.appex)
          NAME=$(basename "$A")

          rm -rf "$APP/PlugIns"; mkdir -p "$APP/PlugIns"; cp -R "$A" "$APP/PlugIns/"
          [ -f "$APP/PlugIns/$NAME/PkgInfo" ] || printf 'XPC!' > "$APP/PlugIns/$NAME/PkgInfo"

          # 先簽擴展，再簽主程式（主程式的 CodeResources 要涵蓋擴展）
          codesign --force --sign - --entitlements ../WidgetExtension.entitlements \
            --generate-entitlement-der "$APP/PlugIns/$NAME"
          codesign --force --sign - --entitlements ../App.entitlements \
            --generate-entitlement-der "$APP"

      - name: Verify
        run: |
          set +e
          cd App.swiftpm
          APP=$(ls -d build/Build/Products/*-iphoneos/*.app)
          A="$APP/PlugIns/$(basename $(ls -d ../widgetbuild/Products/Release-iphoneos/*.appex))"
          F=0
          check() { if [ "$1" -eq 0 ]; then echo "  OK   $2"; else echo "::error::$2"; F=1; fi; }

          test -f "$A/Metadata.appintents/extract.actionsdata"; check $? "擴展含 App Intents 中介資料"
          test -f "$A/PkgInfo";                                  check $? "擴展含 PkgInfo"
          codesign -d --entitlements :- "$A" 2>&1 | grep -q "application-groups"; check $? "擴展含 App Group 授權"
          codesign -d --entitlements :- "$APP" 2>&1 | grep -q "application-groups"; check $? "主程式含 App Group 授權"
          if plutil -p "$A/Info.plist" | grep -q EXAppExtensionAttributes; then
            check 1 "擴展不應有 EXAppExtensionAttributes"
          else
            check 0 "擴展不應有 EXAppExtensionAttributes"
          fi
          otool -l "$A/AppWidget" | grep -q LC_MAIN; check $? "擴展是執行檔（LC_MAIN）"
          exit $F

      - name: Package IPA
        run: |
          cd App.swiftpm
          mkdir -p Payload && cp -r build/Build/Products/*-iphoneos/*.app Payload/
          zip -qry App.ipa Payload
```

### 兩個踩過的坑

**坑 1：`check` 的語意**
`test -f X; check $? "..."` 裡 `$?` 是 **0 代表成功**。
第一版寫成「等於 1 才成功」，結果所有驗證都誤判失敗、產物其實完全正常 —— 白跑一輪 CI。
（正確寫法見上面 `check()` 的實作。）

**坑 2：不要手工編譯擴展**
把 `WidgetExtension/*.swift` 用 `swiftc` 編成執行檔再塞進 `PlugIns/`，
產物在檔案層看起來完全正確（Mach-O 合法、`LC_MAIN` 有、簽章也對），
但就是缺 `Metadata.appintents` —— 小工具永遠不會出現。

---

## 5. 版本號同步

主程式版本由 `Package.swift` 決定，擴展的版本要跟它一致：

```bash
VERSION=$(grep 'displayVersion:' App.swiftpm/Package.swift | head -n1 | sed -E 's/.*"([^"]+)".*/\1/')
BUILD=$(grep 'bundleVersion:'  App.swiftpm/Package.swift | head -n1 | sed -E 's/.*"([^"]+)".*/\1/')

/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $VERSION" "$A/Info.plist"
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion $BUILD"               "$A/Info.plist"
```

**注意**：主程式的 `Info.plist` 用 `PlistBuddy` 補值時，
`Set` 失敗要能 `Add` 回來；`UILaunchScreen` 要先 `Delete` 再 `Add` 成扁平的 `dict`
（SwiftPM 與 `AppInfo.plist` 合併時可能變成巢狀，導致系統判讀錯誤）。

---

## 6. `.gitignore`

```
.build/
.swiftpm/
*.xcodeproj/          # XcodeGen 的產物，由 project.yml 重建
build/
widgetbuild/
DerivedData/
xcuserdata/
```
