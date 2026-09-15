# 小工具擴展：target、Info.plist、內容邏輯

---

## 1. 為什麼一定要用真正的 Xcode target

Xcode 建置 app-extension target 時，除了編譯執行檔，還會產生一批
**只有 Xcode 會產生的東西**：

| 產物 | 用途 | 手工 `swiftc` 會有嗎 |
|---|---|---|
| `Metadata.appintents/extract.actionsdata` | App Intents 靜態抽取結果。**iOS 26 的 WidgetKit 列舉擴展能力時會讀** | ❌ |
| `Metadata.appintents/version.json` | 中介資料版本 | ❌ |
| `Assets.car` | 擴展自己的資源（`WidgetBackground` / `AccentColor`） | ❌ |
| Info.plist 的 `DT*` 平台鍵 | LaunchServices / PlugInKit 的 SDK 資訊 | 要自己補 |
| `PkgInfo`（`XPC!`） | bundle 型別 | 要自己補 |

缺 `Metadata.appintents` 的症狀特別惡劣：**擴展檔案在、簽章正確、Mach-O 完全正常、
沒有任何錯誤訊息，小工具就是不出現在小工具庫。**

驗證（把已知可正常運作的樣本當對照組）：

```bash
unzip -l App.ipa | grep -E "appex|Metadata.appintents"
# 對照組（可正常側載的小工具）都含：Metadata.appintents/* + Assets.car + PkgInfo
python scripts/inspect_ipa.py App.ipa        # 一鍵體檢
```

---

## 2. Info.plist（擴展）

```xml
<key>CFBundleDevelopmentRegion</key><string>zh_TW</string>
<key>CFBundleDisplayName</key><string>顯示名稱</string>
<key>CFBundleExecutable</key><string>AppWidget</string>
<key>CFBundleIdentifier</key><string>com.example.app.widget</string>
<key>CFBundleInfoDictionaryVersion</key><string>6.0</string>
<key>CFBundleName</key><string>AppWidget</string>
<key>CFBundlePackageType</key><string>XPC!</string>
<key>CFBundleShortVersionString</key><string>1.0.0</string>
<key>CFBundleVersion</key><string>1</string>
<key>CFBundleSupportedPlatforms</key><array><string>iPhoneOS</string></array>
<key>MinimumOSVersion</key><string>16.0</string>
<key>UIDeviceFamily</key><array><integer>1</integer><integer>2</integer></array>
<key>UIRequiredDeviceCapabilities</key><array><string>arm64</string></array>
<key>NSExtension</key>
<dict>
    <key>NSExtensionPointIdentifier</key><string>com.apple.widgetkit-extension</string>
</dict>
```

**不要**加：

| 不要加 | 原因 |
|---|---|
| `EXAppExtensionAttributes` | 那是 ExtensionKit 擴展點（`appintents-extension`、`background-asset-downloader-extension` 等）的路徑。iOS 的 WidgetKit 是傳統 NSExtension |
| `NSExtensionPrincipalClass` | 加了會讓安裝失敗（`principal class not allowed for com.apple.widgetkit-extension`） |
| 多餘的資源檔 | 例如把主程式的 `Assets.car` 複製進擴展 —— 那不是擴展的資源 |

`DT*` 平台鍵由 Xcode 的 Info.plist 處理階段自動補。

---

## 3. 時間軸：三種狀態各自該做什麼

```swift
public func getTimeline(in context: Context, completion: @escaping (Timeline<Entry>) -> Void) {
    let data = loadData()
    let now = Date()
    let today = ScheduleCalculator.todayCourses(in: data.courses, at: now)

    let hasCurrent = ScheduleCalculator.currentCourse(in: data.courses, at: now) != nil
    let hasNext = ScheduleCalculator.nextCourse(in: data.courses, at: now) != nil

    // 今天沒有行程，或今天行程已全部結束：
    // 只留單一狀態，跨日零點再重新調度（省電、也避免無意義喚醒）
    if today.isEmpty || (!hasCurrent && !hasNext) {
        completion(Timeline(entries: [makeEntry(at: now, ...)],
                            policy: .after(ScheduleCalculator.startOfNextDay(after: now))))
        return
    }

    // 今天還有行程：預排每分鐘一格，讓進度條精確到分
    var entries: [Entry] = []
    for offset in 0..<30 {
        if let date = Calendar.current.date(byAdding: .minute, value: offset, to: now) {
            entries.append(makeEntry(at: date, ...))
        }
    }
    let reload = Calendar.current.date(byAdding: .minute, value: 30, to: now) ?? now.addingTimeInterval(1800)
    completion(Timeline(entries: entries, policy: .after(reload)))
}
```

### 預覽快照要用範例資料

```swift
public func getSnapshot(in context: Context, completion: @escaping (Entry) -> Void) {
    // Apple 官方文件明確要求：小工具庫的預覽要用範例資料、要快。
    // 若預覽階段去讀共享容器而失敗，WidgetKit 可能因此拿不到 descriptor，
    // 小工具就不會出現在小工具庫。
    if context.isPreview {
        completion(makeEntry(at: Date(), courses: WidgetSampleData.fallback, settings: .init()))
        return
    }
    let data = loadData()
    completion(makeEntry(at: Date(), courses: data.courses, settings: data.settings))
}
```

`placeholder(in:)` 本來就應該用範例資料。

---

## 4. 內容邏輯：不要顯示「已經結束」的行程

**最常見的第二類 bug**：小工具顯示早上的課／上一個行程，看起來像時間沒同步。

原因：挑選邏輯缺少時間判斷。

```swift
// ❌ 行程全部結束後會退回「今天最早的那一筆」
let target = current ?? next?.course ?? todayList.first ?? courses.first

// ✅ 只有「正在進行」或「還有下一筆」時才以行程為主角
let target: Course? = current ?? next?.course     // 其餘為 nil，交給畫面顯示狀態
```

顯示層要能分辨狀態：

```swift
public var isTodayFinished: Bool {
    !todayCourses.isEmpty && currentCourse == nil && nextCourse == nil
}

/// 今日還沒結束的行程，用來顯示「還剩幾筆」
public var remainingTodayCourses: [Course] {
    let now = TimeOfDay(date: date)
    let remaining = todayCourses.filter { $0.endTime >= now }
    return remaining.isEmpty ? todayCourses : remaining
}

/// 「明天」「週三」等下一筆的時間標示
public var nextCourseDayLabel: String? {
    guard let next = nextCourseDate else { return nil }
    let cal = Calendar.current
    if cal.isDateInTomorrow(next) { return "明天" }
    let names = ["日", "一", "二", "三", "四", "五", "六"]
    return "週" + names[cal.component(.weekday, from: next) - 1]
}
```

狀態 → 畫面：

| 狀態 | 顯示 |
|---|---|
| 進行中 | 行程名稱 + 地點 + 剩餘時間 |
| 課間 | 下一筆 + 倒數 |
| **今日已結束** | ✅「今日課程已結束」+ 下一筆（例如「明天 08:10 M008」） |
| 今日無行程 | 「今日無安排」+ 下一筆 |

清單也要時間感知：只列 `endTime >= now` 的項目，標題寫「還剩 N 筆」。

---

## 5. 主程式端要做的兩件事

```swift
// 1. 每次存檔就請系統重畫小工具
WidgetCenter.shared.reloadAllTimelines()

// 2. 小工具庫的搜尋比對的是「主程式」的顯示名稱
//    Info.plist 一定要有 CFBundleDisplayName，否則搜中文名永遠找不到
```

---

## 6. 主程式 Info.plist 的關鍵鍵

| 鍵 | 值 | 為什麼 |
|---|---|---|
| `CFBundleDisplayName` | 你的 App 名稱 | 主畫面與**小工具庫搜尋**用的就是它 |
| `CADisableMinimumFrameDurationOnPhone` | `true` | iPhone ProMotion 解鎖 120Hz |
| `CADisableMinimumFrameDuration` | `true` | iPad 對應鍵 |
| `UIDesignRequiresCompatibility` | 不要存在，或 `false` | 為 `true` 會強制舊版外觀 |
| `UILaunchScreen` | 空的扁平 `<dict/>` | 巢狀會讓系統判讀錯誤 |
