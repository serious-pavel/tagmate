document.addEventListener('DOMContentLoaded', function() {
    let modalBg = document.getElementById('generic-modal-bg');
    let confirmBtn = document.getElementById('modal-confirm-btn');
    let cancelBtn = document.getElementById('modal-cancel-btn');
    let modalText = document.getElementById('generic-modal-text');
    let targetForm = null;

    const MESSAGES = {
        post: "Create Post",
        taggroup: "Create TagGroup",
        default: "Create item"
    };

    const PLACEHOLDERS = {
        post: "Title (optional)",
        taggroup: "Name (optional)",
        default: "Title/Name (optional)"
    };

    // action hidden input field
    const ACTIONS = {
        post: "create_post",
        taggroup: "create_tg",
        default: "create_item"
    };

    document.querySelectorAll('.new-create-item-btn').forEach(btn => {
        btn.addEventListener('click', function(evt) {
            evt.preventDefault();
            // targetForm = btn.closest('form');
            modalBg.style.display = 'flex';

            // Look for a custom message or type
            let type = btn.getAttribute('data-item-type');
            let custom = modalText.textContent;
            modalText.textContent = MESSAGES[type] || custom || MESSAGES.default;

            targetForm = document.getElementById('create-item-form');
            // Change hidden action input value
            if (targetForm) {
                let actionInput = targetForm.querySelector('input[name="action"]');
                if (actionInput) {
                    actionInput.value = ACTIONS[type] || ACTIONS.default;
                }
                // Change placeholder
                let titleInput = targetForm.querySelector('input[name="new_item_name"]');
                if (titleInput) {
                    titleInput.placeholder = PLACEHOLDERS[type] || PLACEHOLDERS.default;
                }
            }
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
