function copyPreviewText() {
const el = document.querySelector('.post-preview-text');
if (!el) return;
const plainText = el.innerText; // strips html, gets plain text only
navigator.clipboard.writeText(plainText)
    .catch(err => {
        alert('Error copying text: ' + err);
    });
}