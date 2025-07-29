document.addEventListener('DOMContentLoaded', function() {
    const hamburgerBtn = document.getElementById('hamburger-btn');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');
    const body = document.body;
    
    // User dropdown elements
    const userDropdownBtn = document.getElementById('user-dropdown-btn');
    const userDropdownMenu = document.getElementById('user-dropdown-menu');
    const userDropdown = userDropdownBtn?.parentElement;
    
    // Help dropdown elements
    const helpBtn = document.getElementById('help-btn');
    const helpDropdownMenu = document.getElementById('help-dropdown-menu');
    const helpDropdown = helpBtn?.parentElement;
    
    // Theme controls
    const darkThemeBtn = document.getElementById('dark-theme-btn');
    const lightThemeBtn = document.getElementById('light-theme-btn');
    
    // Language controls
    const currentLangBtn = document.getElementById('current-lang-btn');
    const currentLangText = document.getElementById('current-lang-text');
    const languageDropdownMenu = document.getElementById('language-dropdown-menu');
    const languageSelector = currentLangBtn?.parentElement;

    // Sidebar functionality
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

    // Help dropdown functionality
    if (helpBtn && helpDropdown) {
        helpBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            helpDropdown.classList.toggle('open');
            // Close user dropdown if open
            if (userDropdown) {
                userDropdown.classList.remove('open');
            }
        });
    }

    // User dropdown functionality
    if (userDropdownBtn && userDropdown) {
        userDropdownBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            userDropdown.classList.toggle('open');
            // Close help dropdown if open
            if (helpDropdown) {
                helpDropdown.classList.remove('open');
            }
        });
    }

    // Close dropdowns when clicking outside
    document.addEventListener('click', function(e) {
        if (userDropdown && !userDropdown.contains(e.target)) {
            userDropdown.classList.remove('open');
        }
        if (helpDropdown && !helpDropdown.contains(e.target)) {
            helpDropdown.classList.remove('open');
        }
    });

    // Theme toggle functionality
    function updateThemeButtons() {
        const isDarkMode = body.classList.contains('dark-mode');
        if (darkThemeBtn && lightThemeBtn) {
            darkThemeBtn.classList.toggle('active', isDarkMode);
            lightThemeBtn.classList.toggle('active', !isDarkMode);
        }
    }

    function setTheme(isDark) {
        if (isDark) {
            body.classList.add('dark-mode');
        } else {
            body.classList.remove('dark-mode');
        }
        localStorage.setItem('darkMode', isDark);
        updateThemeButtons();
    }

    // Load saved dark mode state
    const savedDarkMode = localStorage.getItem('darkMode');
    if (savedDarkMode === 'true') {
        body.classList.add('dark-mode');
    }
    updateThemeButtons();

    // Theme button event listeners
    if (darkThemeBtn) {
        darkThemeBtn.addEventListener('click', function() {
            setTheme(true);
        });
    }

    if (lightThemeBtn) {
        lightThemeBtn.addEventListener('click', function() {
            setTheme(false);
        });
    }

    // Language dropdown functionality
    if (currentLangBtn && languageSelector) {
        currentLangBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            languageSelector.classList.toggle('open');
        });
    }

    // Language option selection
    if (languageDropdownMenu) {
        languageDropdownMenu.addEventListener('click', function(e) {
            const langOption = e.target.closest('.lang-option');
            if (langOption) {
                const selectedLang = langOption.getAttribute('data-lang');
                updateCurrentLanguage(selectedLang);
                languageSelector.classList.remove('open');
                
                // Trigger i18n update
                if (window.i18n) {
                    window.i18n.setLanguage(selectedLang);
                }
            }
        });
    }

    function updateCurrentLanguage(lang) {
        if (currentLangText) {
            if (lang === 'zh') {
                currentLangText.textContent = '🇹🇼 ZH';
            } else {
                currentLangText.textContent = '🇺🇸 EN';
            }
        }
    }

    // Initialize language display
    const savedLang = localStorage.getItem('language') || 'zh';
    updateCurrentLanguage(savedLang);

    // Close language dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (languageSelector && !languageSelector.contains(e.target)) {
            languageSelector.classList.remove('open');
        }
    });
});
