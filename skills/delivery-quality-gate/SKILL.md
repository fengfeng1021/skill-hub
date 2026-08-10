---
name: delivery-quality-gate
description: 交付品質閘門。任何程式碼交付（前端、後端、腳本、基礎設施、資料處理）在宣稱「完成」之前，需要先驗證、再審查、後檢查安全時使用。指揮 obra/superpowers 品質三件套（verification-before-completion、requesting-code-review、receiving-code-review）與 Google mantis 安全審查。觸發關鍵字：驗證、審查、安全、交付、完成聲明、品質把關、漏洞、review。
version: 1.0.0
---

# 交付品質閘門（Delivery Quality Gate）

> **定位：跨技術棧的交付品質總指揮。** 任何程式碼——前端、後端、腳本、基礎設施——在「宣稱完成」之前，都先過這道閘門：**驗證 → 審查 → 安全**，三關全過才准交付。不綁定任何技術棧或 Agent。

## 三道關卡（缺一不可）

```
關卡一　驗證（證據先於斷言）
　→ verification-before-completion：先跑驗證指令並確認輸出，才允許說「完成了」
關卡二　審查（第二雙眼睛）
　→ requesting-code-review：派 code-reviewer 子代理審查（讀 code-reviewer.md）
關卡三　安全（漏洞掃描與修補）
　→ mantis-threat-model → mantis-review → mantis-patch
```

## 閘門流程（標準 6 步，每步回報）

1. **開場宣告**：任務開始時宣告「要交付什麼、會跑哪些驗證指令」，讓使用者可以修正。
2. **驗證**（verification-before-completion）：跑測試／lint／build，**貼出實際輸出**當證據。
3. **審查**（requesting-code-review）：把精確上下文與評估標準送給審查員，早審常審。
4. **處理意見**（receiving-code-review）：每條意見先技術驗證再實作；不同意就用證據說明。
5. **安全**（mantis）：威脅建模 → 掃描 → 複核 → 修補，殘留風險明確記錄。
6. **交付聲明**：跑下面最終清單，逐項打勾回報，全過才宣告完成。

## 最終交付清單（宣告完成前逐項打勾回報）

- [ ] 驗證指令已執行，輸出已確認（證據貼出，不是「我認為應該可以」）
- [ ] 審查員已看過，意見已處理（或明確記錄不處理的原因）
- [ ] 安全審查已跑，漏洞已修補（或明確記錄殘留風險與理由）
- [ ] 所有「完成／修好／測試通過」的聲明都有對應證據

## 常見遺漏警示（歷史漏做模式）

- 只說「測過了」但沒貼輸出 → 等於沒測
- 修完 bug 直接交付、跳過閘門 → 違規，回到關卡一
- 收到審查意見照單全收 → 應該先驗證再實作
- 把「沒找到漏洞」當安全證明 → mantis 的發現需人工複核後才能回報
- 只跑一半流程（驗證完就交付）→ 三關缺一不可

## 原檔讀取指示

先依目前 Agent 的官方 skill 機制找出它實際載入的 skill 目錄。若其中存在下列 skill，**先讀原檔再行動**；本檔濃縮版只是沒有原檔時的最低標準：
- `verification-before-completion/`（SKILL.md）
- `requesting-code-review/`（SKILL.md + code-reviewer.md）
- `receiving-code-review/`（SKILL.md）
- `mantis-*/`（Google 安全審查流水線，18 個 skill：threat-model → researcher → dedupe → critic → review → reproduce → chain → calibrate → patch → report 等）

## 與其他入口的關係

- **前端總指揮**（frontend-director）在「品質閘門」階段觸發本入口 —— 前端任務的第四階段。
- 後端、資料、DevOps 等非前端任務：**直接以本入口為指揮**，不經過前端總指揮。
- 本入口不負責視覺設計；那是前端總指揮的職責。
