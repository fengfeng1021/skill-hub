#!/usr/bin/env node
/**
 * 從 registry/skills/*.json 產生：
 *   docs/api/index.json      全部資料 + 安裝提示詞（網站與 AI 共用的主要接口）
 *   docs/api/skills/<id>.json 單一 skill
 *   docs/api/tags.json       標籤與分類統計
 *   docs/llms.txt            給 AI 直接讀的純文字總覽
 *   docs/api/skills.md       人類可讀的清單
 *
 * 這些檔案都是產物，不要手改。
 */
import { writeFileSync, mkdirSync, rmSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { loadConfig, loadSkills, normalize, DOCS_DIR, ROOT } from './lib/registry.mjs';
import { buildHeader, buildFooter, buildBlock, buildInstallPrompt } from './lib/prompt.mjs';

const cfg = loadConfig();
const raw = loadSkills();
const skills = raw.map((s) => normalize(s, cfg));

const API_DIR = join(DOCS_DIR, 'api');
const API_SKILLS_DIR = join(API_DIR, 'skills');
if (existsSync(API_SKILLS_DIR)) rmSync(API_SKILLS_DIR, { recursive: true, force: true });
mkdirSync(API_SKILLS_DIR, { recursive: true });

// 每個 skill 補上提示詞欄位
for (const s of skills) {
  s.promptBlock = buildBlock(s);
  s.installPrompt = buildInstallPrompt(s, cfg);
  delete s.__file;
}

// 分類與標籤統計
const countBy = (arr, key) => {
  const map = new Map();
  for (const item of arr) {
    for (const v of [].concat(key(item))) {
      if (!v) continue;
      map.set(v, (map.get(v) ?? 0) + 1);
    }
  }
  return [...map.entries()]
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name, 'zh-Hant'));
};

const categories = countBy(skills, (s) => s.category);
const tags = countBy(skills, (s) => s.tags);

const generatedAt = new Date().toISOString().slice(0, 10);

const index = {
  $schema: './schema-note',
  generatedAt,
  site: {
    name: cfg.name,
    tagline: cfg.tagline,
    description: cfg.description,
    url: cfg.configured ? cfg.siteUrl : null,
    repo: cfg.configured ? cfg.repoUrl : null,
    configured: cfg.configured,
  },
  promptTemplate: {
    header: buildHeader(1, cfg),
    headerPlural: buildHeader('{{count}}', cfg), // 前端把 {{count}} 換成實際數量
    footer: buildFooter(),
    separator: '\n\n---\n\n',
  },
  count: skills.length,
  categories,
  tags,
  skills,
};

writeFileSync(join(API_DIR, 'index.json'), JSON.stringify(index, null, 2) + '\n');
for (const s of skills) {
  writeFileSync(join(API_SKILLS_DIR, `${s.id}.json`), JSON.stringify(s, null, 2) + '\n');
}
writeFileSync(join(API_DIR, 'tags.json'), JSON.stringify({ generatedAt, categories, tags }, null, 2) + '\n');

// ---- llms.txt：給 AI 一次讀完整個庫 ----
const llms = [
  `# ${cfg.name}`,
  '',
  `> ${cfg.description}`,
  '',
  `更新日期：${generatedAt}　收錄數量：${skills.length}`,
  cfg.configured ? `網站：${cfg.siteUrl}\nJSON 接口：${cfg.siteUrl}/api/index.json` : 'JSON 接口：docs/api/index.json',
  '',
  '## 怎麼用這份檔案',
  '',
  '每個 skill 底下都有「安裝指令」段落。使用者說要裝哪幾個，就把對應段落的內容當作任務執行：',
  '把 skill 資料夾放到 `~/.claude/skills/<資料夾名>/`，資料夾名不要改，SKILL.md 的 frontmatter 不要動。',
  '完整、可直接貼給 AI 的安裝提示詞在 `api/skills/<id>.json` 的 `installPrompt` 欄位。',
  '',
  '## 收錄清單',
  '',
];

for (const cat of categories) {
  llms.push(`### ${cat.name}`, '');
  for (const s of skills.filter((x) => x.category === cat.name)) {
    llms.push(`#### ${s.name} \`${s.id}\``);
    llms.push('');
    llms.push(`- 摘要：${s.summary}`);
    llms.push(`- 標籤：${s.tags.join('、') || '無'}`);
    llms.push(`- 來源：${s.source.displayUrl ?? '未註明'}`);
    if (s.parts.length) {
      llms.push(`- 這是一組 ${s.parts.length} 個資料夾，要一起裝：${s.parts.map((p) => `\`${p.dirName}\``).join('、')}`);
    } else {
      llms.push(`- 安裝資料夾名：\`${s.install.dirName}\``);
    }
    if (s.install.command) llms.push(`- 一行裝完：\`${s.install.command}\``);
    if (s.source.rawBase) llms.push(`- 下載基底：\`${s.source.rawBase}\``);
    if (s.usage.length) llms.push(`- 何時使用：${s.usage.join('；')}`);
    llms.push('');
  }
}
writeFileSync(join(DOCS_DIR, 'llms.txt'), llms.join('\n'));

// ---- skills.md：人類可讀清單 ----
const md = [
  `# ${cfg.name} 收錄清單`,
  '',
  `共 ${skills.length} 個，更新於 ${generatedAt}。此檔由 \`npm run build\` 產生，請勿手改。`,
  '',
];
for (const cat of categories) {
  md.push(`## ${cat.name}（${cat.count}）`, '');
  md.push('| Skill | 摘要 | 標籤 | 來源 |');
  md.push('| --- | --- | --- | --- |');
  for (const s of skills.filter((x) => x.category === cat.name)) {
    const src = s.source.displayUrl ? `[${s.source.label}](${s.source.displayUrl})` : '—';
    md.push(`| **${s.name}** | ${s.summary} | ${s.tags.join(', ')} | ${src} |`);
  }
  md.push('');
}
writeFileSync(join(API_DIR, 'skills.md'), md.join('\n'));

// GitHub Pages 不要跑 Jekyll，否則 _ 開頭的檔案會被吃掉
writeFileSync(join(DOCS_DIR, '.nojekyll'), '');

console.log(`✓ build 完成：${skills.length} 個 skill、${categories.length} 個分類、${tags.length} 個標籤`);
console.log(`  → docs/api/index.json`);
console.log(`  → docs/api/skills/*.json`);
console.log(`  → docs/llms.txt`);
if (!cfg.configured) {
  console.log('');
  console.log('! site.config.json 的 owner 還是 YOUR_GITHUB_USERNAME，');
  console.log('  改成你的 GitHub 帳號後重新 build，下載網址才會正確。');
}
