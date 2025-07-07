document.addEventListener('DOMContentLoaded', function () {
    const tabPosts = document.getElementById('tab-posts');
    const tabTgs = document.getElementById('tab-tgs');
    const TAB_KEY = 'blockL_selected_tab';

    function showTab(tab) {
        document.body.classList.remove('blockL-show-posts', 'blockL-show-tgs');
        document.body.classList.add(tab === 'tgs' ? 'blockL-show-tgs' : 'blockL-show-posts');
        tabPosts.classList.toggle('active', tab === 'posts');
        tabTgs.classList.toggle('active', tab === 'tgs');
        localStorage.setItem(TAB_KEY, tab);
    }

    // Set correct button's active state at load based on body class
    const activeTab = document.body.classList.contains('blockL-show-tgs') ? 'tgs' : 'posts';
    tabPosts.classList.toggle('active', activeTab === 'posts');
    tabTgs.classList.toggle('active', activeTab === 'tgs');

    tabPosts.addEventListener('click', function () { showTab('posts'); });
    tabTgs.addEventListener('click', function () { showTab('tgs'); });
});
