function showItemCreate(item)
{
    var btn = document.getElementById(item + "-fake-btn");
    if (btn.style.display === "none") {
        btn.style.display = "block";
    } else {
        btn.style.display = "none";
    }
}