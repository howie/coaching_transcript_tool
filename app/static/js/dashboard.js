document.addEventListener('DOMContentLoaded', function() {
    const hamburgerBtn = document.getElementById('hamburger-btn');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');
    const body = document.body;
    const darkModeToggle = document.getElementById('dark-mode-toggle');

    if (hamburgerBtn && sidebar) {
        hamburgerBtn.addEventListener('click', function() {
            if (window.innerWidth > 768) {
                // Desktop: Toggle collapsed state
                sidebar.classList.toggle('collapsed');
                body.classList.toggle('sidebar-collapsed');
                
                // Save state to localStorage
                const isCollapsed = sidebar.classList.contains('collapsed');
                localStorage.setItem('sidebarCollapsed', isCollapsed);
            } else {
                // Mobile: Toggle open state
                sidebar.classList.toggle('open');
            }
        });
    }

    // Load saved sidebar state on desktop
    if (window.innerWidth > 768) {
        const savedState = localStorage.getItem('sidebarCollapsed');
        if (savedState === 'true') {
            sidebar.classList.add('collapsed');
            body.classList.add('sidebar-collapsed');
        }
    }

    // Close sidebar when clicking on the main content area on mobile
    if (mainContent && sidebar) {
        mainContent.addEventListener('click', function() {
            if (window.innerWidth <= 768 && sidebar.classList.contains('open')) {
                sidebar.classList.remove('open');
            }
        });
    }

    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            // Desktop: Remove mobile open class, restore collapsed state
            sidebar.classList.remove('open');
            const savedState = localStorage.getItem('sidebarCollapsed');
            if (savedState === 'true') {
                sidebar.classList.add('collapsed');
                body.classList.add('sidebar-collapsed');
            } else {
                sidebar.classList.remove('collapsed');
                body.classList.remove('sidebar-collapsed');
            }
        } else {
            // Mobile: Remove desktop collapsed classes
            sidebar.classList.remove('collapsed');
            body.classList.remove('sidebar-collapsed');
        }
    });

    // Dark Mode Toggle
    if (darkModeToggle) {
        // Load saved dark mode state
        const savedDarkMode = localStorage.getItem('darkMode');
        if (savedDarkMode === 'true') {
            body.classList.add('dark-mode');
            updateDarkModeToggleText();
        }

        darkModeToggle.addEventListener('click', function() {
            body.classList.toggle('dark-mode');
            const isDarkMode = body.classList.contains('dark-mode');
            localStorage.setItem('darkMode', isDarkMode);
            updateDarkModeToggleText();
        });

        function updateDarkModeToggleText() {
            const isDarkMode = body.classList.contains('dark-mode');
            if (isDarkMode) {
                darkModeToggle.textContent = '☀️ 亮色模式';
            } else {
                darkModeToggle.textContent = '🌙 深色模式';
            }
        }

        // Initialize button text
        updateDarkModeToggleText();
    }
});
