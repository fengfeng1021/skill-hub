#!/usr/bin/env node
/** 本機預覽 docs/：node scripts/serve.mjs [port] */
import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { join, extname, normalize as normalizePath } from 'node:path';
import { DOCS_DIR } from './lib/registry.mjs';

const port = Number(process.argv[2]) || 4321;
const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.webp': 'image/webp',
  '.ico': 'image/x-icon',
};

createServer(async (req, res) => {
  try {
    let path = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    if (path.endsWith('/')) path += 'index.html';
    // 擋住 ../ 逃逸
    const rel = normalizePath(path).replace(/^([/\\])+/, '');
    if (rel.split(/[/\\]/).includes('..')) {
      res.writeHead(403).end('Forbidden');
      return;
    }
    const file = join(DOCS_DIR, rel);
    const info = await stat(file);
    const target = info.isDirectory() ? join(file, 'index.html') : file;
    const body = await readFile(target);
    res.writeHead(200, {
      'Content-Type': TYPES[extname(target)] ?? 'application/octet-stream',
      'Cache-Control': 'no-store',
    });
    res.end(body);
  } catch {
    res.writeHead(404, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end('<h1>404</h1><p>找不到這個檔案。忘記跑 <code>npm run build</code> 了嗎？</p>');
  }
}).listen(port, () => {
  console.log(`預覽網站：http://localhost:${port}/`);
  console.log(`元件與動效總覽：http://localhost:${port}/design-system.html`);
  console.log(`JSON 接口：http://localhost:${port}/api/index.json`);
  console.log('Ctrl+C 結束');
});
