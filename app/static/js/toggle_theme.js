const themeIcons = {
  "light": "🌞",
  "dark": "🌚"
};

function setTheme(theme) {
  document.body.classList.remove("theme-light", "theme-dark");
  document.body.classList.add("theme-" + theme);
  const themeLabel = document.getElementById("theme-label");
  if (themeLabel) {
    themeLabel.textContent = themeIcons[theme];
  } else {
    document.addEventListener("DOMContentLoaded", function () {
      document.getElementById("theme-label").textContent = themeIcons[theme];
    });
  }
}

// Detect theme: from storage or from system
let theme = localStorage.getItem('theme');
if (!theme) {
  theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? "dark" : "light";
  localStorage.setItem('theme', theme);
}
setTheme(theme);

document.addEventListener("DOMContentLoaded", function () {
  document.getElementById("theme-toggle-btn").addEventListener("click", function () {
    theme = theme === "light" ? "dark" : "light";
    localStorage.setItem('theme', theme);
    setTheme(theme);
  });
});

