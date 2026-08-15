# 技術架構：為文字模型注入視覺能力

## 背景問題

opencode 中使用的文字模型（如 `opencode-go/deepseek-v4-flash`）不支援圖片輸入。直接貼圖會遇到：

- **Client 端檢查**：桌面版／Web 版送出前檢查 model 的 modalities（capabilities）是否含 `image`，沒有就顯示 `Cannot read "image.png" (this model does not support image input)` 並拒絕送出
- **Provider 端拒絕**：若圖片 part 真的送出，上游 API 回 400（`unknown variant image_url`）

## 解決方案總覽

兩層配合：

1. **設定層**（`opencode.json`）：覆寫主模型的 `modalities.input` 加入 `image`，讓 client 檢查通過、允許貼圖送出
2. **Plugin 層**（`experimental.chat.messages.transform`）：在訊息送給模型前攔截，把圖片 part 抽出 → 送免費視覺模型識別 → 用文字描述**原位替換**圖片 part → 文字模型收到的是純文字

```
使用者貼圖
  │
  ▼
opencode client（檢查通過，因 modalities 已覆寫）
  │
  ▼
server messages.transform（plugin）
  ├─ 掃描所有訊息中的 file part（mime image/* 或副檔名判斷）
  ├─ data URI → base64
  ├─ 視覺備援鏈識別（見 model-chain.md）
  └─ splice 原位替換為 synthetic text part
  │
  ▼
deepseek（收到文字描述，正常回答）
```

## Plugin 關鍵實作

### Hook 選擇

`experimental.chat.messages.transform`：每次發送請求前對完整 messages 陣列套用。它發生在 **model 能力檢查之前**，因此可以在圖片觸發任何拒絕前先轉換掉。

### 圖片 part 判別

opencode 的圖片訊息是 `FilePart`（`type: "file"`），關鍵欄位：

- `mime`：`image/png` 等
- `url`：data URI（`data:image/png;base64,...`）、http(s) 或本機路徑
- `filename`：如 `image.png`（桌面版貼圖）、`clipboard`（TUI 貼圖）

判別條件（寬鬆版，避免漏接）：

```ts
function isImagePart(p) {
  if (p.type !== "file") return false
  if (p.mime && p.mime.startsWith("image/")) return true
  const name = String(p.filename || p.url || "").toLowerCase()
  if (name.startsWith("data:image/")) return true
  return /\.(png|jpe?g|gif|webp|bmp|avif|heic|svg)$/i.test(name)
}
```

### 原位替換

不要把替換的 text part push 到最後——用 `splice(idx, 1, newPart)` 原位替換，保持訊息內容順序（`prompt.parts` 的位置對應使用者輸入游標位置）。

### Runtime 關鍵：Node 不是 Bun

- opencode CLI（`opencode run`）內建 Bun runtime → `Bun.file()` 可用
- **opencode Desktop sidecar 是 Node runtime** → `Bun.file()` 拋錯且被 opencode 吞掉，導致 key 讀不到、hook 靜默提前 return

因此 plugin **必須只用 Node 標準 API**：`node:fs/promises`、`node:os`、`node:path`。

### 快取

`cacheKey = sessionID:messageID:partID` → 描述文字。同一張圖在同 session 內重複出現（例如歷史訊息重送）不重複呼叫視覺 API。

## 設定原理

`opencode.json` 覆寫模型能力：

```json
{
  "provider": {
    "opencode-go": {
      "models": {
        "deepseek-v4-flash": {
          "modalities": { "input": ["text", "image"], "output": ["text"] }
        }
      }
    }
  }
}
```

- client 檢查 `model.capabilities.input` 有無 `image` → 通過
- 實際圖片不會送到 deepseek（plugin 已轉成文字），所以 provider 不會收到不支援的格式

## 系統提示

`experimental.chat.system.transform` 附加說明，讓文字模型知道 `[使用者貼了一張圖片，已由視覺模型 ...]` 開頭的文字代表圖片內容，直接視為圖片使用。

## 限制

- 依賴第三方視覺 API（aiapi.tw / Gemini / opencode zen），需網路
- 描述品質取決於視覺模型（OCR、細節描述能力）
- 敏感圖片會送往第三方服務
- 每個模型備援鏈節點有自己的速率限制（RPD），用完需等滾動視窗
