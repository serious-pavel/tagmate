// ---- CSRF Helper ----
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === name + "=") {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// ---- Drag and Drop Sorting ----
document.addEventListener("DOMContentLoaded", function() {
    // Make sure SortableJS is loaded
    if (typeof Sortable === "undefined") return;

    const list = document.getElementById("dnd-list-post");
    if (!list) return;

    Sortable.create(list, {
        animation: 150,
        onStart: () => list.classList.add('dragging'),
        onChoose: () => list.classList.add('dragging'),
        onUnchoose: () => list.classList.remove('dragging'),
        onEnd: function (evt) {
            list.classList.remove('dragging')
            // After drag'n'drop, collect new tag order:
            const tagDivs = list.querySelectorAll(".tag");
            const tagOrder = [];
            tagDivs.forEach(div => {
                // Get tag id from hidden input
                const input = div.querySelector('input[name="tag_to_detach"]');
                if (input) tagOrder.push(input.value);
            });

            // Build data for AJAX POST
            const csrftoken = getCookie('csrftoken');
            const postId = list.dataset.postId;

            fetch(`/posts/api/${postId}/reorder_tags`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrftoken,
                },
                body: JSON.stringify({ tag_order: tagOrder }),
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    showMessage("Failed to update tag order: " + (data.error || ""));
                } else {
                    showMessage("Tag order saved!", "success");
                    const preview = document.getElementById("post-preview-tags");
                    if (preview && data.tag_text) {
                        preview.textContent = data.tag_text;
                    }
                }
            })
            .catch(error => {
                showMessage("AJAX error: " + error, "error");
            });
        }
    });
});
