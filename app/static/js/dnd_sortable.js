// var tagList = document.getElementById('dnd-list-post');
// var sortable = Sortable.create(tagList, { draggable: ".tag" });
//

document.addEventListener("DOMContentLoaded", function () {
    const tagList = document.getElementById("dnd-list-post");
    if (tagList) {
        new Sortable(tagList, {
            animation: 150,
            filter: "form,button",        // Avoid dragging when interacting with form/button
            preventOnFilter: false
            // onEnd: function (evt) {
            //     // Collect new order and send to backend here if needed
            // },
        });
    }
});
