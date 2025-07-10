document.addEventListener('DOMContentLoaded', function() {
    const modalBg = document.getElementById('delete-modal-bg');
    const showModalBtn = document.getElementById('show-delete-modal-btn');
    const cancelBtn = document.getElementById('cancel-delete-btn');
    const confirmBtn = document.getElementById('confirm-delete-btn');
    const deleteForm = document.querySelector('.delete-form');

    // Show Modal
    showModalBtn.addEventListener('click', function(e) {
        modalBg.style.display = 'flex';
    });

    // Cancel / Hide Modal
    cancelBtn.addEventListener('click', function(e) {
        modalBg.style.display = 'none';
    });

    // Delete Confirmed
    confirmBtn.addEventListener('click', function(e) {
        deleteForm.submit();
    });

    // Click outside modal window = cancel
    modalBg.addEventListener('mousedown', function(e) {
        if (e.target === modalBg) {
            modalBg.style.display = 'none';
        }
    });

    // (optional) ESC key closes modal
    document.addEventListener('keydown', function(e) {
        if (modalBg.style.display !== 'none' && e.key === "Escape") {
            modalBg.style.display = 'none';
        }
    });
});
