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

// Utility functions for comparing different data types - optimized for performance
const SortUtils = {
  // Cache for parsed dates to avoid repeated parsing
  dateCache: new Map(),
  
  // Cache for numeric values
  numberCache: new Map(),
  
  isDateString(str) {
    return /^\d{4}-\d{2}-\d{2}$/.test(str) || 
           /^\d{1,2}\/\d{1,2}\/\d{4}$/.test(str) ||
           /^\d{1,2}-\d{1,2}-\d{4}$/.test(str);
  },
  
  getParsedDate(dateStr) {
    if (this.dateCache.has(dateStr)) {
      return this.dateCache.get(dateStr);
    }
    const date = new Date(dateStr);
    this.dateCache.set(dateStr, date);
    return date;
  },
  
  compareDates(dateA, dateB, isAscending) {
    const a = this.getParsedDate(dateA);
    const b = this.getParsedDate(dateB);
    return isAscending ? a - b : b - a;
  },
  
  getParsedNumber(numStr) {
    if (this.numberCache.has(numStr)) {
      return this.numberCache.get(numStr);
    }
    const num = parseFloat(numStr);
    this.numberCache.set(numStr, num);
    return num;
  },
  
  compareNumbers(a, b, isAscending) {
    const numA = this.getParsedNumber(a);
    const numB = this.getParsedNumber(b);
    return isAscending ? numA - numB : numB - numA;
  },
  
  compareStrings(a, b, isAscending) {
    return isAscending ? a.localeCompare(b) : b.localeCompare(a);
  },
  
  // Clear caches periodically to prevent memory leaks
  clearCaches() {
    this.dateCache.clear();
    this.numberCache.clear();
  }
};

// Clear caches every 5 minutes to prevent memory buildup
setInterval(() => SortUtils.clearCaches(), 5 * 60 * 1000);

/**
 * Enhanced table sorting function that uses DocumentFragment for better performance
 * and stores row values to avoid expensive DOM operations
 */
function sortTable(table, columnIndex, headerElement) {
  // Throttle sorting to prevent multiple rapid sorts
  if (table.dataset.sorting === 'true') return;
  table.dataset.sorting = 'true';
  
  // Use requestAnimationFrame to ensure UI responsiveness
  requestAnimationFrame(() => {
    try {
      // Get table body to sort
      const tbody = table.querySelector('tbody');
      if (!tbody) {
        table.dataset.sorting = 'false';
        return;
      }
      
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
      
      // Early exit for small tables - no need for virtual rendering
      if (rows.length < 100) {
        // Cache row values to avoid repeated DOM lookups
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
            return SortUtils.compareNumbers(valueA, valueB, isAscending);
          }
          
          // Default to string comparison
          return SortUtils.compareStrings(valueA, valueB, isAscending);
        });
        
        // Build the sorted table fragment
        rowValues.forEach(item => fragment.appendChild(item.row));
        
        // Update the DOM in a single operation - much more efficient
        tbody.innerHTML = '';
        tbody.appendChild(fragment);
      } else {
        // For large tables, use virtual rendering
        // First, cache all row data
        const allRowData = rows.map(row => {
          const cells = Array.from(row.cells);
          const cellData = cells.map(cell => cell.innerHTML);
          const cellValues = cells.map(cell => cell.textContent.trim());
          
          return {
            originalRow: row,
            cells: cellData,
            values: cellValues,
            valueAtSortColumn: cellValues[columnIndex] || ''
          };
        });
        
        // Sort the data
        allRowData.sort((a, b) => {
          const valueA = a.valueAtSortColumn;
          const valueB = b.valueAtSortColumn;
          
          // Handle empty values
          if (!valueA && valueB) return 1;
          if (valueA && !valueB) return -1;
          if (!valueA && !valueB) return 0;
          
          // Check if values are dates
          if (SortUtils.isDateString(valueA) && SortUtils.isDateString(valueB)) {
            return SortUtils.compareDates(valueA, valueB, isAscending);
          }
          
          // Check if values are numbers
          if (!isNaN(parseFloat(valueA)) && !isNaN(parseFloat(valueB))) {
            return SortUtils.compareNumbers(valueA, valueB, isAscending);
          }
          
          // Default to string comparison
          return SortUtils.compareStrings(valueA, valueB, isAscending);
        });
        
        // Only render the visible rows (virtual rendering)
        // Determine visible area - approximate row height of 50px
        const viewportHeight = window.innerHeight;
        const tableTop = table.getBoundingClientRect().top;
        const visibleRowsCount = Math.ceil((viewportHeight - tableTop) / 50) + 10; // Add buffer
        
        // Clear tbody
        tbody.innerHTML = '';
        
        // Create placeholder for all rows to maintain scrollbar
        const placeholderHeight = (allRowData.length - visibleRowsCount) * 50;
        if (placeholderHeight > 0) {
          const placeholder = document.createElement('tr');
          placeholder.style.height = placeholderHeight + 'px';
          placeholder.className = 'virtual-scroll-placeholder';
          fragment.appendChild(placeholder);
        }
        
        // Render visible rows
        allRowData.slice(0, visibleRowsCount).forEach(rowData => {
          const newRow = document.createElement('tr');
          rowData.cells.forEach(cellHTML => {
            const newCell = document.createElement('td');
            newCell.innerHTML = cellHTML;
            newRow.appendChild(newCell);
          });
          fragment.appendChild(newRow);
        });
        
        // Attach the fragment
        tbody.appendChild(fragment);
        
        // Setup scroll handler for virtual rendering
        const scrollHandler = () => {
          requestAnimationFrame(() => {
            const scrollTop = window.scrollY;
            const tableRect = table.getBoundingClientRect();
            
            // Only continue if table is in view
            if (tableRect.bottom < 0 || tableRect.top > window.innerHeight) return;
            
            // Calculate which rows should be visible
            const rowHeight = 50; // Approximate row height
            const startIndex = Math.max(0, Math.floor((scrollTop - tableRect.top) / rowHeight));
            const endIndex = Math.min(allRowData.length, startIndex + visibleRowsCount);
            
            // Update only if different rows need to be shown
            if (tbody.childElementCount === 0 || 
                tbody.querySelector('tr:not(.virtual-scroll-placeholder)') === null ||
                startIndex !== parseInt(tbody.dataset.startIndex || '0')) {
              
              tbody.innerHTML = '';
              tbody.dataset.startIndex = startIndex.toString();
              
              const fragment = document.createDocumentFragment();
              
              // Add top placeholder
              if (startIndex > 0) {
                const topPlaceholder = document.createElement('tr');
                topPlaceholder.style.height = (startIndex * rowHeight) + 'px';
                topPlaceholder.className = 'virtual-scroll-placeholder top-placeholder';
                fragment.appendChild(topPlaceholder);
              }
              
              // Add visible rows
              allRowData.slice(startIndex, endIndex).forEach(rowData => {
                const newRow = document.createElement('tr');
                rowData.cells.forEach(cellHTML => {
                  const newCell = document.createElement('td');
                  newCell.innerHTML = cellHTML;
                  newRow.appendChild(newCell);
                });
                fragment.appendChild(newRow);
              });
              
              // Add bottom placeholder
              if (endIndex < allRowData.length) {
                const bottomPlaceholder = document.createElement('tr');
                bottomPlaceholder.style.height = ((allRowData.length - endIndex) * rowHeight) + 'px';
                bottomPlaceholder.className = 'virtual-scroll-placeholder bottom-placeholder';
                fragment.appendChild(bottomPlaceholder);
              }
              
              tbody.appendChild(fragment);
            }
          });
        };
        
        // Set up the scroll handler once per table
        if (!table.dataset.virtualScrollInitialized) {
          window.addEventListener('scroll', scrollHandler, { passive: true });
          table.dataset.virtualScrollInitialized = 'true';
          // Initial render
          scrollHandler();
        }
      }
    } finally {
      // Reset sorting flag to allow future sorts
      setTimeout(() => {
        table.dataset.sorting = 'false';
      }, 100); // Small delay to prevent too rapid sorting
    }
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
      
      // Add click event with proper binding - use debounce to prevent rapid clicking
      let clickTimeout;
      header.addEventListener('click', function() {
        if (clickTimeout) clearTimeout(clickTimeout);
        
        clickTimeout = setTimeout(() => {
          sortTable(table, index, this);
        }, 50); // Small debounce for rapid clicking
      });
    });
    
    // Mark table as initialized
    table.dataset.sortingInitialized = 'true';
  });
}

// Make functions available globally
window.sortTable = sortTable;
window.initTableSorting = initTableSorting;

// Initialize sorting when DOM is loaded - using passive listener for better performance
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