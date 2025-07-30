document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const gridContainer = document.querySelector('.grid-container');

    sidebar.addEventListener('mouseenter', function() {
        gridContainer.classList.add('sidebar-expanded');
    });

    sidebar.addEventListener('mouseleave', function() {
        gridContainer.classList.remove('sidebar-expanded');
    });
}); 