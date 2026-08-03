import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

export const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');
export const REGISTRY_DIR = join(ROOT, 'registry', 'skills');
export const SKILLS_DIR = join(ROOT, 'skills');
export const DOCS_DIR = join(ROOT, 'docs');

export function loadConfig() {
  const cfg = JSON.parse(readFileSync(join(ROOT, 'site.config.json'), 'utf8'));
  cfg.repoUrl = `https://github.com/${cfg.owner}/${cfg.repo}`;
  cfg.rawBase = `https://raw.githubusercontent.com/${cfg.owner}/${cfg.repo}/${cfg.branch}`;
  cfg.siteUrl = `https://${cfg.owner}.github.io/${cfg.repo}`;
  cfg.configured = !cfg.owner.startsWith('YOUR_');
  return cfg;
}

/** 讀出全部 registry 項目，依 name 排序 */
export function loadSkills() {
  if (!existsSync(REGISTRY_DIR)) return [];
  return readdirSync(REGISTRY_DIR)
    .filter((f) => f.endsWith('.json'))
    .map((f) => {
      const raw = readFileSync(join(REGISTRY_DIR, f), 'utf8');
      try {
        const data = JSON.parse(raw);
        data.__file = `registry/skills/${f}`;
        return data;
      } catch (err) {
        throw new Error(`registry/skills/${f} 不是合法 JSON：${err.message}`);
      }
    })
    .sort((a, b) => String(a.name).localeCompare(String(b.name), 'zh-Hant'));
}

/** 正規化：補上預設值，讓後續流程不用到處判空 */
export function normalize(skill, cfg) {
  const s = { ...skill };
  s.tags = s.tags ?? [];
  s.usage = s.usage ?? [];
  s.highlights = s.highlights ?? [];
  s.links = s.links ?? [];
  s.official = s.official ?? false;
  s.featured = s.featured ?? false;
  s.description = s.description ?? s.summary ?? '';
  s.author = s.author ?? '未註明';
  s.license = s.license ?? '未註明';
  s.install = { scope: 'user', files: ['SKILL.md'], requires: [], ...s.install };
  s.source = { branch: 'main', ...s.source };

  // 來源顯示網址
  if (s.source.kind === 'local') {
    s.source.path = s.source.path ?? `skills/${s.id}`;
    s.source.displayUrl = cfg.configured ? `${cfg.repoUrl}/tree/${cfg.branch}/${s.source.path}` : s.source.path;
    s.source.rawBase = `${cfg.rawBase}/${s.source.path}`;
    s.source.label = '本庫託管';
  } else if (s.source.kind === 'github') {
    const m = /github\.com\/([^/]+)\/([^/#?]+)/.exec(s.source.url ?? '');
    s.source.owner = m?.[1];
    s.source.name = m?.[2]?.replace(/\.git$/, '');
    const sub = s.source.subdir ? `/${s.source.subdir.replace(/^\/+/, '')}` : '';
    s.source.displayUrl = sub
      ? `https://github.com/${s.source.owner}/${s.source.name}/tree/${s.source.branch}${sub}`
      : s.source.url;
    s.source.rawBase =
      s.source.owner && s.source.name
        ? `https://raw.githubusercontent.com/${s.source.owner}/${s.source.name}/${s.source.branch}${sub}`
        : null;
    s.source.label = `${s.source.owner}/${s.source.name}`;
  } else {
    s.source.displayUrl = s.source.url;
    s.source.rawBase = null;
    s.source.label = '外部連結';
  }

  // 組合包：把每一份的路徑與下載網址算好，提示詞與前端都直接用
  s.parts = (s.parts ?? []).map((p) => {
    const rel = p.subdir ?? [s.source.subdir, p.dirName].filter(Boolean).join('/');
    return {
      ...p,
      name: p.name ?? p.dirName,
      subdir: rel,
      rawBase: baseFor(s.source, cfg, rel),
      displayUrl: viewFor(s.source, cfg, rel),
    };
  });
  // 沒有 parts 時，dirName 就是唯一的資料夾名
  s.install.dirName = s.install.dirName ?? s.parts[0]?.dirName ?? s.id;
  s.dirNames = s.parts.length ? s.parts.map((p) => p.dirName) : [s.install.dirName];

  return s;
}

/** 某個 repo 內相對路徑的 raw 下載基底 */
function baseFor(source, cfg, rel) {
  const path = rel ? `/${rel.replace(/^\/+/, '')}` : '';
  if (source.kind === 'github') {
    return source.owner && source.name
      ? `https://raw.githubusercontent.com/${source.owner}/${source.name}/${source.branch}${path}`
      : null;
  }
  if (source.kind === 'local') return `${cfg.rawBase}${path}`;
  return null;
}

/** 同上，但是給人點的瀏覽網址 */
function viewFor(source, cfg, rel) {
  const path = rel ? `/${rel.replace(/^\/+/, '')}` : '';
  if (source.kind === 'github') {
    return `https://github.com/${source.owner}/${source.name}/tree/${source.branch}${path}`;
  }
  if (source.kind === 'local') {
    return cfg.configured ? `${cfg.repoUrl}/tree/${cfg.branch}${path}` : path.replace(/^\//, '');
  }
  return source.url ?? null;
}
