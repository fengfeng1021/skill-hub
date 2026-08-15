# 視覺預處理注入（Vision Preprocess）

讓純文字模型（如 DeepSeek）在 opencode 中獲得「眼睛」：使用者貼圖即自動識別，零操作、全免費。

## 快速開始

1. 複製 `plugin/vision-preprocess.ts` 到 `~/.config/opencode/plugin/`
2. 依 `config/opencode.json.example` 在 `opencode.json` 覆寫主模型 modalities
3. 重啟 opencode，貼圖即可

## 文件

- `SKILL.md` — 入口與安裝說明
- `references/architecture.md` — 完整技術架構（資料流、plugin 逐段說明、設定原理）
- `references/troubleshooting.md` — 踩坑記錄與解法（Bun vs Node、貼圖被擋、image_url 400）
- `references/model-chain.md` — 免費視覺模型實測數據與備援鏈設計
- `plugin/vision-preprocess.ts` — 可運作的 plugin 原始碼（Node 版）
- `config/opencode.json.example` — 設定範例（不含真實金鑰）

## 運作流程

```
貼圖（Ctrl+V / 拖曳 / CLI -f）
  → opencode 訊息帶 file part（data URI）
  → plugin transform 攔截
  → 視覺模型備援鏈識別（gemini lite 系列 → mimo，全免費）
  → 描述文字原位替換圖片 part
  → 文字模型正常回答
```

## 特性

- **零操作**：貼圖即識別，不需要切模型、不需要給路徑
- **全免費**：Gemini Lite 免費額度（RPD 500）+ mimo-v2.5-free 兜底
- **備援鏈**：高版本 lite 優先，失敗自動逐級降級
- **快取**：同一張圖在同 session 不重複識別
- **除錯**：`%TEMP%\opencode\vision-debug.log`

## 授權

MIT
