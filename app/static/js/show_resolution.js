    function updateResolution() {
      const widget = document.getElementById('resolution-widget');
      if (widget) {
        widget.textContent = `${window.innerWidth} × ${window.innerHeight} px`;
      }
    }
    // Initial update
    updateResolution();
    // Update on resize
    window.addEventListener('load', updateResolution);
    window.addEventListener('resize', updateResolution);