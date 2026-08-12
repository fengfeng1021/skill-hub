#!/usr/bin/env node
/** 檢查 registry 資料是否合法。收錄完一定要跑過。 */
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
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
const RELATIVE_PATH = /^(?!\/)(?![A-Za-z]:[\\/])(?!.*(?:^|[\\/])\.\.(?:[\\/]|$))[^\\]+$/;

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
      for (const d of s.install?.directories ?? []) {
        for (const p of s.parts) {
          const target = join(dir, p.dirName, d);
          if (!existsSync(target) || !statSync(target).isDirectory()) {
            warnings.push(`${at}：install.directories 列了 ${d}，但 ${rel}/${p.dirName}/${d}/ 不存在`);
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
      for (const d of s.install?.directories ?? []) {
        const target = join(dir, d);
        if (!existsSync(target) || !statSync(target).isDirectory()) {
          warnings.push(`${at}：install.directories 列了 ${d}，但 ${rel}/${d}/ 不存在`);
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
  for (const field of ['files', 'directories']) {
    const values = s.install?.[field];
    if (values !== undefined && !Array.isArray(values)) {
      errors.push(`${at}：install.${field} 必須是陣列`);
      continue;
    }
    const seenPaths = new Set();
    for (const value of values ?? []) {
      if (typeof value !== 'string' || !value || !RELATIVE_PATH.test(value) || value.endsWith('/')) {
        errors.push(`${at}：install.${field} 的「${value}」必須是使用 / 分隔、不含 .. 且不以 / 結尾的相對路徑`);
        continue;
      }
      if (seenPaths.has(value)) errors.push(`${at}：install.${field} 的路徑「${value}」重複`);
      seenPaths.add(value);
    }
  }
  const installFiles = new Set(s.install?.files ?? []);
  const installDirectories = new Set(s.install?.directories ?? []);
  for (const directory of installDirectories) {
    for (const file of installFiles) {
      if (file === directory || file.startsWith(`${directory}/`)) {
        errors.push(`${at}：install.files 的 ${file} 已被 install.directories 的 ${directory}/ 涵蓋，不能重複列出`);
      }
    }
    for (const other of installDirectories) {
      if (other !== directory && other.startsWith(`${directory}/`)) {
        errors.push(`${at}：install.directories 的 ${directory}/ 已涵蓋 ${other}/，不能重複列出巢狀目錄`);
      }
    }
  }
  if ((s.install?.directories?.length ?? 0) > 0 && s.source?.kind !== 'github' && s.source?.kind !== 'local') {
    errors.push(`${at}：install.directories 只支援 github 或 local 來源`);
  }
  if (s.replaces !== undefined) {
    if (!Array.isArray(s.replaces) || s.replaces.length === 0) {
      errors.push(`${at}：replaces 必須是至少一個舊資料夾／frontmatter name 的陣列`);
    } else {
      const oldNames = new Set();
      for (const oldName of s.replaces) {
        if (typeof oldName !== 'string' || !DIR_NAME.test(oldName)) {
          errors.push(`${at}：replaces 的值 "${oldName}" 不是合法的舊 Skill 名稱`);
        }
        if (oldName === s.install?.dirName) errors.push(`${at}：replaces 不能等於目前 install.dirName`);
        if (oldNames.has(oldName)) errors.push(`${at}：replaces 的舊名稱 "${oldName}" 重複`);
        oldNames.add(oldName);
      }
    }
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

  // runtime 描述執行順序；所有 skill 引用都必須是 registry id，pipeline 必須有階段與 Gate。
  if (s.runtime !== undefined) {
    const runtime = s.runtime;
    const modes = ['pipeline', 'router', 'overlay', 'standalone'];
    if (!runtime || typeof runtime !== 'object' || Array.isArray(runtime)) {
      errors.push(`${at}：runtime 必須是物件`);
    } else {
      if (!modes.includes(runtime.mode)) {
        errors.push(`${at}：runtime.mode 必須是 ${modes.join(' / ')}，目前是 "${runtime.mode}"`);
      }
      if (runtime.stateArtifact !== undefined &&
          (typeof runtime.stateArtifact !== 'string' || runtime.stateArtifact.startsWith('/') || /^[A-Za-z]:[\\/]/.test(runtime.stateArtifact))) {
        errors.push(`${at}：runtime.stateArtifact 必須是專案相對路徑`);
      }
      if (runtime.controller !== undefined) {
        for (const key of ['script', 'stateSchema']) {
          const value = runtime.controller?.[key];
          if (typeof value !== 'string' || !value || value.startsWith('/') || /^[A-Za-z]:[\\/]/.test(value) || value.split(/[\\/]/).includes('..')) {
            errors.push(`${at}：runtime.controller.${key} 必須是入口 skill 內的相對路徑`);
          } else if (s.source?.kind === 'local') {
            const rel = s.source.path ?? `skills/${s.id}`;
            if (!existsSync(join(ROOT, rel, value))) {
              errors.push(`${at}：runtime.controller.${key} 指向不存在的檔案 ${rel}/${value}`);
            }
            if (!new Set(s.install?.files ?? []).has(value)) {
              errors.push(`${at}：runtime.controller.${key} 使用 ${value}，但 install.files 沒有包含它`);
            }
          }
        }
      }
      if (runtime.mode === 'pipeline' && (!Array.isArray(runtime.stages) || runtime.stages.length === 0)) {
        errors.push(`${at}：runtime.mode=pipeline 時必須有至少一個 stage`);
      }
      if (runtime.stages !== undefined && !Array.isArray(runtime.stages)) {
        errors.push(`${at}：runtime.stages 必須是陣列`);
      }
      const stageIds = new Set();
      for (const stage of Array.isArray(runtime.stages) ? runtime.stages : []) {
        if (!stage?.id || !/^[a-z0-9][a-z0-9-]*$/.test(stage.id)) {
          errors.push(`${at}：runtime stage 缺少合法的 kebab-case id`);
        } else if (stageIds.has(stage.id)) {
          errors.push(`${at}：runtime stage id "${stage.id}" 重複`);
        }
        if (stage?.id) stageIds.add(stage.id);
        if (!stage?.name) errors.push(`${at}：runtime stage "${stage?.id ?? '?'}" 缺少 name`);
        if (!stage?.gate) errors.push(`${at}：runtime stage "${stage?.id ?? '?'}" 缺少 gate`);
        if (!Array.isArray(stage?.skills)) {
          errors.push(`${at}：runtime stage "${stage?.id ?? '?'}" 的 skills 必須是陣列`);
        }
        const requiredCount = Array.isArray(stage?.skills) ? stage.skills.length : 0;
        const optionalCount = Array.isArray(stage?.optionalSkills) ? stage.optionalSkills.length : 0;
        const coreCount = Array.isArray(stage?.coreReferences) ? stage.coreReferences.length : 0;
        if (requiredCount + optionalCount + coreCount === 0) {
          errors.push(`${at}：runtime stage "${stage?.id ?? '?'}" 必須指定至少一個必要 skill、可選 skill 或內建 reference`);
        }
        for (const reference of Array.isArray(stage?.coreReferences) ? stage.coreReferences : []) {
          if (typeof reference !== 'string' || !reference || reference.startsWith('/') || /^[A-Za-z]:[\\/]/.test(reference) || reference.split(/[\\/]/).includes('..')) {
            errors.push(`${at}：runtime stage "${stage?.id ?? '?'}" 的 coreReference 必須是相對路徑`);
          } else if (s.source?.kind === 'local') {
            const rel = s.source.path ?? `skills/${s.id}`;
            if (!existsSync(join(ROOT, rel, reference))) {
              errors.push(`${at}：runtime stage "${stage?.id ?? '?'}" 引用了不存在的 ${rel}/${reference}`);
            }
            if (!new Set(s.install?.files ?? []).has(reference)) {
              errors.push(`${at}：runtime stage "${stage?.id ?? '?'}" 使用 ${reference}，但 install.files 沒有包含它`);
            }
          }
        }
      }
      const runtimeRefs = [
        ...(Array.isArray(runtime.stages) ? runtime.stages.flatMap((stage) => [
          ...(Array.isArray(stage?.skills) ? stage.skills : []),
          ...(Array.isArray(stage?.optionalSkills) ? stage.optionalSkills : []),
        ]) : []),
        ...(Array.isArray(runtime.overlays) ? runtime.overlays : []),
        ...(Array.isArray(runtime.finalizers) ? runtime.finalizers : []),
      ];
      for (const id of runtimeRefs) {
        if (typeof id !== 'string' || !/^[a-z0-9][a-z0-9-]*$/.test(id)) {
          errors.push(`${at}：runtime skill 引用 "${id}" 不是合法的 registry id`);
        } else if (!allIds.has(id)) {
          errors.push(`${at}：runtime 引用了不存在的 registry id "${id}"`);
        }
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

// 必要 runtime 能力必須由安裝清單涵蓋。portableCore 階段若有內建 reference，
// optionalSkills 可以只做「已安裝才加強」的能力發現，避免為了一個入口暴露大量子 Skill。
function expandedIncludeIds(skill) {
  const out = new Set();
  const visit = (id) => {
    if (out.has(id)) return;
    out.add(id);
    const item = byId.get(id);
    for (const child of Array.isArray(item?.includes) ? item.includes : []) visit(child);
  };
  for (const id of Array.isArray(skill?.includes) ? skill.includes : []) visit(id);
  return out;
}
for (const skill of skills) {
  if (!skill.runtime) continue;
  const installed = expandedIncludeIds(skill);
  const refs = [
    ...(Array.isArray(skill.runtime.stages) ? skill.runtime.stages.flatMap((stage) => [
      ...(Array.isArray(stage?.skills) ? stage.skills : []),
      ...(
        skill.runtime.portableCore && Array.isArray(stage?.coreReferences) && stage.coreReferences.length
          ? []
          : (Array.isArray(stage?.optionalSkills) ? stage.optionalSkills : [])
      ),
    ]) : []),
    ...(Array.isArray(skill.runtime.overlays) ? skill.runtime.overlays : []),
    ...(Array.isArray(skill.runtime.finalizers) ? skill.runtime.finalizers : []),
  ];
  for (const ref of new Set(refs)) {
    if (ref !== skill.id && byId.has(ref) && !installed.has(ref)) {
      errors.push(`${skill.__file}：runtime 必須使用 "${ref}"，但 includes 的完整安裝清單沒有涵蓋它`);
    }
  }
}

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
