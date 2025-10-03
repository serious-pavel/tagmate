const toggleVisibleElement = (element, key) => {
  element.classList.toggle('visible');
  if (key) {
    const isVisible = element.classList.contains('visible');
    window.localStorage.setItem(key, isVisible.toString());
    if (isVisible) {
      setTextAreaMaxHeight();
    }
  }
};

const setPreviewStateFromLocalStorage = (element, key) => {
  const storedState = window.localStorage.getItem(key);
  if (storedState === 'true') {
    element.classList.add('visible');
  } else {
    element.classList.remove('visible');
  }
}

const togglePostsMenu = (postsMenu, postsMenuToggle, defaultButtonText) => {
  toggleVisibleElement(postsMenu);
  if (postsMenu.classList.contains('visible')) {
    postsMenuToggle.innerHTML = '< Back';
  } else {
    postsMenuToggle.innerHTML = defaultButtonText;
  }
};

document.addEventListener("DOMContentLoaded", function () {
  const postsMenuToggle = document.querySelector('#mobile-posts-toggle');
  const defaultText = postsMenuToggle.innerHTML;
  const postsMenu = document.querySelector('.app-block-L');
  const previewModeToggle = document.querySelector('#preview-toggle');
  const tagsModeToggle = document.querySelector('#tags-toggle');
  const postPreview = document.querySelector('.post-preview');

  setPreviewStateFromLocalStorage(postPreview, 'preview');

  postsMenuToggle?.addEventListener('click', function () {
    togglePostsMenu(postsMenu, postsMenuToggle, defaultText);
  });

  previewModeToggle?.addEventListener('click', function () {
    toggleVisibleElement(postPreview, 'preview');
  });
  tagsModeToggle?.addEventListener('click', function () {
    toggleVisibleElement(postPreview, 'preview');
  });
});
