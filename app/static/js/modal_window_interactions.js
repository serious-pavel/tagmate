document.addEventListener('DOMContentLoaded', function() {
    let modalBg = document.getElementById('generic-modal-bg');
    let confirmBtn = document.getElementById('modal-confirm-btn');
    let cancelBtn = document.getElementById('modal-cancel-btn');
    let modalText = document.getElementById('generic-modal-text');
    let targetForm = null;

    // Optionally, set default messages per type
    const MESSAGES = {
        post: "Create Post",
        taggroup: "Create TagGroup",
        default: "Create item"
    };

    document.querySelectorAll('.new-create-item-btn').forEach(btn => {
        btn.addEventListener('click', function(evt) {
            evt.preventDefault();
            // targetForm = btn.closest('form');
            modalBg.style.display = 'flex';

            targetForm = document.getElementById('create-item-form');

            // Look for a custom message or type
            let type = btn.getAttribute('data-item-type');
            let custom = modalText.textContent;
            modalText.textContent = MESSAGES[type] || custom || MESSAGES.default;
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
