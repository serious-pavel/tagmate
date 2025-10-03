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
