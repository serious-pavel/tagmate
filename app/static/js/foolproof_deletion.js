document.addEventListener('DOMContentLoaded', function() {
    let modalBg = document.getElementById('delete-modal-bg');
    let confirmBtn = document.getElementById('confirm-delete-btn');
    let cancelBtn = document.getElementById('cancel-delete-btn');
    let modalText = document.getElementById('delete-modal-text');
    let targetForm = null;

    // Optionally, set default messages per type
    const MESSAGES = {
        post: "Are you sure you want to delete this post?",
        taggroup: "Are you sure you want to delete this TagGroup?",
        default: "Are you sure you want to delete this item?"
    };

    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', function(evt) {
            evt.preventDefault();
            targetForm = btn.closest('form');

            // Look for a custom message or type
            let type = btn.getAttribute('data-delete-type');
            let custom = btn.getAttribute('data-delete-message');
            modalText.textContent = custom || MESSAGES[type] || MESSAGES.default;

            modalBg.style.display = 'flex';
        });
    });

    confirmBtn.addEventListener('click', function() {
        if (targetForm) {
            targetForm.submit();
        }
    });
    cancelBtn.addEventListener('click', function() {
        modalBg.style.display = 'none';
        targetForm = null;
    });

    // Clicking on background closes modal
    modalBg.addEventListener('mousedown', function(evt) {
        if (evt.target === modalBg) {
            modalBg.style.display = 'none';
            targetForm = null;
        }
    });

    document.addEventListener('keydown', function(e) {
        if (modalBg.style.display !== 'none' && e.key === "Escape") {
            modalBg.style.display = 'none';
            targetForm = null;
        }
    });
});
