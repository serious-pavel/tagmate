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

document.addEventListener('DOMContentLoaded', function () {
    const descInput = document.getElementById('post-title');
    const updateBtn = document.getElementById('update-post-title-btn');

    const initialDesc = descInput.value;

    function checkChanged() {
        const changed = (
            descInput.value !== initialDesc
        );
        if (changed) {
            updateBtn.classList.add('btn-active');
        } else {
            updateBtn.classList.remove('btn-active');
        }
    }

    descInput.addEventListener('input', checkChanged);

    checkChanged();
});

document.addEventListener('DOMContentLoaded', function () {
    const descInput = document.getElementById('tg-name');
    const updateBtn = document.getElementById('update-tg-name-btn');

    const initialDesc = descInput.value;

    function checkChanged() {
        const changed = (
            descInput.value !== initialDesc
        );
        if (changed) {
            updateBtn.classList.add('btn-active');
        } else {
            updateBtn.classList.remove('btn-active');
        }
    }

    descInput.addEventListener('input', checkChanged);

    checkChanged();
});