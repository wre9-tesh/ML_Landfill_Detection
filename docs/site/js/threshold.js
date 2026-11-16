// Threshold slider: what any threshold other than the frozen 0.5 would have traded.
// Data: site/data/threshold.json (validation points by region and class; Gujarat pixels and sites).
(function () {
  const root = document.getElementById("thr");
  if (!root) return;
  const $ = (id) => document.getElementById(id);
  const slider = $("thr-t");
  const NAMES = { landfill: "Landfill (recall)", quarry: "Quarry", bare_soil: "Bare soil", ash_pond: "Ash pond", near_site: "Near-site background", random: "Random background" };
  const ORDER = ["landfill", "quarry", "bare_soil", "ash_pond", "near_site", "random"];
  let D, curve;

  function valAt(i) {
    const v = D.val, bg = v.classes.filter((k) => k !== "landfill");
    let P = 0, R = 0, F = 0, tp = 0, fp = 0;
    v.regions.forEach((r) => {
      const t = v.flagged[r].landfill[i], f = bg.reduce((s, k) => s + v.flagged[r][k][i], 0);
      const p = t + f ? t / (t + f) : 0, rc = t / v.n[r].landfill;
      P += p; R += rc; F += p + rc ? (2 * p * rc) / (p + rc) : 0; tp += t; fp += f;
    });
    const n = v.regions.length;
    return { p: P / n, r: R / n, f: F / n, pooled: tp + fp ? tp / (tp + fp) : 0 };
  }
  function classShare(k, i) {
    let a = 0, b = 0;
    D.val.regions.forEach((r) => { a += D.val.flagged[r][k][i]; b += D.val.n[r][k]; });
    return a / b;
  }

  function update() {
    const t = +slider.value, i = Math.round(t * 100), c = site.colors();
    const frozen = i === 50;
    slider.setAttribute("aria-valuetext", "threshold " + t.toFixed(2));
    $("thr-read").textContent = t.toFixed(2);
    const v = frozen ? Object.assign(valAt(i), { p: D.val.published.precision, r: D.val.published.recall, f: D.val.published.f1 }) : valAt(i);
    $("thr-p").textContent = v.p.toFixed(2);
    $("thr-r").textContent = v.r.toFixed(2);
    $("thr-f").textContent = v.f.toFixed(2);
    const g = D.guj;
    const found = frozen ? g.published.sites_found : g.sites.filter((s) => s.flagged[i] / s.pixels >= 0.5).length;
    const flagged = frozen ? g.published.pixels_flagged : g.flagged[i];
    $("thr-sites").textContent = found + " of " + g.sites.length;
    $("thr-land").textContent = site.pct(flagged / g.pixels_scored);
    $("thr-km").textContent = Math.round(flagged / 1e4).toLocaleString("en") + " km² flagged";
    const inSites = g.sites.reduce((s, x) => s + x.flagged[i], 0);
    $("thr-sentence").textContent = "At " + t.toFixed(2) + ": of every 100 validation points flagged, " + Math.round(v.pooled * 100) + " are landfill. In Gujarat, the " +
      g.sites.length + " known sites make up " + site.pct(inSites / Math.max(1, g.flagged[i])) + " of the flagged land.";
    $("thr-meters").innerHTML = ORDER.map((k) => {
      const s = classShare(k, i);
      return "<span>" + NAMES[k] + "</span><span class='bar'><i class='" + (k === "landfill" ? "lf" : "") + "' style='width:" + (s * 100).toFixed(1) + "%'></i></span><span class='val'>" + Math.round(s * 100) + "%</span>";
    }).join("");
    const el = $("thr-chart"), w = Math.max(280, el.clientWidth);
    const at = curve[i];
    el.replaceChildren(Plot.plot({
      width: w, height: 250, marginLeft: 36, marginRight: 64, marginTop: 14, marginBottom: 36,
      style: { background: "transparent", color: c.ink, fontSize: "12.5px", fontFamily: "'Inter Tight', system-ui, sans-serif" },
      x: { domain: [0, 1], label: "Threshold", grid: true }, y: { domain: [0, 1], label: null, grid: true },
      marks: [
        Plot.ruleX([0.5], { stroke: c.muted, strokeDasharray: "4 3" }),
        Plot.text([{}], { x: 0.5, frameAnchor: "bottom", dy: -4, dx: 4, text: () => "frozen", textAnchor: "start", fill: c.ink2 }),
        Plot.line(curve, { x: "t", y: "p", stroke: c.s1, strokeWidth: 2.2 }),
        Plot.line(curve, { x: "t", y: "r", stroke: c.s2, strokeWidth: 2.2 }),
        Plot.line(curve, { x: "t", y: "f", stroke: c.s3, strokeWidth: 2.2 }),
        Plot.text([curve[97]], { x: "t", y: "p", text: () => "Precision", dx: 8, textAnchor: "start", fill: c.ink }),
        Plot.text([curve[97]], { x: "t", y: "r", text: () => "Recall", dx: 8, textAnchor: "start", fill: c.ink }),
        Plot.text([curve[97]], { x: "t", y: "f", text: () => "F1", dx: 8, textAnchor: "start", fill: c.ink }),
        Plot.ruleX([t], { stroke: c.ink, strokeWidth: 1.5 }),
        Plot.dot([{ y: at.p, c: c.s1 }, { y: at.r, c: c.s2 }, { y: at.f, c: c.s3 }], { x: () => t, y: "y", fill: "c", r: 5, stroke: c.surface, strokeWidth: 2 }),
      ],
    }));
  }

  document.addEventListener("DOMContentLoaded", () => {
    site.load("threshold").then((d) => {
      D = d;
      curve = d.t.map((t, i) => Object.assign({ t }, valAt(i)));
      slider.addEventListener("input", update);
      slider.addEventListener("keydown", (e) => {
        const d5 = e.key === "PageUp" ? 0.05 : e.key === "PageDown" ? -0.05 : 0;
        if (d5) { e.preventDefault(); slider.value = Math.min(0.95, Math.max(0.05, +slider.value + d5)).toFixed(2); update(); }
      });
      $("thr-reset").addEventListener("click", () => { slider.value = "0.50"; update(); });
      update();
      site.onRedraw(update);
    }).catch((e) => { console.error(e); $("thr-chart").textContent = "The slider could not be loaded."; });
  });
})();
