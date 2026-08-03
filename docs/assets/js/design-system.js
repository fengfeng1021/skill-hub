/* ==========================================================================
   Design System 展示頁的示範資料與互動
   這裡的程式碼只服務展示頁，不會被網站本體用到。
   ========================================================================== */

import Components from './components.js';
import Motion from './motion.js';
import { renderSkillCard } from './skill-card.js';

/* ---- 色票 --------------------------------------------------------------- */
const SWATCHES = [
  ['--bg', '底色'],
  ['--surface-1', '表面 1'],
  ['--surface-2', '表面 2'],
  ['--surface-3', '表面 3'],
  ['--border', '邊框'],
  ['--border-strong', '強邊框'],
  ['--text', '主要文字'],
  ['--text-muted', '次要文字'],
  ['--text-faint', '輔助文字'],
  ['--accent', '主色'],
  ['--accent-2', '副色'],
  ['--warn', '警告'],
  ['--danger', '危險'],
  ['--info', '資訊'],
];

function renderSwatches() {
  const host = document.getElementById('swatches');
  if (!host) return;
  host.innerHTML = SWATCHES.map(
    ([token, label]) => `
      <div class="ds-swatch">
        <div class="ds-swatch__chip" style="background: var(${token})"></div>
        <span class="ds-swatch__name">${token}</span>
        <span class="ds-swatch__name" style="color: var(--text-faint)">${label}</span>
      </div>`
  ).join('');
}

/* ---- 卡片示範 ----------------------------------------------------------- */
const DEMO_SKILLS = [
  {
    id: 'gsap',
    name: 'GSAP',
    summary: '官方動畫 skill 全套：tween、時間軸、ScrollTrigger、外掛與效能。',
    tags: ['animation', 'scroll', 'gsap'],
    official: true,
    category: '前端 / 動效',
    parts: [{ dirName: 'gsap-core' }, { dirName: 'gsap-timeline' }, { dirName: 'gsap-scrolltrigger' }],
    source: { kind: 'github', label: 'greensock/gsap-skills' },
  },
  {
    id: 'pdf-reading',
    name: 'PDF 閱讀',
    summary: '把 PDF 轉成可讀文字與表格，處理掃描檔與多欄排版。',
    tags: ['document', 'pdf', 'ocr'],
    featured: true,
    category: '文件處理',
    source: { kind: 'github', label: 'anthropics/skills' },
  },
  {
    id: 'my-deploy-flow',
    name: '我的部署流程',
    summary: '自製：專案的部署檢查清單與回滾步驟，含環境變數確認。',
    tags: ['devops', 'custom'],
    category: '自製',
    source: { kind: 'local', label: '本庫託管' },
  },
];

function renderCards() {
  const host = document.getElementById('cardDemo');
  if (!host) return;
  host.innerHTML = DEMO_SKILLS.map((s, i) => renderSkillCard(s, { selected: i === 2 })).join('');
  Components.scan(host);

  // 示範用：點卡片切換選取狀態
  host.addEventListener('click', (e) => {
    const card = e.target.closest('.skill-card');
    if (!card) return;
    const label = card.querySelector('[data-check]');
    const input = label?.querySelector('.check__input');
    if (!input) return;
    // 點在勾選框本身時交給原生 label 行為處理，避免切兩次
    if (e.target.closest('[data-select-stop]')) {
      card.classList.toggle('is-selected', input.checked);
      return;
    }
    Components.setChecked(label, !input.checked);
    card.classList.toggle('is-selected', input.checked);
    Motion.pulse(card.querySelector('.check__box'));
  });
}

/* ---- Toast / 浮出操作列 -------------------------------------------------- */
function bindFeedbackDemos() {
  const MESSAGES = {
    success: '已複製 3 個 skill 的安裝提示詞',
    error: '複製失敗，請手動選取內容',
    info: '收錄庫已更新到最新版本',
  };
  for (const btn of document.querySelectorAll('[data-demo-toast]')) {
    const type = btn.dataset.demoToast;
    btn.addEventListener('click', () => Motion.toast(MESSAGES[type], { type }));
  }

  const bar = document.getElementById('dsBar');
  const num = document.getElementById('dsBarNum');
  const toggle = document.getElementById('dsBarToggle');
  if (bar && toggle) {
    const ctrl = Motion.floatingBar(bar);
    let open = false;
    let count = 3;
    toggle.addEventListener('click', () => {
      open = !open;
      if (open) {
        ctrl.show();
      } else {
        ctrl.hide();
      }
    });
    bar.addEventListener('click', (e) => {
      if (!e.target.closest('.btn')) return;
      count = count > 1 ? count - 1 : 5;
      num.textContent = String(count);
      ctrl.bump(num);
    });
  }
}

/* ---- Flip 篩選示範 ------------------------------------------------------- */
function bindFlipDemo() {
  const host = document.getElementById('flipDemo');
  if (!host) return;
  const items = [...host.children];
  for (const btn of document.querySelectorAll('[data-flip-filter]')) {
    btn.addEventListener('click', () => {
      const f = btn.dataset.flipFilter;
      Motion.flip(host, () => {
        for (const el of items) {
          el.style.display = f === 'all' || el.dataset.group === f ? '' : 'none';
        }
      });
    });
  }
}

/* ---- 側邊導覽 scrollspy -------------------------------------------------- */
function bindNav() {
  const links = [...document.querySelectorAll('.ds-nav__link')];
  const sections = links
    .map((l) => document.querySelector(l.getAttribute('href')))
    .filter(Boolean);
  if (!sections.length || !window.ScrollTrigger) return;

  sections.forEach((section, i) => {
    ScrollTrigger.create({
      trigger: section,
      start: 'top 40%',
      end: 'bottom 40%',
      onToggle: (self) => {
        if (!self.isActive) return;
        links.forEach((l, j) => l.classList.toggle('is-active', i === j));
      },
    });
  });
}

/* ---- 啟動 --------------------------------------------------------------- */
function start() {
  renderSwatches();
  renderCards();
  bindFeedbackDemos();
  bindFlipDemo();
  Components.init();
  bindNav();
}

// GSAP 是用 defer 從 CDN 載入的，等 DOM 與 script 都到位再啟動
if (document.readyState === 'loading') {
  window.addEventListener('DOMContentLoaded', start);
} else {
  start();
}
