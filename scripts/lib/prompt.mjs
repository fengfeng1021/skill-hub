/**
 * 安裝提示詞產生器。
 *
 * 輸出結構刻意拆成 header / block / footer 三段，
 * 前端多選時只要 header(n) + block[] + footer 就能組出一份合法的提示詞，
 * 不必在瀏覽器端重複實作這裡的邏輯。
 */

export function buildHeader(count, cfg) {
  // count 傳數字就照數字判斷單複數；傳字串（例如 '{{count}}' 佔位符）一律當多個處理，
  // 讓前端組多選提示詞時能自己把數量填進去。
  const n = typeof count === 'number' && count <= 1 ? '下面這個' : `下列 ${count} 個`;
  return `你是我的 Skill 安裝助手。請幫我安裝${n} Claude Skill。

## 安裝規則

1. **安裝位置** — 每個 skill 是一個資料夾，放在：
   - 全域（所有專案共用）：\`${cfg.installRoots.user.posix}/<資料夾名>/\`
     Windows 為 \`${cfg.installRoots.user.windows}\\<資料夾名>\\\`
   - 只給目前專案用：\`<專案根目錄>/${cfg.installRoots.project.posix}/<資料夾名>/\`
   下面每個 skill 都標了建議範圍，照著放；我另外指定時以我說的為準。
2. **資料夾名不要改**。Claude 用資料夾名對應 SKILL.md 的 \`name\`，改了會載入不到。
3. **取得檔案的優先順序**：
   a. 直接抓下面給的 raw 下載網址
   b. 抓不到就 \`git clone\` 整個 repo 到暫存目錄，複製出需要的子目錄，再刪暫存
   c. 都不行（無網路等）就直接告訴我，我把檔案貼給你
4. **不要改寫 SKILL.md 的 frontmatter**（\`name\`、\`description\`）。那是 Claude 判斷何時自動載入這個 skill 的依據，改了就失效。
5. 目標資料夾**已存在**時，先停下來問我要覆蓋還是跳過，不要直接蓋掉。`;
}

export function buildFooter() {
  return `## 完成後請做這幾件事

1. 列出每個 skill 實際安裝的完整路徑，以及該資料夾下的檔案
2. 逐一讀取 SKILL.md 的 frontmatter，確認 \`name\` 與資料夾名一致、\`description\` 沒有空白
3. 告訴我要重新啟動 Claude Code，新的 skill 才會被載入
4. 只要有任何一個沒裝成功，明確講是哪一個、卡在哪一步 —— 不要為了看起來完成而略過`;
}

/** 單一 skill 的說明區塊（不含 header / footer） */
export function buildBlock(skill, index = null) {
  const title = index === null ? `### ${skill.name}` : `### ${index}. ${skill.name}`;
  const scope = skill.install.scope === 'project' ? '專案內（.claude/skills）' : '全域（~/.claude/skills）';
  const files = skill.install.files?.length ? skill.install.files : ['SKILL.md'];
  const parts = skill.parts ?? [];

  const head = parts.length
    ? `${title}  →  一組 ${parts.length} 個資料夾，要全部裝齊`
    : `${title}  →  資料夾名 \`${skill.install.dirName}\``;

  const lines = [head, '', `- **這個 skill 做什麼**：${skill.summary}`, `- **建議安裝範圍**：${scope}`];

  if (skill.install.command) {
    lines.push(`- **一行裝完**（能用就優先用這個，成功了就跳過下面的手動取檔）：`);
    lines.push(`  \`\`\`bash`);
    lines.push(`  ${skill.install.command}`);
    lines.push(`  \`\`\``);
  }

  if (skill.source.kind === 'github') {
    const sub = skill.source.subdir ? `，子目錄 \`${skill.source.subdir}\`` : '（repo 根目錄即為 skill）';
    lines.push(`- **來源**：GitHub \`${skill.source.label}\`（分支 \`${skill.source.branch}\`${sub}）`);
    lines.push(`- **repo 網址**：${skill.source.url}`);
  } else if (skill.source.kind === 'local') {
    lines.push(`- **來源**：Skill Hub 託管`);
    lines.push(`- **瀏覽位置**：${skill.source.displayUrl}`);
  } else {
    lines.push(`- **來源**：${skill.source.url}`);
  }

  if (parts.length) {
    // 組合包：每一份都是獨立資料夾，路徑不同，逐一列出下載基底
    lines.push(`- **這一組的 ${parts.length} 個資料夾**（缺一不可，資料夾名照抄）：`);
    for (const p of parts) {
      lines.push(`  - \`${p.dirName}\`${p.summary ? ` — ${p.summary}` : ''}`);
      if (p.rawBase) lines.push(`    下載基底：\`${p.rawBase}\``);
    }
    lines.push(`- **每個資料夾都要拿的檔案**：`);
    for (const f of files) lines.push(`  - \`<下載基底>/${f}\``);
  } else {
    if (skill.source.rawBase) {
      lines.push(`- **下載基底網址**：\`${skill.source.rawBase}\``);
      lines.push(`  取檔方式：\`<下載基底網址>/<下面的檔案路徑>\``);
    }
    lines.push(`- **要拿的檔案**（相對於 skill 資料夾）：`);
    for (const f of files) lines.push(`  - \`${f}\``);
  }

  if (skill.install.requires?.length) {
    lines.push(`- **額外相依**（先確認有沒有，缺的話問我要不要裝）：`);
    for (const r of skill.install.requires) lines.push(`  - \`${r}\``);
  }

  if (skill.install.notes) {
    lines.push(`- **注意**：${skill.install.notes}`);
  }

  return lines.join('\n');
}

/** 完整的單一 skill 安裝提示詞 */
export function buildInstallPrompt(skill, cfg) {
  if (skill.prompt) return skill.prompt;
  return [buildHeader(1, cfg), '---', buildBlock(skill), '---', buildFooter()].join('\n\n');
}
