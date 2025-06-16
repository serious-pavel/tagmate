function copyPreviewText() {
const el = document.querySelector('.post-preview-text');
if (!el) return;
const plainText = el.innerText; // strips html, gets plain text only
navigator.clipboard.writeText(plainText)
    .then(() => {
        showMessage('Copied to clipboard!', 'success');
    })
    .catch(err => {
        showMessage('Error copying text: ' + err, 'error');
    });
}