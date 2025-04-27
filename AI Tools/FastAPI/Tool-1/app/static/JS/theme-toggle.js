/**
 * Theme Toggle Script for Modern UI
 * Handles switching between light and dark mode
 */

document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('theme-toggle');
    const htmlEl = document.documentElement;
    const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Check for saved theme preference or use OS preference
    const savedTheme = localStorage.getItem('theme');
    let currentTheme = savedTheme || (prefersDarkMode ? 'dark' : 'light');
    
    // Set initial theme
    setTheme(currentTheme);
    
    // Theme toggle button click handler
    themeToggle.addEventListener('click', function() {
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        setTheme(newTheme);
        currentTheme = newTheme;
        localStorage.setItem('theme', newTheme);
    });
    
    // Function to set theme and update UI
    function setTheme(theme) {
        if (theme === 'dark') {
            htmlEl.classList.add('dark-theme');
            themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
            themeToggle.setAttribute('title', 'Switch to light mode');
        } else {
            htmlEl.classList.remove('dark-theme');
            themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
            themeToggle.setAttribute('title', 'Switch to dark mode');
        }
    }
    
    // Update theme when OS preference changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem('theme')) {
            const newTheme = e.matches ? 'dark' : 'light';
            setTheme(newTheme);
            currentTheme = newTheme;
        }
    });
}); 