// Shared helpers: theme switch, menu, colours read from CSS, cached JSON loading, redraw hooks.
(function () {
  const root = document.documentElement;
  const redraws = [];
  const cache = {};
  const site = (window.site = {
    colors() {
      const s = getComputedStyle(root);
      const g = (n) => s.getPropertyValue(n).trim();
      return { page: g("--page"), surface: g("--surface"), ink: g("--ink"), ink2: g("--ink-2"), muted: g("--muted"), grid: g("--grid"),
        axis: g("--axis"), wash: g("--wash"), s1: g("--series-1"), s2: g("--series-2"), s3: g("--series-3"), neutral: g("--neutral"),
        good: g("--good"), critical: g("--critical") };
    },
    load(name) {
      return (cache[name] = cache[name] || fetch("site/data/" + name + ".json").then((r) => {
        if (!r.ok) throw new Error(name + ".json: " + r.status);
        return r.json();
      }));
    },
    onRedraw(fn) { redraws.push(fn); },
    redraw() { redraws.forEach((fn) => { try { fn(); } catch (e) { console.error(e); } }); },
    pct(x, d) { x *= 100; return x.toFixed(d === undefined ? (x < 10 ? 1 : 0) : d) + "%"; },
  });

  function isDark() {
    const t = root.getAttribute("data-theme");
    return t ? t === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  }
  document.querySelector(".theme").addEventListener("click", () => {
    const next = isDark() ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("theme", next); } catch (e) { /* not stored */ }
    site.redraw();
  });
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => site.redraw());

  const menu = document.querySelector(".menu"), nav = document.getElementById("nav");
  menu.addEventListener("click", () => {
    const open = nav.classList.toggle("open");
    menu.setAttribute("aria-expanded", open);
  });

  // Margin notes are placed beside the paragraph before them; keep them from overlapping.
  function spreadNotes() {
    let floor = -Infinity;
    const wideEls = Array.from(document.querySelectorAll("article .wide, article .stats, article .widget"));
    document.querySelectorAll("aside.note").forEach((n) => {
      n.style.marginTop = "";
      n.classList.remove("inline");
      if (getComputedStyle(n).position !== "absolute") return;
      let r = n.getBoundingClientRect();
      if (r.top + scrollY < floor + 12) n.style.marginTop = "calc(-5.2em + " + (floor + 12 - r.top - scrollY) + "px)";
      r = n.getBoundingClientRect();
      // A note that would sit on top of a full-width figure goes back into the text column.
      const hit = (e) => { const w = e.getBoundingClientRect(); return r.bottom > w.top - 6 && r.top < w.bottom + 6; };
      if (wideEls.some(hit)) { n.style.marginTop = ""; n.classList.add("inline"); return; }
      floor = r.bottom + scrollY;
    });
  }
  addEventListener("load", spreadNotes);
  site.onRedraw(spreadNotes);
  // Charts and widgets change the page height after they load; place the notes again when they do.
  let noteTimer;
  if (window.ResizeObserver) new ResizeObserver(() => { clearTimeout(noteTimer); noteTimer = setTimeout(spreadNotes, 80); }).observe(document.querySelector("main"));

  let w = innerWidth, timer;
  addEventListener("resize", () => {
    if (innerWidth === w) return;
    w = innerWidth;
    clearTimeout(timer);
    timer = setTimeout(() => site.redraw(), 150);
  });
})();
