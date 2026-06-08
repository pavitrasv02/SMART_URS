/**
 * SMART URS — Night Sky theme toggle
 * Single click handler only (duplicate handlers were canceling toggles).
 */
(function () {
    'use strict';

    const STORAGE_KEY = 'smarturs_theme';
    const LOG = '[SMART URS Theme]';
    const root = document.documentElement;
    let handlerBound = false;

    function getPreferred() {
        try {
            const saved = localStorage.getItem(STORAGE_KEY);
            if (saved === 'dark' || saved === 'light') return saved;
        } catch (err) {
            console.warn(LOG, 'localStorage read failed', err);
        }
        return 'light';
    }

    function getCurrentTheme() {
        const attr = root.getAttribute('data-theme');
        if (attr === 'dark' || attr === 'light') return attr;
        return getPreferred();
    }

    function applyTheme(theme) {
        if (theme !== 'dark' && theme !== 'light') {
            console.warn(LOG, 'applyTheme ignored invalid value:', theme);
            return;
        }

        const isNight = theme === 'dark';
        console.log(LOG, 'applyTheme →', theme);

        root.setAttribute('data-theme', theme);
        root.classList.toggle('night-sky', isNight);
        root.setAttribute('data-bs-theme', isNight ? 'dark' : 'light');
        root.style.colorScheme = isNight ? 'dark' : 'light';

        if (document.body) {
            document.body.classList.add('urs-themed');
            document.body.classList.toggle('night-sky-active', isNight);
        }

        try {
            localStorage.setItem(STORAGE_KEY, theme);
            console.log(LOG, 'localStorage saved:', theme);
        } catch (err) {
            console.warn(LOG, 'localStorage write failed', err);
        }

        const icon = document.getElementById('themeIcon');
        if (icon) {
            icon.className = isNight ? 'fas fa-sun' : 'fas fa-moon';
            console.log(LOG, 'icon updated →', isNight ? 'sun' : 'moon');
        }

        const btn = document.getElementById('themeToggle');
        if (btn) {
            const label = isNight ? 'Switch to Light Mode' : 'Switch to Night Sky Mode';
            btn.setAttribute('title', label);
            btn.setAttribute('aria-label', label);
        }
    }

    function toggleTheme() {
        const current = getCurrentTheme();
        const next = current === 'dark' ? 'light' : 'dark';
        console.log(LOG, 'toggleTheme:', current, '→', next);
        applyTheme(next);
        return next;
    }

    function onToggleClick(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log(LOG, 'themeToggle clicked');
        toggleTheme();
    }

    function bindToggle() {
        if (handlerBound) {
            console.log(LOG, 'bindToggle skipped — already bound');
            return;
        }

        const btn = document.getElementById('themeToggle');
        if (!btn) {
            console.warn(LOG, 'bindToggle failed — #themeToggle not found');
            return;
        }

        btn.addEventListener('click', onToggleClick);
        handlerBound = true;
        console.log(LOG, 'click handler bound to #themeToggle');
    }

    function init() {
        const theme = getCurrentTheme();
        console.log(LOG, 'init — current theme:', theme);

        if (document.body) {
            document.body.classList.add('urs-themed');
            document.body.classList.toggle('night-sky-active', theme === 'dark');
        }

        bindToggle();
    }

    /* Set <html> attributes before body exists (no body access) */
    (function applyEarly() {
        const theme = getPreferred();
        root.setAttribute('data-theme', theme);
        root.classList.toggle('night-sky', theme === 'dark');
        root.setAttribute('data-bs-theme', theme === 'dark' ? 'dark' : 'light');
        root.style.colorScheme = theme === 'dark' ? 'dark' : 'light';
        console.log(LOG, 'early apply —', theme);
    })();

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    window.SMARTURSTheme = {
        applyTheme: applyTheme,
        toggleTheme: toggleTheme,
        getPreferred: getPreferred,
        getCurrentTheme: getCurrentTheme,
    };

    console.log(LOG, 'ready — SMARTURSTheme exposed');
})();
