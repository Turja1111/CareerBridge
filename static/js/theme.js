/**
 * CareerBridge Theme Manager
 * - Reads saved theme from localStorage immediately on load (no FOUC)
 * - Falls back to OS preference (prefers-color-scheme)
 * - Wires the #theme-toggle button to switch & persist theme
 */
(function () {
    "use strict";

    const STORAGE_KEY = "careerbridge-theme";
    const root = document.documentElement;

    // ── 1. Resolve theme (run immediately, before paint) ─────────────────────
    const saved = localStorage.getItem(STORAGE_KEY);
    const prefersDark = window.matchMedia
        ? window.matchMedia("(prefers-color-scheme: dark)").matches
        : false;
    const initialTheme = saved || (prefersDark ? "dark" : "light");
    root.setAttribute("data-theme", initialTheme);

    // ── 2. Update button UI to match current theme ────────────────────────────
    function syncButton(theme) {
        const toggle = document.getElementById("theme-toggle");
        if (!toggle) return;

        const icon = toggle.querySelector(".theme-toggle-icon");
        const label = toggle.querySelector(".theme-toggle-text");

        if (icon) {
            icon.setAttribute("data-lucide", theme === "dark" ? "sun" : "moon");
        }
        if (label) {
            label.textContent = theme === "dark" ? "Light" : "Dark";
        }
        // Re-render Lucide icons after attribute change
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }

    // ── 3. Apply theme + sync button ─────────────────────────────────────────
    function applyTheme(theme) {
        root.setAttribute("data-theme", theme);
        localStorage.setItem(STORAGE_KEY, theme);
        syncButton(theme);
    }

    // ── 4. Wire up toggle button once DOM is ready ────────────────────────────
    function init() {
        syncButton(root.getAttribute("data-theme"));

        const toggle = document.getElementById("theme-toggle");
        if (!toggle) return;

        toggle.addEventListener("click", function () {
            const current = root.getAttribute("data-theme");
            applyTheme(current === "dark" ? "light" : "dark");
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
