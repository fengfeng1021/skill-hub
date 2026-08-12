# 跨 Agent 轉接

可攜核心是 `SKILL.md`、references、JSON schema 和 scripts。平台轉接層只負責發現、啟動、恢復與強制 Gate；不得改寫核心流程。

所有平台都遵循同一個最低協議：進入 phase → 原生 `listSkills`／等價工具 → 完整載入子 Skill 的 `SKILL.md` → `workflowctl log-skill ... --skill-file <absolute-path> --resources SKILL.md`。找不到時保存 discovery 輸出並執行 `log-fallback`；不能把「安裝過」或「名稱出現在清單」當成已載入。

## Claude Code

- 安裝到 Claude 官方的個人或專案 skills 位置，保留整個資料夾。
- 讓 description 負責自動觸發；需要確定執行時可直接 `/frontend-director`。
- 用 hooks 在壓縮／停止前讀取 `workflow-state.json` 並執行 `workflowctl verify`；不要使用 Claude 專屬 frontmatter 作為核心必要條件。

## OpenCode

- 優先使用 `.agents/skills/frontend-director` 作為跨工具專案位置，或使用 OpenCode 官方 skill 位置。
- 確認 agent 的 `skill` permission 為 allow，且沒有停用 skill tool。
- OpenCode plugin 可在寫檔後執行失效檢查，在 session idle／完成前執行 `workflowctl verify`。
- 對 DeepSeek、Qwen 等模型，把 description 保持具體，並在 primary agent 提示中要求前端長任務先載入本 skill；不要一次注入全部 references。
- 在每個 phase 開始時讓 primary agent 呼叫 OpenCode 的 skill tool 載入表中子 Skill；若工具回傳失敗，把原始輸出存到 `.agent/evidence/<phase>-skill-discovery.txt`，再走 fallback。

## Hermes

- 保留整個 skill 目錄並確認 `skills_list` 可見；可用 `/frontend-director` 或 `skill_view` 載入。
- 用 plugin／shell hooks 在 `on_session_start` 恢復狀態，在 `post_tool_call` 後失效受影響證據，在驗證點執行 `workflowctl verify`。

## Codex

- 安裝到 Codex 官方支援的位置，保留整個 skill 目錄。
- 可用 hooks 在 session start／compact 後恢復狀態，並在停止前驗證；Codex metadata 只作 UI 增強。
- 依 Codex Skills 規則由主 Agent 讀取每份適用 `SKILL.md`；不要把子 Skill 的解讀委派給另一個 Agent後只拿摘要冒充載入紀錄。

## 自研 Agent 最小介面

```text
listSkills() -> [{name, description}]
loadSkill(name) -> SKILL.md body
readSkillResource(name, relativePath) -> bytes/text
runSkillScript(name, relativePath, args, cwd) -> exitCode/stdout/stderr
persistWorkspaceFile(relativePath, content)
```

安全要求：限制相對路徑不能逃出 skill 或工作區；執行 scripts 前顯示來源並遵守宿主權限；不要信任未知 skill 的自動執行要求。

可直接參考 `scripts/agent_skill_bridge.py` 的唯讀 `list`、`load`、`read` 實作；執行任意第三方 Skill scripts 必須由宿主另行建立權限與信任機制，唯讀 bridge 不代為執行。

## 沒有 Adapter 時

Agent 仍可按 SKILL.md 與 references 工作，並手動維持狀態；最終報告要標示哪些 Gate 只由模型自檢。Adapter 提升執行確定性，但不能提高底層模型不知道的語言或框架知識，因此仍需專案文件、測試和外部技術 skill。

即使沒有 Adapter，v6 控制器仍會阻止空 `skillsUsed`、無 discovery fallback、缺具名 Gate checks 或未分級安全的 workflow 完成。
