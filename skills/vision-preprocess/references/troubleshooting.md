# 踩坑記錄與解法

本文記錄架設視覺預處理時實際遇到的問題與根因，給未來維護者參考。

## 1. 桌面版貼圖全掛，CLI 卻正常

**症狀**：headless `opencode run -f image.jpg` 正常識別；Desktop 版貼圖出現 `ERROR: Cannot read "image.png" (this model does not support image input). Inform the user.`，plugin 完全沒反應（debug log 無記錄）。

**根因**：opencode Desktop 的 sidecar server 用 **Node runtime** 執行 plugin；CLI（`opencode run`）用內建 **Bun runtime**。早期 plugin 用了 `Bun.file()`／`Bun.write()`：

- Node 下 `Bun.file()` 直接拋 ReferenceError
- opencode 的 hook 執行有 try/catch，錯誤被靜默吞掉
- 後果：API key 讀不到 → transform 提早 return → 圖片 part 原樣送到 provider → 上游 400

**解法**：全部改用 Node 標準 API（`node:fs/promises` 的 `readFile`/`appendFile`/`mkdir`、`node:os`、`node:path`）。

**判別**：執行環境是 Bun 還是 Node，不要用 `Bun.` 全域（唯一可靠做法）。

## 2. 貼圖被 client 端擋下

**症狀**：桌面版／Web 版貼圖直接顯示 `Cannot read "image.png" (this model does not support image input)`，訊息根本沒送出（server 日誌無請求、plugin 無觸發）。

**根因**：client 在送出前檢查 model 的 modalities/capabilities，文字模型沒有 `image` input。

**解法**：在 `opencode.json` 覆寫該模型的 modalities，讓 client 檢查通過。實際圖片仍會被 plugin 轉成文字，不會真的送給文字模型。

## 3. 上游 400：`unknown variant image_url`

**症狀**：貼圖偶爾成功，偶爾回 `Error from provider: Upstream request failed: [invalid_request_error] ... unknown variant 'image_url', expected 'text'`（messages[N] 是歷史深處的舊訊息）。

**根因**：該 session 歷史中殘留早期失敗的 user message（含圖片 file part，存在 DB）。發送時若 transform 沒處理到（例如 key 讀取失敗提早 return），file part 原樣轉成 image_url 送給上游。

**解法**：
1. 修好 key 讀取（Node 相容）後，transform 每次請求都會處理歷史中的圖片 part（快取命中或重新識別），舊 session 會自癒
2. 嚴重時直接開新 session

## 4. gemini 免費 tier 額度

- 新 Google 帳號免費額度很低（Gemini 3.5 Flash：RPM 5、RPD 20；Flash Lite：RPM 15、RPD 500），會隨使用時間自動調升
- RPD 是滾動 24 小時制，429 後要等視窗滑動
- 付費 tier（Tier 1）沒有免費額度；AI Studio 可停用計費回到免費 tier
- 多帳號規避額度違反 Google ToS，有整批停權風險

## 5. 除錯方法

plugin 內建的 `logDebug()` 寫入 `%TEMP%\opencode\vision-debug.log`：

- `TRANSFORM messages=N info=... parts=... types=[...]`：每次 hook 呼叫、每條訊息的 part 類型
- `PART type=... mime=... filename=... urlHead=... keys=[...]`：每個 part 的形狀
- 若完全沒有記錄 → hook 沒被呼叫或 plugin 沒載入（檢查 server log 的 MODULE_TYPELESS 警告）

## 6. 其他

- `~/.config/opencode/package.json` 加 `"type": "module"` 可消 `MODULE_TYPELESS_PACKAGE_JSON` 警告
- `opencode run`（CLI）在 PowerShell 下直接呼叫 `opencode.cmd` 有參數傳遞問題（中文被誤判為檔案路徑），用底層 `opencode.exe` 或英文訊息較穩
