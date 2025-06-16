// ---- Message Timeout (shared) ----
const MESSAGE_TIMEOUT = 2000;

// ---- Show Message (Django-like) ----
function showMessage(msg, type = "error") {
    // Try to find existing message area or create one
    let area = document.querySelector('.message-area');
    if (!area) {
        area = document.createElement('div');
        area.className = 'message-area';
        // Add at top of body, or wherever you like
        document.body.prepend(area);
    }
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${type}`;
    msgDiv.textContent = msg;
    area.appendChild(msgDiv);
    // Auto-hide after 3s
    setTimeout(() => {
        msgDiv.remove();
    }, MESSAGE_TIMEOUT);
}

// On DOMContentLoaded: auto-hide Django-rendered messages too
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.message-area .message').forEach(function(msgDiv) {
        setTimeout(function() {
            msgDiv.remove();
        }, MESSAGE_TIMEOUT); // Match your showMessage timeout
    });
});
