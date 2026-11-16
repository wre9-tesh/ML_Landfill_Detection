// Static charts. Each <figure data-chart="ID"> gets the chart registered under that ID,
// drawn from site/data/tables.json and redrawn when the theme or the width changes.
(function () {
  const CH = {};
  const LBL = { near_site: "Near-site background", random: "Random background", bare_soil: "Bare soil", quarry: "Quarry", ash_pond: "Ash pond", landfill: "Landfill" };

  function base(c, o) {
    return Object.assign({ style: { background: "transparent", color: c.ink, fontSize: "13px", fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif", "--plot-background": c.surface }, marginTop: 24, marginBottom: 44 }, o);
  }
  const pc = (d) => Math.round(d * 100) + "%";

  function bars(rows, ykey, xkey, c, w, o) {
    o = o || {};
    const fmt = o.fmt || pc;
    return Plot.plot(base(c, {
      width: w, height: 34 * rows.length + 48, marginLeft: o.left || 190, marginRight: 54,
      x: Object.assign({ grid: true, label: o.xlabel || null, tickFormat: o.tick || pc, domain: o.domain }, o.x || {}),
      y: { label: null, domain: rows.map((r) => r[ykey]), tickSize: 0 },
      marks: [
        Plot.barX(rows, { y: ykey, x: xkey, fill: (r) => (o.fill ? o.fill(r) : c.s1), rx2: 3, insetTop: 5, insetBottom: 5, tip: true,
          title: (r) => r[ykey] + ": " + fmt(r[xkey]) }),
        Plot.text(rows, { y: ykey, x: xkey, text: (r) => fmt(r[xkey]) + (o.suffix ? o.suffix(r) : ""), dx: 6, textAnchor: "start", fill: c.ink }),
        Plot.ruleX([0], { stroke: c.axis }),
      ].concat(o.extra || []),
    }));
  }

  CH["F-D1"] = (T, c, w) => bars(T["F-D1"], "step", "count", c, w, { left: Math.min(330, w * 0.5), fmt: (v) => v.toLocaleString("en"), tick: (v) => v.toLocaleString("en") });

  CH["F-R1"] = (T, c, w) => {
    const rows = T["F-R1"].slice().sort((a, b) => b.held_out_region - a.held_out_region);
    const order = rows.map((r) => r.model);
    return Plot.plot(base(c, {
      width: w, height: 36 * rows.length + 56, marginLeft: 180, marginRight: 20,
      x: { domain: [0, 1], grid: true, label: "F1 for the landfill class" },
      y: { domain: order, label: null, tickSize: 0 },
      marks: [
        Plot.ruleY(rows, { y: "model", x1: "held_out_region", x2: "random_pixel", stroke: c.axis, strokeWidth: 2 }),
        Plot.ruleY(rows, { y: "model", x1: (r) => r.held_out_region - r.region_sd, x2: (r) => r.held_out_region + r.region_sd, stroke: c.s1, strokeWidth: 5, strokeOpacity: 0.3 }),
        Plot.dot(rows, { y: "model", x: "random_pixel", r: 5, stroke: c.neutral, strokeWidth: 2, fill: c.surface, tip: true, title: (r) => r.model + "\nRandom pixel split: " + r.random_pixel.toFixed(3) }),
        Plot.dot(rows, { y: "model", x: "held_out_site", r: 5, stroke: c.s2, strokeWidth: 2, fill: c.surface, symbol: "diamond", tip: true, title: (r) => r.model + "\nHeld-out site: " + r.held_out_site.toFixed(3) }),
        Plot.dot(rows, { y: "model", x: "held_out_region", r: 6, fill: c.s1, stroke: c.surface, strokeWidth: 2, tip: true, title: (r) => r.model + "\nHeld-out region: " + r.held_out_region.toFixed(3) + " (SD " + r.region_sd.toFixed(3) + ")" }),
      ],
    }));
  };

  CH["F-R2"] = (T, c, w) => {
    const rows = T["F-R2"];
    return Plot.plot(base(c, {
      width: w, height: 38 * rows.length + 56, marginLeft: 120, marginRight: 80,
      x: { domain: [0, 1], grid: true, label: null },
      y: { label: null, tickSize: 0 },
      marks: [
        Plot.ruleY(rows, { y: "region", x1: "precision", x2: "recall", stroke: c.axis, strokeWidth: 2 }),
        Plot.dot(rows, { y: "region", x: "precision", r: 6, fill: c.s1, stroke: c.surface, strokeWidth: 2, tip: true, title: (r) => r.region + "\nPrecision " + r.precision.toFixed(3) }),
        Plot.dot(rows, { y: "region", x: "recall", r: 6, fill: c.s2, stroke: c.surface, strokeWidth: 2, tip: true, title: (r) => r.region + "\nRecall " + r.recall.toFixed(3) }),
        Plot.text(rows, { y: "region", frameAnchor: "right", dx: 74, text: (r) => "F1 " + r.f1.toFixed(2), fill: c.ink2, textAnchor: "end" }),
      ],
    }));
  };

  CH["F-R3"] = (T, c, w) => bars(T["F-R3"], "site", "share_flagged", c, w, {
    left: 170, domain: [0, 1.08], fill: (r) => (r.status === "found" ? c.s1 : c.critical), suffix: (r) => (r.status === "found" ? "" : "  ✗ missed"),
    extra: [Plot.ruleX([0.5], { stroke: c.ink, strokeDasharray: "4 3" }), Plot.text([{}], { x: 0.5, frameAnchor: "top", dy: -14, text: () => "half the outline", fill: c.ink2 })],
  });

  CH["F-R4"] = (T, c, w) => bars(T["F-R4"], "box", "share_flagged", c, w, { left: 120, fill: () => c.s2, fmt: (v) => site.pct(v), tick: pc });

  CH["F-R6"] = (T, c, w) => {
    const rows = T["F-R6"];
    const lab = rows.filter((r, i) => i === 0 || r.status !== "found");
    return Plot.plot(base(c, {
      width: w, height: 130, marginLeft: 20, marginRight: 30, marginBottom: 42,
      x: { type: "log", domain: [10, 8000], label: "Rank of the patch that holds the site (1 = strongest alarm), log scale", grid: true, tickFormat: (d) => d.toLocaleString("en") },
      y: { axis: null, domain: [0, 1] },
      marks: [
        Plot.rect([{}], { x1: 10, x2: 100, y1: 0, y2: 1, fill: c.s1, fillOpacity: 0.1 }),
        Plot.text([{}], { x: 72, y: 0.92, text: () => "top 100", fill: c.ink2 }),
        Plot.ruleX(rows, { x: "rank", y1: 0.15, y2: 0.7, stroke: (r) => (r.status === "found" ? c.s1 : c.critical), strokeWidth: 3, tip: true,
          title: (r) => r.city + " (" + r.id + ")\nrank " + r.rank.toLocaleString("en") + (r.status === "found" ? "" : ", missed") }),
        Plot.text(lab, { x: "rank", y: 0.82, text: (r) => r.city + " " + r.rank.toLocaleString("en"), fill: c.ink, fontSize: 12 }),
      ],
    }));
  };

  CH["F-R7"] = (T, c, w) => (T["F-R7"].length ? bars(T["F-R7"], "seen", "alarms", c, w, {
    left: 190, fmt: (v) => String(v), tick: (v) => String(v), xlabel: "Alarms, of the top 100",
    fill: (r) => (r.key === "dump" ? c.s1 : r.key === "unsure" ? c.neutral : c.s2) }) : null);

  const classBars = (id, label) => (T, c, w) => bars(T[id], "class", "share", c, w, {
    left: 170, fill: (r) => (r.class === "Landfill" ? c.s1 : c.s2), fmt: (v) => site.pct(v), xlabel: label });
  CH["F-X2"] = classBars("F-X2", "Share of points whose 15 nearest neighbours are mostly landfill");
  CH["F-X4"] = classBars("F-X4", "Share of points flagged when their region is held out");

  CH["F-X3"] = (T, c, w) => {
    const pts = T["F-X3"];
    const panels = [["Ordinary land", ["near_site", "random"]], ["Bare soil and quarry", ["bare_soil", "quarry"]], ["Ash pond", ["ash_pond"]]];
    const lf = pts.filter((p) => p.c === "landfill");
    const rows = [];
    panels.forEach(([name, cls]) => {
      pts.filter((p) => cls.includes(p.c)).forEach((p) => rows.push({ panel: name, x: p.x, y: p.y, k: 0 }));
      lf.forEach((p) => rows.push({ panel: name, x: p.x, y: p.y, k: 1 }));
    });
    const narrow = w < 640;
    return Plot.plot(base(c, {
      width: w, height: narrow ? 900 : 330, marginLeft: 40,
      fx: narrow ? undefined : { domain: panels.map((p) => p[0]), label: null },
      fy: narrow ? { domain: panels.map((p) => p[0]), label: null } : undefined,
      x: { label: "First principal component", domain: [-8, 10], grid: true },
      y: { label: "Second", domain: [-7, 9], grid: true },
      marks: [Plot.dot(rows, { x: "x", y: "y", fx: narrow ? undefined : "panel", fy: narrow ? "panel" : undefined, r: 1.6,
        fill: (r) => (r.k ? c.s1 : c.s2), fillOpacity: 0.45, clip: true })],
    }));
  };

  CH["F-X5"] = (T, c, w) => bars(T["F-X5"].groups.slice().sort((a, b) => b.share - a.share).map((r) => ({ group: r.group[0].toUpperCase() + r.group.slice(1), share: r.share })),
    "group", "share", c, w, { left: 170, fill: () => c.s1, xlabel: "Share of the model's total SHAP value" });
  CH["F-X5b"] = (T, c, w) => bars(T["F-X5"].features, "feature", "share", c, w, { left: 90, fill: () => c.s1, xlabel: "Share of total SHAP value, single features" });

  CH["F-X6"] = (T, c, w) => {
    const rows = T["F-X6"];
    const last = rows[rows.length - 1];
    return Plot.plot(base(c, {
      width: w, height: 340, marginLeft: 50, marginRight: 30, marginBottom: 44,
      x: { type: "log", label: "How rare landfill is: one pixel in …", grid: true, tickFormat: (d) => d.toLocaleString("en"), ticks: [2, 10, 100, 1000, 10000, 100000] },
      y: { domain: [0, 1], label: "Precision", grid: true, tickFormat: pc },
      marks: [
        Plot.ruleX([9, 4100], { stroke: c.axis, strokeDasharray: "4 3" }),
        Plot.text([{ x: 9, t: "training mix\n(1 in 9)" }, { x: 4100, t: "known sites in\nGujarat (1 in 4,100)" }], { x: "x", frameAnchor: "top", dy: 4, dx: 5, text: "t", textAnchor: "start", fill: c.ink2, lineHeight: 1.2 }),
        Plot.line(rows, { x: "one_in", y: "validation_rates", stroke: c.s1, strokeWidth: 2.5 }),
        Plot.line(rows, { x: "one_in", y: "gujarat_rates", stroke: c.s2, strokeWidth: 2.5 }),
        Plot.dot(rows, { x: "one_in", y: "validation_rates", r: 3, fill: c.s1, tip: true, title: (r) => "1 in " + r.one_in.toLocaleString("en") + "\nValidation rates: " + site.pct(r.validation_rates) + "\nGujarat rates: " + site.pct(r.gujarat_rates) }),
      ],
    }));
  };

  function draw(T) {
    const c = site.colors();
    document.querySelectorAll("figure[data-chart]").forEach((fig) => {
      const el = fig.querySelector(".chart"), fn = CH[fig.dataset.chart];
      if (!el || !fn) return;
      const w = Math.max(300, el.clientWidth - 28);
      let node = null;
      try { node = fn(T, c, w); } catch (e) { console.error(fig.dataset.chart, e); }
      el.replaceChildren(node || Object.assign(document.createElement("p"), { className: "pendingnote", textContent: "Not available yet." }));
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    if (!document.querySelector("figure[data-chart]")) return;
    site.load("tables").then((T) => { draw(T); site.onRedraw(() => draw(T)); })
      .catch((e) => { console.error(e); document.querySelectorAll("figure[data-chart] .chart").forEach((el) => (el.textContent = "The chart could not be loaded. The numbers are in the table below.")); });
  });
})();
