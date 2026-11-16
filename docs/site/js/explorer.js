// Feature explorer: for one of the 26 variables, the distribution of landfill points against
// each kind of non-landfill point. Data: site/data/features_hist.json.
(function () {
  const root = document.getElementById("ex");
  if (!root) return;
  const $ = (id) => document.getElementById(id);
  const sel = $("ex-f"), panels = $("ex-panels");
  const OTHERS = ["near_site", "random", "bare_soil", "quarry", "ash_pond"];
  let H, cur, hoverPanel = null;

  const num = (v) => (Math.abs(v) >= 100 ? v.toFixed(0) : Math.abs(v) >= 10 ? v.toFixed(1) : Math.abs(v) >= 1 ? v.toFixed(2) : v.toFixed(3));
  const share = (v) => (v * 100).toFixed(1) + "%";

  function reading(f, cls) {
    const a = f.auc[cls], name = H.class_labels[cls].toLowerCase();
    const s = a >= 0.5 ? "A landfill pixel has a higher value than a " + name + " pixel " + Math.round(a * 100) + " times in 100."
      : "A landfill pixel has a lower value than a " + name + " pixel " + Math.round((1 - a) * 100) + " times in 100.";
    return s + (Math.abs(a - 0.5) < 0.1 ? " This variable hardly separates the two." : "");
  }

  function draw() {
    const f = H.features.find((x) => x.name === cur) || H.features[0];
    const c = site.colors();
    sel.value = f.name;
    $("ex-group").textContent = "Group: " + f.group;
    $("ex-def").innerHTML = "<b>" + f.label + "</b> (" + f.unit + "). " + f.definition;
    const dens = {};
    H.classes.forEach((k) => (dens[k] = f.counts[k].map((v) => v / H.n[k])));
    const ymax = d3.max(H.classes, (k) => d3.max(dens[k])) * 1.05;
    panels.replaceChildren();
    const svgs = [];
    const rows = OTHERS.concat(["axis"]);
    rows.forEach((cls) => {
      const row = document.createElement("div");
      row.className = "hpanel";
      const isAxis = cls === "axis";
      row.innerHTML = isAxis ? "<div class='name'></div><div class='plot'></div><div class='auc'></div>"
        : "<div class='name'><b>Landfill vs " + H.class_labels[cls].toLowerCase() + "</b>" + H.n[cls].toLocaleString("en") + " points</div><div class='plot'></div>" +
          "<div class='auc'>AUC<b>" + f.auc[cls].toFixed(2) + "</b></div>";
      if (isAxis) row.style.borderTop = "none";
      panels.appendChild(row);
      const holder = row.querySelector(".plot");
      const W = Math.max(200, holder.clientWidth), Hh = isAxis ? 38 : 96;
      const x = d3.scaleLinear().domain([f.edges[0], f.edges[40]]).range([4, W - 4]);
      const y = d3.scaleLinear().domain([0, ymax]).range([Hh - 2, 6]);
      const svg = d3.select(holder).append("svg").attr("viewBox", "0 0 " + W + " " + Hh).attr("preserveAspectRatio", "none").style("height", Hh + "px");
      if (isAxis) {
        const g = svg.append("g").attr("transform", "translate(0,2)").call(d3.axisBottom(x).ticks(Math.min(8, W / 80)).tickSizeOuter(0));
        g.selectAll("text").attr("fill", c.muted).style("font-size", "12px");
        g.selectAll("line,path").attr("stroke", c.axis);
        svg.append("text").attr("x", W - 4).attr("y", 34).attr("text-anchor", "end").attr("fill", c.ink2).style("font-size", "12px").text(f.label + ", " + f.unit);
        return;
      }
      svg.attr("role", "img").attr("aria-label", "Distribution of " + f.name + " for landfill and " + H.class_labels[cls].toLowerCase() + " points");
      svg.selectAll("rect.o").data(dens[cls]).join("rect").attr("x", (d, i) => x(f.edges[i]) + 0.5).attr("width", (d, i) => Math.max(1, x(f.edges[i + 1]) - x(f.edges[i]) - 1))
        .attr("y", (d) => y(d)).attr("height", (d) => y(0) - y(d)).attr("fill", c.s2).attr("fill-opacity", 0.75);
      let p = "M" + x(f.edges[0]) + "," + y(0);
      dens.landfill.forEach((d, i) => { p += "V" + y(d) + "H" + x(f.edges[i + 1]); });
      p += "V" + y(0);
      svg.append("path").attr("d", p).attr("fill", "none").attr("stroke", c.surface).attr("stroke-width", 5);
      svg.append("path").attr("d", p).attr("fill", "none").attr("stroke", c.s1).attr("stroke-width", 2.2);
      svg.append("line").attr("x1", 0).attr("x2", W).attr("y1", y(0)).attr("y2", y(0)).attr("stroke", c.axis);
      [["landfill", c.s1], [cls, c.s2]].forEach(([k, col]) => svg.append("path").attr("d", "M" + x(Math.max(f.edges[0], Math.min(f.edges[40], f.median[k]))) + "," + (y(0) + 1) + "l-4,-7h8z").attr("fill", col).attr("stroke", c.surface));
      const guide = svg.append("line").attr("y1", 0).attr("y2", Hh).attr("stroke", c.ink).attr("stroke-width", 1).style("display", "none");
      svgs.push({ guide, x });
      svg.on("pointermove pointerdown", (ev) => {
        const r = svg.node().getBoundingClientRect();
        const v = x.invert(((ev.clientX - r.left) / r.width) * W);
        const i = Math.max(0, Math.min(39, Math.floor(((v - f.edges[0]) / (f.edges[40] - f.edges[0])) * 40)));
        const mid = (f.edges[i] + f.edges[i + 1]) / 2;
        svgs.forEach((s) => s.guide.attr("x1", s.x(mid)).attr("x2", s.x(mid)).style("display", null));
        hoverPanel = cls;
        const edge = i === 0 ? "below " + num(f.edges[1]) : i === 39 ? "above " + num(f.edges[39]) : num(f.edges[i]) + " to " + num(f.edges[i + 1]);
        $("ex-hover").textContent = "Values " + edge + " " + (f.unit.startsWith("index") ? "" : f.unit) + ": landfill " + share(dens.landfill[i]) + " of its points; " +
          OTHERS.map((k) => H.class_labels[k].toLowerCase() + " " + share(dens[k][i])).join("; ") + ".";
        $("ex-reading").textContent = reading(f, cls);
      });
    });
    const dflt = OTHERS.slice().sort((a, b) => Math.abs(f.auc[b] - 0.5) - Math.abs(f.auc[a] - 0.5))[0];
    $("ex-reading").textContent = reading(f, hoverPanel || dflt);
    $("ex-hover").textContent = "Move over a panel to read the shares in one range of values. Triangles mark the medians.";
    const head = "<tr><th>Class</th><th class='num'>Points</th><th class='num'>25th percentile</th><th class='num'>Median</th><th class='num'>75th percentile</th><th class='num'>AUC, landfill against it</th></tr>";
    $("ex-table").innerHTML = "<div class='tablewrap'><table><thead>" + head + "</thead><tbody>" + H.classes.map((k) =>
      "<tr><td>" + H.class_labels[k] + "</td><td class='num'>" + H.n[k].toLocaleString("en") + "</td><td class='num'>" + num(f.q25[k]) + "</td><td class='num'>" + num(f.median[k]) +
      "</td><td class='num'>" + num(f.q75[k]) + "</td><td class='num'>" + (k === "landfill" ? "" : f.auc[k].toFixed(3)) + "</td></tr>").join("") + "</tbody></table></div>";
  }

  function pick(name, push) {
    if (!H.features.some((x) => x.name === name)) return;
    cur = name;
    hoverPanel = null;
    if (push) history.replaceState(null, "", "#f=" + name);
    draw();
  }
  function fromHash() {
    const m = /^#f=([\w]+)$/.exec(location.hash);
    if (m) { pick(m[1], false); root.scrollIntoView(); }
  }
  function step(d) {
    const i = H.features.findIndex((x) => x.name === cur);
    pick(H.features[(i + d + H.features.length) % H.features.length].name, true);
  }

  document.addEventListener("DOMContentLoaded", () => {
    site.load("features_hist").then((h) => {
      H = h;
      h.groups.forEach((g) => {
        const og = document.createElement("optgroup");
        og.label = g[0].toUpperCase() + g.slice(1);
        h.features.filter((x) => x.group === g).forEach((x) => og.appendChild(new Option(x.name + ": " + x.label, x.name)));
        sel.appendChild(og);
      });
      sel.addEventListener("change", () => pick(sel.value, true));
      $("ex-prev").addEventListener("click", () => step(-1));
      $("ex-next").addEventListener("click", () => step(1));
      sel.addEventListener("keydown", (e) => { if (e.key === "ArrowLeft") { e.preventDefault(); step(-1); } if (e.key === "ArrowRight") { e.preventDefault(); step(1); } });
      addEventListener("hashchange", fromHash);
      cur = "LST_anom";
      draw();
      fromHash();
      site.onRedraw(draw);
    }).catch((e) => { console.error(e); panels.textContent = "The explorer could not be loaded."; });
  });
})();
