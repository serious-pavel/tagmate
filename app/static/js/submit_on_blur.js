document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll('input.submit-on-blur, textarea.submit-on-blur').forEach(function(field) {
        // Save initial value as a property on the DOM node
        field.dataset.initialValue = field.value;

        field.addEventListener('blur', function() {
            // Only submit if changed (and optional simple validation)
            const changed = field.value !== field.dataset.initialValue;

            if (changed) {
                // Find an associated button
                let btn = document.getElementById(`update-${field.id}-btn`);
                if (btn) {
                    btn.click();
                } else if (field.form) {
                    // fallback to submitting the form directly
                    field.form.submit();
                }
            }
        });

        field.addEventListener('keydown', function(e) {
            if (e.key === "Escape") {
                field.value = field.dataset.initialValue;
                field.blur();
                e.preventDefault();
            } else if (
                field.tagName.toLowerCase() === 'textarea' &&
                e.key === "Enter" && e.shiftKey
            ) {
                // Submit on Shift+Enter ONLY for textarea fields
                let btn = document.getElementById(`update-${field.id}-btn`);
                if (btn) {
                    btn.click();
                } else if (field.form) {
                    field.form.submit();
                }
                // Prevent inserting a newline
                e.preventDefault();
            }

        });
    });
});
