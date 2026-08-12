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
import { writeFileSync, readFileSync, mkdirSync, rmSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { loadConfig, loadSkills, normalize, DOCS_DIR, ROOT } from './lib/registry.mjs';
import {
  buildHeader,
  buildFooter,
  buildBlock,
  buildPromptBlock,
  buildInstallPrompt,
  isPortableCommand,
} from './lib/prompt.mjs';

const cfg = loadConfig();
const raw = loadSkills();
const skills = raw.map((s) => normalize(s, cfg));
const skillById = new Map(skills.map((s) => [s.id, s]));

/** includes 可再引用其他精選組合包；建置時攤平並去重，順序跟 registry 宣告一致。 */
function expandIncludes(skill) {
  const out = [];
  const visited = new Set([skill.id]);
  const visit = (id) => {
    if (visited.has(id)) return;
    visited.add(id);
    const item = skillById.get(id);
    if (!item) return; // validate 會給維護者明確錯誤；build 保持可診斷
    out.push(item);
    for (const childId of item.includes ?? []) visit(childId);
  };
  for (const id of skill.includes ?? []) visit(id);
  return out;
}

const API_DIR = join(DOCS_DIR, 'api');
const API_SKILLS_DIR = join(API_DIR, 'skills');
if (existsSync(API_SKILLS_DIR)) rmSync(API_SKILLS_DIR, { recursive: true, force: true });
mkdirSync(API_SKILLS_DIR, { recursive: true });

// 每個 skill 補上組合包資訊與提示詞欄位
for (const s of skills) {
  const included = expandIncludes(s);
  const installItems = [s, ...included];
  s.includedSkills = included.map((item) => ({
    id: item.id,
    name: item.name,
    summary: item.summary,
    category: item.category,
    folderCount: item.dirNames.length,
    dirNames: item.dirNames,
  }));
  s.installIds = installItems.map((item) => item.id);
  s.installCount = installItems.length;
  s.installFolderCount = installItems.reduce((total, item) => total + item.dirNames.length, 0);
  s.promptBlockSingle = buildBlock(s);
  s.promptBlock = buildPromptBlock(s, included);
  s.installPrompt = buildInstallPrompt(s, included);
  // 固定 Agent／固定目錄的來源命令只留在 registry 供維護者參考，
  // 不發布到跨 Agent API，也不在網站上誘導使用者原樣執行。
  if (s.install.command && !isPortableCommand(s.install.command)) delete s.install.command;
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

/**
 * 給「讀這份 JSON 的 AI」看的說明。
 * 別的 AI 想幫使用者裝 skill、或想幫忙收錄新的 skill，只要讀到這一段就知道規矩，
 * 不必先去翻 repo 裡的 CLAUDE.md。
 */
const forAI = {
  whatIsThis: `${cfg.name} 是一個跨 Agent 的 Skills 收藏庫。每一筆 skill 都附了環境自適應的安裝提示詞，會先辨識目前 Agent 的官方 skill 機制，再選擇正確的安裝方式。`,
  endpoints: {
    'api/index.json': '全部資料：站台資訊、分類、標籤、每個 skill 的完整欄位與 installPrompt。',
    'api/skills/<id>.json': '單一 skill 的完整資料。',
    'api/tags.json': '分類與標籤統計。',
    'api/schema.json': 'registry 項目的 JSON Schema，要新增收錄時照這個格式寫。',
    'llms.txt': '純文字總覽，適合整份貼給 AI。',
  },
  howToInstall:
    '使用者說要裝哪幾個，就把對應 skill 的 installPrompt 欄位當成任務執行；' +
    '多選時先合併並去重每筆的 installIds，再把對應項目的 promptBlockSingle 依序接起來，' +
    '前後補上 promptTemplate.header／footer，中間用 promptTemplate.separator 分隔。',
  howToContribute: {
    where: 'registry/skills/<id>.json，格式見 api/schema.json。改完跑 npm run validate && npm run build。',
    language: '所有面向使用者的文字都用繁體中文（台灣用語）。',
    summaryRule:
      'summary 是卡片上唯一會被看到的說明，必須是「不需要任何專業知識就看得懂的一句話」：' +
      '25 字內，只講能幫使用者做到什麼，不要出現 API／函式庫／外掛／框架／frontmatter 這類術語，' +
      '也不要寫成「名稱：功能一、功能二」的羅列。技術細節一律寫進 description。',
    summaryGood: '讓網頁上的東西動起來，淡入、滑動、跟著捲動變化都能做。',
    summaryBad: 'GreenSock 官方動畫 skill 全套：tween、時間軸、ScrollTrigger、外掛與效能。',
    bundles:
      '同來源套件拆成多個資料夾（例如 GSAP 的 8 份）用 parts；跨來源、由入口 skill 統籌的精選組合包用 includes。' +
      'includes 會展開成完整安裝清單，不能寫進 install.requires 假裝成可選相依。',
    workflows:
      'includes 只表示要一起安裝哪些收錄項目；入口若能自動分階段執行，另用 runtime 描述 mode、狀態檔、stages、overlays 與 finalizers。' +
      'runtime 裡引用的 skill 必須已被 includes 的完整安裝清單涵蓋，真正的路由、Gate、回退與續跑規則寫在入口 SKILL.md。',
    migrations:
      'skill 改過資料夾或 frontmatter name 時，用 replaces 列出舊名稱。安裝提示詞會先比對自訂修改，驗證新版成功後才安全停用無自訂的舊入口，避免兩份同時觸發。',
  },
};

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
  forAI,
  promptTemplate: {
    header: buildHeader(1),
    headerPlural: buildHeader('{{count}}'), // 前端把 {{count}} 換成實際數量
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

// registry 格式一起發佈，別的 AI 要幫忙收錄時可以直接讀
writeFileSync(join(API_DIR, 'schema.json'), readFileSync(join(ROOT, 'registry', 'schema.json'), 'utf8'));

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
  '每個 skill 底下都有「安裝提示詞」段落。使用者說要裝哪幾個，就把對應段落的內容當作任務執行：',
  '先辨識目前 Agent 的官方 skill 機制與支援範圍，再把資料夾安裝到它實際使用的位置；不要預設品牌或猜測路徑。資料夾名與 SKILL.md 的 frontmatter 不要改。',
  '完整、可直接貼給 AI 的安裝提示詞在 `api/skills/<id>.json` 的 `installPrompt` 欄位。',
  '',
  '## 要幫忙收錄新的 skill 的話',
  '',
  '資料寫在 `registry/skills/<id>.json`，格式見 `api/schema.json`，改完跑 `npm run validate && npm run build`。',
  '',
  `**摘要（summary）的寫法**：${forAI.howToContribute.summaryRule}`,
  '',
  `- 好的寫法：${forAI.howToContribute.summaryGood}`,
  `- 不好的寫法：${forAI.howToContribute.summaryBad}`,
  `- ${forAI.howToContribute.bundles}`,
  `- ${forAI.howToContribute.workflows}`,
  `- ${forAI.howToContribute.migrations}`,
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
      llms.push(`- 同來源套件含 ${s.parts.length} 個資料夾，要一起裝：${s.parts.map((p) => `\`${p.dirName}\``).join('、')}`);
    } else {
      llms.push(`- 安裝資料夾名：\`${s.install.dirName}\``);
    }
    if (s.includedSkills.length) {
      llms.push(`- 精選組合包：連同入口共 ${s.installCount} 個收錄項目、${s.installFolderCount} 個資料夾`);
      llms.push(`- 組合內容：${s.includedSkills.map((item) => `\`${item.name}\``).join('、')}`);
    }
    if (s.runtime) {
      llms.push(`- 執行模式：${s.runtime.mode}`);
      if (s.runtime.stateArtifact) llms.push(`- 續跑狀態：\`${s.runtime.stateArtifact}\``);
      if (s.runtime.stages?.length) {
        llms.push(`- 工作流階段：${s.runtime.stages.map((stage) => stage.name).join(' → ')}`);
      }
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
console.log(`  → docs/api/schema.json`);
console.log(`  → docs/llms.txt`);
if (!cfg.configured) {
  console.log('');
  console.log('! site.config.json 的 owner 還是 YOUR_GITHUB_USERNAME，');
  console.log('  改成你的 GitHub 帳號後重新 build，下載網址才會正確。');
}
