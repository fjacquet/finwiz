/**
 * Search enhancements for FinWiz documentation
 * Adds search result highlighting and filtering capabilities
 */

document.addEventListener('DOMContentLoaded', function() {
    // Add search result highlighting
    enhanceSearchResults();
    
    // Add search filters
    addSearchFilters();
    
    // Add keyboard shortcuts
    addKeyboardShortcuts();
});

/**
 * Enhance search results with better highlighting and context
 */
function enhanceSearchResults() {
    // Wait for search to be initialized
    setTimeout(() => {
        const searchInput = document.querySelector('[data-md-component="search-query"]');
        if (!searchInput) return;
        
        // Add search result enhancement
        searchInput.addEventListener('input', function(e) {
            const query = e.target.value.toLowerCase();
            if (query.length < 2) return;
            
            // Enhance search results after a short delay
            setTimeout(() => {
                enhanceResultDisplay(query);
            }, 100);
        });
    }, 1000);
}

/**
 * Enhance the display of search results
 */
function enhanceResultDisplay(query) {
    const results = document.querySelectorAll('[data-md-component="search-result"]');
    
    results.forEach(result => {
        const title = result.querySelector('.md-search-result__title');
        const text = result.querySelector('.md-search-result__teaser');
        
        if (title) {
            highlightText(title, query);
        }
        
        if (text) {
            highlightText(text, query);
            addContextualInfo(result, text);
        }
    });
}

/**
 * Highlight search terms in text
 */
function highlightText(element, query) {
    const text = element.textContent;
    const regex = new RegExp(`(${escapeRegex(query)})`, 'gi');
    
    if (regex.test(text)) {
        element.innerHTML = text.replace(regex, '<mark class="search-highlight">$1</mark>');
    }
}

/**
 * Add contextual information to search results
 */
function addContextualInfo(resultElement, textElement) {
    const link = resultElement.querySelector('a');
    if (!link) return;
    
    const href = link.getAttribute('href');
    const category = getCategoryFromPath(href);
    
    if (category && !resultElement.querySelector('.search-category')) {
        const categoryBadge = document.createElement('span');
        categoryBadge.className = 'search-category';
        categoryBadge.textContent = category;
        categoryBadge.style.cssText = `
            display: inline-block;
            background: var(--md-primary-fg-color);
            color: var(--md-primary-bg-color);
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.7em;
            margin-left: 8px;
            text-transform: uppercase;
        `;
        
        const title = resultElement.querySelector('.md-search-result__title');
        if (title) {
            title.appendChild(categoryBadge);
        }
    }
}

/**
 * Get category from file path
 */
function getCategoryFromPath(path) {
    if (path.includes('/tutorials/')) return 'Tutorial';
    if (path.includes('/how-to/')) return 'How-to';
    if (path.includes('/reference/')) return 'Reference';
    if (path.includes('/explanations/')) return 'Explanation';
    return null;
}

/**
 * Add search filters for different content types
 */
function addSearchFilters() {
    const searchForm = document.querySelector('[data-md-component="search"]');
    if (!searchForm) return;
    
    // Create filter container
    const filterContainer = document.createElement('div');
    filterContainer.className = 'search-filters';
    filterContainer.style.cssText = `
        padding: 8px 16px;
        border-bottom: 1px solid var(--md-default-fg-color--lightest);
        display: none;
    `;
    
    // Create filter buttons
    const filters = [
        { label: 'All', value: '' },
        { label: 'Tutorials', value: 'tutorials' },
        { label: 'How-to', value: 'how-to' },
        { label: 'Reference', value: 'reference' },
        { label: 'Explanations', value: 'explanations' }
    ];
    
    filters.forEach(filter => {
        const button = document.createElement('button');
        button.textContent = filter.label;
        button.className = 'search-filter-btn';
        button.dataset.filter = filter.value;
        button.style.cssText = `
            margin-right: 8px;
            padding: 4px 8px;
            border: 1px solid var(--md-default-fg-color--light);
            background: transparent;
            color: var(--md-default-fg-color);
            border-radius: 3px;
            cursor: pointer;
            font-size: 0.8em;
        `;
        
        if (filter.value === '') {
            button.classList.add('active');
            button.style.background = 'var(--md-primary-fg-color)';
            button.style.color = 'var(--md-primary-bg-color)';
        }
        
        button.addEventListener('click', () => {
            setActiveFilter(button, filter.value);
        });
        
        filterContainer.appendChild(button);
    });
    
    // Insert filter container
    const searchQuery = searchForm.querySelector('[data-md-component="search-query"]');
    if (searchQuery && searchQuery.parentNode) {
        searchQuery.parentNode.insertBefore(filterContainer, searchQuery.nextSibling);
    }
    
    // Show filters when search is active
    const searchInput = document.querySelector('[data-md-component="search-query"]');
    if (searchInput) {
        searchInput.addEventListener('focus', () => {
            filterContainer.style.display = 'block';
        });
    }
}

/**
 * Set active filter and filter results
 */
function setActiveFilter(activeButton, filterValue) {
    // Update button states
    document.querySelectorAll('.search-filter-btn').forEach(btn => {
        btn.classList.remove('active');
        btn.style.background = 'transparent';
        btn.style.color = 'var(--md-default-fg-color)';
    });
    
    activeButton.classList.add('active');
    activeButton.style.background = 'var(--md-primary-fg-color)';
    activeButton.style.color = 'var(--md-primary-bg-color)';
    
    // Filter results
    filterSearchResults(filterValue);
}

/**
 * Filter search results by category
 */
function filterSearchResults(category) {
    const results = document.querySelectorAll('[data-md-component="search-result"]');
    
    results.forEach(result => {
        const link = result.querySelector('a');
        if (!link) return;
        
        const href = link.getAttribute('href');
        const shouldShow = !category || href.includes(`/${category}/`);
        
        result.style.display = shouldShow ? 'block' : 'none';
    });
}

/**
 * Add keyboard shortcuts for search
 */
function addKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('[data-md-component="search-query"]');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Escape to close search
        if (e.key === 'Escape') {
            const searchInput = document.querySelector('[data-md-component="search-query"]');
            if (searchInput && document.activeElement === searchInput) {
                searchInput.blur();
                const searchForm = document.querySelector('[data-md-component="search"]');
                if (searchForm) {
                    searchForm.classList.remove('md-search--active');
                }
            }
        }
    });
}

/**
 * Escape special regex characters
 */
function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Add search tips and help
 */
function addSearchHelp() {
    const searchInput = document.querySelector('[data-md-component="search-query"]');
    if (!searchInput) return;
    
    // Add placeholder with tip
    searchInput.placeholder = 'Search documentation... (Ctrl+K)';
    
    // Add search tips
    const searchForm = document.querySelector('[data-md-component="search"]');
    if (searchForm) {
        const helpText = document.createElement('div');
        helpText.className = 'search-help';
        helpText.innerHTML = `
            <div style="padding: 8px 16px; font-size: 0.8em; color: var(--md-default-fg-color--light);">
                <strong>Search tips:</strong>
                Use quotes for exact phrases, 
                filter by category with buttons above,
                or press <kbd>Ctrl+K</kbd> to focus search
            </div>
        `;
        
        searchForm.appendChild(helpText);
    }
}

/**
 * Add accessibility enhancements
 */
function addAccessibilityEnhancements() {
    // Add skip link
    addSkipLink();
    
    // Enhance keyboard navigation
    enhanceKeyboardNavigation();
    
    // Add ARIA labels
    addAriaLabels();
    
    // Improve focus management
    improveFocusManagement();
}

/**
 * Add skip link for screen readers
 */
function addSkipLink() {
    const skipLink = document.createElement('a');
    skipLink.href = '#main-content';
    skipLink.className = 'skip-link';
    skipLink.textContent = 'Skip to main content';
    
    document.body.insertBefore(skipLink, document.body.firstChild);
    
    // Add main content ID if not present
    const mainContent = document.querySelector('main') || document.querySelector('.md-content');
    if (mainContent && !mainContent.id) {
        mainContent.id = 'main-content';
    }
}

/**
 * Enhance keyboard navigation
 */
function enhanceKeyboardNavigation() {
    // Add keyboard support for filter buttons
    document.addEventListener('keydown', function(e) {
        const activeElement = document.activeElement;
        
        if (activeElement && activeElement.classList.contains('search-filter-btn')) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                activeElement.click();
            }
            
            // Arrow key navigation between filter buttons
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                e.preventDefault();
                const buttons = Array.from(document.querySelectorAll('.search-filter-btn'));
                const currentIndex = buttons.indexOf(activeElement);
                
                let nextIndex;
                if (e.key === 'ArrowLeft') {
                    nextIndex = currentIndex > 0 ? currentIndex - 1 : buttons.length - 1;
                } else {
                    nextIndex = currentIndex < buttons.length - 1 ? currentIndex + 1 : 0;
                }
                
                buttons[nextIndex].focus();
            }
        }
    });
}

/**
 * Add ARIA labels and descriptions
 */
function addAriaLabels() {
    // Add ARIA labels to search elements
    const searchInput = document.querySelector('[data-md-component="search-query"]');
    if (searchInput) {
        searchInput.setAttribute('aria-label', 'Search documentation');
        searchInput.setAttribute('aria-describedby', 'search-help-text');
    }
    
    // Add ARIA labels to filter buttons
    document.querySelectorAll('.search-filter-btn').forEach(btn => {
        const filterValue = btn.dataset.filter;
        const label = filterValue ? `Filter by ${filterValue}` : 'Show all results';
        btn.setAttribute('aria-label', label);
        btn.setAttribute('role', 'button');
        btn.setAttribute('tabindex', '0');
    });
    
    // Add ARIA live region for search results
    const searchResults = document.querySelector('[data-md-component="search-result"]');
    if (searchResults && searchResults.parentNode) {
        searchResults.parentNode.setAttribute('aria-live', 'polite');
        searchResults.parentNode.setAttribute('aria-label', 'Search results');
    }
}

/**
 * Improve focus management
 */
function improveFocusManagement() {
    // Trap focus in search when active
    const searchForm = document.querySelector('[data-md-component="search"]');
    if (searchForm) {
        searchForm.addEventListener('keydown', function(e) {
            if (e.key === 'Tab' && searchForm.classList.contains('md-search--active')) {
                const focusableElements = searchForm.querySelectorAll(
                    'input, button, [tabindex]:not([tabindex="-1"])'
                );
                
                const firstElement = focusableElements[0];
                const lastElement = focusableElements[focusableElements.length - 1];
                
                if (e.shiftKey && document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                } else if (!e.shiftKey && document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement.focus();
                }
            }
        });
    }
}

/**
 * Add mobile-specific enhancements
 */
function addMobileEnhancements() {
    // Detect mobile device
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    if (isMobile) {
        // Add mobile class to body
        document.body.classList.add('mobile-device');
        
        // Improve touch targets
        document.querySelectorAll('.md-nav__link').forEach(link => {
            link.style.minHeight = '44px';
            link.style.display = 'flex';
            link.style.alignItems = 'center';
        });
        
        // Add touch-friendly search
        const searchInput = document.querySelector('[data-md-component="search-query"]');
        if (searchInput) {
            searchInput.addEventListener('touchstart', function() {
                // Prevent zoom on iOS
                searchInput.style.fontSize = '16px';
            });
        }
    }
}

/**
 * Add theme toggle accessibility
 */
function enhanceThemeToggle() {
    const themeToggle = document.querySelector('[data-md-component="palette"]');
    if (themeToggle) {
        const toggleButton = themeToggle.querySelector('label');
        if (toggleButton) {
            toggleButton.setAttribute('aria-label', 'Toggle dark/light theme');
            toggleButton.setAttribute('role', 'button');
            
            // Add keyboard support
            toggleButton.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    const input = themeToggle.querySelector('input');
                    if (input) {
                        input.click();
                    }
                }
            });
        }
    }
}

/**
 * Announce search results to screen readers
 */
function announceSearchResults() {
    const searchInput = document.querySelector('[data-md-component="search-query"]');
    if (!searchInput) return;
    
    let announceTimeout;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(announceTimeout);
        
        announceTimeout = setTimeout(() => {
            const results = document.querySelectorAll('[data-md-component="search-result"]:not([style*="display: none"])');
            const count = results.length;
            
            // Create or update announcement
            let announcement = document.getElementById('search-announcement');
            if (!announcement) {
                announcement = document.createElement('div');
                announcement.id = 'search-announcement';
                announcement.className = 'sr-only';
                announcement.setAttribute('aria-live', 'polite');
                document.body.appendChild(announcement);
            }
            
            if (count === 0) {
                announcement.textContent = 'No search results found';
            } else {
                announcement.textContent = `${count} search result${count === 1 ? '' : 's'} found`;
            }
        }, 500);
    });
}

// Initialize all enhancements
document.addEventListener('DOMContentLoaded', function() {
    addAccessibilityEnhancements();
    addMobileEnhancements();
    enhanceThemeToggle();
    announceSearchResults();
    addSearchHelp();
});