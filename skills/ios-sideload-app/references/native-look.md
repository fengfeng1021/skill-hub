# 原生外觀（液態玻璃 / ProMotion / SDK 版本）

---

## 1. 最常見的原因：SDK 版本，不是程式碼

**Liquid Glass 只在以 iOS 26 SDK 建置時才會被系統啟用。**
用舊 SDK 建置的 App 裝在 iOS 26/27 上，系統會以「相容模式」渲染：

| 應該有 | 相容模式下會變成 |
|---|---|
| 工具列按鈕的液態玻璃圓盤底盤 | 幾乎看不到底框、只剩圖示 |
| 浮動玻璃工具列 | 傳統不透明／模糊列 |
| 彈窗與轉場的新型材質 | 舊版外觀 |

而 **Swift Playgrounds 用裝置自身的 SDK 建置**，所以在 iPadOS 26/27 上一定是新外觀 ——
這就是「同一份程式碼、兩邊不一樣」的根本原因。**程式碼再怎麼調都追不上。**

### 驗證方式（不需要 Mac）

```bash
python scripts/inspect_ipa.py App.ipa     # 會印出主程式與擴展的 SDK 版本
```

期望 `sdk = 26.x`。若 CI 產物是 `18.5` 之類的舊版號，就是這個問題。

### 修法

CI 用 `macos-26`（內建 Xcode 26），並在 SDK 版本小於 26 時直接讓建置失敗：

```bash
SDK=$(xcrun --sdk iphoneos --show-sdk-version); echo "iOS SDK: ${SDK}"
[ "${SDK%%.*}" -ge 26 ] || { echo "::error::需要 iOS 26 以上的 SDK"; exit 1; }
```

---

## 2. 有了新 SDK 之後，要改的地方

### 2.1 移除「舊版為了畫出底盤」而加的手動樣式

用新 SDK 之後，**工具列上的按鈕系統會自己給玻璃底盤**。
這時再手動加 `.buttonStyle(.bordered)` + 自畫外框 + `.tint(.primary)`，
就會變成雙層外框或顏色不對。

```swift
// iOS 26：交給系統工具列，什麼都不加
// 舊版：才需要自己畫
@ViewBuilder
func toolbarActionStyle() -> some View {
    #if compiler(>=6.2)              // Swift 6.2 = Xcode 26
    if #available(iOS 26.0, *) {
        self
    } else {
        self.buttonStyle(.bordered).tint(.primary)
    }
    #else                             // 舊工具鏈（例如舊版 Swift Playgrounds）
    self.buttonStyle(.bordered).tint(.primary)
    #endif
}
```

> 只有 `if #available` **不夠**：沒有 `#if compiler` 的話，
> 舊工具鏈會編譯失敗（不認識 `glassEffect` 等符號），整個專案連編都編不過。

### 2.2 自製元件改用真 API，不要用純色模仿

```swift
// iOS 26
Text("標題").padding().glassEffect(.regular, in: Capsule())
GlassEffectContainer(spacing: 6) { ... }        // 多個玻璃形狀互相形變
.glassEffectID(isSelected ? id : nil, in: ns)   // 選取狀態流體移動
.buttonStyle(.glassProminent)                   // 主要動作按鈕
```

### 2.3 相容層要集中管理

把所有 `#if compiler(>=6.2)` / `if #available(iOS 26.0, *)` 收在**一個檔案**裡
（例如 `Views/LiquidGlassSupport.swift`），其餘程式碼只呼叫包好的介面。
這樣舊系統的後備實作只有一處需要維護。

---

## 3. 120Hz：只能由 Info.plist 解鎖

| 鍵 | 對象 |
|---|---|
| `CADisableMinimumFrameDurationOnPhone` = `true` | iPhone ProMotion |
| `CADisableMinimumFrameDuration` = `true` | iPad |

**常見誤解**：用 `CADisplayLink` 常駐在 main run loop 去「強迫 120Hz」。實際上：

1. 它會讓螢幕**永遠**鎖在最高刷新率，即使畫面靜止也一樣，明顯耗電
2. 它不會改變彈窗轉場與滾動的渲染管線 —— 那些本來就由系統依手勢動態調度
3. 參考裝置（Playgrounds）根本沒有這段程式碼，**加了反而更不像**

結論：只在 Info.plist 宣告，其餘交給系統。

---

## 4. 其他會造成落差的小地方

| 症狀 | 原因 |
|---|---|
| 內容被 letterbox、不是滿版 | `UILaunchScreen` 缺失或是**巢狀**字典；要扁平的 `<dict/>` |
| 一直用舊外觀 | Info.plist 有 `UIDesignRequiresCompatibility = true`，要移除或設 `false` |
| 小工具庫搜不到中文名 | 主程式缺 `CFBundleDisplayName` |
| 分頁切換器看得出是「自己畫的」 | 用純色藥丸 + 陰影模擬。新系統要用 `glassEffect` + `glassEffectID`，舊系統才走純色後備 |

---

## 5. 用 Playgrounds 當「正確外觀」的基準

因為 Playgrounds 用裝置原生 SDK，**它就是這台裝置上「正確外觀」的參考實作**：

1. 同一份原始碼在 Playgrounds 跑一次 → 截圖留存（這是目標）
2. 打包 IPA 安裝 → 逐項比對
3. 有落差就依序查三件事：**SDK 版本 → `UIDesignRequiresCompatibility` → 是不是在模仿系統材質**

這個順序比「憑感覺調參數」快得多。
