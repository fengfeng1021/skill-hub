/* ==========================================================================
   Page — 靜態頁面（目前是 api.html）
   ==========================================================================
   沒有卡片、沒有篩選，只需要把 api/index.json 裡的幾個值填進畫面：
   實際網址、接口清單、summary 的好壞例子。

   刻意從 index.json 讀而不是寫死在 HTML 裡 —— build.mjs 改了規矩，
   這一頁就跟著改，不會兩邊講不一樣的話。
   ========================================================================== */

import Components from './components.js';
import Motion from './motion.js';
import { Icons } from './icons.js';
import { escapeHTML } from './skill-card.js';

const $ = (sel, root = document) => root.querySelector(sel);

async function start() {
  fillIcons();
  Components.init();

  try {
    const data = await fetch('./api/index.json', { cache: 'no-cache' }).then((r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    });
    render(data);
  } catch (err) {
    console.error('[Page] 載入 api/index.json 失敗', err);
    showError(err);
  }
}

/** HTML 裡寫 data-icon="copy"，這裡換成實際的 SVG，省得每頁貼一份 */
function fillIcons() {
  for (const node of document.querySelectorAll('[data-icon]')) {
    const svg = Icons[node.dataset.icon];
    if (svg) node.innerHTML = svg;
  }
}

function render(data) {
  const base = String(data.site?.url ?? new URL('.', location.href).href).replace(/\/+$/, '');

  renderRepoLinks(data);
  renderPrompt(data, base);
  renderEndpoints(data, base);

  const rule = data.forAI?.howToContribute ?? {};
  setText('#ruleGood', rule.summaryGood);
  setText('#ruleBad', rule.summaryBad);

  Motion.scan(document.body);
  Motion.refresh();
}

function setText(sel, text) {
  const node = $(sel);
  if (!node || !text) return;
  // mask recipe 已經把內容包進 .mask__inner 了，直接改外層的 textContent
  // 會把那層包裝一起洗掉，標題就不會由下往上刷進來。寫進裡面那層才對。
  (node.querySelector('.mask__inner') ?? node).textContent = text;
}

function renderRepoLinks(data) {
  const repo = data.site?.repo;
  for (const link of [$('#repoLink'), $('#footerRepo')]) {
    if (!link) continue;
    if (repo) {
      link.href = repo;
      link.hidden = false;
      link.style.display = '';
    } else {
      link.href = './api/index.json';
    }
  }
}

/** 使用者複製這段貼給任何一個 AI，AI 自己會把 forAI 那段規矩讀完 */
function renderPrompt(data, base) {
  const node = $('#aiPrompt');
  if (!node) return;
  const name = data.site?.name ?? 'Skill Hub';
  node.textContent = [
    `我要用「${name}」這個 Claude Skills 收藏庫，目前收錄 ${data.count ?? 0} 個。`,
    '',
    `- 網站：${base}/`,
    `- 全部資料（JSON）：${base}/api/index.json`,
    `- 純文字總覽：${base}/llms.txt`,
    `- 收錄格式：${base}/api/schema.json`,
    '',
    '請先讀 api/index.json，裡面的 forAI 欄位寫了怎麼用。接著：',
    '',
    '1. 我問有什麼 skill，就照 skills 陣列回答我，用 summary 那句白話講，不要講技術細節。',
    '2. 我說要裝哪幾個，就把那幾筆的 installPrompt 當成任務執行；',
    '   多選時把每筆的 promptBlock 接起來，前後補上 promptTemplate 的 header／footer。',
    '3. 我說找到新的 skill 要收錄，就照 forAI.howToContribute 的規矩寫進 registry，',
    '   特別是 summary 一定要「不懂程式的人看一眼就懂」的一句話。',
  ].join('\n');
}

function renderEndpoints(data, base) {
  const host = $('#endpointList');
  if (!host) return;

  const entries = Object.entries(data.forAI?.endpoints ?? {});
  if (!entries.length) {
    host.innerHTML = '<p class="faint">這份資料還沒有接口說明，跑一次 npm run build 就會有了。</p>';
    return;
  }

  // 標題的數字跟著 build 出來的接口數走，之後多一個接口不用回來改文案
  setText('#endpointHeading', `${entries.length} 個接口，各有各的用途`);

  host.innerHTML = entries
    .map(([path, desc]) => {
      // <id> 這種佔位路徑點下去是 404，只給看不給連
      const isTemplate = path.includes('<');
      const url = `${base}/${path}`;
      const link = isTemplate
        ? `<span class="endpoint__path mono">${escapeHTML(path)}</span>`
        : `<a class="endpoint__path mono" href="./${escapeHTML(path)}" target="_blank" rel="noopener">${escapeHTML(path)}</a>`;
      return `
        <article class="endpoint card" data-motion="lift">
          <div class="endpoint__head">
            ${link}
            <button class="btn btn--sm btn--ghost" data-copy="${escapeHTML(url)}"
                    data-copy-message="已複製網址" data-motion="press">
              <span class="btn__icon">${Icons.copy}</span>
              <span data-copy-label>複製網址</span>
            </button>
          </div>
          <p class="endpoint__desc">${escapeHTML(desc)}</p>
        </article>`;
    })
    .join('');

  Components.scan(host);
}

function showError(err) {
  const node = $('#aiPrompt');
  if (node) {
    node.textContent =
      '讀不到 api/index.json。還沒跑過 npm run build，或是直接用 file:// 開啟（瀏覽器會擋住 fetch）。\n' +
      `本機預覽請跑 npm run dev。\n\n${err?.message ?? err}`;
  }
  const host = $('#endpointList');
  if (host) host.innerHTML = '<p class="faint">資料載入失敗，接口清單無法顯示。</p>';
}

/* ---- GSAP 是 defer 載入的，等 DOM 與 script 都到位再啟動 ------------------ */
if (document.readyState === 'loading') {
  window.addEventListener('DOMContentLoaded', start);
} else {
  start();
}
