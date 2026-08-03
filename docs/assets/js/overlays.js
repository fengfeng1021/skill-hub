/* ==========================================================================
   Overlays — 三個頁面共用的浮層
   ==========================================================================
   詳情面板、安裝提示詞、使用說明、多選操作列、toast 容器。
   每頁的 HTML 都複製一份太容易走鐘，所以集中在這裡由 JS 掛上去。
   結構與樣式仍然是 components.css 那一套，這裡只負責組裝。
   ========================================================================== */

import { Icons } from './icons.js';

const closeButton = (label = '關閉') => `
  <button class="btn btn--icon btn--ghost" data-modal-close aria-label="${label}" data-motion="press">
    <span class="btn__icon">${Icons.close}</span>
  </button>`;

const detailModal = () => `
  <div class="modal modal--wide" id="detailModal" role="dialog" aria-modal="true" aria-labelledby="detailTitle" tabindex="-1">
    <div class="modal__backdrop"></div>
    <div class="modal__panel">
      <div class="modal__head">
        <div class="detail__head grow" data-modal-item>
          <span class="detail__icon" id="detailIcon">—</span>
          <div class="grow" style="min-width: 0">
            <h2 class="modal__title" id="detailTitle">—</h2>
            <p class="mono faint" id="detailId">—</p>
          </div>
        </div>
        ${closeButton()}
      </div>
      <div class="modal__body stack" style="gap: var(--space-6)" id="detailBody"></div>
      <div class="modal__foot">
        <a class="btn btn--ghost" id="detailSource" href="#" target="_blank" rel="noopener" data-motion="press">查看來源</a>
        <button class="btn btn--primary" id="detailCopy" data-copy="#detailPromptText" data-motion="press ripple">
          <span class="btn__icon">${Icons.copy}</span>
          <span data-copy-label>複製安裝提示詞</span>
        </button>
      </div>
    </div>
  </div>`;

const installModal = () => `
  <div class="modal modal--wide" id="installModal" role="dialog" aria-modal="true" aria-labelledby="installTitle" tabindex="-1">
    <div class="modal__backdrop"></div>
    <div class="modal__panel">
      <div class="modal__head">
        <div class="grow">
          <p class="eyebrow" data-modal-item>一併安裝</p>
          <h2 class="modal__title" id="installTitle" data-modal-item>安裝提示詞</h2>
          <p class="muted" style="font-size: var(--text-sm); margin-top: var(--space-2)" data-modal-item>
            複製下面全部內容，貼進 Claude Code（或任何有檔案存取權的 AI），它會照著把 skills 裝好。
          </p>
        </div>
        ${closeButton()}
      </div>
      <div class="modal__body">
        <div class="code" data-modal-item>
          <div class="code__bar">
            <span class="code__title" id="installMeta">—</span>
            <button class="btn btn--sm btn--ghost" data-copy="closest" data-motion="press">
              <span class="btn__icon">${Icons.copy}</span>
              <span data-copy-label>複製</span>
            </button>
          </div>
          <pre class="code__body" id="installPrompt">—</pre>
        </div>
      </div>
      <div class="modal__foot">
        <button class="btn btn--ghost" data-modal-close data-motion="press">關閉</button>
        <button class="btn btn--primary" id="installCopy" data-copy="#installPrompt" data-motion="press ripple">
          <span class="btn__icon">${Icons.copy}</span>
          <span data-copy-label>複製全部</span>
        </button>
      </div>
    </div>
  </div>`;

const howtoModal = () => `
  <div class="modal" id="howtoModal" role="dialog" aria-modal="true" aria-labelledby="howtoTitle" tabindex="-1">
    <div class="modal__backdrop"></div>
    <div class="modal__panel">
      <div class="modal__head">
        <div class="grow">
          <p class="eyebrow" data-modal-item>How to</p>
          <h2 class="modal__title" id="howtoTitle" data-modal-item>三步驟裝好 skill</h2>
        </div>
        ${closeButton()}
      </div>
      <div class="modal__body stack" style="gap: var(--space-5)">
        <ol class="detail__list" style="gap: var(--space-4)" data-modal-item>
          <li><strong>勾選</strong>：在卡片右上角勾選想裝的，可以一次選很多個。</li>
          <li><strong>複製</strong>：底部會浮出操作列，按「複製安裝指令」拿到一整段文字。</li>
          <li><strong>貼上</strong>：貼進 Claude Code 或任何能存取檔案的 AI，它會自己下載、放到正確位置、檢查有沒有裝好。</li>
        </ol>
        <div class="divider"></div>
        <div data-modal-item>
          <p class="detail__section-title">不用會寫程式</p>
          <p class="muted" style="font-size: var(--text-sm)">
            整個過程你只要做「勾選 → 複製 → 貼上」三件事，剩下的都是 AI 在做。
            裝完記得把 Claude Code 重開，新的能力才會生效。
          </p>
        </div>
      </div>
      <div class="modal__foot">
        <button class="btn btn--primary" data-modal-close data-motion="press ripple">知道了</button>
      </div>
    </div>
  </div>`;

const selectionBar = () => `
  <div class="selection-bar" id="selectionBar">
    <span class="selection-bar__count">
      <span class="selection-bar__num" id="selectionCount">0</span> 個已選取
    </span>
    <div class="row" style="gap: var(--space-2)">
      <button class="btn btn--ghost btn--sm" id="selectionClear" data-motion="press">清除</button>
      <button class="btn btn--primary btn--sm" id="selectionInstall" data-motion="press ripple">
        <span class="btn__icon">${Icons.copy}</span>
        複製安裝指令
      </button>
    </div>
  </div>`;

/**
 * 把浮層掛到 <body> 最後面。
 * 一定要在 Components.init() 之前呼叫，元素才會被掃到並綁上行為。
 */
export function mountOverlays() {
  if (document.getElementById('detailModal')) return; // 重複呼叫不做事
  const host = document.createElement('div');
  host.innerHTML = [
    detailModal(),
    installModal(),
    howtoModal(),
    selectionBar(),
    '<div class="toast-stack"></div>',
  ].join('');
  document.body.append(...host.children);
}

export default mountOverlays;
