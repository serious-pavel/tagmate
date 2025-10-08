// ---- Message Timeout (shared) ----
const MESSAGE_TIMEOUT = 2500;

function fadeOutAndRemove(msgDiv, timeout = MESSAGE_TIMEOUT) {
    setTimeout(() => {
        msgDiv.classList.remove('in');
        msgDiv.addEventListener('transitionend', function() {
            msgDiv.remove();
        }, { once: true });
    }, timeout);
}

// ---- Show Message (Django-like) ----
function showMessage(msg, type = "error") {
    let area = document.querySelector('.message-area');
    if (!area) {
        area = document.createElement('div');
        area.className = 'message-area';
        document.body.prepend(area);
    }
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${type}`;
    msgDiv.textContent = msg;
    area.appendChild(msgDiv);

    requestAnimationFrame(() => {
        msgDiv.classList.add('in');
        fadeOutAndRemove(msgDiv);
    });
}

// On DOMContentLoaded: auto-show and hide Django-rendered messages too
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.message-area .message').forEach(function(msgDiv) {
        requestAnimationFrame(() => {
            msgDiv.classList.add('in');
            fadeOutAndRemove(msgDiv);
        });
    });
});