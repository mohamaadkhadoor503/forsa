/* فرصة — front-end behaviour.
 * Each feature is a small self-contained module initialised on DOM ready.
 * Everything degrades gracefully: pages work without JS, GSAP or Swiper. */
(function () {
  "use strict";

  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const isRTL = document.documentElement.dir === "rtl";
  const finePointer = window.matchMedia("(pointer: fine)").matches;
  const csrf = () => (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || ($("[name=csrfmiddlewaretoken]") || {}).value || "";

  /* ---------- Toasts ---------- */
  const TOAST_ICONS = {
    success: '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    error: '<path d="M6 6l12 12M18 6 6 18"/>',
    warning: '<path d="M12 7.5v5.5M12 16.5v.01"/>',
    info: '<path d="M12 11v5.5M12 7.5v.01"/>',
  };
  function toast(message, type = "success") {
    let box = $(".toasts");
    if (!box) {
      box = document.createElement("div");
      box.className = "toasts";
      box.setAttribute("role", "status");
      box.setAttribute("aria-live", "polite");
      document.body.appendChild(box);
    }
    const el = document.createElement("div");
    el.className = `toast toast--${type}`;
    el.innerHTML = `<span class="toast__icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round">${TOAST_ICONS[type] || TOAST_ICONS.info}</svg></span><span class="toast__text"></span><button class="toast__close" type="button" aria-label="close">✕</button>`;
    el.querySelector(".toast__text").textContent = message;
    const close = () => { el.classList.add("is-leaving"); setTimeout(() => el.remove(), 350); };
    el.querySelector(".toast__close").addEventListener("click", close);
    box.appendChild(el);
    setTimeout(close, 5000);
  }
  window.toast = toast;
  function initFlashMessages() {
    $$("[data-flash]").forEach((n, i) => setTimeout(() => toast(n.dataset.flash, n.dataset.type || "info"), 250 + i * 150));
  }

  /* ---------- Theme ---------- */
  function initTheme() {
    $$("[data-theme-toggle]").forEach((btn) =>
      btn.addEventListener("click", () => {
        const root = document.documentElement;
        const next = root.dataset.theme === "dark" ? "light" : "dark";
        const apply = () => { root.dataset.theme = next; try { localStorage.setItem("theme", next); } catch (e) {} };
        if (document.startViewTransition && !reduceMotion) document.startViewTransition(apply); else apply();
      })
    );
  }

  /* ---------- Navigation ---------- */
  function initNav() {
    const nav = $(".nav");
    if (nav && !nav.classList.contains("nav--solid")) {
      const onScroll = () => nav.classList.toggle("is-scrolled", window.scrollY > 12);
      onScroll();
      window.addEventListener("scroll", onScroll, { passive: true });
    }
    // Drawer
    const drawer = $("#mobile-drawer");
    $$("[data-drawer-open]").forEach((b) => b.addEventListener("click", () => toggleDrawer(true)));
    $$("[data-drawer-close]").forEach((b) => b.addEventListener("click", () => toggleDrawer(false)));
    function toggleDrawer(open) {
      if (!drawer) return;
      drawer.classList.toggle("is-open", open);
      drawer.setAttribute("aria-hidden", String(!open));
      document.body.style.overflow = open ? "hidden" : "";
      $$(".drawer__panel > a", drawer).forEach((a, i) => (a.style.transitionDelay = open ? `${80 + i * 35}ms` : "0ms"));
      if (open) setTimeout(() => ($(".drawer__panel a", drawer) || {}).focus?.(), 300);
    }
    // Dropdowns
    $$("[data-dropdown]").forEach((dd) => {
      const trigger = $("[data-dropdown-trigger]", dd);
      trigger?.addEventListener("click", (e) => {
        e.stopPropagation();
        const open = !dd.classList.contains("is-open");
        $$("[data-dropdown].is-open").forEach((o) => o.classList.remove("is-open"));
        dd.classList.toggle("is-open", open);
        trigger.setAttribute("aria-expanded", String(open));
      });
    });
    document.addEventListener("click", (e) => {
      $$("[data-dropdown].is-open").forEach((dd) => { if (!dd.contains(e.target)) dd.classList.remove("is-open"); });
    });
    document.addEventListener("keydown", (e) => {
      if (e.key !== "Escape") return;
      $$("[data-dropdown].is-open").forEach((dd) => dd.classList.remove("is-open"));
      toggleDrawer(false);
      $$(".modal.is-open").forEach(closeModal);
      closeFilters();
      $(".dash__side")?.classList.remove("is-open");
    });
    // Dashboard sidebar
    $$("[data-dash-toggle]").forEach((b) => b.addEventListener("click", () => $(".dash__side")?.classList.toggle("is-open")));
  }

  /* ---------- Modals ---------- */
  let lastFocus = null;
  function openModal(m) {
    lastFocus = document.activeElement;
    m.classList.add("is-open");
    m.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
    setTimeout(() => ($("input, textarea, select, button", $(".modal__dialog", m)) || {}).focus?.(), 200);
  }
  function closeModal(m) {
    m.classList.remove("is-open");
    m.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
    lastFocus?.focus?.();
  }
  function initModals() {
    $$("[data-modal-open]").forEach((b) => b.addEventListener("click", (e) => {
      const m = document.getElementById(b.dataset.modalOpen);
      if (m) { e.preventDefault(); openModal(m); }
    }));
    $$(".modal").forEach((m) => $$("[data-modal-close], .modal__backdrop", m).forEach((c) => c.addEventListener("click", () => closeModal(m))));
    $$("[data-confirm]").forEach((f) => f.addEventListener("submit", (e) => { if (!window.confirm(f.dataset.confirm)) e.preventDefault(); }));
  }

  /* ---------- Reveal on scroll ---------- */
  function initReveal() {
    const items = $$("[data-reveal]");
    $$("[data-stagger]").forEach((group) => {
      const step = parseFloat(group.dataset.stagger) || 0.08;
      $$(":scope > *", group).forEach((child, i) => {
        if (!child.hasAttribute("data-reveal")) { child.setAttribute("data-reveal", ""); items.push(child); }
        child.style.setProperty("--d", `${Math.min(i * step, 0.8)}s`);
      });
    });
    if (reduceMotion || !("IntersectionObserver" in window)) { items.forEach((el) => el.classList.add("is-in")); return; }
    const io = new IntersectionObserver((entries) => entries.forEach((en) => {
      if (en.isIntersecting) { en.target.classList.add("is-in"); io.unobserve(en.target); }
    }), { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    items.forEach((el) => io.observe(el));
  }

  /* ---------- Animated counters ---------- */
  function initCounters() {
    const els = $$("[data-count]");
    if (!els.length) return;
    const fmt = new Intl.NumberFormat(document.documentElement.lang === "ar" ? "ar-EG" : "en-US");
    const run = (el) => {
      const target = parseInt(el.dataset.count, 10) || 0;
      if (reduceMotion || target === 0) { el.textContent = fmt.format(target); return; }
      const dur = 1600, t0 = performance.now();
      const tick = (t) => {
        const p = Math.min((t - t0) / dur, 1);
        el.textContent = fmt.format(Math.round(target * (1 - Math.pow(1 - p, 4))));
        if (p < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    };
    const io = new IntersectionObserver((entries) => entries.forEach((en) => { if (en.isIntersecting) { run(en.target); io.unobserve(en.target); } }), { threshold: 0.4 });
    els.forEach((el) => io.observe(el));
  }

  /* ---------- Progress bars ---------- */
  function initProgress() {
    const bars = $$("[data-progress]");
    const io = new IntersectionObserver((entries) => entries.forEach((en) => {
      if (en.isIntersecting) { en.target.style.width = `${en.target.dataset.progress}%`; io.unobserve(en.target); }
    }));
    bars.forEach((b) => io.observe(b));
  }

  /* ---------- Pointer effects: magnetic buttons, tilt, glow ---------- */
  function initPointerFx() {
    if (reduceMotion || !finePointer) return;
    $$("[data-magnetic]").forEach((el) => {
      el.addEventListener("pointermove", (e) => {
        const r = el.getBoundingClientRect();
        const x = (e.clientX - r.left - r.width / 2) * 0.25;
        const y = (e.clientY - r.top - r.height / 2) * 0.35;
        el.style.transform = `translate(${x}px, ${y}px)`;
      });
      el.addEventListener("pointerleave", () => (el.style.transform = ""));
    });
    $$("[data-tilt]").forEach((el) => {
      el.addEventListener("pointermove", (e) => {
        const r = el.getBoundingClientRect();
        const px = (e.clientX - r.left) / r.width - 0.5;
        const py = (e.clientY - r.top) / r.height - 0.5;
        el.style.transform = `perspective(900px) rotateX(${(-py * 6).toFixed(2)}deg) rotateY(${(px * 6).toFixed(2)}deg) translateY(-6px)`;
      });
      el.addEventListener("pointerleave", () => (el.style.transform = ""));
    });
    document.addEventListener("pointermove", (e) => {
      const card = e.target.closest?.(".card-glow");
      if (!card) return;
      const r = card.getBoundingClientRect();
      card.style.setProperty("--mx", `${e.clientX - r.left}px`);
      card.style.setProperty("--my", `${e.clientY - r.top}px`);
    }, { passive: true });
  }

  /* ---------- Hero ---------- */
  function initHero() {
    const hero = $(".hero");
    if (!hero) return;

    // Rotating headline words
    const rot = $(".hero__rotator", hero);
    if (rot && !reduceMotion) {
      const words = $$("span", rot);
      let i = 0;
      setInterval(() => {
        const cur = words[i];
        cur.classList.remove("is-active"); cur.classList.add("is-leaving");
        setTimeout(() => cur.classList.remove("is-leaving"), 700);
        i = (i + 1) % words.length;
        words[i].classList.add("is-active");
      }, 2800);
    }

    // Hiring notifications that appear/disappear
    const note = $(".hero-notify", hero);
    const notes = $$("[data-hero-note]", hero).map((n) => ({ title: n.dataset.title, sub: n.dataset.sub }));
    if (note && notes.length) {
      let k = 0;
      const show = () => {
        $(".hero-notify__title", note).textContent = notes[k].title;
        $(".hero-notify__sub", note).textContent = notes[k].sub;
        note.classList.add("is-visible");
        setTimeout(() => note.classList.remove("is-visible"), 3600);
        k = (k + 1) % notes.length;
      };
      setTimeout(show, 1400);
      if (!reduceMotion) setInterval(show, 5200);
    }

    // Mouse parallax on depth layers
    const layers = $$("[data-depth]", hero);
    if (!reduceMotion && finePointer && layers.length) {
      let tx = 0, ty = 0, cx = 0, cy = 0, raf = null;
      hero.addEventListener("pointermove", (e) => {
        const r = hero.getBoundingClientRect();
        tx = (e.clientX - r.left) / r.width - 0.5;
        ty = (e.clientY - r.top) / r.height - 0.5;
        if (!raf) raf = requestAnimationFrame(loop);
      });
      function loop() {
        cx += (tx - cx) * 0.08; cy += (ty - cy) * 0.08;
        layers.forEach((l) => {
          const d = parseFloat(l.dataset.depth);
          l.style.translate = `${(-cx * d * 40).toFixed(1)}px ${(-cy * d * 40).toFixed(1)}px`;
        });
        raf = Math.abs(tx - cx) + Math.abs(ty - cy) > 0.001 ? requestAnimationFrame(loop) : null;
      }
    }

    // Calm particle field (paused when off-screen or tab hidden)
    const canvas = $(".hero__particles", hero);
    if (canvas && !reduceMotion) particles(canvas, hero);

    // GSAP intro timeline
    if (window.gsap && !reduceMotion) {
      const tl = gsap.timeline({ defaults: { ease: "expo.out" } });
      tl.from(".hero__title .line > span", { yPercent: 110, duration: 1.2, stagger: 0.12 })
        .from(".hero__lead, .hero-search, .hero__ctas, .hero__trust", { y: 24, opacity: 0, duration: 1, stagger: 0.1 }, "-=0.8")
        .from(".hero-visual__blob", { scale: 0.6, opacity: 0, duration: 1.4 }, 0.1)
        .from(".hero-person", { y: 80, opacity: 0, duration: 1.4, stagger: 0.15 }, 0.25)
        .from(".float-card, .skill-bubble", { scale: 0.6, opacity: 0, duration: 0.9, stagger: 0.07, ease: "back.out(1.8)" }, 0.7);
      if (window.ScrollTrigger) {
        gsap.registerPlugin(ScrollTrigger);
        gsap.to(".hero-visual", { yPercent: 12, ease: "none", scrollTrigger: { trigger: hero, start: "top top", end: "bottom top", scrub: true } });
        gsap.to(".hero__bg .orb", { yPercent: 30, ease: "none", scrollTrigger: { trigger: hero, start: "top top", end: "bottom top", scrub: true } });
      }
    }
  }

  function particles(canvas, host) {
    const ctx = canvas.getContext("2d");
    let w, h, pts = [], running = true, visible = true;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const count = window.innerWidth < 700 ? 22 : 48;
    const colors = ["37,99,235", "124,58,237", "6,182,212"];
    function resize() {
      w = canvas.clientWidth; h = canvas.clientHeight;
      canvas.width = w * dpr; canvas.height = h * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    function seed() {
      pts = Array.from({ length: count }, () => ({
        x: Math.random() * w, y: Math.random() * h, r: Math.random() * 2 + 0.6,
        vx: (Math.random() - 0.5) * 0.25, vy: (Math.random() - 0.5) * 0.25, c: colors[(Math.random() * 3) | 0], a: Math.random() * 0.5 + 0.25,
      }));
    }
    function frame() {
      if (!running || !visible) return;
      ctx.clearRect(0, 0, w, h);
      for (let i = 0; i < pts.length; i++) {
        const p = pts[i];
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${p.c},${p.a})`; ctx.fill();
        for (let j = i + 1; j < pts.length; j++) {
          const q = pts[j], dx = p.x - q.x, dy = p.y - q.y, d = dx * dx + dy * dy;
          if (d < 12000) {
            ctx.strokeStyle = `rgba(${p.c},${0.12 * (1 - d / 12000)})`;
            ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y); ctx.stroke();
          }
        }
      }
      requestAnimationFrame(frame);
    }
    resize(); seed(); frame();
    window.addEventListener("resize", () => { resize(); seed(); });
    new IntersectionObserver(([en]) => { visible = en.isIntersecting; if (visible) frame(); }).observe(host);
    document.addEventListener("visibilitychange", () => { running = !document.hidden; if (running) frame(); });
  }

  /* ---------- GSAP scroll scenes ---------- */
  function initScrollScenes() {
    if (!window.gsap || !window.ScrollTrigger || reduceMotion) return;
    gsap.registerPlugin(ScrollTrigger);
    const path = $(".how__path path");
    if (path) {
      const len = path.getTotalLength();
      gsap.set(path, { strokeDasharray: len, strokeDashoffset: len });
      gsap.to(path, { strokeDashoffset: 0, ease: "none", scrollTrigger: { trigger: ".how", start: "top 70%", end: "center 50%", scrub: 1 } });
    }
    $$(".how__step").forEach((step, i) => {
      gsap.from(step, { y: 60, opacity: 0, duration: 1, ease: "expo.out", delay: i * 0.12, scrollTrigger: { trigger: step, start: "top 85%" } });
      gsap.from($(".how__art img", step), { scale: 0.7, rotate: i % 2 ? 8 : -8, duration: 1.2, ease: "back.out(1.6)", scrollTrigger: { trigger: step, start: "top 85%" } });
    });
    $$("[data-parallax]").forEach((el) => {
      gsap.to(el, { yPercent: parseFloat(el.dataset.parallax) || -15, ease: "none", scrollTrigger: { trigger: el.closest("section") || el, scrub: true } });
    });
    const cta = $(".cta");
    if (cta) gsap.from(cta, { scale: 0.94, opacity: 0, duration: 1.2, ease: "expo.out", scrollTrigger: { trigger: cta, start: "top 85%" } });
  }

  /* ---------- Carousels (Swiper) ---------- */
  function initCarousels() {
    if (!window.Swiper) return;
    $$("[data-carousel]").forEach((root) => {
      const type = root.dataset.carousel;
      const el = $(".swiper", root);
      const base = {
        speed: 700, grabCursor: true, watchOverflow: true,
        navigation: { nextEl: $("[data-next]", root), prevEl: $("[data-prev]", root) },
        pagination: { el: $(".carousel-dots", root), clickable: true },
        a11y: { enabled: true },
      };
      const opts = {
        talents: { slidesPerView: 1.15, spaceBetween: 16, breakpoints: { 560: { slidesPerView: 2.1 }, 900: { slidesPerView: 3.1 }, 1200: { slidesPerView: 4, spaceBetween: 20 } } },
        quotes: { slidesPerView: 1, spaceBetween: 20, loop: false, autoplay: reduceMotion ? false : { delay: 6000, pauseOnMouseEnter: true }, breakpoints: { 760: { slidesPerView: 2 }, 1100: { slidesPerView: 3 } } },
        jobs: { slidesPerView: 1.1, spaceBetween: 16, breakpoints: { 700: { slidesPerView: 2 }, 1100: { slidesPerView: 3, spaceBetween: 20 } } },
      }[type] || {};
      new Swiper(el, Object.assign({}, base, opts));
    });
  }

  /* ---------- Save job (AJAX) ---------- */
  function initSaveButtons() {
    document.addEventListener("submit", async (e) => {
      const form = e.target.closest("[data-save-form]");
      if (!form) return;
      e.preventDefault();
      const btn = $("button", form);
      try {
        const res = await fetch(form.action, { method: "POST", headers: { "X-CSRFToken": csrf(), "X-Requested-With": "fetch" }, credentials: "same-origin" });
        if (res.redirected || res.status === 403 || res.url.includes("/accounts/login")) { window.location = form.dataset.loginUrl || "/accounts/login/"; return; }
        const data = await res.json();
        btn.classList.toggle("is-saved", data.saved);
        btn.setAttribute("aria-pressed", String(data.saved));
        btn.classList.remove("pop"); void btn.offsetWidth; btn.classList.add("pop");
        toast(data.message, "success");
      } catch (err) { form.submit(); }
    });
  }

  /* ---------- Async filters for listing pages ---------- */
  let filterCtl = null;
  function closeFilters() { $(".filters")?.classList.remove("is-open"); $(".filters-backdrop")?.classList.remove("is-open"); }
  function initFilters() {
    const form = $("[data-filter-form]");
    const results = $("[data-results]");
    if (!form || !results) return;
    $$("[data-filters-open]").forEach((b) => b.addEventListener("click", () => { $(".filters").classList.add("is-open"); $(".filters-backdrop").classList.add("is-open"); }));
    $$("[data-filters-close], .filters-backdrop").forEach((b) => b.addEventListener("click", closeFilters));

    const skeleton = () => Array.from({ length: 4 }, () => '<div class="skeleton skeleton-card"></div>').join("");
    let timer;
    async function load(url, push = true) {
      filterCtl?.abort();
      filterCtl = new AbortController();
      const grid = $("[data-results-grid]", results);
      results.setAttribute("aria-busy", "true");
      if (grid) { grid.classList.add("is-loading"); }
      try {
        const res = await fetch(url, { headers: { "X-Partial": "1" }, signal: filterCtl.signal });
        if (!res.ok) throw new Error(res.status);
        const html = await res.text();
        results.innerHTML = html;
        if (push) history.pushState({}, "", url);
        applyViewMode();
        animateIn(results);
        initReveal();
      } catch (err) {
        if (err.name === "AbortError") return;
        results.innerHTML = `<div class="empty"><h3>${form.dataset.errorText || "Error"}</h3></div>`;
      } finally { results.removeAttribute("aria-busy"); }
    }
    function animateIn(root) {
      const cards = $$("[data-results-grid] > *", root);
      if (reduceMotion) return;
      if (window.gsap) gsap.from(cards, { y: 24, opacity: 0, duration: 0.6, stagger: 0.05, ease: "expo.out" });
    }
    function urlFromForm() {
      const fd = new FormData(form);
      const params = new URLSearchParams();
      for (const [k, v] of fd.entries()) if (String(v).trim() !== "") params.append(k, v);
      return `${form.action || location.pathname}?${params.toString()}`;
    }
    // Listen on document: some controls live outside the <form> and use form="…".
    const textLike = "input[type=text], input[type=search], input[type=number]";
    document.addEventListener("change", (e) => { if (e.target.form !== form || e.target.matches(textLike)) return; load(urlFromForm()); });
    document.addEventListener("input", (e) => {
      if (e.target.form !== form || !e.target.matches(textLike)) return;
      clearTimeout(timer); timer = setTimeout(() => load(urlFromForm()), 450);
    });
    form.addEventListener("submit", (e) => { e.preventDefault(); closeFilters(); load(urlFromForm()); });
    results.addEventListener("click", (e) => {
      const a = e.target.closest("a[data-partial-link], .pagination a");
      if (!a) return;
      e.preventDefault();
      load(a.href);
      window.scrollTo({ top: results.getBoundingClientRect().top + window.scrollY - 110, behavior: reduceMotion ? "auto" : "smooth" });
    });
    document.addEventListener("click", (e) => {
      const chip = e.target.closest("[data-remove-filter]");
      if (!chip) return;
      e.preventDefault();
      const [name, value] = chip.dataset.removeFilter.split("::");
      $$(`[name="${name}"]`, form).forEach((inp) => {
        if (inp.type === "checkbox" || inp.type === "radio") { if (inp.value === value) inp.checked = false; }
        else if (inp.tagName === "SELECT" || inp.value === value) inp.value = "";
      });
      load(urlFromForm());
    });
    document.addEventListener("click", (e) => {
      if (!e.target.closest("[data-clear-filters]")) return;
      e.preventDefault(); form.reset();
      $$("input[type=text], input[type=number], select", form).forEach((i) => (i.value = ""));
      $$("input[type=checkbox], input[type=radio]", form).forEach((i) => (i.checked = false));
      load(form.action || location.pathname);
    });
    window.addEventListener("popstate", () => load(location.href, false));

    // grid / list toggle (remembered per browser)
    function applyViewMode() {
      let mode = "grid";
      try { mode = localStorage.getItem("view-mode") || "grid"; } catch (e) {}
      $$("[data-results-grid]").forEach((g) => g.classList.toggle("results--list", mode === "list"));
      $$("[data-view]").forEach((b) => b.classList.toggle("is-active", b.dataset.view === mode));
    }
    document.addEventListener("click", (e) => {
      const b = e.target.closest("[data-view]");
      if (!b) return;
      try { localStorage.setItem("view-mode", b.dataset.view); } catch (err) {}
      applyViewMode();
    });
    applyViewMode();
  }

  /* ---------- Forms: password visibility & strength, tags preview, file names ---------- */
  function initForms() {
    $$("input[type=password]").forEach((inp) => {
      if (inp.closest(".password-wrap")) return;
      const wrap = document.createElement("div");
      wrap.className = "password-wrap";
      inp.parentNode.insertBefore(wrap, inp);
      wrap.appendChild(inp);
      const btn = document.createElement("button");
      btn.type = "button";
      btn.setAttribute("aria-label", "show password");
      btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M2.5 12S6 5 12 5s9.5 7 9.5 7-3.5 7-9.5 7-9.5-7-9.5-7Z"/><circle cx="12" cy="12" r="3"/></svg>';
      btn.addEventListener("click", () => { inp.type = inp.type === "password" ? "text" : "password"; });
      wrap.appendChild(btn);
    });
    $$("input[data-strength]").forEach((inp) => {
      const meter = document.createElement("div");
      meter.className = "strength";
      meter.innerHTML = "<span></span>";
      inp.closest(".field")?.appendChild(meter);
      const bar = $("span", meter);
      inp.addEventListener("input", () => {
        const v = inp.value;
        let s = 0;
        if (v.length >= 8) s++; if (/[A-Z]/.test(v) && /[a-z]/.test(v)) s++; if (/\d/.test(v)) s++; if (/[^A-Za-z0-9]/.test(v)) s++; if (v.length >= 12) s++;
        const colors = ["#EF4444", "#F59E0B", "#EAB308", "#10B981", "#059669"];
        bar.style.width = `${(s / 5) * 100}%`;
        bar.style.background = colors[Math.max(0, s - 1)];
      });
    });
    $$("input[data-tags]").forEach((inp) => {
      const preview = document.createElement("div");
      preview.className = "tag-preview";
      inp.insertAdjacentElement("afterend", preview);
      const render = () => {
        preview.innerHTML = "";
        inp.value.replace(/،/g, ",").split(",").map((t) => t.trim()).filter(Boolean).slice(0, 15)
          .forEach((t) => { const c = document.createElement("span"); c.className = "chip chip--removable"; c.textContent = t; preview.appendChild(c); });
      };
      inp.addEventListener("input", render); render();
    });
    // Disable double submit + loading state
    $$("form:not([data-save-form]):not([data-filter-form])").forEach((f) => f.addEventListener("submit", () => {
      const b = $("button[type=submit]:not([name]), button:not([type])", f);
      if (b && f.checkValidity()) setTimeout(() => b.classList.add("is-loading"), 0);
    }));
  }

  /* ---------- Chat ---------- */
  function initChat() {
    const chat = $("[data-chat]");
    if (!chat) return;
    const body = $(".chat__body", chat);
    const form = $(".chat__composer", chat);
    const area = $("textarea", form);
    const scroll = () => (body.scrollTop = body.scrollHeight);
    scroll();
    const lastId = () => { const b = $$(".bubble[data-id]", body).pop(); return b ? b.dataset.id : 0; };
    const add = (m) => {
      if ($(`.bubble[data-id="${m.id}"]`, body)) return;
      const div = document.createElement("div");
      div.className = `bubble ${m.mine ? "bubble--me" : "bubble--them"}`;
      div.dataset.id = m.id;
      div.textContent = m.body;
      const t = document.createElement("small"); t.textContent = m.time; div.appendChild(t);
      body.appendChild(div); scroll();
      $(".empty", body)?.remove();
    };
    area.addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); } });
    area.addEventListener("input", () => { area.style.height = "auto"; area.style.height = `${Math.min(area.scrollHeight, 140)}px`; });
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const text = area.value.trim();
      if (!text) return;
      area.value = ""; area.style.height = "";
      try {
        const res = await fetch(form.action, { method: "POST", headers: { "X-CSRFToken": csrf(), "X-Requested-With": "fetch" }, body: new URLSearchParams({ body: text }) });
        add(await res.json());
      } catch (err) { area.value = text; toast(chat.dataset.errorText || "Error", "error"); }
    });
    const poll = async () => {
      if (document.hidden) return;
      try {
        const res = await fetch(`${chat.dataset.pollUrl}?after=${lastId()}`);
        const data = await res.json();
        data.messages.forEach(add);
      } catch (e) {}
    };
    setInterval(poll, 6000);
  }

  /* ---------- Page leave transition (fallback when View Transitions unsupported) ---------- */
  function initPageTransitions() {
    if (reduceMotion || "startViewTransition" in document) return;
    document.body.classList.add("page-fade");
  }

  function ready(fn) { document.readyState !== "loading" ? fn() : document.addEventListener("DOMContentLoaded", fn); }
  ready(() => {
    [initTheme, initNav, initModals, initReveal, initCounters, initProgress, initPointerFx, initHero,
      initScrollScenes, initCarousels, initSaveButtons, initFilters, initForms, initChat, initPageTransitions, initFlashMessages]
      .forEach((fn) => { try { fn(); } catch (err) { if (window.console) console.warn(fn.name, err); } });
  });
})();
