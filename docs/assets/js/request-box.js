/* ==========================================================================
   Request Box — 「幫我收這個 skill」提示詞產生器
   ==========================================================================
   使用者手上通常只有兩種東西：一個名字，或一張連結。這一塊把它變成一段
   可以直接貼給 AI 的話 —— 查證出處、寫 registry、驗證、build 全部交給 AI，
   使用者不用開專案、不用碰 JSON。

   三個頁面共用，掛在 [data-request-box] 上。提示詞裡的網址一律用 api/index.json
   的 site.url（也就是發佈後的網址）—— 本機預覽時也一樣，因為 AI 要連得到才讀得到。
   ========================================================================== */

import Components from './components.js';
import Motion from './motion.js';
import { Icons } from './icons.js';

const MODES = new Set(['catalog', 'install']);

/**
 * @param {Element} root  .request-box 節點
 * @param {{name?: string, url?: string|null, repo?: string|null}} site
 */
export function mountRequestBox(root, site = {}) {
  if (!root || root.dataset.requestReady === '1') return;
  root.dataset.requestReady = '1';

  // 圖示在這裡填，四個頁面的 HTML 就不用各貼一份 SVG
  for (const node of root.querySelectorAll('[data-icon]')) {
    const svg = Icons[node.dataset.icon];
    if (svg) node.innerHTML = svg;
  }

  const input = root.querySelector('[data-request-input]');
  const output = root.querySelector('[data-request-output]');
  const kind = root.querySelector('[data-request-kind]');
  const copyBtn = root.querySelector('[data-request-copy]');
  const modeGroup = root.querySelector('[data-request-mode]');
  if (!input || !output) return;

  const base = String(site.url || new URL('.', location.href).href).replace(/\/+$/, '');
  const repo = site.repo || `${base}（原始碼位置請問使用者）`;
  const name = site.name || 'Skill Hub';

  let mode = 'catalog';
  let text = '';
  let painted = false;

  function update() {
    const raw = input.value.trim();
    const target = parseTarget(raw);
    text = buildPrompt({ target, mode, base, repo, name });

    if (kind) kind.textContent = KIND_LABEL[target.kind];
    root.classList.toggle('is-empty', target.kind === 'empty');
    if (copyBtn) copyBtn.disabled = target.kind === 'empty';

    if (output.textContent === text) return;
    if (!painted) {
      // 第一次直接寫進去。走動效的話文字要等 timeline 跑完才出現，
      // 頁面剛載入那一瞬間會看到一塊空白。
      painted = true;
      output.textContent = text;
      return;
    }
    // 之後每次都是整段換掉，很跳，用共用的 swap 動效接一下
    Motion.swap(output, () => (output.textContent = text));
  }

  input.addEventListener('input', update);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      copy();
    }
  });

  modeGroup?.addEventListener('segmented:change', (e) => {
    const next = e.detail?.value;
    if (MODES.has(next)) mode = next;
    update();
  });

  copyBtn?.addEventListener('click', () => copy());

  function copy() {
    if (!input.value.trim()) {
      input.focus();
      Motion.shake(input.closest('.field') ?? input);
      Motion.toast('先打個名字或貼上網址', { type: 'error' });
      return;
    }
    Components.copyWithFeedback(text, copyBtn, '已複製，貼給 AI 就可以了');
  }

  update();
}

/** 頁面上可能不只一個，掃整份文件比較省事 */
export function mountRequestBoxes(site, root = document) {
  for (const node of root.querySelectorAll('[data-request-box]')) mountRequestBox(node, site);
}

/* ---- 判斷使用者到底貼了什麼 ---------------------------------------------- */

const KIND_LABEL = {
  empty: '等你輸入',
  url: '看起來是網址',
  repo: '看起來是 GitHub repo',
  name: '只有名字，AI 會先去找',
};

/**
 * 使用者不會分「這是網址還是名字」，所以自己判斷：
 * 完整網址 → url；owner/repo 這種簡寫 → repo；其餘一律當名字。
 */
export function parseTarget(raw) {
  const value = raw.trim();
  if (!value) return { kind: 'empty', value: '' };

  if (/^https?:\/\/\S+$/i.test(value)) return { kind: 'url', value };
  if (/^(www\.|github\.com\/)/i.test(value)) return { kind: 'url', value: `https://${value.replace(/^www\./i, '')}` };

  // owner/repo 或 owner/repo/tree/main/skills/xxx
  if (/^[\w.-]+\/[\w.-]+(\/\S*)?$/.test(value) && !value.includes(' ')) {
    return { kind: 'repo', value: `https://github.com/${value}` };
  }

  return { kind: 'name', value };
}

/* ---- 產生提示詞 ---------------------------------------------------------- */

export function buildPrompt({ target, mode, base, repo, name }) {
  if (!target || target.kind === 'empty') {
    return `打上 skill 的名字，或貼上它的 GitHub 網址，這裡就會生出一段可以直接貼給 AI 的話。`;
  }

  const isName = target.kind === 'name';
  const lines = [];

  lines.push(
    isName
      ? `我想收一個叫「${target.value}」的 AI Agent Skill 進我的收藏庫，但我手上只有名字。`
      : `我找到一個想收進收藏庫的 AI Agent Skill：`
  );
  if (!isName) lines.push('', `  ${target.value}`);

  lines.push(
    '',
    `我的收藏庫叫「${name}」：`,
    `- 網站：${base}/`,
    `- 全部資料：${base}/api/index.json`,
    `- 收錄格式：${base}/api/schema.json`,
    `- 原始碼：${repo}`,
    '',
    '請幫我做這幾件事：',
    ''
  );

  let n = 0;
  const step = (s) => lines.push(`${++n}. ${s}`);

  if (isName) {
    step(
      '先找到它的出處（GitHub repo 或官方發佈頁）。\n' +
        '   如果找到好幾個同名的，先列出來讓我確認是哪一個，不要自己猜。'
    );
  }
  step(
    '讀它的 SKILL.md 和 README，搞清楚它實際上能幫使用者做到什麼。'
  );
  step(
    `讀 ${base}/api/index.json 的 forAI.howToContribute，那裡是這個庫的收錄規矩。\n` +
      '   最重要的一條：summary 要寫成「完全不懂程式的人看一眼就懂」的一句話，\n' +
      '   25 字內、不要出現技術名詞，技術細節一律寫進 description。'
  );
  step(
    '先確認 registry 裡沒有同一個 id。已經有了就是更新那一筆，不要另外開一筆。'
  );
  step(
    `照 ${base}/api/schema.json 的格式，在專案裡寫 registry/skills/<id>.json。\n` +
      `   專案原始碼在 ${repo}，我本機沒有的話就先 clone 下來再改。\n` +
      '   同一個 repo 拆成好幾個資料夾、實際使用時會一起載入的，用 parts 收成一筆。'
  );
  step('跑 npm run validate && npm run build，兩個都要全綠。');

  if (mode === 'install') {
    step(
      'build 完之後，順手幫我把這個 skill 裝到我的電腦上：\n' +
        '   讀 docs/api/skills/<id>.json 的 installPrompt，照那一段執行。'
    );
  }

  step('告訴我收了什麼、放在哪個分類、目前總共幾個。先不要 commit / push，我自己決定。');

  return lines.join('\n');
}

export default { mountRequestBox, mountRequestBoxes, buildPrompt, parseTarget };
