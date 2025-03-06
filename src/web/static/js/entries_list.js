/**
 * Entries List JavaScript Functions
 * Contains all JavaScript functionality for the entries list page
 */

/**
 * Submits the form with the specified action
 * @param {string} action - The action to perform
 */
function submitForm(action) {
    // Check if we're in a modal (using actionsForm) or in the results table
    const isModal = document.querySelector('.modal.show') !== null;
    
    if (isModal) {
        // We're in a modal, use the actionsForm
        const actionInput = document.getElementById('action_input');
        const form = document.getElementById('actionsForm');
        
        if (actionInput && form) {
            // Transfer all checked checkboxes from the search results to the actions form
            const checkedBoxes = document.querySelectorAll('.entry-checkbox:checked');
            
            // First, remove any existing checkboxes from previous submissions
            const existingInputs = form.querySelectorAll('input[name^="Select&"]');
            existingInputs.forEach(input => input.remove());
            
            // Add the checked checkboxes to the form
            checkedBoxes.forEach(checkbox => {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = checkbox.id;
                input.value = 'on';
                form.appendChild(input);
            });
            
            // Set the action and submit
            actionInput.value = action;
            form.submit();
        } else {
            console.error('Form or action input element not found');
        }
    } else {
        // We're in the results table, use the form in the results container
        const resultsForm = document.querySelector('#resultsContainer form');
        const actionInput = document.getElementById('results_action_input');
        
        if (resultsForm && actionInput) {
            actionInput.value = action;
            resultsForm.submit();
        } else {
            console.error('Results form or action input element not found');
        }
    }
}

/**
 * Copies text to clipboard and shows a temporary tooltip
 * @param {HTMLElement} element - The element containing text to copy
 */
function copy_2_clipboard(element) {
    navigator.clipboard.writeText(element.textContent);
    
    // Show a temporary tooltip
    const tooltip = document.createElement('div');
    tooltip.textContent = 'Copied!';
    tooltip.style.position = 'fixed';
    tooltip.style.left = (event.clientX + 10) + 'px';
    tooltip.style.top = (event.clientY - 10) + 'px';
    tooltip.style.backgroundColor = 'rgba(0,0,0,0.7)';
    tooltip.style.color = 'white';
    tooltip.style.padding = '5px 10px';
    tooltip.style.borderRadius = '3px';
    tooltip.style.zIndex = '1000';
    document.body.appendChild(tooltip);
    
    setTimeout(() => {
        tooltip.remove();
    }, 1000);
}

/**
 * Ensures consistent table styling for search results
 * This function applies the same styling to dynamically generated tables
 * as the original entries_list.html table
 */
function applyTableStyling() {
    // Find all tables that might be dynamically added to the page
    const tables = document.querySelectorAll('table');
    
    tables.forEach(table => {
        // Add the necessary classes if they don't exist
        if (!table.classList.contains('table')) {
            table.classList.add('table');
        }
        if (!table.classList.contains('table-hover')) {
            table.classList.add('table-hover');
        }
        if (!table.classList.contains('table-bordered')) {
            table.classList.add('table-bordered');
        }
        if (!table.classList.contains('table-striped')) {
            table.classList.add('table-striped');
        }
        if (!table.classList.contains('table-sortable')) {
            table.classList.add('table-sortable');
        }
        
        // Ensure the header has the correct styling
        const thead = table.querySelector('thead');
        if (thead && !thead.classList.contains('table-dark')) {
            thead.classList.add('table-dark');
        }
        
        // Ensure cells have proper alignment and padding
        const cells = table.querySelectorAll('td');
        cells.forEach(cell => {
            if (!cell.classList.contains('align-middle')) {
                cell.classList.add('align-middle');
            }
            if (!cell.classList.contains('py-3')) {
                cell.classList.add('py-3');
            }
        });
    });
}

// Function to initialize table sorting
function initializeTableSorting() {
  const sortableTables = document.querySelectorAll('table.table-sortable');
  
  sortableTables.forEach(table => {
    const thead = table.querySelector('thead');
    if (!thead) return;
    
    const headers = thead.querySelectorAll('th');
    
    // Add click event listeners to all headers
    headers.forEach((header, index) => {
      // Skip the checkbox column (usually the first column)
      if (header.querySelector('input[type="checkbox"]')) return;
      
      // Add sort indicators and styling if not already added
      if (!header.classList.contains('sortable')) {
        header.classList.add('sortable');
        header.style.cursor = 'pointer';
        
        // Create sort indicator element
        const sortIndicator = document.createElement('span');
        sortIndicator.className = 'sort-indicator ms-1';
        sortIndicator.innerHTML = '⇕';
        header.appendChild(sortIndicator);
        
        // Add click event to header
        header.addEventListener('click', function() {
          sortTable(table, index, this);
        });
      }
    });
  });
}

// Function to sort table
function sortTable(table, columnIndex, headerElement) {
  const tbody = table.querySelector('tbody');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  const isAscending = headerElement.getAttribute('data-sort') !== 'asc';
  
  // Reset all headers
  table.querySelectorAll('th').forEach(th => {
    if (th.querySelector('.sort-indicator')) {
      th.querySelector('.sort-indicator').innerHTML = '⇕';
    }
    th.removeAttribute('data-sort');
  });
  
  // Set current header sort direction
  headerElement.setAttribute('data-sort', isAscending ? 'asc' : 'desc');
  headerElement.querySelector('.sort-indicator').innerHTML = isAscending ? '↑' : '↓';
  
  // Sort the rows
  rows.sort((rowA, rowB) => {
    const cellA = rowA.querySelectorAll('td')[columnIndex];
    const cellB = rowB.querySelectorAll('td')[columnIndex];
    
    if (!cellA || !cellB) return 0;
    
    let valueA = cellA.textContent.trim();
    let valueB = cellB.textContent.trim();
    
    // Check if the column contains dates
    if (isDateString(valueA) && isDateString(valueB)) {
      return compareDates(valueA, valueB, isAscending);
    }
    
    // Check if the column contains numbers
    if (!isNaN(valueA) && !isNaN(valueB)) {
      return compareNumbers(valueA, valueB, isAscending);
    }
    
    // Default to string comparison
    return compareStrings(valueA, valueB, isAscending);
  });
  
  // Reorder the rows in the table
  rows.forEach(row => tbody.appendChild(row));
}

// Helper function to check if a string is a date
function isDateString(str) {
  // Check common date formats (YYYY-MM-DD, MM/DD/YYYY, etc.)
  return /^\d{4}-\d{2}-\d{2}$/.test(str) || 
         /^\d{1,2}\/\d{1,2}\/\d{4}$/.test(str) ||
         /^\d{1,2}-\d{1,2}-\d{4}$/.test(str);
}

// Helper function to compare dates
function compareDates(dateA, dateB, isAscending) {
  const a = new Date(dateA);
  const b = new Date(dateB);
  return isAscending ? a - b : b - a;
}

// Helper function to compare numbers
function compareNumbers(a, b, isAscending) {
  return isAscending ? a - b : b - a;
}

// Helper function to compare strings
function compareStrings(a, b, isAscending) {
  return isAscending ? 
    a.localeCompare(b) : 
    b.localeCompare(a);
}

// Initialize event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add select all functionality
    const selectAllCheckbox = document.getElementById('selectAll');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.entry-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = selectAllCheckbox.checked;
            });
        });
    }
    
    // Apply consistent table styling
    applyTableStyling();
    
    // Initialize table sorting for any existing tables
    initializeTableSorting();
    
    // Add a mutation observer to apply styling to dynamically added tables
    const resultsContainer = document.getElementById('resultsContainer');
    if (resultsContainer) {
        const observer = new MutationObserver(function(mutations) {
            applyTableStyling();
        });
        
        observer.observe(resultsContainer, { 
            childList: true,
            subtree: true 
        });
    }
}); 

document.addEventListener('DOMContentLoaded', function() {
    // Date range toggle functionality
    const dateCheckbox = document.getElementById('date_bool');
    const dateStart = document.getElementById('date_start');
    const dateEnd = document.getElementById('date_end');
    
    if (dateCheckbox && dateStart && dateEnd) {
      function updateDateFields() {
        const isEnabled = dateCheckbox.checked;
        dateStart.disabled = !isEnabled;
        dateEnd.disabled = !isEnabled;
      }
      
      dateCheckbox.addEventListener('change', updateDateFields);
      // Initialize on page load
      updateDateFields();
    }
    
    // Manual toggle for advanced search section
    const advancedSearchToggle = document.getElementById('advancedSearchToggle');
    const advancedSearchCollapse = document.getElementById('advancedSearchCollapse');
    const collapseIcon = document.getElementById('collapseIcon');
    
    if (advancedSearchToggle && advancedSearchCollapse && collapseIcon) {
      advancedSearchToggle.addEventListener('click', function() {
        const isVisible = advancedSearchCollapse.style.display !== 'none';
        
        if (isVisible) {
          advancedSearchCollapse.style.display = 'none';
          collapseIcon.classList.remove('bi-chevron-up');
          collapseIcon.classList.add('bi-chevron-down');
        } else {
          advancedSearchCollapse.style.display = 'block';
          collapseIcon.classList.remove('bi-chevron-down');
          collapseIcon.classList.add('bi-chevron-up');
        }
      });
    }
    
    // Real-time search functionality
    let searchTimeout;
    const searchDelay = 300; // milliseconds
    let currentOffset = 0;
    
    // Function to perform real-time search
    function performRealTimeSearch() {
      const searchForm = document.getElementById('searchForm');
      if (!searchForm) {
        console.error('Search form not found');
        return;
      }
      
      const formData = new FormData(searchForm);
      
      // Add offset for pagination
      formData.append('offset', currentOffset);
      
      // Show loading indicator
      const resultsContainer = document.getElementById('resultsContainer');
      if (resultsContainer) {
        resultsContainer.innerHTML = `
          <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Searching...</p>
          </div>
        `;
      }
      
      // Show results card
      const resultsCard = document.getElementById('resultsCard');
      if (resultsCard) {
        resultsCard.style.display = 'block';
      }
      
      // Reset pagination
      currentOffset = 0;
      
      // Send AJAX request
      fetch('/realtime_search', {
        method: 'POST',
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        // Update results container
        updateResultsTable(data.entries);
        
        // Update pagination
        const loadMoreContainer = document.getElementById('loadMoreContainer');
        if (loadMoreContainer) {
          if (data.has_more) {
            loadMoreContainer.style.display = 'block';
          } else {
            loadMoreContainer.style.display = 'none';
          }
        }
      })
      .catch(error => {
        console.error('Error performing real-time search:', error);
        const resultsContainer = document.getElementById('resultsContainer');
        if (resultsContainer) {
          resultsContainer.innerHTML = `
            <div class="alert alert-danger m-3">
              <i class="bi bi-exclamation-triangle me-2"></i> Error performing search
            </div>
          `;
        }
      });
    }
    
    // Function to update results table
    function updateResultsTable(entries) {
      if (entries.length === 0) {
        const resultsContainer = document.getElementById('resultsContainer');
        if (resultsContainer) {
          resultsContainer.innerHTML = `
            <div class="alert alert-info text-center">
              No entries found matching your search criteria.
            </div>
          `;
        }
        return;
      }
      
      // Create table HTML - wrap in a form
      let tableHtml = `
        <form action="${document.getElementById('actionsForm').action}" method="post" enctype="multipart/form-data">
          <div class="table-responsive p-3">
            <table class="table table-hover table-bordered table-striped table-sortable">
              <thead class="table-dark">
                <tr>
                  <th scope="col" width="2.5%" class="text-center"><input type="checkbox" id="selectAll" class="form-check-input"></th>
                  <th scope="col" width="35%" class="text-center">Title</th>
                  <th scope="col" width="15%" class="text-center">Hash ID</th>
                  <th scope="col" width="15%" class="text-center">Date</th>
                  <th scope="col" width="5%" class="text-center">Author</th>
                  <th scope="col" width="13.75%" class="text-center">Tags</th>
                  <th scope="col" width="13.75%" class="text-center">Conditions</th>
                </tr>
              </thead>
              <tbody>
      `;
      
      // Add rows for each entry
      entries.forEach(entry => {
        tableHtml += `
          <tr>
            <td class="text-center align-middle py-3">
              <input class="form-check-input entry-checkbox" type="checkbox" id="Select&${entry.id}" name="Select&${entry.id}">
            </td>
            <td class="align-middle py-3">
              <a href="/entry/${entry.id}" class="text-decoration-none">
                <span class="fw-bold">${entry.title}</span>
              </a>
            </td>
            <td class="align-middle py-3">
              <div class="d-flex align-items-center">
                <span class="text-monospace font-monospace small" id="hash_id_${entry.hash_id}">${entry.hash_id}</span>
              </div>
            </td>
            <td class="align-middle py-3">${entry.date}</td>
            <td class="align-middle py-3">${entry.author}</td>
            <td class="align-middle py-3">
              ${Array.isArray(entry.tags) ? entry.tags.map(tag => `<span class="text-dark me-1">${tag}</span>`).join('') : ''}
            </td>
            <td class="align-middle py-3">
              ${Array.isArray(entry.conditions) ? entry.conditions.map(condition => `<span class="text-dark me-1">${condition}</span>`).join('') : ''}
            </td>
          </tr>`;
      });
      
      // Close table
      tableHtml += `
            </tbody>
          </table>
        </div>
      `;
      
      // Add the actions button section
      tableHtml += `
        <div class="input-group mb-3 row mx-1 p-4 bg-light rounded">
            <div class="col-md-3">
                <div class="dropdown">
                    <button class="btn btn-primary dropdown-toggle w-100" type="button" id="actionDropdown" 
                            data-bs-toggle="dropdown" aria-expanded="false">
                        <i class="bi bi-gear me-1"></i> Actions
                    </button>
                    <ul class="dropdown-menu" aria-labelledby="actionDropdown">
                        <li>
                            <button type="button" class="dropdown-item" data-bs-toggle="modal" data-bs-target="#emailNotifyModal">
                                <i class="bi bi-envelope me-2"></i> Notify by Email
                            </button>
                        </li>
                        <li>
                            <button type="button" class="dropdown-item" data-bs-toggle="modal" data-bs-target="#setParentModal">
                                <i class="bi bi-diagram-3 me-2"></i> Set Parent Entry
                            </button>
                        </li>
                        <li>
                            <button type="button" class="dropdown-item" onclick="submitForm('bulk_report')">
                                <i class="bi bi-file-earmark-text me-2"></i> Generate Reports
                            </button>
                        </li>
                    </ul>
                </div>
            </div>
            <div class="col-md-9">
                <div class="alert alert-info mb-0">
                    <i class="bi bi-info-circle me-2"></i> Select entries and choose an action from the dropdown
                </div>
            </div>
        </div>
        <input type="hidden" name="action" id="results_action_input" value="">
        </form>
      `;
      
      // Update results container
      const resultsContainer = document.getElementById('resultsContainer');
      if (resultsContainer) {
        resultsContainer.innerHTML = tableHtml;
      }
      
      // Add select all functionality
      const selectAllCheckbox = document.getElementById('selectAll');
      if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
          const checkboxes = document.querySelectorAll('.entry-checkbox');
          checkboxes.forEach(checkbox => {
            checkbox.checked = selectAllCheckbox.checked;
          });
        });
      }
      
      // Initialize table sorting for the newly created table
      initializeTableSorting();
    }
    
    // Add event listeners to search fields
    const realtimeSearchInputs = document.querySelectorAll('.realtime-search');
    if (realtimeSearchInputs.length > 0) {
      realtimeSearchInputs.forEach(input => {
        input.addEventListener('input', function() {
          clearTimeout(searchTimeout);
          searchTimeout = setTimeout(performRealTimeSearch, searchDelay);
        });
        
        if (input.type === 'checkbox') {
          input.addEventListener('change', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(performRealTimeSearch, searchDelay);
          });
        }
      });
    }
    
    // Handle form reset
    const resetFormBtn = document.getElementById('resetFormBtn');
    if (resetFormBtn) {
      resetFormBtn.addEventListener('click', function() {
        const resultsCard = document.getElementById('resultsCard');
        if (resultsCard) {
          setTimeout(function() {
            resultsCard.style.display = 'none';
          }, 100);
        }
      });
    }
    
    // Load more results functionality
    const loadMoreResults = document.getElementById('loadMoreResults');
    if (loadMoreResults) {
      loadMoreResults.addEventListener('click', function() {
        const button = this;
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';
        
        // Increment offset for pagination
        currentOffset += 10;
        
        // Get form data
        const searchForm = document.getElementById('searchForm');
        if (!searchForm) {
          console.error('Search form not found');
          button.disabled = false;
          return;
        }
        
        const formData = new FormData(searchForm);
        formData.append('offset', currentOffset);
        formData.append('limit', 10);
        
        // Send AJAX request
        fetch('/realtime_search', {
          method: 'POST',
          body: formData
        })
        .then(response => response.json())
        .then(data => {
          // Get table body
          const tbody = document.querySelector('.table tbody');
          
          // Add new rows
          data.entries.forEach(entry => {
            const row = document.createElement('tr');
            row.innerHTML = `
              <td class="text-center align-middle py-3">
                <input class="form-check-input entry-checkbox" type="checkbox" id="Select&${entry.id}" name="Select&${entry.id}">
              </td>
              <td class="align-middle py-3">
                <a href="/entry/${entry.id}" class="text-decoration-none">
                  <span class="fw-bold">${entry.title}</span>
                </a>
              </td>
              <td class="align-middle py-3">
                <div class="d-flex align-items-center">
                  <span class="text-monospace font-monospace small" id="hash_id_${entry.hash_id}">${entry.hash_id}</span>
                </div>
              </td>
              <td class="align-middle py-3">${entry.date}</td>
              <td class="align-middle py-3">${entry.author}</td>
              <td class="align-middle py-3">
                ${Array.isArray(entry.tags) ? entry.tags.map(tag => `<span class="text-dark me-1">${tag}</span>`).join('') : ''}
              </td>
              <td class="align-middle py-3">
                ${Array.isArray(entry.conditions) ? entry.conditions.map(condition => `<span class="text-dark me-1">${condition}</span>`).join('') : ''}
              </td>
            `;
            tbody.appendChild(row);
          });
          
          // Update button state
          button.disabled = false;
          button.innerHTML = '<i class="bi bi-arrow-down-circle me-1"></i> Show More Results';
          
          // Hide button if no more results
          if (!data.has_more) {
            const loadMoreContainer = document.getElementById('loadMoreContainer');
            if (loadMoreContainer) {
              loadMoreContainer.style.display = 'none';
            }
          }
          
          // Re-apply sorting if a column is already sorted
          const sortedHeader = document.querySelector('th[data-sort]');
          if (sortedHeader) {
            const table = document.querySelector('.table-sortable');
            const headerIndex = Array.from(sortedHeader.parentNode.children).indexOf(sortedHeader);
            sortTable(table, headerIndex, sortedHeader);
          }
        })
        .catch(error => {
          console.error('Error loading more results:', error);
          button.disabled = false;
          button.innerHTML = '<i class="bi bi-arrow-down-circle me-1"></i> Show More Results';
        });
      });
    }
  });