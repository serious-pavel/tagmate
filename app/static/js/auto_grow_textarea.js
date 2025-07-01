function auto_grow(element) {
  element.style.height = "5px";
  element.style.height = (element.scrollHeight) + "px";
}

// Expand on page load for prefilled content
window.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('textarea').forEach(auto_grow);
});