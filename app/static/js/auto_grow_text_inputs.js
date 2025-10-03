function autoGrow(element) {
  if (element.innerHTML) {
    element.style.height = `${element.scrollHeight}px`;
  }
}

// Expand on page load for prefilled content
// Use window.onload ensures all resources (including styles/fonts) loaded
window.addEventListener('load', function () {
  document.querySelectorAll('textarea').forEach(autoGrow);
});


document.addEventListener("DOMContentLoaded", function () {
  function autoResizeInput(input) {
    if (input.tagName !== "INPUT") return;
    input.style.width = "2ch"; // reset to minimum
    input.style.width = (input.value.length + 1) + "ch";
  }
  document.querySelectorAll('.shrinkable-input').forEach(input => {
    autoResizeInput(input);
    input.addEventListener('input', function () {
      autoResizeInput(input);
    });
  });
});
