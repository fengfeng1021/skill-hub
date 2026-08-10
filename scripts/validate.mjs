#!/usr/bin/env node
/** 檢查 registry 資料是否合法。收錄完一定要跑過。 */
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { join, basename } from 'node:path';
import { loadConfig, loadSkills, ROOT, SKILLS_DIR } from './lib/registry.mjs';

const cfg = loadConfig();
const skills = loadSkills();

const errors = [];
const warnings = [];
const seen = new Map();
const allIds = new Set(skills.map((s) => s.id).filter(Boolean));

const REQUIRED = ['id', 'name', 'summary', 'category', 'tags', 'source', 'install'];
const DIR_NAME = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;

/**
 * summary 是卡片上唯一會被看到的說明，必須白話到不需要任何專業知識就看得懂。
 * 這裡只能用啟發式抓明顯的違規：太長、術語、以及「名詞：A、B、C」這種功能羅列。
 * 抓到就提醒改寫，不擋 build。
 */
const JARGON = [
  'API', 'SDK', 'CLI', 'frontmatter', 'plugin', 'runtime', 'hook', 'repo',
  '函式庫', '外掛', '框架', '套件', '模組', '參數', '介面', '編排', '實例', '非同步',
];
const PLAIN_MAX = 25;

function checkPlainSummary(at, summary) {
  if (!summary) return;
  const len = [...summary].length;
  if (len > PLAIN_MAX) {
    warnings.push(`${at}：summary 有 ${len} 字，白話一句話建議 ${PLAIN_MAX} 字內，太長就不好懂了`);
  }
  const hits = JARGON.filter((w) => summary.toLowerCase().includes(w.toLowerCase()));
  if (hits.length) {
    warnings.push(`${at}：summary 出現術語「${hits.join('、')}」，改寫成不懂程式的人也看得懂的講法，技術細節放 description`);
  }
  if (/[：:]/.test(summary)) {
    warnings.push(`${at}：summary 用「名詞：功能一、功能二」的羅列寫法，改成一句完整的話講「能幫我做到什麼」`);
  }
}

for (const s of skills) {
  const at = s.__file;

  for (const key of REQUIRED) {
    if (s[key] === undefined || s[key] === null || s[key] === '') {
      errors.push(`${at}：缺少必填欄位 ${key}`);
    }
  }
  if (!s.id) continue;

  if (!/^[a-z0-9][a-z0-9-]*$/.test(s.id)) {
    errors.push(`${at}：id "${s.id}" 必須是小寫 kebab-case`);
  }
  if (basename(at, '.json') !== s.id) {
    errors.push(`${at}：檔名必須與 id 一致（應為 ${s.id}.json）`);
  }
  if (seen.has(s.id)) {
    errors.push(`${at}：id "${s.id}" 與 ${seen.get(s.id)} 重複`);
  }
  seen.set(s.id, at);

  checkPlainSummary(at, s.summary);
  for (const p of s.parts ?? []) {
    if (p?.summary) checkPlainSummary(`${at}（parts ${p.dirName}）`, p.summary);
  }
  if (!Array.isArray(s.tags) || s.tags.length === 0) {
    warnings.push(`${at}：沒有 tags，篩選時找不到`);
  }

  // source
  const kind = s.source?.kind;
  if (!['github', 'local', 'url'].includes(kind)) {
    errors.push(`${at}：source.kind 必須是 github / local / url，目前是 "${kind}"`);
  }
  if (kind === 'github') {
    if (!/^https:\/\/github\.com\/[^/]+\/[^/]+/.test(s.source.url ?? '')) {
      errors.push(`${at}：source.url 不是合法的 GitHub repo 網址`);
    }
  }
  if (kind === 'url' && !/^https?:\/\//.test(s.source.url ?? '')) {
    errors.push(`${at}：source.url 必須是 http(s) 網址`);
  }
  if (kind === 'local') {
    const rel = s.source.path ?? `skills/${s.id}`;
    const dir = join(ROOT, rel);
    if (!existsSync(dir)) {
      errors.push(`${at}：source.kind=local 但找不到資料夾 ${rel}/`);
    } else if (s.parts?.length) {
      // local + parts 組合包：每個 part 資料夾都要有 SKILL.md，dirName 與 frontmatter name 一致
      for (const p of s.parts) {
        const pDir = join(dir, p.dirName);
        if (!existsSync(join(pDir, 'SKILL.md'))) {
          errors.push(`${at}：${rel}/${p.dirName}/ 底下沒有 SKILL.md`);
          continue;
        }
        const md = readFileSync(join(pDir, 'SKILL.md'), 'utf8');
        const fm = /^---\r?\n([\s\S]*?)\r?\n---/.exec(md);
        if (!fm) {
          errors.push(`${at}：${rel}/${p.dirName}/SKILL.md 沒有 frontmatter（--- 區塊）`);
          continue;
        }
        const nameLine = /^name:\s*(.+)$/m.exec(fm[1]);
        const descLine = /^description:\s*(.+)$/m.exec(fm[1]);
        if (!nameLine) errors.push(`${at}：${rel}/${p.dirName}/SKILL.md frontmatter 缺少 name`);
        if (!descLine) errors.push(`${at}：${rel}/${p.dirName}/SKILL.md frontmatter 缺少 description`);
        const mdName = nameLine?.[1].trim().replace(/^["']|["']$/g, '');
        if (mdName && mdName !== p.dirName) {
          errors.push(
            `${at}：parts 的 dirName "${p.dirName}" 與 SKILL.md 的 name "${mdName}" 不一致，AI 會載入不到`
          );
        }
      }
      // install.files 是「每個資料夾都要拿的檔案」清單，逐一對照每個 part 資料夾
      for (const f of s.install?.files ?? []) {
        for (const p of s.parts) {
          if (!existsSync(join(dir, p.dirName, f))) {
            warnings.push(`${at}：install.files 列了 ${f}，但 ${rel}/${p.dirName}/${f} 不存在`);
          }
        }
      }
    } else if (!existsSync(join(dir, 'SKILL.md'))) {
      errors.push(`${at}：${rel}/ 底下沒有 SKILL.md`);
    } else {
      // dirName 應與 SKILL.md frontmatter 的 name 一致，否則 AI 載入不到
      const md = readFileSync(join(dir, 'SKILL.md'), 'utf8');
      const fm = /^---\r?\n([\s\S]*?)\r?\n---/.exec(md);
      if (!fm) {
        errors.push(`${at}：${rel}/SKILL.md 沒有 frontmatter（--- 區塊）`);
      } else {
        const nameLine = /^name:\s*(.+)$/m.exec(fm[1]);
        const descLine = /^description:\s*(.+)$/m.exec(fm[1]);
        if (!nameLine) errors.push(`${at}：${rel}/SKILL.md frontmatter 缺少 name`);
        if (!descLine) errors.push(`${at}：${rel}/SKILL.md frontmatter 缺少 description`);
        const mdName = nameLine?.[1].trim().replace(/^["']|["']$/g, '');
        if (mdName && s.install?.dirName && mdName !== s.install.dirName) {
          errors.push(
            `${at}：install.dirName "${s.install.dirName}" 與 SKILL.md 的 name "${mdName}" 不一致，AI 會載入不到`
          );
        }
      }
      // 對照 install.files 是否真的存在
      for (const f of s.install?.files ?? []) {
        if (!existsSync(join(dir, f))) {
          warnings.push(`${at}：install.files 列了 ${f}，但 ${rel}/${f} 不存在`);
        }
      }
    }
  }

  // 組合包（parts）用 parts[].dirName，單一 skill 用 install.dirName，兩者至少要有一個
  const parts = s.parts;
  if (parts !== undefined) {
    if (!Array.isArray(parts) || parts.length === 0) {
      errors.push(`${at}：parts 必須是至少一個項目的陣列，只有一個資料夾的 skill 請直接刪掉 parts`);
    } else {
      if (parts.length === 1) {
        warnings.push(`${at}：parts 只有一個項目，用 install.dirName 就好`);
      }
      const dirs = new Set();
      for (const p of s.parts) {
        if (!p?.dirName) {
          errors.push(`${at}：parts 裡有項目缺少 dirName`);
          continue;
        }
        if (!DIR_NAME.test(p.dirName)) {
          errors.push(`${at}：parts 的 dirName "${p.dirName}" 含有不適合當資料夾名的字元`);
        }
        if (dirs.has(p.dirName)) errors.push(`${at}：parts 的 dirName "${p.dirName}" 重複`);
        dirs.add(p.dirName);
      }
    }
  } else if (!s.install?.dirName) {
    errors.push(`${at}：缺少 install.dirName（安裝後的資料夾名）`);
  }
  if (s.install?.dirName && !DIR_NAME.test(s.install.dirName)) {
    errors.push(`${at}：install.dirName "${s.install.dirName}" 含有不適合當資料夾名的字元`);
  }
  if (s.install?.scope && !['user', 'project'].includes(s.install.scope)) {
    errors.push(`${at}：install.scope 必須是 user 或 project`);
  }

  // 精選組合包（includes）引用其他收錄項目；它不是 parts，也不是 install.requires。
  if (s.includes !== undefined) {
    if (!Array.isArray(s.includes) || s.includes.length === 0) {
      errors.push(`${at}：includes 必須是至少一個 registry id 的陣列；不是組合包就刪掉 includes`);
    } else {
      const ids = new Set();
      for (const id of s.includes) {
        if (typeof id !== 'string' || !/^[a-z0-9][a-z0-9-]*$/.test(id)) {
          errors.push(`${at}：includes 的值 "${id}" 不是合法的 registry id`);
          continue;
        }
        if (id === s.id) errors.push(`${at}：includes 不能引用自己`);
        if (ids.has(id)) errors.push(`${at}：includes 的 registry id "${id}" 重複`);
        if (!allIds.has(id)) errors.push(`${at}：includes 引用了不存在的 registry id "${id}"`);
        ids.add(id);
      }
    }
  }
}

// 避免 A 包 B、B 又包 A。建置雖會去重，資料語意仍然是錯的，必須擋下來。
const visiting = new Set();
const visited = new Set();
const byId = new Map(skills.map((s) => [s.id, s]));
function detectIncludeCycle(id, path = []) {
  if (visiting.has(id)) {
    errors.push(`精選組合包 includes 形成循環：${[...path, id].join(' → ')}`);
    return;
  }
  if (visited.has(id)) return;
  visiting.add(id);
  const item = byId.get(id);
  for (const child of Array.isArray(item?.includes) ? item.includes : []) {
    if (byId.has(child)) detectIncludeCycle(child, [...path, id]);
  }
  visiting.delete(id);
  visited.add(id);
}
for (const id of byId.keys()) detectIncludeCycle(id);

// skills/ 底下有資料夾卻沒收錄
if (existsSync(SKILLS_DIR)) {
  const registered = new Set(skills.filter((s) => s.source?.kind === 'local').map((s) => s.source.path ?? `skills/${s.id}`));
  for (const d of readdirSync(SKILLS_DIR, { withFileTypes: true })) {
    if (d.isDirectory() && !registered.has(`skills/${d.name}`)) {
      warnings.push(`skills/${d.name}/ 存在但沒有對應的 registry 項目，不會出現在網站上`);
    }
  }
}

if (!cfg.configured) {
  warnings.push('site.config.json 的 owner 還是 YOUR_GITHUB_USERNAME，安裝提示詞裡的下載網址會是錯的');
}

for (const w of warnings) console.log(`⚠ ${w}`);
for (const e of errors) console.log(`✗ ${e}`);

console.log('');
if (errors.length) {
  console.log(`驗證失敗：${errors.length} 個錯誤、${warnings.length} 個警告`);
  process.exit(1);
}
console.log(`✓ 驗證通過：${skills.length} 個 skill、${warnings.length} 個警告`);
