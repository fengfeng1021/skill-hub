/* ==========================================================================
   Skill Card — 卡片模板
   收藏庫首頁與設計系統展示頁共用同一份模板，
   確保示範看到的樣子跟實際網站完全一致。
   ========================================================================== */

import { Icons } from './icons.js';

/**
 * 格狀 ↔ 清單切換要傳給 Motion.viewSwitch() 的選擇器。
 * 跟模板放在一起，改了結構才不會忘了同步動效。
 * fadeSelector 是「排成一列時會被擠到」的那幾塊：先淡出，卡片定位好再淡回來。
 * 勾選框、圖示、名稱不在裡面 —— 全程留著，使用者才看得出哪張卡片跑到哪裡。
 */
export const VIEW_SWITCH_OPTIONS = {
  itemSelector: '.skill-card',
  fadeSelector: '.skill-card__summary, .skill-card__tags, .skill-card__foot',
};

export const escapeHTML = (s) =>
  String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

/** 沒有圖示時用名稱開頭當視覺標記 */
export function initials(name = '') {
  const cleaned = String(name).replace(/[^\p{L}\p{N}\s-]/gu, '').trim();
  const parts = cleaned.split(/[\s-]+/).filter(Boolean);
  if (!parts.length) return '?';
  if (/^[\x00-\x7F]+$/.test(cleaned)) {
    return (parts.length > 1 ? parts[0][0] + parts[1][0] : parts[0].slice(0, 2)).toUpperCase();
  }
  return cleaned.slice(0, 1);
}

function badges(skill) {
  const out = [];
  if (skill.official) out.push(`<span class="badge badge--official">${Icons.check}官方</span>`);
  if (skill.source?.kind === 'local') out.push(`<span class="badge badge--local">本庫託管</span>`);
  if (skill.includedSkills?.length) {
    out.push(`<span class="badge badge--curated">精選組合 · ${skill.installCount}</span>`);
  }
  // parts 是同來源套件的多個資料夾；跨來源精選組合包由 includedSkills 表示。
  if (skill.parts?.length > 1) out.push(`<span class="badge badge--bundle">${skill.parts.length} 個資料夾</span>`);
  return out.join('');
}

function sourceLine(skill) {
  const kind = skill.source?.kind;
  const icon = kind === 'github' ? Icons.github : kind === 'local' ? Icons.folder : Icons.link;
  const label = escapeHTML(skill.source?.label ?? '未註明來源');
  return `<span class="skill-card__source"><span style="width:.95em;height:.95em;flex:none">${icon}</span><span class="truncate">${label}</span></span>`;
}

/**
 * 產生一張 skill 卡片。
 * @param {object} skill    api/index.json 裡的 skill 物件
 * @param {object} options  { selected: boolean, selectable: boolean }
 */
export function renderSkillCard(skill, { selected = false, selectable = true } = {}) {
  const tags = (skill.tags ?? [])
    .slice(0, 3)
    .map((t) => `<span class="tag">${escapeHTML(t)}</span>`)
    .join('');
  const included = skill.includedSkills ?? [];
  const bundleSummary = included.length
    ? `<div class="skill-card__bundle-summary">
         <span class="skill-card__bundle-label">完整內含</span>
         <span class="skill-card__bundle-names">${included.map((item) => escapeHTML(item.name)).join('、')}</span>
       </div>`
    : '';

  return `
    <article class="card card--glow skill-card${selected ? ' is-selected' : ''}"
             data-motion="lift glow" data-intro
             data-skill-id="${escapeHTML(skill.id)}"
             data-category="${escapeHTML(skill.category ?? '')}"
             tabindex="0" role="button"
             aria-label="查看 ${escapeHTML(skill.name)} 的詳細資訊">
      ${
        selectable
          ? `<label class="check skill-card__check" data-check data-select-stop>
               <input class="check__input" type="checkbox" ${selected ? 'checked' : ''}
                      aria-label="選取 ${escapeHTML(skill.name)}" />
               <span class="check__box">${Icons.check}</span>
             </label>`
          : ''
      }

      <div class="skill-card__top">
        <span class="skill-card__icon" aria-hidden="true">${escapeHTML(initials(skill.name))}</span>
        <h3 class="skill-card__name"><span class="truncate">${escapeHTML(skill.name)}</span></h3>
      </div>

      <p class="skill-card__summary clamp-3">${escapeHTML(skill.summary)}</p>

      ${bundleSummary}

      <div class="skill-card__tags">${badges(skill)}${tags}</div>

      <div class="skill-card__foot">
        ${sourceLine(skill)}
        <div class="skill-card__actions">
          <button class="btn btn--sm btn--ghost" data-copy-skill="${escapeHTML(skill.id)}"
                  data-motion="press" data-tooltip="複製這個 skill 的安裝提示詞" aria-label="複製安裝提示詞">
            <span class="btn__icon">${Icons.copy}</span>
          </button>
        </div>
      </div>
    </article>`;
}

export default renderSkillCard;
