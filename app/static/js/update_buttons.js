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
            updateBtn.style.opacity = 1;
            updateBtn.style.pointerEvents = 'auto';
            updateBtn.classList.add('highlighted'); // Use your .highlighted CSS for extra emphasis
        } else {
            updateBtn.style.opacity = 0.4;
            updateBtn.style.pointerEvents = 'none';
            updateBtn.classList.remove('highlighted');
        }
    }

    descInput.addEventListener('input', checkChanged);

    // Initial check
    checkChanged();
});