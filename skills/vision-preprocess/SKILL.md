---
name: vision-preprocess
description: 為純文字模型（如 DeepSeek）注入視覺能力：貼圖即自動識別，零操作、全免費。用於 opencode（TUI／桌面版／CLI）想貼圖讓文字模型看懂，或為其他 Agent 環境架設「圖片自動預處理」時。
---

# 視覺預處理注入（Vision Preprocess）

## 這是什麼

讓**不支援圖片的文字模型**（例如 `deepseek-v4-flash`）也能「看懂」使用者貼上的圖片：

```
使用者貼圖 → opencode plugin 攔截 → 免費視覺模型識別 → 文字描述注入對話 → 文字模型照常回答
```

全程自動，使用者不需要任何額外操作——就像在跟多模態模型對話一樣。

## 使用情境

- 使用者直接貼圖（Ctrl+V、拖曳）給文字模型，希望模型認得圖片內容
- 不想為了看圖而把主模型換成多模態（貴或額度有限）
- opencode 桌面版／TUI 貼圖被「model does not support image input」擋下

## 安裝（opencode 環境）

### 1. 複製 plugin 到全域 plugin 目錄

```
~/.config/opencode/plugin/vision-preprocess.ts
```

### 2. 設定檔

`opencode.json` 需要覆寫主模型的 modalities（讓 client 端允許貼圖送出）：

```json
{
  "provider": {
    "opencode-go": {
      "models": {
        "deepseek-v4-flash": {
          "name": "DeepSeek V4 Flash",
          "reasoning": true,
          "tool_call": true,
          "modalities": { "input": ["text", "image"], "output": ["text"] }
        }
      }
    }
  }
}
```

`~/.config/opencode/package.json` 加 `"type": "module"`（消警告）。

### 3. 重啟 opencode

### 4. 驗證

貼一張圖送出，若回覆出現 `[使用者貼了一張圖片，已由視覺模型 ...]` 即成功。

## 視覺模型備援鏈（全部免費）

```
gemini-3.5-flash-lite（aiapi.tw，~2 秒）
  ↓ 失敗
gemini-3.1-flash-lite
  ↓ 失敗
gemini-3.1-flash-lite-preview
  ↓ 失敗
mimo-v2.5-free（opencode zen）
```

## 重要注意事項

- **桌面版（Desktop）sidecar 用 Node 執行 plugin，不是 Bun**——plugin 必須用 `node:fs/promises`，用 `Bun.file()` 會在桌面版靜默失敗（見 references/troubleshooting.md）
- 圖片會送往第三方 API（aiapi.tw / Gemini / opencode zen），敏感圖片請斟酌
- 環境變數可調：`OPENCODE_VISION_GEMINI_BASE`、`OPENCODE_VISION_GEMINI_KEY`、`OPENCODE_VISION_MIMO_MODEL`

詳細技術文件見 `references/architecture.md`。
