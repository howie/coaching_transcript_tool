
document.addEventListener('DOMContentLoaded', function() {
    // Sidebar toggle functionality
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.querySelector('.main-content');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            if (window.innerWidth <= 768) {
                sidebar.classList.toggle('mobile-open');
            } else {
                mainContent.classList.toggle('sidebar-collapsed');
            }
        });
    }

    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth <= 768) {
            sidebar.classList.add('collapsed');
            mainContent.classList.add('sidebar-collapsed');
        } else {
            sidebar.classList.remove('mobile-open');
            if (!sidebar.classList.contains('collapsed')) {
                mainContent.classList.remove('sidebar-collapsed');
            }
        }
    });

    // Flash message handling
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            setTimeout(function() {
                message.remove();
            }, 300);
        }, 5000);
    });

    // Close flash messages on click
    const closeButtons = document.querySelectorAll('.flash-close');
    closeButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const message = button.parentElement;
            message.style.opacity = '0';
            setTimeout(function() {
                message.remove();
            }, 300);
        });
    });

    // Active navigation highlighting
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(function(link) {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // Mobile sidebar overlay
    if (window.innerWidth <= 768) {
        const overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 850;
            display: none;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        document.body.appendChild(overlay);

        // Show overlay when sidebar is open on mobile
        if (sidebar) {
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.attributeName === 'class') {
                        if (sidebar.classList.contains('mobile-open')) {
                            overlay.style.display = 'block';
                            setTimeout(() => overlay.style.opacity = '1', 10);
                        } else {
                            overlay.style.opacity = '0';
                            setTimeout(() => overlay.style.display = 'none', 300);
                        }
                    }
                });
            });
            observer.observe(sidebar, { attributes: true });
        }

        // Close sidebar when clicking overlay
        overlay.addEventListener('click', function() {
            sidebar.classList.remove('mobile-open');
        });
    }
});
