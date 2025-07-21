    function updateResolution() {
      const widget = document.getElementById('resolutionWidget');
      if (widget) {
        widget.textContent = `${window.innerWidth} × ${window.innerHeight} px`;
      }
    }
    // Initial update
    updateResolution();
    // Update on resize
    window.addEventListener('load', updateResolution);
    window.addEventListener('resize', updateResolution);