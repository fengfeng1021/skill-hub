#!/usr/bin/env node
/**
 * 用一行指令新增／更新 registry 項目。給 AI 收錄時用。
 *
 * 範例：
 *   node scripts/add-skill.mjs \
 *     --id gsap-core --name "GSAP Core" \
 *     --summary "GSAP 核心動畫 API，tween、easing、stagger" \
 *     --category "前端 / 動效" --tags animation,gsap,frontend \
 *     --github https://github.com/greensock/gsap --subdir skills/gsap-core \
 *     --dir-name gsap-core --files SKILL.md
 *
 *   node scripts/add-skill.mjs --id my-skill --name "我的 Skill" \
 *     --summary "..." --category "自製" --tags custom --local
 *
 *   # 跨來源精選組合包（值是已存在的 registry id）
 *   node scripts/add-skill.mjs --id my-bundle --includes skill-a,skill-b,skill-c
 *
 * 未提供的欄位會沿用既有檔案的值（等於「部分更新」）。
 */
import { writeFileSync, existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { REGISTRY_DIR, ROOT } from './lib/registry.mjs';

const argv = process.argv.slice(2);
const args = {};
for (let i = 0; i < argv.length; i++) {
  if (!argv[i].startsWith('--')) continue;
  const key = argv[i].slice(2);
  const next = argv[i + 1];
  if (next === undefined || next.startsWith('--')) {
    args[key] = true;
  } else {
    args[key] = next;
    i++;
  }
}

if (args.help || !args.id) {
  console.log(readFileSync(new URL(import.meta.url)).toString().split('*/')[0].replace('#!/usr/bin/env node\n/**', ''));
  process.exit(args.id ? 0 : 1);
}

const id = String(args.id).trim();
if (!/^[a-z0-9][a-z0-9-]*$/.test(id)) {
  console.error(`✗ id "${id}" 必須是小寫 kebab-case`);
  process.exit(1);
}

const file = join(REGISTRY_DIR, `${id}.json`);
const existing = existsSync(file) ? JSON.parse(readFileSync(file, 'utf8')) : null;
const today = new Date().toISOString().slice(0, 10);
const list = (v) => (v ? String(v).split(',').map((x) => x.trim()).filter(Boolean) : undefined);

const entry = {
  id,
  name: args.name ?? existing?.name ?? id,
  summary: args.summary ?? existing?.summary ?? '',
  description: args.description ?? existing?.description ?? '',
  category: args.category ?? existing?.category ?? '未分類',
  tags: list(args.tags) ?? existing?.tags ?? [],
  author: args.author ?? existing?.author,
  license: args.license ?? existing?.license,
  version: args.version ?? existing?.version,
  official: args.official ? true : existing?.official ?? false,
  featured: args.featured ? true : existing?.featured ?? false,
  source: existing?.source ?? {},
  install: existing?.install ?? {},
  parts: existing?.parts,
  includes: list(args.includes) ?? existing?.includes,
  usage: list(args.usage) ?? existing?.usage ?? [],
  highlights: list(args.highlights) ?? existing?.highlights ?? [],
  prompt: existing?.prompt ?? null,
  links: existing?.links ?? [],
  addedAt: existing?.addedAt ?? today,
  updatedAt: today,
};

if (args.github) {
  entry.source = {
    kind: 'github',
    url: String(args.github).replace(/\/+$/, ''),
    ...(args.subdir ? { subdir: String(args.subdir).replace(/^\/+|\/+$/g, '') } : {}),
    branch: args.branch ?? entry.source.branch ?? 'main',
  };
} else if (args.local) {
  entry.source = { kind: 'local', path: args.path ?? `skills/${id}` };
} else if (args.url) {
  entry.source = { kind: 'url', url: String(args.url) };
}

entry.install = {
  dirName: args['dir-name'] ?? entry.install.dirName ?? id,
  ...(entry.install.command ? { command: entry.install.command } : {}),
  scope: args.scope ?? entry.install.scope ?? 'user',
  files: list(args.files) ?? entry.install.files ?? ['SKILL.md'],
  requires: list(args.requires) ?? entry.install.requires ?? [],
  ...(args.notes ? { notes: args.notes } : entry.install.notes ? { notes: entry.install.notes } : {}),
};

// 移除 undefined，保持 JSON 乾淨
for (const k of Object.keys(entry)) if (entry[k] === undefined) delete entry[k];

if (!entry.source.kind) {
  console.error('✗ 必須指定來源：--github <repo網址> [--subdir 路徑] / --local / --url <網址>');
  process.exit(1);
}
if (!entry.summary) {
  console.error('✗ 必須提供 --summary（一句話摘要，繁中，40 字內）');
  process.exit(1);
}

writeFileSync(file, JSON.stringify(entry, null, 2) + '\n');
console.log(`${existing ? '✓ 已更新' : '✓ 已新增'} registry/skills/${id}.json`);
console.log(`  ${entry.name}｜${entry.category}｜${entry.tags.join(', ')}`);
console.log('');
console.log('接著跑：npm run validate && npm run build');
