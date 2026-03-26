// Apply saved theme immediately (before paint) to avoid flash
(function () {
  var saved = localStorage.getItem("theme") || "dark";
  document.documentElement.setAttribute("data-theme", saved);
})();

function setTheme(name) {
  document.documentElement.setAttribute("data-theme", name);
  localStorage.setItem("theme", name);
  // Update active button
  document.querySelectorAll(".theme-switcher button").forEach(function (btn) {
    btn.classList.toggle("active", btn.dataset.theme === name);
  });
}
