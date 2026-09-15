# iPhone App 打包出貨

把 iPhone/iPad App 打包成可側載安裝的 IPA，並確保 **WidgetKit 桌面小工具真的會出現在小工具庫**、
主程式與小工具能共享資料、外觀使用 iOS 26 的原生液態玻璃。

這不是通用教學，而是一份**實際踩過坑之後留下的規則集**。
每一條規則都對應一個「看起來全部正常、卻什麼都不會動，而且沒有任何錯誤訊息」的真實問題。

## 它解決什麼

| 症狀 | 對應鐵則 |
|---|---|
| 小工具庫完全找不到（但其他側載 App 的小工具正常） | 1：擴展要用真正的 Xcode app-extension target 建置 |
| 同上，但中介資料齊全 | 4：安裝時要選 Register App ID for Each Extension |
| 小工具顯示範例資料、永遠不變 | 3：App Group 授權與 `ALTAppGroups` |
| 更新後小工具消失 | 6：刪除後重新安裝 |
| Swift Playgrounds 有質感、IPA 沒有 | 5：要用 iOS 26 SDK 建置 |
| 小工具顯示已經結束的行程 | 小工具內容邏輯（時間感知） |

## 檔案結構

```
ios-sideload-app/
├── SKILL.md                              ← 入口：七條鐵則、標準流程、症狀對照表
├── references/
│   ├── build-pipeline.md                 ← GitHub Actions、XcodeGen、entitlements、簽章與 CI 驗證
│   ├── widget-extension.md               ← 擴展 target、Info.plist、時間軸、內容邏輯
│   ├── sideload-and-sharing.md           ← 側載安裝選項、App Group 共享、ALTAppGroups
│   ├── native-look.md                    ← 液態玻璃、ProMotion、SDK 版本造成的外觀落差
│   ├── dual-track-build.md               ← 同時保留 Swift Playgrounds 與 CI 兩條路
│   └── troubleshooting.md                ← 決策樹、App 內診斷面板程式碼、交付前檢查清單
└── scripts/
    └── inspect_ipa.py                    ← 一鍵體檢 IPA（純 Python，不需 Xcode）
```

## 快速開始

```bash
# 體檢一份 IPA：擴展有沒有被安裝、簽章有沒有涵蓋自己、中介資料齊不齊、二進位對不對
python scripts/inspect_ipa.py App.ipa

# 機器可讀
python scripts/inspect_ipa.py App.ipa --json
```

離開碼 `0` = 全部通過；`1` = 有項目不合格，報告最後會列出問題與修法。

## 三句話版本（記不住細節時只記這三句）

1. **小工具擴展一律用真正的 Xcode app-extension target 建置**，不要用 `swiftc` 手工組裝 `.appex`。
2. **側載安裝時選「為每個擴展註冊 App ID」**，不要選「使用主程式設定檔」。
3. **CI 用 macOS 26 + Xcode 26（iOS 26 SDK）建置**，否則不會有液態玻璃。

## 授權

MIT
