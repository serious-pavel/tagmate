function copyPreviewText() {
    // Get the textarea value
    const descEl = document.getElementById('post-desc');
    const descText = descEl ? descEl.value : '';

    // Get the tags text (strip HTML, use innerText for plain text, trim just in case)
    const tagsEl = document.getElementById('post-preview-tags');
    const tagsText = tagsEl ? tagsEl.innerText.trim() : '';

    // Combine them and paste line breaks
    const combinedText = descText + (tagsText ? '\n\n' + tagsText : '');

    // Copy the combined text to clipboard
    navigator.clipboard.writeText(combinedText)
        .then(() => {
            showMessage('Copied to clipboard!', 'success');
        })
        .catch(err => {
            showMessage('Error copying text: ' + err, 'error');
        });
}