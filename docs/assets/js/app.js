/* ==========================================================================
   App — 收藏庫首頁
   ==========================================================================
   這一頁只負責「資料 → 狀態 → 畫面」，
   所有樣式來自 components.css / site.css，所有動效來自 motion.js。
   這裡不寫任何一次性的 gsap.to()。
   ========================================================================== */

import Components from './components.js';
import Motion from './motion.js';
import { renderSkillCard, escapeHTML, initials } from './skill-card.js';
import { Icons } from './icons.js';

const SELECTION_KEY = 'skill-hub-selection';
const VIEW_KEY = 'skill-hub-view';

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

const state = {
  site: null,
  template: null,
  skills: [],
  byId: new Map(),
  cards: new Map(), // id → 卡片元素（一次建立後就固定，Flip 才能對得上）
  visible: [],
  selected: new Set(),
  query: '',
  category: 'all',
  tag: null,
  view: 'grid',
};

const el = {};
let selectionBar = null;
let refreshTimer = null;

/* ==========================================================================
   啟動
   ========================================================================== */
async function start() {
  cacheElements();
  Components.init();
  selectionBar = Motion.floatingBar(el.selectionBar);
  bindStaticEvents();

  try {
    const data = await fetch('./api/index.json', { cache: 'no-cache' }).then((r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    });
    hydrate(data);
  } catch (err) {
    console.error('[App] 載入 api/index.json 失敗', err);
    showLoadError(err);
  }
}

function cacheElements() {
  el.grid = $('#grid');
  el.filters = $('#filters');
  el.search = $('#search');
  el.resultCount = $('#resultCount');
  el.emptyState = $('#emptyState');
  el.setupNote = $('#setupNote');
  el.selectionBar = $('#selectionBar');
  el.selectionCount = $('#selectionCount');
  el.viewSwitch = $('#viewSwitch');
  el.heroMeta = $('#heroMeta');
  el.clearFilters = $('#clearFilters');
  el.detailBody = $('#detailBody');
}

function hydrate(data) {
  state.site = data.site;
  state.template = data.promptTemplate;
  state.skills = sortSkills(data.skills ?? []);
  for (const s of state.skills) {
    // 組合包的各分項也要能搜到（搜 scrolltrigger 要找得到 GSAP 這一筆）
    const parts = (s.parts ?? []).flatMap((p) => [p.dirName, p.name, p.summary]);
    s.__haystack = [s.id, s.name, s.summary, s.category, ...(s.tags ?? []), ...(s.usage ?? []), ...parts]
      .filter(Boolean)
      .join(' ')
      .toLowerCase();
    state.byId.set(s.id, s);
  }

  renderSiteChrome(data);
  renderHeroMeta(data);
  renderFilters(data);
  renderCards();
  restoreFromStorage();
  readURL();
  apply({ animate: false });
  syncSelection({ animate: false });
  // 篩掉的卡片先藏好再跑進場，才不會animate到看不見的卡片
  Motion.intro(el.grid);
  openFromHash();
}

/** 推薦 → 官方 → 新加入的在前 → 名稱 */
function sortSkills(list) {
  return [...list].sort(
    (a, b) =>
      Number(b.featured) - Number(a.featured) ||
      Number(b.official) - Number(a.official) ||
      String(b.addedAt ?? '').localeCompare(String(a.addedAt ?? '')) ||
      a.name.localeCompare(b.name, 'zh-Hant')
  );
}

/* ==========================================================================
   靜態區塊
   ========================================================================== */
function renderSiteChrome(data) {
  if (data.site?.name) document.title = `${data.site.name} — ${data.site.tagline ?? ''}`.trim();

  const repo = data.site?.repo;
  if (repo) {
    for (const link of [$('#repoLink'), $('#footerRepo')]) {
      if (!link) continue;
      link.href = repo;
      link.hidden = false;
      link.style.display = '';
    }
  } else {
    $('#footerRepo')?.setAttribute('href', './api/index.json');
  }

  if (data.site?.configured === false) {
    el.setupNote.innerHTML = `
      <div class="setup-note">
        <span class="setup-note__icon">${Icons.sparkle}</span>
        <div>
          <strong>還沒設定 GitHub 帳號</strong><br />
          把 <code class="tag">site.config.json</code> 的 <code class="tag">owner</code> 改成你的 GitHub 帳號，
          再跑一次 <code class="tag">npm run build</code>，安裝提示詞裡的下載網址才會正確。
        </div>
      </div>`;
  }
}

/** hero 底下那行小字。數字滾動由 motion.js 的 count recipe 負責 */
function renderHeroMeta(data) {
  const count = data.count ?? state.skills.length;
  const cats = (data.categories ?? []).length;
  el.heroMeta.innerHTML = `
    <span>收錄 <b data-motion="count" data-motion-to="${count}">0</b> 個 skill</span>
    ${cats > 1 ? `<span>·</span><span>${cats} 個分類</span>` : ''}
    <span>·</span><span>更新於 ${escapeHTML(data.generatedAt ?? '—')}</span>`;
  Motion.scan(el.heroMeta);
}

/**
 * 篩選 chips。數量少的時候篩選只是多餘的介面，
 * 所以只有分類超過一個、或 skill 夠多時才顯示。
 */
function renderFilters(data) {
  const cats = data.categories ?? [];
  const tags = state.skills.length >= 4 ? (data.tags ?? []).slice(0, 10) : [];
  const showCats = cats.length > 1;

  const chip = (label, count, attrs, pressed) =>
    `<button class="chip" ${attrs} aria-pressed="${pressed}" data-motion="press">
       ${escapeHTML(label)}${count === null ? '' : `<span class="chip__count">${count}</span>`}
     </button>`;

  const chips = [];
  if (showCats) {
    chips.push(chip('全部', state.skills.length, 'data-filter-category="all"', true));
    chips.push(...cats.map((c) => chip(c.name, c.count, `data-filter-category="${escapeHTML(c.name)}"`, false)));
  }
  chips.push(...tags.map((t) => chip(t.name, t.count, `data-filter-tag="${escapeHTML(t.name)}"`, false)));

  el.filters.innerHTML = chips.join('');
  Components.scan(el.filters);
}

function renderCards() {
  el.grid.innerHTML = state.skills.map((s) => renderSkillCard(s)).join('');
  for (const card of $$('.skill-card', el.grid)) {
    state.cards.set(card.dataset.skillId, card);
  }
  Components.scan(el.grid); // 內含 Motion.scan，卡片的 lift / glow 在這裡綁上
}

function showLoadError(err) {
  el.resultCount.textContent = '載入失敗';
  el.grid.innerHTML = `
    <div class="empty" style="grid-column: 1 / -1">
      <div class="empty__icon">${Icons.close}</div>
      <p class="empty__title">讀不到 api/index.json</p>
      <p style="font-size: var(--text-xs)">
        還沒跑過 <code class="tag">npm run build</code>，或是直接用 file:// 開啟（瀏覽器會擋住 fetch）。<br />
        本機預覽請跑 <code class="tag">npm run dev</code>。
      </p>
      <p class="faint mono" style="font-size: var(--text-2xs)">${escapeHTML(err?.message ?? err)}</p>
    </div>`;
}

/* ==========================================================================
   篩選
   ========================================================================== */
function matches(skill) {
  if (state.category !== 'all' && skill.category !== state.category) return false;
  if (state.tag && !(skill.tags ?? []).includes(state.tag)) return false;
  const q = state.query.trim().toLowerCase();
  if (!q) return true;
  return q.split(/\s+/).every((word) => skill.__haystack.includes(word));
}

/**
 * 套用目前的篩選條件。
 * 卡片元素從頭到尾都是同一批，只切換 display，Flip 才能算出正確的位移。
 */
function apply({ animate = true } = {}) {
  const visible = [];
  const mutate = () => {
    for (const s of state.skills) {
      const card = state.cards.get(s.id);
      if (!card) continue;
      const ok = matches(s);
      card.style.display = ok ? '' : 'none';
      if (ok) visible.push(s);
    }
    el.grid.dataset.view = state.view;
  };

  if (animate) {
    Motion.flip(el.grid, mutate, { itemSelector: '.skill-card' });
  } else {
    mutate();
  }

  state.visible = visible;
  el.resultCount.textContent = describeResult(visible.length);
  el.emptyState.hidden = visible.length > 0;
  el.clearFilters.hidden = !isFiltered();
  scheduleRefresh();
  writeURL();
}

function isFiltered() {
  return state.category !== 'all' || Boolean(state.tag) || Boolean(state.query.trim());
}

function describeResult(n) {
  const bits = [`${n} 個 skill`];
  if (state.category !== 'all') bits.push(`分類「${state.category}」`);
  if (state.tag) bits.push(`標籤「${state.tag}」`);
  if (state.query.trim()) bits.push(`關鍵字「${state.query.trim()}」`);
  return bits.join('　·　');
}

/** 版面變動後讓 ScrollTrigger 重算位置，合併多次呼叫避免抖動 */
function scheduleRefresh() {
  clearTimeout(refreshTimer);
  refreshTimer = setTimeout(() => Motion.refresh(), 640);
}

function syncChips() {
  for (const btn of $$('[data-filter-category]', el.filters)) {
    btn.setAttribute('aria-pressed', String(btn.dataset.filterCategory === state.category));
  }
  for (const btn of $$('[data-filter-tag]', el.filters)) {
    btn.setAttribute('aria-pressed', String(btn.dataset.filterTag === state.tag));
  }
}

function resetFilters() {
  state.query = '';
  state.category = 'all';
  state.tag = null;
  el.search.value = '';
  syncChips();
  apply();
}

/* ==========================================================================
   多選
   ========================================================================== */
function setSelected(id, on, { syncInput = true } = {}) {
  const card = state.cards.get(id);
  if (!card) return;
  if (on) state.selected.add(id);
  else state.selected.delete(id);
  card.classList.toggle('is-selected', on);
  if (syncInput) {
    const label = card.querySelector('[data-check]');
    if (label) Components.setChecked(label, on);
  }
}

function syncSelection({ animate = true } = {}) {
  const n = state.selected.size;
  el.selectionCount.textContent = String(n);
  if (n > 0) {
    selectionBar.show();
    if (animate) selectionBar.bump(el.selectionCount);
  } else {
    selectionBar.hide();
  }
  try {
    localStorage.setItem(SELECTION_KEY, JSON.stringify([...state.selected]));
  } catch {
    /* 隱私模式忽略 */
  }
}

function clearSelection() {
  for (const id of [...state.selected]) setSelected(id, false);
  syncSelection({ animate: false });
}

function selectedSkills() {
  // 依畫面順序輸出，提示詞的編號才跟使用者看到的一致
  return state.skills.filter((s) => state.selected.has(s.id));
}

/* ==========================================================================
   安裝提示詞
   ========================================================================== */
function buildCombinedPrompt(list) {
  if (!list.length) return '';
  if (list.length === 1) return list[0].installPrompt;

  const t = state.template;
  const header = t.headerPlural.replace('{{count}}', String(list.length));
  const blocks = list.map((s, i) => s.promptBlock.replace(/^### /, `### ${i + 1}. `));
  return [header, ...blocks, t.footer].join(t.separator);
}

function openInstallModal(list) {
  const text = buildCombinedPrompt(list);
  const names = list.map((s) => s.name).join('、');
  $('#installPrompt').textContent = text;
  $('#installTitle').textContent = list.length > 1 ? `一次安裝 ${list.length} 個 skill` : `安裝 ${list[0].name}`;
  $('#installMeta').textContent = `${list.length} 個 skill · ${text.length.toLocaleString('en-US')} 字元`;
  const copyBtn = $('#installCopy');
  copyBtn.dataset.copyMessage = `已複製安裝提示詞：${names}`;
  Components.getModal('#installModal')?.open();
}

/* ==========================================================================
   詳情
   ========================================================================== */
function openDetail(id) {
  const skill = state.byId.get(id);
  if (!skill) return;

  $('#detailIcon').textContent = initials(skill.name);
  $('#detailTitle').textContent = skill.name;
  $('#detailId').textContent = skill.id;

  const sourceLink = $('#detailSource');
  const href = sourceURL(skill);
  if (href) {
    sourceLink.href = href;
    sourceLink.style.display = '';
    sourceLink.textContent = skill.source.kind === 'local' ? '查看檔案' : '查看來源';
  } else {
    sourceLink.style.display = 'none';
  }
  $('#detailCopy').dataset.copyMessage = `已複製 ${skill.name} 的安裝提示詞`;

  el.detailBody.innerHTML = detailHTML(skill);
  Components.scan(el.detailBody);
  Components.getModal('#detailModal')?.open();
  Motion.intro(el.detailBody);

  if (location.hash !== `#${skill.id}`) history.replaceState(null, '', `#${skill.id}`);
}

/**
 * 來源連結。site.config.json 還沒填 GitHub 帳號時，local 託管的 displayUrl
 * 只是 `skills/<id>` 這種相對路徑，連出去會 404，所以只認絕對網址。
 */
function sourceURL(skill) {
  const url = skill?.source?.displayUrl;
  return typeof url === 'string' && /^https?:\/\//.test(url) ? url : null;
}

function detailHTML(skill) {
  const section = (title, body) =>
    body ? `<section data-intro><p class="detail__section-title">${title}</p>${body}</section>` : '';

  const list = (items) =>
    items?.length ? `<ul class="detail__list">${items.map((i) => `<li>${escapeHTML(i)}</li>`).join('')}</ul>` : '';

  const parts = skill.parts ?? [];

  const badges = [
    skill.official ? '<span class="badge badge--official">官方</span>' : '',
    skill.featured ? '<span class="badge badge--featured">推薦</span>' : '',
    skill.source?.kind === 'local' ? '<span class="badge badge--local">本庫託管</span>' : '',
    parts.length > 1 ? `<span class="badge badge--bundle">${parts.length} 合 1</span>` : '',
  ].join('');

  const meta = [
    ['分類', escapeHTML(skill.category ?? '—')],
    parts.length
      ? ['安裝資料夾', `${parts.length} 個，一起裝（見下方清單）`]
      : ['安裝資料夾名', `<code class="tag mono">${escapeHTML(skill.install?.dirName ?? '—')}</code>`],
    ['建議範圍', skill.install?.scope === 'project' ? '專案內 <code class="tag">.claude/skills</code>' : '全域 <code class="tag">~/.claude/skills</code>'],
    ['來源', sourceURL(skill)
      ? `<a href="${escapeHTML(sourceURL(skill))}" target="_blank" rel="noopener" class="link-arrow">${escapeHTML(skill.source.label ?? sourceURL(skill))}</a>`
      : escapeHTML(skill.source?.label ?? '—')],
    skill.author ? ['作者', escapeHTML(skill.author)] : null,
    skill.license ? ['授權', escapeHTML(skill.license)] : null,
    skill.addedAt ? ['收錄於', escapeHTML(skill.addedAt)] : null,
    skill.updatedAt ? ['更新於', escapeHTML(skill.updatedAt)] : null,
  ].filter(Boolean);

  const links = (skill.links ?? [])
    .map(
      (l) =>
        `<a class="link-arrow" href="${escapeHTML(l.url)}" target="_blank" rel="noopener">${escapeHTML(l.label ?? l.url)}</a>`
    )
    .join('<br />');

  return `
    <div data-intro>
      <div class="row" style="gap: var(--space-2); flex-wrap: wrap; margin-bottom: var(--space-3)">
        ${badges}${(skill.tags ?? []).map((t) => `<span class="tag">${escapeHTML(t)}</span>`).join('')}
      </div>
      <p style="color: var(--text-muted)">${escapeHTML(skill.summary)}</p>
    </div>

    ${section('什麼時候會用到', list(skill.usage))}
    ${section('重點', list(skill.highlights))}

    ${
      parts.length
        ? section(
            `包含 ${parts.length} 份，安裝時一起裝`,
            `<ul class="detail__list">${parts
              .map(
                (p) =>
                  `<li><span><code class="tag mono">${escapeHTML(p.dirName)}</code>${
                    p.summary ? ` ${escapeHTML(p.summary)}` : ''
                  }</span></li>`
              )
              .join('')}</ul>`
          )
        : ''
    }

    ${
      skill.install?.command
        ? section(
            '一行裝完',
            `<div class="code">
               <div class="code__bar">
                 <span class="code__title">terminal</span>
                 <button class="btn btn--sm btn--ghost" data-copy="closest"
                         data-copy-message="已複製安裝指令" data-motion="press">
                   <span class="btn__icon">${Icons.copy}</span>
                   <span data-copy-label>複製</span>
                 </button>
               </div>
               <pre class="code__body">${escapeHTML(skill.install.command)}</pre>
             </div>`
          )
        : ''
    }

    ${section(
      '基本資料',
      `<dl class="detail__meta">${meta.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('')}</dl>`
    )}

    ${section(
      '包含的檔案',
      list(skill.install?.files) || '<p class="faint" style="font-size: var(--text-sm)">未特別註明，預設為整個 skill 資料夾</p>'
    )}

    ${skill.install?.requires?.length ? section('需要先有', list(skill.install.requires)) : ''}
    ${skill.install?.notes ? section('注意事項', `<p class="muted" style="font-size: var(--text-sm)">${escapeHTML(skill.install.notes)}</p>`) : ''}
    ${links ? section('相關連結', `<div class="stack" style="gap: var(--space-2); font-size: var(--text-sm)">${links}</div>`) : ''}

    <section data-intro>
      <p class="detail__section-title">安裝提示詞（貼給 AI 就會自己裝好）</p>
      <div class="code">
        <div class="code__bar">
          <span class="code__title">install-${escapeHTML(skill.id)}.md</span>
          <button class="btn btn--sm btn--ghost" data-copy="#detailPromptText"
                  data-copy-message="已複製 ${escapeHTML(skill.name)} 的安裝提示詞" data-motion="press">
            <span class="btn__icon">${Icons.copy}</span>
            <span data-copy-label>複製</span>
          </button>
        </div>
        <pre class="code__body" id="detailPromptText">${escapeHTML(skill.installPrompt)}</pre>
      </div>
    </section>`;
}

/* ==========================================================================
   事件
   ========================================================================== */
function bindStaticEvents() {
  /* 搜尋 */
  el.search.addEventListener('input', () => {
    state.query = el.search.value;
    apply();
  });
  el.search.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      el.search.value = '';
      state.query = '';
      apply();
    }
  });
  document.addEventListener('keydown', (e) => {
    if (e.key !== '/' || e.metaKey || e.ctrlKey) return;
    const tag = document.activeElement?.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA') return;
    e.preventDefault();
    el.search.focus();
    el.search.select();
  });

  /* 篩選 chips */
  el.filters.addEventListener('click', (e) => {
    const catBtn = e.target.closest('[data-filter-category]');
    const tagBtn = e.target.closest('[data-filter-tag]');
    if (catBtn) {
      state.category = catBtn.dataset.filterCategory;
    } else if (tagBtn) {
      const value = tagBtn.dataset.filterTag;
      state.tag = state.tag === value ? null : value; // 再按一次取消
    } else {
      return;
    }
    syncChips();
    apply();
  });

  /* 檢視切換 */
  el.viewSwitch.addEventListener('segmented:change', (e) => {
    state.view = e.detail.value;
    try {
      localStorage.setItem(VIEW_KEY, state.view);
    } catch {
      /* 忽略 */
    }
    Motion.flip(el.grid, () => {
      el.grid.dataset.view = state.view;
    }, { itemSelector: '.skill-card' });
    scheduleRefresh();
  });

  /* 卡片：勾選 / 複製 / 開詳情 */
  el.grid.addEventListener('change', (e) => {
    const input = e.target.closest('.check__input');
    if (!input) return;
    const card = input.closest('.skill-card');
    if (!card) return;
    setSelected(card.dataset.skillId, input.checked, { syncInput: false });
    syncSelection();
  });

  el.grid.addEventListener('click', (e) => {
    const card = e.target.closest('.skill-card');
    if (!card) return;

    const copyBtn = e.target.closest('[data-copy-skill]');
    if (copyBtn) {
      const skill = state.byId.get(copyBtn.dataset.copySkill);
      if (skill) Components.copyWithFeedback(skill.installPrompt, copyBtn, `已複製 ${skill.name} 的安裝提示詞`);
      return;
    }

    if (e.target.closest('[data-select-stop]')) return; // 勾選框交給原生 label 行為
    openDetail(card.dataset.skillId);
  });

  el.grid.addEventListener('keydown', (e) => {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    const card = e.target.closest('.skill-card');
    if (!card || e.target !== card) return;
    e.preventDefault();
    openDetail(card.dataset.skillId);
  });

  /* 多選操作列 */
  $('#selectionClear').addEventListener('click', clearSelection);
  $('#selectionInstall').addEventListener('click', async () => {
    const list = selectedSkills();
    if (!list.length) return;
    const text = buildCombinedPrompt(list);
    openInstallModal(list);
    await Components.copyWithFeedback(
      text,
      null,
      `已複製 ${list.length} 個 skill 的安裝提示詞，貼給 AI 就會開始裝`
    );
  });

  /* 工具列按鈕 */
  $('#selectAll').addEventListener('click', () => {
    if (!state.visible.length) return;
    const allSelected = state.visible.every((s) => state.selected.has(s.id));
    for (const s of state.visible) setSelected(s.id, !allSelected);
    syncSelection();
  });
  $('#clearFilters').addEventListener('click', resetFilters);
  $('#emptyReset').addEventListener('click', resetFilters);

  /* 開著詳情時按上下頁 / 直接改網址 */
  window.addEventListener('hashchange', openFromHash);
}

/* ==========================================================================
   狀態保存與網址
   ========================================================================== */
function restoreFromStorage() {
  try {
    const saved = JSON.parse(localStorage.getItem(SELECTION_KEY) ?? '[]');
    for (const id of saved) {
      if (state.byId.has(id)) setSelected(id, true);
    }
    // 檢視模式可能是舊版存下來的，對不上就退回預設
    const view = localStorage.getItem(VIEW_KEY);
    const available = $$('.segmented__item', el.viewSwitch).map((i) => i.dataset.value);
    if (view && available.includes(view)) state.view = view;
  } catch {
    /* 壞掉就當作沒選 */
  }

  // segmented 初始化時排了一次 rAF 定位指示塊，這裡也排在 rAF 之後才不會被蓋回去
  const item = $$('.segmented__item', el.viewSwitch).find((i) => i.dataset.value === state.view);
  if (item && item.getAttribute('aria-selected') !== 'true') {
    requestAnimationFrame(() => el.viewSwitch.__segmentedSelect?.(item, false));
  }
}

function readURL() {
  const p = new URLSearchParams(location.search);
  if (p.get('q')) {
    state.query = p.get('q');
    el.search.value = state.query;
  }
  if (p.get('cat')) state.category = p.get('cat');
  if (p.get('tag')) state.tag = p.get('tag');
  syncChips();
}

function writeURL() {
  const p = new URLSearchParams();
  if (state.query.trim()) p.set('q', state.query.trim());
  if (state.category !== 'all') p.set('cat', state.category);
  if (state.tag) p.set('tag', state.tag);
  const qs = p.toString();
  history.replaceState(null, '', `${location.pathname}${qs ? `?${qs}` : ''}${location.hash}`);
}

function openFromHash() {
  const id = decodeURIComponent(location.hash.slice(1));
  if (id && state.byId.has(id)) openDetail(id);
}

/* ---- GSAP 是 defer 載入的，等 DOM 與 script 都到位再啟動 ------------------ */
if (document.readyState === 'loading') {
  window.addEventListener('DOMContentLoaded', start);
} else {
  start();
}
