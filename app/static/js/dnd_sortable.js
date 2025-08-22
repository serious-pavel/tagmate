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

// Generalized Drag and Drop Sorting
function setupDndSortable(config) {
    const list = document.getElementById(config.listId);
    if (!list) return;

    const tagSelector = ".tag";
    const inputSelector = 'input[name="tag_to_detach"]';
    const dataIdKey = 'itemId' // will correspond to data-item-id

    Sortable.create(list, {
        animation: 150,
        forceFallback: true,
        onStart: () => list.classList.add('dragging'),
        onChoose: () => list.classList.add('dragging'),
        onUnchoose: () => list.classList.remove('dragging'),
        onEnd: function (evt) {
            list.classList.remove('dragging');
            const tagDivs = list.querySelectorAll(tagSelector);
            const tagOrder = [];
            tagDivs.forEach(div => {
                const input = div.querySelector(inputSelector);
                if (input) tagOrder.push(input.value);
            });

            // Prepare data for AJAX POST
            const csrftoken = getCookie('csrftoken');
            const objectId = list.dataset[dataIdKey];

            fetch(config.ajaxUrl(objectId), {
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
                    if (config.previewId && data.tag_text) {
                        const preview = document.getElementById(config.previewId);
                        if (preview) preview.textContent = data.tag_text;
                    }
                }
            })
            .catch(error => {
                showMessage("AJAX error: " + error, "error");
            });
        }
    });
}

// Setup both lists once DOM is loaded
document.addEventListener("DOMContentLoaded", function() {
    if (typeof Sortable === "undefined") return;

    // Posts
    setupDndSortable({
        listId: "dnd-list-post",
        ajaxUrl: postId => `/posts/api/${postId}/reorder_tags`,
        previewId: "post-preview-tags"
    });

    // For TagGroups
    setupDndSortable({
        listId: "dnd-list-tg",
        ajaxUrl: tgId => `/tags/api/${tgId}/reorder_tags`
    });
});
