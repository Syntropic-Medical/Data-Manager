/**
 * Enhanced Table Sorting Functionality for Data Manager
 * This file provides fast, efficient table sorting that works with dynamically loaded content
 */

// Store sorting state for tables across the application
const TableSortState = {
  // Map to store sorting state for each table (using table ID or data attribute)
  states: new Map(),

  // Get current state for a table
  getState(tableId) {
    if (!this.states.has(tableId)) {
      this.states.set(tableId, { column: null, direction: null });
    }
    return this.states.get(tableId);
  },

  // Update state for a table
  setState(tableId, column, direction) {
    this.states.set(tableId, { column, direction });
  }
};

// Utility functions for comparing different data types
const SortUtils = {
  isDateString(str) {
    return /^\d{4}-\d{2}-\d{2}$/.test(str) || 
           /^\d{1,2}\/\d{1,2}\/\d{4}$/.test(str) ||
           /^\d{1,2}-\d{1,2}-\d{4}$/.test(str);
  },
  
  compareDates(dateA, dateB, isAscending) {
    const a = new Date(dateA);
    const b = new Date(dateB);
    return isAscending ? a - b : b - a;
  },
  
  compareNumbers(a, b, isAscending) {
    return isAscending ? a - b : b - a;
  },
  
  compareStrings(a, b, isAscending) {
    return isAscending ? a.localeCompare(b) : b.localeCompare(a);
  }
};

/**
 * Enhanced table sorting function that uses DocumentFragment for better performance
 * and stores row values to avoid expensive DOM operations
 */
function sortTable(table, columnIndex, headerElement) {
  // Performance: Use requestAnimationFrame to ensure UI responsiveness
  requestAnimationFrame(() => {
    // Get table body to sort
    const tbody = table.querySelector('tbody');
    if (!tbody) return;
    
    // Assign a unique ID to the table if it doesn't have one
    if (!table.id) {
      table.id = 'sortable-table-' + Date.now();
    }
    
    // Get current sort state
    const tableId = table.id;
    const currentState = TableSortState.getState(tableId);
    
    // Determine sort direction
    let newDirection = 'asc';
    if (currentState.column === columnIndex) {
      newDirection = currentState.direction === 'asc' ? 'desc' : 'asc';
    }
    const isAscending = newDirection === 'asc';
    
    // Update sort state
    TableSortState.setState(tableId, columnIndex, newDirection);
    
    // Update header styling - Reset all headers first
    table.querySelectorAll('th').forEach(th => {
      th.removeAttribute('data-sort');
      const indicator = th.querySelector('.sort-indicator, .sort-icon');
      if (indicator) {
        indicator.textContent = '⇕';
        indicator.style.opacity = '0.7';
        indicator.style.fontWeight = 'normal';
      }
    });
    
    // Update active header
    headerElement.setAttribute('data-sort', newDirection);
    const indicator = headerElement.querySelector('.sort-indicator, .sort-icon');
    if (indicator) {
      indicator.textContent = isAscending ? '↑' : '↓';
      indicator.style.opacity = '1';
      indicator.style.fontWeight = 'bold';
    }
    
    // Performance optimization: Use document fragment and avoid repeated DOM operations
    const fragment = document.createDocumentFragment();
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Cache row values to avoid repeated DOM lookups - huge performance gain
    const rowValues = rows.map(row => {
      const cell = row.cells[columnIndex];
      let value = '';
      
      if (cell) {
        value = cell.textContent.trim();
      }
      
      return { row, value };
    });
    
    // Sort function with data type detection
    rowValues.sort((a, b) => {
      const valueA = a.value;
      const valueB = b.value;
      
      // Handle empty values (send to end of sort)
      if (!valueA && valueB) return 1;
      if (valueA && !valueB) return -1;
      if (!valueA && !valueB) return 0;
      
      // Check if values are dates
      if (SortUtils.isDateString(valueA) && SortUtils.isDateString(valueB)) {
        return SortUtils.compareDates(valueA, valueB, isAscending);
      }
      
      // Check if values are numbers
      if (!isNaN(parseFloat(valueA)) && !isNaN(parseFloat(valueB))) {
        return SortUtils.compareNumbers(parseFloat(valueA), parseFloat(valueB), isAscending);
      }
      
      // Default to string comparison
      return SortUtils.compareStrings(valueA, valueB, isAscending);
    });
    
    // Build the sorted table fragment
    rowValues.forEach(item => fragment.appendChild(item.row));
    
    // Update the DOM in a single operation - much more efficient
    tbody.innerHTML = '';
    tbody.appendChild(fragment);
  });
}

/**
 * Efficiently initialize table sorting on a specific table or all tables
 * Can be called multiple times without duplicating event handlers
 */
function initTableSorting(targetTable = null) {
  // Find all sortable tables or use the target table if provided
  const sortableTables = targetTable ? [targetTable] : document.querySelectorAll('table.table-sortable');
  
  sortableTables.forEach(table => {
    // Skip tables already initialized
    if (table.dataset.sortingInitialized === 'true') return;
    
    const thead = table.querySelector('thead');
    if (!thead) return;
    
    const headers = thead.querySelectorAll('th');
    
    headers.forEach((header, index) => {
      // Skip checkbox columns
      if (header.querySelector('input[type="checkbox"]')) return;
      
      // Add sortable class and style
      header.classList.add('sortable');
      header.style.cursor = 'pointer';
      
      // Add sort indicator if needed
      let sortIndicator = header.querySelector('.sort-indicator, .sort-icon');
      if (!sortIndicator) {
        // Create new sort indicator
        sortIndicator = document.createElement('span');
        sortIndicator.className = 'sort-indicator ms-1';
        header.appendChild(sortIndicator);
      }
      
      // Always ensure the indicator is visible with the default symbol
      sortIndicator.textContent = '⇕';
      sortIndicator.style.display = 'inline-block';
      sortIndicator.style.marginLeft = '5px';
      sortIndicator.style.fontSize = '0.8em';
      sortIndicator.style.opacity = '0.7';
      
      // Add click event with proper binding
      header.addEventListener('click', function() {
        sortTable(table, index, this);
      });
    });
    
    // Mark table as initialized
    table.dataset.sortingInitialized = 'true';
  });
}

// Make functions available globally
window.sortTable = sortTable;
window.initTableSorting = initTableSorting;

// Initialize sorting when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  // Initialize all existing tables
  initTableSorting();
  
  // Use Intersection Observer for performance - only initialize tables when they come into view
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting && entry.target.classList.contains('table-sortable')) {
        initTableSorting(entry.target);
      }
    });
  });
  
  // Observe all sortable tables
  document.querySelectorAll('table.table-sortable').forEach(table => {
    observer.observe(table);
  });
  
  // Setup MutationObserver to handle dynamically added tables
  const mutationObserver = new MutationObserver((mutations) => {
    // Check if any new tables were added
    let needsInitialization = false;
    
    mutations.forEach(mutation => {
      if (mutation.type === 'childList') {
        mutation.addedNodes.forEach(node => {
          // Check if the added node is a table or contains tables
          if (node.nodeType === Node.ELEMENT_NODE) {
            if (node.matches('table.table-sortable') || node.querySelector('table.table-sortable')) {
              needsInitialization = true;
            }
          }
        });
      }
    });
    
    // Only initialize if needed
    if (needsInitialization) {
      // Use requestIdleCallback for better performance if available
      if (window.requestIdleCallback) {
        window.requestIdleCallback(() => initTableSorting());
      } else {
        // Fallback to setTimeout for browsers that don't support requestIdleCallback
        setTimeout(() => initTableSorting(), 0);
      }
    }
  });
  
  // Start observing the body for added/removed nodes
  mutationObserver.observe(document.body, { 
    childList: true, 
    subtree: true 
  });
}); 