/**
 * 安裝提示詞產生器。
 *
 * 輸出結構刻意拆成 header / block / footer 三段，
 * 前端多選時只要 header(n) + block[] + footer 就能組出一份合法的提示詞，
 * 不必在瀏覽器端重複實作這裡的邏輯。
 */

export function buildHeader(count) {
  // count 傳數字就照數字判斷單複數；傳字串（例如 '{{count}}' 佔位符）一律當多個處理，
  // 讓前端組多選提示詞時能自己把數量填進去。
  const n = typeof count === 'number' && count <= 1 ? '下面這個' : `下列 ${count} 個`;
  return `你是我的 Skill 安裝助手。請幫我把${n} AI Agent Skill 安裝到「你目前所在的 Agent 環境」。

## 安裝規則

1. **先辨識目前環境** — 讀取你自己的官方說明、系統設定或既有 skills，確認這個 Agent 支援的 skill 格式、安裝方式與可用範圍。不要預設任何品牌，也不要自行猜一個 \`~/.<名稱>/skills\` 路徑。
2. **自動選擇正確位置** — 我有指定全域或專案範圍時照做；沒有指定時，沿用目前 Agent 的既有慣例。若這個 Agent 只支援其中一種，就使用它官方支援的方式。只有真的無法判定時才停下來問我。
3. **保持原始結構** — 每個 skill 都是獨立資料夾；資料夾名、SKILL.md frontmatter 的 \`name\`／\`description\` 與相對檔案結構都不要改。
4. **取得檔案的優先順序**：
   a. 直接抓下面給的 raw 下載網址
   b. 抓不到就 \`git clone\` 整個 repo 到暫存目錄，複製出需要的子目錄，再刪暫存
   c. 都不行（無網路等）就直接告訴我，我把檔案貼給你
5. 來源若提供綁定特定 Agent 或固定路徑的安裝指令，只把它當作來源線索；請改用目前 Agent 的官方安裝方式，不要原樣執行。
6. 目標資料夾**已存在**時，先比較版本與差異，再問我要更新、覆蓋或跳過，不要直接蓋掉。`;
}

export function buildFooter() {
  return `## 完成後請做這幾件事

1. 說明你辨識到的 Agent 與採用的官方 skill 機制，不要只回報「已完成」
2. 列出每個 skill 實際安裝的位置，以及該資料夾下的檔案
3. 逐一讀取 SKILL.md 的 frontmatter，確認 \`name\` 與資料夾名一致、\`description\` 沒有空白
4. 依目前 Agent 的載入方式驗證 skill 已可被發現；只有官方流程確實要求時，才提醒我重新載入或重啟
5. 只要有任何一個沒裝成功，明確講是哪一個、卡在哪一步 —— 不要為了看起來完成而略過`;
}

/** 只有不綁 Agent 名稱、使用者目錄或固定 skills 路徑的命令才可直接執行。 */
export function isPortableCommand(command) {
  if (!command) return false;
  return !/(?:claude|cursor|hermes|codex|\.claude|\.cursor|\.hermes|\.codex|USERPROFILE|HOME|skills[\\/])/i.test(
    command
  );
}

/** 單一 skill 的說明區塊（不含 header / footer） */
export function buildBlock(skill, index = null) {
  const title = index === null ? `### ${skill.name}` : `### ${index}. ${skill.name}`;
  const scope = skill.install.scope === 'project' ? '專案內（只給目前專案用）' : '全域（所有專案共用）';
  const files = skill.install.files?.length ? skill.install.files : ['SKILL.md'];
  const parts = skill.parts ?? [];

  const head = parts.length
    ? `${title}  →  一組 ${parts.length} 個資料夾，要全部裝齊`
    : `${title}  →  資料夾名 \`${skill.install.dirName}\``;

  const lines = [head, '', `- **這個 skill 做什麼**：${skill.summary}`];

  // summary 是寫給使用者看的白話，技術上的涵蓋範圍在 description，安裝的 AI 兩個都要知道
  const detail = String(skill.description ?? '').split('\n')[0].trim();
  if (detail && detail !== skill.summary) lines.push(`- **詳細一點**：${detail}`);

  lines.push(`- **使用範圍偏好**：${scope}；若目前 Agent 不支援此範圍，採用它官方提供的等效方式`);

  if (isPortableCommand(skill.install.command)) {
    lines.push(`- **可攜式安裝指令**（確認適用目前 Agent 後可優先使用，成功就跳過手動取檔）：`);
    lines.push(`  \`\`\`bash`);
    lines.push(`  ${skill.install.command}`);
    lines.push(`  \`\`\``);
  }

  if (skill.source.kind === 'github') {
    const sub = skill.source.subdir
      ? `，來源 repo 內子目錄 \`${skill.source.subdir}\`（只用來取檔，不是安裝位置）`
      : '（repo 根目錄即為 skill）';
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

  if (skill.replaces?.length) {
    lines.push(`- **舊名稱遷移**：這個入口取代 ${skill.replaces.map((name) => `\`${name}\``).join('、')}。`);
    lines.push(`  安裝前先在目前 Agent 的官方 skills 位置尋找這些舊資料夾或 frontmatter name。`);
    lines.push(`  若找到，先與新版比較：有自訂修改就停止並列出差異讓使用者決定；沒有自訂時，先安裝並驗證新版可被發現，再把舊入口的 \`SKILL.md\` 改名為 \`SKILL.md.disabled\`，保留可恢復備份，避免兩份入口同時觸發。`);
  }

  return lines.join('\n');
}

/**
 * 一筆收錄項目的提示詞區塊。
 * includes 是跨來源精選組合包：入口 skill 與被引用的收錄項目都必須安裝。
 */
export function buildPromptBlock(skill, included = []) {
  if (!included.length) return buildBlock(skill);

  const all = [skill, ...included];
  const folderCount = all.reduce((total, item) => total + (item.dirNames?.length ?? 1), 0);
  const intro = [
    `### ${skill.name} — 精選組合包`,
    '',
    `> 這不是單一 skill，而是一套已整理好的完整資產。請一次安裝下列 ${all.length} 個收錄項目、共 ${folderCount} 個 skill 資料夾，不能把其餘內容當成可選相依。`,
    '',
    `- **組合入口**：${skill.name}（負責整合與分工）`,
    `- **完整內容**：${included.map((item) => item.name).join('、')}`,
  ].join('\n');

  return [intro, ...all.map((item, index) => buildBlock(item, index + 1))].join('\n\n---\n\n');
}

/** 完整安裝提示詞；精選組合包會展開成完整內容與正確總數。 */
export function buildInstallPrompt(skill, included = []) {
  if (skill.prompt && !included.length) return skill.prompt;
  const count = 1 + included.length;
  return [buildHeader(count), '---', buildPromptBlock(skill, included), '---', buildFooter()].join('\n\n');
}
