document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll('input.submit-on-blur, textarea.submit-on-blur').forEach(function(field) {
        field.addEventListener('blur', function() {
            if (field.form) {
                field.form.submit();
            }
        });
    });
});
