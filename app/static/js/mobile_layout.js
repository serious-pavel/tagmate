const toggleVisibleElement = (element, key) => {
  element.classList.toggle('visible');
  if (key) {
    const isVisible = element.classList.contains('visible');
    window.localStorage.setItem(key, isVisible.toString());
    if (isVisible) {
      setTextAreaStyle();
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

const togglePostsMenu = (postsMenu, postsMenuOverlay, postsMenuToggle) => {
  toggleVisibleElement(postsMenu);
  toggleVisibleElement(postsMenuOverlay);
  const prevNavActive = document.querySelector('#nav-toggle-btn + a');
  if (postsMenu.classList.contains('visible')) {
    postsMenuToggle.classList.add('show-nav-back');
    postsMenuToggle.classList.remove('show-nav-list');
    postsMenuToggle.classList.add('nav-active');
    prevNavActive.classList.remove('nav-active');
  } else {
    postsMenuToggle.classList.add('show-nav-list');
    postsMenuToggle.classList.remove('show-nav-back');
    postsMenuToggle.classList.remove('nav-active');
    prevNavActive.classList.add('nav-active');
  }
};

document.addEventListener("DOMContentLoaded", function () {
  const navToggleButton = document.querySelector('#nav-toggle-btn');
  const postsMenu = document.querySelector('.app-block-L');
  const postsMenuOverlay = document.querySelector('.posts-menu-overlay');
  const previewModeToggle = document.querySelector('#preview-toggle');
  const tagsModeToggle = document.querySelector('#tags-toggle');
  const postPreview = document.querySelector('.post-preview');

  setPreviewStateFromLocalStorage(postPreview, 'preview');

  navToggleButton?.addEventListener('click', function () {
    togglePostsMenu(postsMenu, postsMenuOverlay, navToggleButton);
  });

  previewModeToggle?.addEventListener('click', function () {
    toggleVisibleElement(postPreview, 'preview');
  });
  tagsModeToggle?.addEventListener('click', function () {
    toggleVisibleElement(postPreview, 'preview');
  });
});
