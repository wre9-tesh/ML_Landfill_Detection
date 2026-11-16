// Runs in <head> before first paint: apply a stored theme choice, if any.
(function () {
  document.documentElement.classList.add("js");
  try {
    var t = localStorage.getItem("theme");
    if (t === "light" || t === "dark") document.documentElement.setAttribute("data-theme", t);
  } catch (e) { /* storage unavailable: follow the system setting */ }
})();
