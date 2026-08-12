# 狀態與控制器

`scripts/workflowctl.py` 使用 Python 標準函式庫管理 `.agent/workflow-state.json`。所有命令都接受 `--root <project-root>`；不要把狀態寫進 skill 安裝目錄。

## 常用命令

```text
workflowctl init --mode full|targeted
workflowctl status [--json]
workflowctl add-requirement FR-001 --kind functional --text "..."
workflowctl add-task T-001 --title "..." --requirements FR-001 --files src/a.ts,tests/a.test.ts --checks unit,typecheck
workflowctl start-task T-001
workflowctl record-check T-001 --name unit --command "..." --exit-code 0 --evidence .agent/evidence/T-001-unit.txt
workflowctl complete-task T-001 --summary "..."
workflowctl pass-gate ui --evidence .agent/evidence/ui.md --summary "..."
workflowctl skip-phase motion --reason "本任務不新增動效"
workflowctl invalidate --files src/a.ts --reason "共用行為已修改"
workflowctl verify
workflowctl finish
```

在命令前加：

```text
python <skill-root>/scripts/workflowctl.py --root <project-root>
```

## 強制條件

- `start-task` 拒絕尚未滿足相依的任務。
- `record-check` 保存退出碼、證據路徑、時間和目前工作樹指紋。
- `complete-task` 要求至少一個退出碼為 0、證據內容未被改寫且檔案範圍指紋仍新鮮的檢查；任務有 `--checks` 時必須全部具備新鮮通過證據。
- `invalidate` 依檔案交集使任務、檢查與下游 Gate 失效。
- `finish` 要求需求全覆蓋、任務完成且證據新鮮、必要階段通過、可選階段通過或有理由跳過，且沒有 Critical／High 風險。

## 回退

發現上游問題時，用 `invalidate --phase <phase>` 把該階段及下游重新設為 pending。不得直接手改狀態，把失敗改成通過。狀態檔損壞時先備份，再以 schema 和真實證據重建；不要臆造已完成紀錄。

控制器不能替代實際測試。它只保證證據結構、順序、失效與完成條件不被輕易跳過。
