# 狀態與控制器

`scripts/workflowctl.py` 使用 Python 標準函式庫管理 `.agent/workflow-state.json`。所有命令都接受 `--root <project-root>`；不要把狀態寫進 skill 安裝目錄。

## 常用命令

```text
workflowctl init --mode full|targeted
workflowctl upgrade-policy
workflowctl status [--json]
workflowctl add-requirement FR-001 --kind functional --text "..."
workflowctl add-task T-001 --title "..." --requirements FR-001 --files src/a.ts,tests/a.test.ts --checks unit,typecheck
workflowctl log-skill impeccable --skill-file /absolute/path/impeccable/SKILL.md --resources SKILL.md --source native
workflowctl log-fallback --missing-skills impeccable --reason "宿主 discovery 找不到" --reference references/ui-quality.md --discovery-evidence .agent/evidence/ui-skill-discovery.txt
workflowctl record-gate-check ui --name design-direction --kind manual --evidence .agent/evidence/ui-direction.md --summary "產品特異設計方向已審查"
workflowctl validate-visual-evidence --manifest .agent/evidence/visual-evidence.json
workflowctl start-task T-001
workflowctl record-check T-001 --name unit --command "..." --exit-code 0 --evidence .agent/evidence/T-001-unit.txt
workflowctl complete-task T-001 --summary "..."
workflowctl pass-gate ui --evidence .agent/evidence/ui.md --summary "..."
workflowctl skip-phase motion --reason "本任務不新增動效"
workflowctl invalidate --files src/a.ts --reason "共用行為已修改"
workflowctl classify-security --level low --reason "僅靜態本地資料，沒有新信任邊界" --evidence .agent/evidence/security-classification.md
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
- 同一任務或 Gate 重新記錄同名檢查時，新結果會使舊結果失效；後來的失敗不能被較早的通過掩蓋。
- `complete-task` 要求至少一個退出碼為 0、證據內容未被改寫且檔案範圍指紋仍新鮮的檢查；任務有 `--checks` 時必須全部具備新鮮通過證據。
- `invalidate` 依檔案交集使任務、檢查與下游 Gate 失效。
- `pass-gate` 要求該階段的子 Skill 已用 `log-skill` 記錄；缺少能力時必須有 discovery 證據和對應內建 reference 的 `log-fallback`。
- `pass-gate` 要求下表所有具名檢查都有完整、未被改寫且與工作區一致的證據；`not-applicable` 也要保存具體理由。
- `finish` 要求需求全覆蓋、任務完成且證據新鮮、必要階段通過、可選階段通過或有理由跳過、安全已分級，且沒有 Critical／High 風險。
- v5／policy v1 與 v6／policy v2 狀態可用 `status` 讀取，但 `verify --finish` 與 `finish` 會拒絕；`upgrade-policy` 保留需求／任務定義、使舊任務證據與所有 Gate 失效，再從 contract 依 v6.1 重驗。

## Gate 必要檢查

| Phase | 必要檢查名稱 |
|---|---|
| contract | `requirements-review` |
| plan | `coverage-review` |
| ui | `design-direction`、`responsive-spec`、`state-inventory`、`product-specificity`、`signature-visual-plan` |
| ux | `primary-flow-model`、`failure-recovery-plan`、`accessibility-plan` |
| motion | `motion-purpose`、`reduced-motion-plan`、`interruption-plan` |
| implementation | `tests`、`typecheck`、`lint`、`format`、`diff-review` |
| integration | `build`、`desktop-browser`、`mobile-browser`、`keyboard-focus`、`semantic-oracles`、`reduced-motion`、`console-clean`、`visual-fidelity`、`interaction-stress` |
| security | `security-baseline`、`negative-paths`、`dependency-review` |

自動檢查使用 `--kind automated --command "..." --exit-code <code>`。人工渲染、鍵盤或審查使用 `--kind manual`。專案確實不適用時使用 `--kind not-applicable`，並在 `--summary` 說明替代驗證與限制；不得用它掩蓋缺少 lint、瀏覽器或安全工具。

## 子 Skill 規則

- contract：`define-acceptance-contract`
- plan：`plan-implementation`
- ui：`impeccable`、`taste`、`hue` 三者都要載入
- ux：`interaction-experience-design`
- motion：通過時至少載入一個與需求相符的 `gsap-*` 作為動效規格與性能審查能力；純 CSS 不等於缺少 Skill，也不要求把 GSAP 套件加入產品。只有 Skill 確實不可發現時才可使用 fallback
- implementation／integration／security：各階段載入 `delivery-quality-gate`
- high security：除 `delivery-quality-gate` 外，還要載入 Mantis 或同等 threat/security specialist

控制器只接受 resources 中含 `SKILL.md` 且 `--skill-file` 指向真實檔案的 `log-skill`；會核對 frontmatter 名稱並保存檔案 hash，避免把「看見名稱」誤記成「讀取並使用」。fallback 必須保存 discovery 輸出 hash；外部 Skill 可用時不得選 fallback。

## 回退

發現上游問題時，用 `invalidate --phase <phase>` 把該階段及下游重新設為 pending。不得直接手改狀態，把失敗改成通過。狀態檔損壞時先備份，再以 schema 和真實證據重建；不要臆造已完成紀錄。

控制器不能替代實際測試。它只保證證據結構、順序、失效與完成條件不被輕易跳過。
