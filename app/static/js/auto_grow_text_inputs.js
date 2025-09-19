function auto_grow(element) {
  element.style.height = "5px";
  element.style.height = (element.scrollHeight) + "px";
}

// Expand on page load for prefilled content
// Use window.onload ensures all resources (including styles/fonts) loaded
window.addEventListener('load', function() {
  document.querySelectorAll('textarea').forEach(auto_grow);
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
