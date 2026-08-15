# 免費視覺模型評估與備援鏈設計

本文件的模型實測數據來自實際呼叫（同一張 Windows 10 桌布測試圖）。

## 實測結果

| 模型 | 存取方式 | 結果 | 延遲 | 備註 |
|---|---|---|---|---|
| gemini-3.5-flash-lite | aiapi.tw（Google 格式） | ✅ 描述正確 | ~1.4–3 秒 | 推薦主視覺模型 |
| gemini-3.5-flash | aiapi.tw | ✅（有時 503） | ~6.5 秒 | 高需求時 503，不穩 |
| gemini-3.1-flash-lite | aiapi.tw | ✅ | ~3.5–8 秒 | 次選 |
| mimo-v2.5-free | opencode zen | ✅（需較大 max_tokens） | ~3–4 秒 | reasoning 模型，content 在思考後才輸出 |
| gemini-3.5-flash（官方 key） | Google API | ✅ | ~1.4 秒 | 需免費 tier 帳號 |
| kimi-k3 | opencode zen | ❌ 回傳空內容 | — | 名義支援但不可用 |
| qwen3.8-max / qwen3.7-plus | opencode zen | ✅ | ~10 秒 | 品質好但付費 |

## 備援鏈設計

```
gemini-3.5-flash-lite      ← 主（aiapi.tw，免費額度，速度快）
  ↓ 失敗（4xx/5xx/timeout）
gemini-3.1-flash-lite
  ↓ 失敗
gemini-3.1-flash-lite-preview
  ↓ 失敗
mimo-v2.5-free             ← 兜底（opencode zen，免費無硬限）
```

原則：

1. **高版本優先**：3.5 → 3.1 → preview 逐級降
2. **只用 lite 系列**：免費額度較大（Flash Lite RPD 500 vs Flash RPD 20），日常貼圖用不完
3. **mimo 兜底**：opencode zen 的免費模型，無每日硬限制感，品質可接受
4. **不用的方案**（已評估）：多 Google key 輪詢（違反 ToS）、New API 中轉（需要額外架設）、付費 qwen 系列（燒額度）

## 額度參考（Google 免費 tier 新帳號起點）

| 模型 | RPM | RPD |
|---|---|---|
| Gemini 3.5 Flash | 5 | 20 |
| Gemini 3.5 Flash Lite | 15 | 500 |
| Gemini 3.1 Flash Lite | 15 | 500 |

- RPD 滾動 24 小時制；額度隨帳號使用時間自動調升
- 每個模型額度獨立計算，一個用完不影響其他

## mimo-v2.5-free 注意

reasoning 模型：`max_tokens` 至少要 1024（2048 較穩），否則思考過程吃光 token 配額後 content 欄位會是空。
