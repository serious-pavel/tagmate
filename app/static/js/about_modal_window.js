document.addEventListener('DOMContentLoaded', function() {
    let modalBg = document.getElementById('about-modal-bg');
    let cancelBtn = document.getElementById('about-close-btn');


    let aboutBtn = document.getElementById('about-btn');
    aboutBtn.addEventListener('click', function(evt) {
        evt.preventDefault();
        modalBg.style.display = 'flex';
    });

    cancelBtn.addEventListener('click', function() {
        modalBg.style.display = 'none';
    });

    // Clicking on background closes modal
    modalBg.addEventListener('mousedown', function(evt) {
        if (evt.target === modalBg) {
            modalBg.style.display = 'none';
        }
    });

    document.addEventListener('keydown', function(e) {
        if (modalBg.style.display !== 'none' && e.key === "Escape") {
            modalBg.style.display = 'none';
        }
    });
});
