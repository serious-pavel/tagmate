const sum = (array) => array.reduce((a, b) => a + b, 0);
const toNumber = (array) => array.map(m => parseFloat(m) || 0);

const setTextAreaMaxHeight = () => {
  document.querySelectorAll('textarea.edit-like-text').forEach(textarea => {
    setTimeout(() => {
      const parentBlock = document.querySelector('.app-block-R');
      const postPreviewTags = document.querySelector('#post-preview-tags');
      const copyPreviewBtn = document.querySelector('#copy-preview-btn');
      const postPreviewHeader = document.querySelector('.post-preview-header');

      const { marginTop, marginBottom } = window.getComputedStyle(postPreviewTags);
      const { paddingTop, paddingBottom } = window.getComputedStyle(textarea);
      const {
        paddingTop: parentPaddingTop,
        paddingBottom: parentPaddingBottom,
        gap: parentGap
      } = window.getComputedStyle(parentBlock);

      const margins = sum(toNumber([marginTop, marginBottom]));
      const textareaPaddings = sum(toNumber([paddingTop, paddingBottom]));
      const parentPaddings = sum(toNumber([parentPaddingTop, parentPaddingBottom, parentGap, parentGap]));

      const parentHeight = parentBlock.clientHeight;
      const siblingsHeight = (postPreviewTags?.clientHeight || 0) + (copyPreviewBtn?.clientHeight || 0) + (postPreviewHeader?.clientHeight || 0);

      const maxHeight = parentHeight - parentPaddings - siblingsHeight - margins - textareaPaddings;

      textarea.style.maxHeight = `${maxHeight}px`;
    }, 100);
  });
}

document.addEventListener("DOMContentLoaded", function () {
  function autoResizeInput(input) {
    if (input.tagName !== "INPUT") return;
    input.style.width = "2ch"; // reset to minimum
    input.style.width = (input.value.length + 1) + "ch";
  }
  document.querySelectorAll('.shrinkable-input').forEach(input => {
    autoResizeInput(input);
    input.addEventListener('input', function () {
      autoResizeInput(input);
    });
  });
});

document.addEventListener('DOMContentLoaded', setTextAreaMaxHeight);
window.addEventListener('resize', setTextAreaMaxHeight);
