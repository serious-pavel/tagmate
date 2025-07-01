document.addEventListener('DOMContentLoaded', function () {
    // const form = document.getElementById('update-post-form');
    const descInput = document.getElementById('post-desc');
    const updateBtn = document.getElementById('update-post-desc-btn');

    // Save initial values
    const initialDesc = descInput.value;

    function checkChanged() {
        const changed = (
            descInput.value !== initialDesc
        );
        if (changed) {
            // updateBtn.classList.remove('btn-inactive');
            updateBtn.classList.add('btn-active');
        } else {
            updateBtn.classList.remove('btn-active');
            // updateBtn.classList.add('btn-inactive');
        }
    }

    descInput.addEventListener('input', checkChanged);

    // Initial check
    checkChanged();
});