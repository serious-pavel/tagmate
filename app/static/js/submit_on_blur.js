document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll('input.submit-on-blur, textarea.submit-on-blur').forEach(function(field) {
        // Save initial value as a property on the DOM node
        field.dataset.initialValue = field.value;

        field.addEventListener('blur', function() {
            // Only submit if changed (and optional simple validation)
            const changed = field.value !== field.dataset.initialValue;

            if (changed) {
                // Find an associated button
                let btn = null;
                if (field.id === "tg-name") {
                    btn = document.getElementById("update-tg-name-btn");
                } else if (field.id === "post-title") {
                    btn = document.getElementById("update-post-title-btn");
                } else if (field.id === "post-desc") {
                    btn = document.getElementById("update-post-desc-btn");
                }

                if (btn) {
                    btn.click();
                } else if (field.form) {
                    // fallback to submitting the form directly
                    field.form.submit();
                }
            }
        });
    });
});
