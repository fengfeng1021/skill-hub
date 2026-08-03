/* ==========================================================================
   Motion — 全站共用 GSAP 動效
   ==========================================================================
   使用方式有兩種：

   1. 宣告式（優先用這個）：在 HTML 上加 data-motion
        <div data-motion="reveal">…</div>
        <button data-motion="press ripple">…</button>
        <article data-motion="lift glow">…</article>
      多個效果用空白分隔，參數用 data-motion-* 傳。

   2. 程式式：Motion.toast()、Motion.modal()、Motion.flip() …

   規則：
   - 頁面裡不要自己寫一次性的 gsap.to()。要新效果就在這裡加一個 recipe，
     這樣所有頁面共用同一套手感，改一次全站都會跟著改。
   - reduced motion 由 gsap.matchMedia() 統一處理：所有 recipe 都會拿到
     ctx.reduced，為 true 時直接跳到最終狀態，不做位移。
   ========================================================================== */

const Motion = (() => {
  'use strict';

  const hasGSAP = typeof window !== 'undefined' && typeof window.gsap !== 'undefined';
  if (!hasGSAP) {
    console.warn('[Motion] 找不到 GSAP，動效停用，功能仍可正常使用。');
  }

  const gsap = window.gsap;
  const ScrollTrigger = window.ScrollTrigger;
  const Flip = window.Flip;

  /** 目前是否為減少動態模式；init() 之後才有正確值 */
  let reduced = false;
  let mm = null;
  let inited = false;

  /** recipe 名稱 → 綁定函式 */
  const recipes = new Map();
  /** 已綁定過的元素，避免 scan() 重複掛 */
  const bound = new WeakMap();

  /* ---- 共用參數 --------------------------------------------------------- */
  const D = {
    fast: 0.24,
    base: 0.42,
    slow: 0.72,
    ease: 'power2.out',
    easeStrong: 'power3.out',
    easeBack: 'back.out(1.7)',
    easeInOut: 'power2.inOut',
  };

  const num = (el, key, fallback) => {
    const v = el.dataset[key];
    return v === undefined || v === '' ? fallback : parseFloat(v);
  };
  const str = (el, key, fallback) => el.dataset[key] ?? fallback;

  /* ======================================================================
     初始化
     ====================================================================== */
  function init(options = {}) {
    if (inited) return;
    if (!hasGSAP) {
      // GSAP 沒載入成功：拿掉 .js，讓 CSS 預先隱藏的內容直接顯示，
      // 網站功能不受影響，只是沒有動效。
      document.documentElement.classList.remove('js');
      inited = true;
      return;
    }
    inited = true;

    if (ScrollTrigger) gsap.registerPlugin(ScrollTrigger);
    if (Flip) gsap.registerPlugin(Flip);

    gsap.defaults({ duration: D.base, ease: D.ease });

    mm = gsap.matchMedia();
    mm.add(
      {
        motionOK: '(prefers-reduced-motion: no-preference)',
        motionReduce: '(prefers-reduced-motion: reduce)',
      },
      (ctx) => {
        reduced = !!ctx.conditions.motionReduce;
        scan(options.root ?? document);
        // matchMedia 條件切換時，GSAP 會自動 revert 這個區塊建立的所有動畫與
        // ScrollTrigger，所以只要把綁定紀錄清掉，下次就能重新掛。
        return () => {
          for (const el of document.querySelectorAll('[data-motion]')) bound.delete(el);
        };
      }
    );
  }

  /** 掃描並綁定 root 底下所有 [data-motion]。動態插入 DOM 後要再呼叫一次。 */
  function scan(root = document) {
    if (!hasGSAP) return;
    const nodes = root.querySelectorAll('[data-motion]');
    for (const el of nodes) {
      const names = el.dataset.motion.split(/\s+/).filter(Boolean);
      let applied = bound.get(el);
      if (!applied) {
        applied = new Set();
        bound.set(el, applied);
      }
      for (const name of names) {
        if (applied.has(name)) continue;
        const recipe = recipes.get(name);
        if (!recipe) {
          console.warn(`[Motion] 未知的效果："${name}"`, el);
          continue;
        }
        applied.add(name);
        recipe(el, { reduced });
      }
    }
    // batch 型的 reveal 需要在全部登記完後統一建立
    flushReveal();
  }

  const define = (name, fn) => recipes.set(name, fn);

  /* ======================================================================
     Recipe：進場
     ====================================================================== */

  /** 等待收集的 reveal 元素，依 preset 分組後用 ScrollTrigger.batch 一次建立 */
  let revealQueue = [];
  let revealScheduled = false;

  const REVEAL_PRESETS = {
    up: { from: { y: 26, autoAlpha: 0 }, to: { y: 0, autoAlpha: 1 } },
    down: { from: { y: -26, autoAlpha: 0 }, to: { y: 0, autoAlpha: 1 } },
    left: { from: { x: -32, autoAlpha: 0 }, to: { x: 0, autoAlpha: 1 } },
    right: { from: { x: 32, autoAlpha: 0 }, to: { x: 0, autoAlpha: 1 } },
    fade: { from: { autoAlpha: 0 }, to: { autoAlpha: 1 } },
    scale: { from: { scale: 0.94, autoAlpha: 0 }, to: { scale: 1, autoAlpha: 1 } },
    blur: { from: { autoAlpha: 0, filter: 'blur(10px)' }, to: { autoAlpha: 1, filter: 'blur(0px)' } },
  };

  define('reveal', (el, ctx) => {
    const preset = REVEAL_PRESETS[str(el, 'motionPreset', 'up')] ?? REVEAL_PRESETS.up;

    if (ctx.reduced || !ScrollTrigger) {
      gsap.set(el, preset.to);
      return;
    }
    gsap.set(el, preset.from);
    revealQueue.push({ el, preset });
    revealScheduled = true;
  });

  function flushReveal() {
    if (!revealScheduled || !ScrollTrigger) return;
    revealScheduled = false;
    const queue = revealQueue;
    revealQueue = [];
    if (!queue.length) return;

    // 依 preset + start 分組，同組共用一個 batch，進場才有整齊的 stagger
    const groups = new Map();
    for (const item of queue) {
      const start = str(item.el, 'motionStart', 'top 88%');
      const key = `${JSON.stringify(item.preset.to)}|${start}`;
      if (!groups.has(key)) groups.set(key, { preset: item.preset, start, els: [] });
      groups.get(key).els.push(item.el);
    }

    for (const g of groups.values()) {
      ScrollTrigger.batch(g.els, {
        start: g.start,
        once: true,
        onEnter: (batch) => {
          gsap.to(batch, {
            ...g.preset.to,
            duration: D.slow,
            ease: D.easeStrong,
            stagger: { each: 0.06, from: 'start' },
            overwrite: true,
            onComplete: () => gsap.set(batch, { clearProps: 'willChange,filter' }),
          });
        },
      });
    }
  }

  /** 子元素依序進場：容器加 data-motion="stagger"，子元素用 data-motion-child 選取 */
  define('stagger', (el, ctx) => {
    const sel = str(el, 'motionChild', ':scope > *');
    const children = el.querySelectorAll(sel);
    if (!children.length) return;

    if (ctx.reduced || !ScrollTrigger) {
      gsap.set(children, { autoAlpha: 1, y: 0 });
      return;
    }
    gsap.set(children, { y: 20, autoAlpha: 0 });
    ScrollTrigger.create({
      trigger: el,
      start: str(el, 'motionStart', 'top 85%'),
      once: true,
      onEnter: () =>
        gsap.to(children, {
          y: 0,
          autoAlpha: 1,
          duration: D.slow,
          ease: D.easeStrong,
          stagger: num(el, 'motionStagger', 0.07),
        }),
    });
  });

  /* ======================================================================
     Recipe：滑鼠互動
     ====================================================================== */

  /** hover 抬升 */
  define('lift', (el, ctx) => {
    if (ctx.reduced) return;
    const dist = num(el, 'motionLift', 4);
    const scale = num(el, 'motionScale', 1);
    const tween = gsap.to(el, {
      y: -dist,
      scale,
      duration: D.fast,
      ease: D.ease,
      paused: true,
    });
    el.addEventListener('mouseenter', () => tween.play());
    el.addEventListener('mouseleave', () => tween.reverse());
    el.addEventListener('focusin', () => tween.play());
    el.addEventListener('focusout', () => tween.reverse());
  });

  /** 按下回饋 */
  define('press', (el, ctx) => {
    if (ctx.reduced) return;
    const to = num(el, 'motionPress', 0.96);
    const down = () => gsap.to(el, { scale: to, duration: 0.1, ease: D.ease, overwrite: 'auto' });
    const up = () => gsap.to(el, { scale: 1, duration: 0.32, ease: D.easeBack, overwrite: 'auto' });
    el.addEventListener('pointerdown', down);
    el.addEventListener('pointerup', up);
    el.addEventListener('pointercancel', up);
    el.addEventListener('pointerleave', up);
  });

  /** 點擊漣漪 */
  define('ripple', (el, ctx) => {
    if (ctx.reduced) return;
    el.addEventListener('pointerdown', (e) => {
      const rect = el.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height) * 2;
      const dot = document.createElement('span');
      dot.className = 'btn__ripple';
      dot.style.width = dot.style.height = `${size}px`;
      dot.style.left = `${e.clientX - rect.left - size / 2}px`;
      dot.style.top = `${e.clientY - rect.top - size / 2}px`;
      el.appendChild(dot);
      gsap.fromTo(
        dot,
        { scale: 0, opacity: 0.35 },
        { scale: 1, opacity: 0, duration: 0.62, ease: D.easeStrong, onComplete: () => dot.remove() }
      );
    });
  });

  /** 磁吸：元素朝游標偏移 */
  define('magnetic', (el, ctx) => {
    if (ctx.reduced) return;
    const strength = num(el, 'motionStrength', 0.32);
    const xTo = gsap.quickTo(el, 'x', { duration: 0.5, ease: 'power3.out' });
    const yTo = gsap.quickTo(el, 'y', { duration: 0.5, ease: 'power3.out' });
    el.addEventListener('pointermove', (e) => {
      const r = el.getBoundingClientRect();
      xTo((e.clientX - (r.left + r.width / 2)) * strength);
      yTo((e.clientY - (r.top + r.height / 2)) * strength);
    });
    el.addEventListener('pointerleave', () => {
      xTo(0);
      yTo(0);
    });
  });

  /** 游標光暈：把座標寫進 --mx / --my，實際樣式在 CSS */
  define('glow', (el, ctx) => {
    if (ctx.reduced) return;
    el.addEventListener('pointermove', (e) => {
      const r = el.getBoundingClientRect();
      el.style.setProperty('--mx', `${e.clientX - r.left}px`);
      el.style.setProperty('--my', `${e.clientY - r.top}px`);
    });
  });

  /** 3D 傾斜 */
  define('tilt', (el, ctx) => {
    if (ctx.reduced) return;
    const max = num(el, 'motionTilt', 7);
    gsap.set(el, { transformPerspective: 900, transformOrigin: 'center' });
    const rx = gsap.quickTo(el, 'rotationX', { duration: 0.5, ease: 'power3.out' });
    const ry = gsap.quickTo(el, 'rotationY', { duration: 0.5, ease: 'power3.out' });
    el.addEventListener('pointermove', (e) => {
      const r = el.getBoundingClientRect();
      rx((0.5 - (e.clientY - r.top) / r.height) * max * 2);
      ry(((e.clientX - r.left) / r.width - 0.5) * max * 2);
    });
    el.addEventListener('pointerleave', () => {
      rx(0);
      ry(0);
    });
  });

  /* ======================================================================
     Recipe：持續 / 捲動
     ====================================================================== */

  /** 數字滾動 */
  define('count', (el, ctx) => {
    const target = num(el, 'motionTo', parseFloat(el.textContent) || 0);
    const decimals = num(el, 'motionDecimals', 0);
    const render = (v) => {
      el.textContent = v.toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      });
    };
    if (ctx.reduced || !ScrollTrigger) {
      render(target);
      return;
    }
    const obj = { v: 0 };
    render(0);
    ScrollTrigger.create({
      trigger: el,
      start: 'top 92%',
      once: true,
      onEnter: () =>
        gsap.to(obj, {
          v: target,
          duration: num(el, 'motionDuration', 1.4),
          ease: 'power2.out',
          onUpdate: () => render(obj.v),
        }),
    });
  });

  /** 視差 */
  define('parallax', (el, ctx) => {
    if (ctx.reduced || !ScrollTrigger) return;
    gsap.to(el, {
      yPercent: num(el, 'motionShift', -12),
      ease: 'none',
      scrollTrigger: {
        trigger: str(el, 'motionTrigger', null) ? document.querySelector(el.dataset.motionTrigger) : el,
        start: 'top bottom',
        end: 'bottom top',
        scrub: true,
      },
    });
  });

  /** 漂浮 */
  define('float', (el, ctx) => {
    if (ctx.reduced) return;
    gsap.to(el, {
      y: num(el, 'motionAmp', 10),
      duration: num(el, 'motionDuration', 3),
      ease: 'sine.inOut',
      repeat: -1,
      yoyo: true,
      delay: num(el, 'motionDelay', 0),
    });
  });

  /** 無縫跑馬燈：內容會自動複製一份 */
  define('marquee', (el, ctx) => {
    const track = el.firstElementChild;
    if (!track) return;
    if (ctx.reduced) return;
    track.append(...[...track.children].map((c) => c.cloneNode(true)));
    const half = track.scrollWidth / 2;
    const tween = gsap.to(track, {
      x: -half,
      duration: half / num(el, 'motionSpeed', 42),
      ease: 'none',
      repeat: -1,
    });
    el.addEventListener('pointerenter', () => gsap.to(tween, { timeScale: 0.25, duration: 0.4 }));
    el.addEventListener('pointerleave', () => gsap.to(tween, { timeScale: 1, duration: 0.4 }));
  });

  /** 捲動進度條 */
  define('scroll-progress', (el, ctx) => {
    if (!ScrollTrigger) return;
    gsap.to(el, {
      scaleX: 1,
      ease: 'none',
      scrollTrigger: { start: 0, end: 'max', scrub: 0.25 },
    });
  });

  /** 捲動時縮起的 header */
  define('shrink-header', (el, ctx) => {
    if (!ScrollTrigger) return;
    ScrollTrigger.create({
      start: 'top -80',
      end: 'max',
      onToggle: (self) => el.classList.toggle('is-stuck', self.isActive),
    });
  });

  /* ======================================================================
     程式化 API
     ====================================================================== */

  /** 勾選框的勾勾動畫 */
  function check(boxEl, checked) {
    const path = boxEl.querySelector('svg path');
    if (!path) return;
    const len = path.getTotalLength?.() ?? 24;
    boxEl.style.setProperty('--check-len', len);
    if (!hasGSAP || reduced) {
      path.style.strokeDashoffset = checked ? 0 : len;
      return;
    }
    gsap.to(path, {
      strokeDashoffset: checked ? 0 : len,
      duration: checked ? 0.3 : 0.16,
      ease: checked ? D.easeStrong : D.ease,
      overwrite: true,
    });
    if (checked) {
      gsap.fromTo(boxEl, { scale: 0.8 }, { scale: 1, duration: 0.42, ease: D.easeBack, overwrite: 'auto' });
    }
  }

  /** Modal 開關。回傳 { open, close, isOpen } */
  function modal(root) {
    const backdrop = root.querySelector('.modal__backdrop');
    const panel = root.querySelector('.modal__panel');
    let tl = null;
    let lastFocus = null;

    const build = () => {
      const t = gsap.timeline({ paused: true, defaults: { ease: D.easeStrong } });
      t.set(root, { visibility: 'visible' })
        .fromTo(backdrop, { opacity: 0 }, { opacity: 1, duration: D.fast }, 0)
        .fromTo(
          panel,
          { opacity: 0, y: reduced ? 0 : 24, scale: reduced ? 1 : 0.97 },
          { opacity: 1, y: 0, scale: 1, duration: reduced ? 0.01 : 0.46 },
          0.04
        )
        .fromTo(
          panel.querySelectorAll('[data-modal-item]'),
          { opacity: 0, y: reduced ? 0 : 12 },
          { opacity: 1, y: 0, duration: 0.4, stagger: 0.05 },
          0.12
        );
      return t;
    };

    function open() {
      if (!hasGSAP) {
        root.classList.add('is-open');
        return;
      }
      lastFocus = document.activeElement;
      root.classList.add('is-open');
      document.body.classList.add('is-locked');
      tl = tl ?? build();
      tl.play(0);
      (panel.querySelector('[data-autofocus]') ?? panel).focus?.({ preventScroll: true });
    }

    function close() {
      if (!hasGSAP) {
        root.classList.remove('is-open');
        return;
      }
      tl?.timeScale(1.5).reverse().eventCallback('onReverseComplete', () => {
        root.classList.remove('is-open');
        gsap.set(root, { visibility: 'hidden' });
      });
      document.body.classList.remove('is-locked');
      lastFocus?.focus?.({ preventScroll: true });
    }

    // 點背景、按 Esc 關閉
    backdrop?.addEventListener('click', close);
    root.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') close();
      if (e.key === 'Tab') trapFocus(e, panel);
    });

    return { open, close, isOpen: () => root.classList.contains('is-open'), root, panel };
  }

  function trapFocus(e, panel) {
    const items = panel.querySelectorAll(
      'a[href], button:not([disabled]), input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    if (!items.length) return;
    const first = items[0];
    const last = items[items.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }

  /* ---- Toast ------------------------------------------------------------ */
  const ICONS = {
    success:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>',
    error:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>',
    info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><path d="M12 8h.01M11 12h1v4h1"/></svg>',
  };

  let toastStack = null;

  function toast(message, { type = 'success', duration = 2600 } = {}) {
    if (!toastStack) {
      toastStack = document.querySelector('.toast-stack');
      if (!toastStack) {
        toastStack = document.createElement('div');
        toastStack.className = 'toast-stack';
        document.body.appendChild(toastStack);
      }
    }

    const el = document.createElement('div');
    el.className = `toast toast--${type}`;
    el.setAttribute('role', type === 'error' ? 'alert' : 'status');
    el.innerHTML = `
      <span class="toast__icon">${ICONS[type] ?? ICONS.info}</span>
      <span class="toast__text">${escapeHTML(message)}</span>
      <span class="toast__timer"></span>`;
    toastStack.appendChild(el);

    if (!hasGSAP) {
      setTimeout(() => el.remove(), duration);
      return el;
    }

    const timer = el.querySelector('.toast__timer');
    const tl = gsap.timeline();
    tl.fromTo(
      el,
      { autoAlpha: 0, y: reduced ? 0 : 16, scale: reduced ? 1 : 0.96 },
      { autoAlpha: 1, y: 0, scale: 1, duration: reduced ? 0.01 : 0.42, ease: D.easeBack }
    )
      .fromTo(timer, { scaleX: 1 }, { scaleX: 0, duration: duration / 1000, ease: 'none' }, 0)
      .to(el, {
        autoAlpha: 0,
        y: reduced ? 0 : -8,
        scale: reduced ? 1 : 0.98,
        duration: reduced ? 0.01 : 0.3,
        ease: D.ease,
        onComplete: () => el.remove(),
      });

    el.addEventListener('pointerenter', () => tl.pause());
    el.addEventListener('pointerleave', () => tl.resume());
    return el;
  }

  const escapeHTML = (s) =>
    String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

  /* ---- 浮出式操作列 ------------------------------------------------------ */
  function floatingBar(el) {
    let visible = false;
    if (hasGSAP) gsap.set(el, { xPercent: -50, y: 24, autoAlpha: 0 });

    return {
      show() {
        if (visible) return;
        visible = true;
        el.classList.add('is-visible');
        if (!hasGSAP) return;
        gsap.to(el, {
          y: 0,
          autoAlpha: 1,
          duration: reduced ? 0.01 : 0.5,
          ease: D.easeBack,
          overwrite: 'auto',
        });
      },
      hide() {
        if (!visible) return;
        visible = false;
        if (!hasGSAP) {
          el.classList.remove('is-visible');
          return;
        }
        gsap.to(el, {
          y: 24,
          autoAlpha: 0,
          duration: reduced ? 0.01 : 0.28,
          ease: D.ease,
          overwrite: 'auto',
          onComplete: () => el.classList.remove('is-visible'),
        });
      },
      /** 數字變化時彈一下 */
      bump(target) {
        if (!hasGSAP || reduced) return;
        gsap.fromTo(target, { scale: 1.3 }, { scale: 1, duration: 0.42, ease: D.easeBack, overwrite: 'auto' });
      },
    };
  }

  /* ---- Segmented 指示塊 -------------------------------------------------- */
  function segmented(container) {
    const thumb = container.querySelector('.segmented__thumb');
    const move = (target, animate = true) => {
      if (!thumb || !target) return;
      const cRect = container.getBoundingClientRect();
      const tRect = target.getBoundingClientRect();
      const vars = { x: tRect.left - cRect.left - 3, width: tRect.width };
      if (!hasGSAP || !animate || reduced) {
        gsap.set?.(thumb, vars) ?? Object.assign(thumb.style, { width: `${vars.width}px` });
        return;
      }
      gsap.to(thumb, { ...vars, duration: 0.44, ease: D.easeStrong, overwrite: 'auto' });
    };
    return { move };
  }

  /* ---- 篩選重排：有 Flip 就用 Flip，沒有就淡入 --------------------------- */
  function flip(container, mutate, { itemSelector = ':scope > *' } = {}) {
    if (!hasGSAP || !Flip || reduced) {
      mutate();
      return;
    }
    const items = container.querySelectorAll(itemSelector);
    const state = Flip.getState(items, { props: 'opacity' });
    mutate();
    Flip.from(state, {
      duration: 0.55,
      ease: D.easeStrong,
      scale: true,
      stagger: 0.02,
      absolute: true,
      onEnter: (els) =>
        gsap.fromTo(
          els,
          { opacity: 0, scale: 0.92 },
          { opacity: 1, scale: 1, duration: 0.45, ease: D.easeStrong, stagger: 0.02 }
        ),
      onLeave: (els) => gsap.to(els, { opacity: 0, scale: 0.92, duration: 0.28, ease: D.ease }),
    });
  }

  /* ---- 小回饋 ------------------------------------------------------------ */
  function pulse(el) {
    if (!hasGSAP || reduced) return;
    gsap.fromTo(el, { scale: 0.88 }, { scale: 1, duration: 0.5, ease: D.easeBack, overwrite: 'auto' });
  }

  function shake(el) {
    if (!hasGSAP || reduced) return;
    gsap.fromTo(el, { x: -6 }, { x: 0, duration: 0.5, ease: 'elastic.out(1, 0.3)', overwrite: 'auto' });
  }

  /** 內容換掉時的交叉淡入，回傳 Promise */
  function swap(el, update) {
    if (!hasGSAP || reduced) {
      update();
      return Promise.resolve();
    }
    return new Promise((resolve) => {
      gsap
        .timeline()
        .to(el, { autoAlpha: 0, y: -6, duration: 0.16, ease: D.ease })
        .add(() => update())
        .to(el, { autoAlpha: 1, y: 0, duration: 0.3, ease: D.easeStrong, onComplete: resolve });
    });
  }

  /** 首屏載入序列：對 [data-intro] 依序進場 */
  function intro(root = document) {
    if (!hasGSAP) return;
    const items = root.querySelectorAll('[data-intro]');
    if (!items.length) return;
    if (reduced) {
      gsap.set(items, { autoAlpha: 1, y: 0 });
      return;
    }
    gsap.set(items, { autoAlpha: 0, y: 18 });
    gsap.to(items, {
      autoAlpha: 1,
      y: 0,
      duration: 0.85,
      ease: D.easeStrong,
      stagger: 0.08,
      delay: 0.1,
      onComplete: () => gsap.set(items, { clearProps: 'willChange' }),
    });
  }

  /** 主題切換：用圓形擴散遮罩過場 */
  function themeSwitch(apply, originEl) {
    if (!hasGSAP || reduced || !document.startViewTransition) {
      apply();
      return;
    }
    const r = originEl?.getBoundingClientRect();
    const x = r ? r.left + r.width / 2 : innerWidth - 60;
    const y = r ? r.top + r.height / 2 : 40;
    const end = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));

    document
      .startViewTransition(apply)
      .ready.then(() => {
        document.documentElement.animate(
          { clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${end}px at ${x}px ${y}px)`] },
          { duration: 520, easing: 'cubic-bezier(0.165, 0.84, 0.44, 1)', pseudoElement: '::view-transition-new(root)' }
        );
      })
      .catch(() => {});
  }

  /* ---- 工具 -------------------------------------------------------------- */
  const refresh = () => ScrollTrigger?.refresh();
  const isReduced = () => reduced;

  return {
    init,
    scan,
    define,
    check,
    modal,
    toast,
    floatingBar,
    segmented,
    flip,
    pulse,
    shake,
    swap,
    intro,
    themeSwitch,
    refresh,
    isReduced,
    D,
  };
})();

window.Motion = Motion;
export default Motion;
