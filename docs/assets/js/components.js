/* ==========================================================================
   Components — 元件行為
   ==========================================================================
   只處理「互動邏輯」；所有位移／縮放／淡入等動效一律呼叫 Motion。
   全部用 data-* 自動綁定，頁面不需要寫初始化程式碼。

     data-theme-toggle      主題切換按鈕
     data-copy="…"          點擊複製；值為文字，或 #id 指向來源元素
     data-check             勾選框（.check 結構）
     data-segmented         分段切換容器
     data-tooltip="…"       hover 顯示提示
     data-modal="#id"       點擊開啟指定 modal
     data-modal-close       關閉所在的 modal
   ========================================================================== */

import Motion from './motion.js';

const Components = (() => {
  'use strict';

  /* ---- 主題 -------------------------------------------------------------- */
  const THEME_KEY = 'skill-hub-theme';

  function currentTheme() {
    return document.documentElement.dataset.theme ?? 'dark';
  }

  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch {
      /* 隱私模式下 localStorage 可能不可用，忽略即可 */
    }
  }

  function initTheme() {
    for (const btn of document.querySelectorAll('[data-theme-toggle]')) {
      const icons = btn.querySelectorAll('svg');
      const sync = () => {
        const dark = currentTheme() === 'dark';
        icons.forEach((svg, i) => {
          const show = i === (dark ? 0 : 1);
          svg.style.opacity = show ? '1' : '0';
          svg.style.transform = show ? 'none' : 'rotate(-90deg) scale(0.6)';
          svg.style.transition = 'opacity .3s var(--ease-out), transform .4s var(--ease-back)';
        });
        btn.setAttribute('aria-label', dark ? '切換為淺色模式' : '切換為深色模式');
      };
      sync();
      btn.addEventListener('click', () => {
        Motion.themeSwitch(() => {
          applyTheme(currentTheme() === 'dark' ? 'light' : 'dark');
          sync();
        }, btn);
      });
    }
  }

  /* ---- 複製 -------------------------------------------------------------- */
  async function copyText(text) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      // clipboard API 在非 https 或舊瀏覽器不可用，退回 execCommand
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.cssText = 'position:fixed;opacity:0;pointer-events:none';
      document.body.appendChild(ta);
      ta.select();
      const ok = document.execCommand?.('copy') ?? false;
      ta.remove();
      return ok;
    }
  }

  function resolveCopySource(btn) {
    const raw = btn.dataset.copy ?? '';
    if (raw.startsWith('#')) {
      const src = document.querySelector(raw);
      return src ? src.textContent : '';
    }
    if (raw === 'closest') {
      const src = btn.closest('.code')?.querySelector('.code__body');
      return src ? src.textContent : '';
    }
    return raw;
  }

  /** 供外部直接呼叫（例如複製多選提示詞） */
  async function copyWithFeedback(text, btn, message = '已複製到剪貼簿') {
    const ok = await copyText(text);
    if (ok) {
      if (btn) {
        Motion.pulse(btn);
        flashLabel(btn, '已複製');
      }
      Motion.toast(message, { type: 'success' });
    } else {
      if (btn) Motion.shake(btn);
      Motion.toast('複製失敗，請手動選取內容', { type: 'error' });
    }
    return ok;
  }

  function flashLabel(btn, text) {
    const label = btn.querySelector('[data-copy-label]');
    if (!label) return;
    const original = label.dataset.original ?? label.textContent;
    label.dataset.original = original;
    clearTimeout(btn.__labelTimer);
    Motion.swap(label, () => {
      label.textContent = text;
    });
    btn.__labelTimer = setTimeout(() => {
      Motion.swap(label, () => {
        label.textContent = original;
      });
    }, 1800);
  }

  function initCopy(root = document) {
    for (const btn of root.querySelectorAll('[data-copy]')) {
      if (btn.__copyBound) continue;
      btn.__copyBound = true;
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const text = resolveCopySource(btn);
        if (!text) {
          Motion.toast('沒有可複製的內容', { type: 'error' });
          return;
        }
        copyWithFeedback(text, btn, btn.dataset.copyMessage ?? '已複製到剪貼簿');
      });
    }
  }

  /* ---- 勾選框 ------------------------------------------------------------ */
  function initChecks(root = document) {
    for (const wrap of root.querySelectorAll('[data-check]')) {
      if (wrap.__checkBound) continue;
      wrap.__checkBound = true;
      const input = wrap.querySelector('.check__input');
      const box = wrap.querySelector('.check__box');
      if (!input || !box) continue;
      Motion.check(box, input.checked);
      input.addEventListener('change', () => Motion.check(box, input.checked));
    }
  }

  /** 外部改變勾選狀態時同步動畫 */
  function setChecked(wrap, checked) {
    const input = wrap.querySelector('.check__input');
    const box = wrap.querySelector('.check__box');
    if (!input || !box) return;
    input.checked = checked;
    Motion.check(box, checked);
  }

  /* ---- Segmented --------------------------------------------------------- */
  function initSegmented(root = document) {
    for (const group of root.querySelectorAll('[data-segmented]')) {
      if (group.__segBound) continue;
      group.__segBound = true;
      const ctrl = Motion.segmented(group);
      const items = [...group.querySelectorAll('.segmented__item')];
      const select = (item, animate = true) => {
        items.forEach((i) => i.setAttribute('aria-selected', String(i === item)));
        ctrl.move(item, animate);
        group.dispatchEvent(new CustomEvent('segmented:change', { detail: { value: item.dataset.value, item } }));
      };
      items.forEach((item) => item.addEventListener('click', () => select(item)));

      const initial = items.find((i) => i.getAttribute('aria-selected') === 'true') ?? items[0];
      // 等版面穩定（字體載入會影響寬度）再定位指示塊
      requestAnimationFrame(() => ctrl.move(initial, false));
      group.__segmentedSelect = select;
      window.addEventListener('resize', () => {
        const active = items.find((i) => i.getAttribute('aria-selected') === 'true');
        ctrl.move(active, false);
      });
    }
  }

  /* ---- Tooltip ----------------------------------------------------------- */
  let tooltipEl = null;

  function initTooltips() {
    if (tooltipEl) return;
    tooltipEl = document.createElement('div');
    tooltipEl.className = 'tooltip';
    tooltipEl.setAttribute('role', 'tooltip');
    document.body.appendChild(tooltipEl);

    const show = (e) => {
      const target = e.target.closest('[data-tooltip]');
      if (!target) return;
      tooltipEl.textContent = target.dataset.tooltip;
      const r = target.getBoundingClientRect();
      // 先量出 tooltip 尺寸再定位，避免第一次顯示位置跑掉
      tooltipEl.style.left = '0px';
      tooltipEl.style.top = '0px';
      const t = tooltipEl.getBoundingClientRect();
      const left = Math.min(Math.max(8, r.left + r.width / 2 - t.width / 2), innerWidth - t.width - 8);
      tooltipEl.style.left = `${left}px`;
      tooltipEl.style.top = `${Math.max(8, r.top - t.height - 8)}px`;
      window.gsap?.to(tooltipEl, { opacity: 1, y: 0, duration: 0.2, ease: 'power2.out', overwrite: true });
    };

    const hide = () => window.gsap?.to(tooltipEl, { opacity: 0, duration: 0.14, overwrite: true });

    document.addEventListener('pointerover', show);
    document.addEventListener('pointerout', hide);
    document.addEventListener('focusin', show);
    document.addEventListener('focusout', hide);
    window.addEventListener('scroll', hide, { passive: true });
  }

  /* ---- Modal ------------------------------------------------------------- */
  const modals = new Map();

  function getModal(selector) {
    if (modals.has(selector)) return modals.get(selector);
    const root = document.querySelector(selector);
    if (!root) return null;
    const inst = Motion.modal(root);
    modals.set(selector, inst);
    return inst;
  }

  function initModals(root = document) {
    for (const btn of root.querySelectorAll('[data-modal]')) {
      if (btn.__modalBound) continue;
      btn.__modalBound = true;
      btn.addEventListener('click', () => getModal(btn.dataset.modal)?.open());
    }
    for (const btn of root.querySelectorAll('[data-modal-close]')) {
      if (btn.__modalCloseBound) continue;
      btn.__modalCloseBound = true;
      btn.addEventListener('click', () => {
        const root = btn.closest('.modal');
        if (root?.id) getModal(`#${root.id}`)?.close();
      });
    }
  }

  /* ---- 入口 -------------------------------------------------------------- */
  function init() {
    try {
      const saved = localStorage.getItem(THEME_KEY);
      if (saved) document.documentElement.dataset.theme = saved;
    } catch {
      /* 忽略 */
    }

    Motion.init();
    initTheme();
    initTooltips();
    scan();
    Motion.intro();
  }

  /** 動態插入 DOM 之後呼叫，把新元素的行為與動效補綁 */
  function scan(root = document) {
    initCopy(root);
    initChecks(root);
    initSegmented(root);
    initModals(root);
    Motion.scan(root);
  }

  return { init, scan, copyText, copyWithFeedback, setChecked, getModal, applyTheme, currentTheme };
})();

window.Components = Components;
export default Components;
