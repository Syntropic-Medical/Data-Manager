/**
 * Table sorting functionality for Data Manager
 * This file contains JavaScript code for sorting tables in the application
 */

document.addEventListener('DOMContentLoaded', function() {
  // Find all sortable tables in the document
  const sortableTables = document.querySelectorAll('table.table-sortable');
  
  sortableTables.forEach(table => {
    const thead = table.querySelector('thead');
    if (!thead) return;
    
    const headers = thead.querySelectorAll('th');
    
    // Add click event listeners to all headers
    headers.forEach((header, index) => {
      // Skip the checkbox column (usually the first column)
      if (header.querySelector('input[type="checkbox"]')) return;
      
      // Add sort indicators and styling
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
    });
  });
  
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
      // Skip checkbox column if it's the first column
      const adjustedIndex = columnIndex;
      
      const cellA = rowA.querySelectorAll('td')[adjustedIndex];
      const cellB = rowB.querySelectorAll('td')[adjustedIndex];
      
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
}); 