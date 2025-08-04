const DISPLAY_BLOCK = "block";
const DISPLAY_NONE = "none";

function focusInputForItem(item) {
    if (item === "post") {
        const input = document.querySelector('input[name="new_post_title"]');
        if (input) input.focus();
    } else if (item === "tg") {
        const input = document.querySelector('input[name="new_tg_name"]');
        if (input) input.focus();
    }
}

function toggleItemCreateVisibility(item) {
    const btn = document.getElementById(item + "-fake-btn");
    if (btn.style.display === DISPLAY_NONE) {
        btn.style.display = DISPLAY_BLOCK;
    } else {
        btn.style.display = DISPLAY_NONE;
        focusInputForItem(item);
    }
}