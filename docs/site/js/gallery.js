// Chip galleries. Each <div class="gallery" data-gallery="..."> is filled from the chip index
// (tables.json: chips, verdicts). Sections marked .needs-chips stay hidden until chips exist.
(function () {
  const SEEN = { bare_soil: "Bare soil or open plot", field_or_grass: "Field, grass or scrub", building: "Buildings", industrial_plant: "Industrial plant",
    other: "Other", riverbed: "Riverbed", blue_roof: "Blue roof", water: "Water", salt_pan: "Salt pan" };
  function card(ch, caption) {
    const fig = document.createElement("figure");
    fig.className = "chip";
    const poly = (ch.outline || []).map((ring) => "<polygon points='" + ring.map((p) => (p[0] * 100).toFixed(1) + "," + (p[1] * 100).toFixed(1)).join(" ") + "'/>").join("");
    fig.innerHTML = "<a class='img' href='https://www.google.com/maps/@" + ch.lat + "," + ch.lon + ",700m/data=!3m1!1e3' target='_blank' rel='noopener' title='Open this place in Google Maps'>" +
      "<img loading='lazy' src='site/img/chips/" + ch.id + ".jpg' alt='Sentinel-2 true-colour image, " + (ch.size_m / 1000) + " km across, of " + caption.alt + "'>" +
      "<img class='score' loading='lazy' src='site/img/chips/" + ch.id + "_score.png' alt=''>" +
      (poly ? "<svg viewBox='0 0 100 100' preserveAspectRatio='none'>" + poly + "</svg>" : "") + "</a><figcaption><b>" + caption.title + "</b>" + caption.text + "</figcaption>";
    return fig;
  }
  const cap = (s) => s[0].toUpperCase() + s.slice(1);
  function fill(el, chips, verdicts) {
    const spec = el.dataset.gallery;
    const alarmCap = (ch) => ({ title: ch.id + ", rank " + ch.rank, alt: "alarm " + ch.id, text: cap(ch.city) + ". Mean score " + ch.mean_score.toFixed(2) + ", " + ch.area_ha + " ha." });
    const siteCap = (ch) => ({ title: ch.name || ch.id, alt: "the site " + (ch.name || ch.id), text: ch.note || "" });
    let list = [];
    if (spec === "sites") list = chips.filter((c) => c.kind === "site").map((c) => card(c, siteCap(c)));
    else if (spec.startsWith("id:")) list = chips.filter((c) => spec.slice(3).split(",").includes(c.id)).map((c) => card(c, c.kind === "alarm" ? alarmCap(c) : siteCap(c)));
    else if (spec === "dumps") list = chips.filter((c) => c.kind === "alarm" && (verdicts[c.id] || {}).verdict === "dump").map((c) => card(c, alarmCap(c)));
    else if (spec.startsWith("seen:")) {
      const k = spec.slice(5);
      list = chips.filter((c) => c.kind === "alarm" && (verdicts[c.id] || {}).verdict === "lookalike" && (verdicts[c.id].seen === k)).sort((a, b) => a.rank - b.rank).slice(0, +el.dataset.max || 6).map((c) => card(c, alarmCap(c)));
    }
    el.replaceChildren(...list);
    return list.length;
  }
  document.addEventListener("DOMContentLoaded", () => {
    const gs = document.querySelectorAll("[data-gallery]");
    if (!gs.length) return;
    site.load("tables").then((T) => {
      if (!T.chips || !T.chips.length) return;
      document.querySelectorAll(".needs-chips").forEach((el) => (el.hidden = false));
      document.querySelectorAll(".no-chips").forEach((el) => (el.hidden = true));
      gs.forEach((el) => { if (!fill(el, T.chips, T.verdicts || {})) { const s = el.closest(".gsection"); if (s) s.hidden = true; } });
      document.querySelectorAll("input.gscore").forEach((cb) => cb.addEventListener("change", () => {
        document.querySelectorAll(cb.dataset.for).forEach((g) => g.classList.toggle("showscore", cb.checked));
      }));
    });
  });
})();
