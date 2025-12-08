/**
 * Universal Tab State Persistence Module
 * Handles tab state persistence across page reloads using localStorage
 * Works with all CENRO admin panel pages
 * 
 * @author CENRO Development Team
 * @version 1.0.0
 */

(function() {
    'use strict';

    const TabPersistence = {
        /**
         * Storage key prefix for tab states
         */
        STORAGE_PREFIX: 'cenro_tab_state_',

        /**
         * Get the current page identifier
         * @returns {string} Page identifier based on current URL path
         */
        getPageIdentifier: function() {
            const path = window.location.pathname;
            // Extract the last segment of the path as page identifier
            const segments = path.split('/').filter(seg => seg.length > 0);
            return segments[segments.length - 1] || 'home';
        },

        /**
         * Get the storage key for the current page
         * @returns {string} Storage key
         */
        getStorageKey: function() {
            return this.STORAGE_PREFIX + this.getPageIdentifier();
        },

        /**
         * Save the active tab state to localStorage
         * @param {string} tabName - The name/id of the active tab
         */
        saveTabState: function(tabName) {
            try {
                const storageKey = this.getStorageKey();
                localStorage.setItem(storageKey, tabName);
                console.log(`[Tab Persistence] Saved tab state: ${tabName} for page: ${this.getPageIdentifier()}`);
            } catch (e) {
                console.warn('[Tab Persistence] Failed to save tab state:', e);
            }
        },

        /**
         * Retrieve the saved tab state from localStorage
         * @returns {string|null} The saved tab name or null if not found
         */
        getTabState: function() {
            try {
                const storageKey = this.getStorageKey();
                const savedTab = localStorage.getItem(storageKey);
                if (savedTab) {
                    console.log(`[Tab Persistence] Retrieved tab state: ${savedTab} for page: ${this.getPageIdentifier()}`);
                }
                return savedTab;
            } catch (e) {
                console.warn('[Tab Persistence] Failed to retrieve tab state:', e);
                return null;
            }
        },

        /**
         * Clear the saved tab state for the current page
         */
        clearTabState: function() {
            try {
                const storageKey = this.getStorageKey();
                localStorage.removeItem(storageKey);
                console.log(`[Tab Persistence] Cleared tab state for page: ${this.getPageIdentifier()}`);
            } catch (e) {
                console.warn('[Tab Persistence] Failed to clear tab state:', e);
            }
        },

        /**
         * Initialize tab persistence for the current page
         * Automatically restores the last active tab if available
         * 
         * @param {Object} options - Configuration options
         * @param {string} options.tabButtonsSelector - CSS selector for tab buttons (default: '.tab-button')
         * @param {string} options.tabContentsSelector - CSS selector for tab contents (default: '.tab-content')
         * @param {string} options.activeClass - CSS class for active state (default: 'active')
         * @param {Function} options.onTabSwitch - Callback function when tab is switched
         * @param {Function} options.customSwitchFunction - Custom tab switch function to use instead of default
         * @returns {boolean} True if initialization was successful
         */
        init: function(options = {}) {
            const config = {
                tabButtonsSelector: options.tabButtonsSelector || '.tab-button',
                tabContentsSelector: options.tabContentsSelector || '.tab-content',
                activeClass: options.activeClass || 'active',
                onTabSwitch: options.onTabSwitch || null,
                customSwitchFunction: options.customSwitchFunction || null
            };

            console.log('[Tab Persistence] Initializing for page:', this.getPageIdentifier());

            // Get all tab buttons
            const tabButtons = document.querySelectorAll(config.tabButtonsSelector);
            if (tabButtons.length === 0) {
                console.warn('[Tab Persistence] No tab buttons found. Skipping initialization.');
                return false;
            }

            // Restore saved tab state on page load
            this.restoreTabState(config);

            // Add event listeners to all tab buttons to save state on click
            tabButtons.forEach(button => {
                // Store the original onclick handler if it exists
                const originalOnClick = button.onclick;

                button.addEventListener('click', (event) => {
                    // Extract tab name from various possible attributes
                    const tabName = this.extractTabName(button, event);
                    
                    if (tabName) {
                        // Save the tab state
                        this.saveTabState(tabName);

                        // Call the callback if provided
                        if (config.onTabSwitch) {
                            config.onTabSwitch(tabName, button);
                        }
                    }
                });
            });

            console.log('[Tab Persistence] Initialization complete. Monitoring', tabButtons.length, 'tab buttons.');
            return true;
        },

        /**
         * Extract tab name from button element
         * Supports multiple patterns used across different pages
         * 
         * @param {HTMLElement} button - The tab button element
         * @param {Event} event - The click event
         * @returns {string|null} The tab name or null
         */
        extractTabName: function(button, event) {
            // Pattern 1: onclick="switchTab('tabName')" or onclick="openTab(event, 'tabName')"
            const onclickAttr = button.getAttribute('onclick');
            if (onclickAttr) {
                // Match switchTab('xxx'), openTab(event, 'xxx'), or switchTab(event, 'xxx')
                const match = onclickAttr.match(/(?:switchTab|openTab)\s*\(\s*(?:event\s*,\s*)?['"]([^'"]+)['"]\s*\)/);
                if (match && match[1]) {
                    return match[1];
                }
            }

            // Pattern 2: data-tab attribute
            const dataTab = button.getAttribute('data-tab');
            if (dataTab) {
                return dataTab;
            }

            // Pattern 3: Find associated tab content by matching text or ID
            const buttonText = button.textContent.trim().toLowerCase().replace(/\s+/g, '-');
            const possibleTabId = buttonText + '-tab';
            if (document.getElementById(possibleTabId)) {
                return buttonText;
            }

            console.warn('[Tab Persistence] Could not extract tab name from button:', button);
            return null;
        },

        /**
         * Restore the saved tab state
         * @param {Object} config - Configuration object
         */
        restoreTabState: function(config) {
            const savedTab = this.getTabState();
            if (!savedTab) {
                console.log('[Tab Persistence] No saved tab state found. Using default active tab.');
                return;
            }

            // Find the button for the saved tab
            const tabButtons = document.querySelectorAll(config.tabButtonsSelector);
            let targetButton = null;

            for (const button of tabButtons) {
                const tabName = this.extractTabName(button);
                if (tabName === savedTab) {
                    targetButton = button;
                    break;
                }
            }

            if (targetButton) {
                console.log('[Tab Persistence] Restoring tab:', savedTab);
                
                // Programmatically click the button to activate it
                // Use a small delay to ensure DOM is fully ready
                setTimeout(() => {
                    targetButton.click();
                }, 50);
            } else {
                console.warn('[Tab Persistence] Saved tab not found:', savedTab);
            }
        },

        /**
         * Manually switch to a specific tab and save the state
         * Useful for programmatic tab switching
         * 
         * @param {string} tabName - The name of the tab to switch to
         * @param {Function} switchFunction - The switch function to call (e.g., window.switchTab)
         */
        switchToTab: function(tabName, switchFunction) {
            if (typeof switchFunction === 'function') {
                switchFunction(tabName);
                this.saveTabState(tabName);
            } else {
                console.error('[Tab Persistence] Invalid switch function provided');
            }
        },

        /**
         * Add URL hash support for tab persistence
         * Allows direct linking to specific tabs via URL hash (#tab-name)
         */
        enableHashNavigation: function() {
            // Check for hash on page load
            const hash = window.location.hash.substring(1); // Remove '#'
            if (hash) {
                console.log('[Tab Persistence] Hash navigation detected:', hash);
                this.saveTabState(hash);
                
                // Find and click the corresponding tab button
                const tabButtons = document.querySelectorAll('.tab-button');
                for (const button of tabButtons) {
                    const tabName = this.extractTabName(button);
                    if (tabName === hash) {
                        setTimeout(() => button.click(), 100);
                        break;
                    }
                }
            }

            // Listen for hash changes
            window.addEventListener('hashchange', () => {
                const newHash = window.location.hash.substring(1);
                if (newHash) {
                    this.saveTabState(newHash);
                }
            });
        }
    };

    // Export to global scope
    window.TabPersistence = TabPersistence;

    console.log('[Tab Persistence] Module loaded successfully');
})();
