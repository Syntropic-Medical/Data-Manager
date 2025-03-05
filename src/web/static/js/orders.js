// Initialize variables
if (typeof window.currentlyShown === 'undefined') {
    window.currentlyShown = [];
}

// Define global functions that need to be accessible from HTML
window.showOrderDetails = function(orderId) {
    if (typeof $ === 'undefined') {
        console.error('jQuery not loaded yet');
        return;
    }
    
    // Show loading state
    $('#orderDetailsModal').modal('show');
    $('#orderDetailsContent').html('<div class="text-center"><div class="spinner-border" role="status"></div><p>Loading order details...</p></div>');
    
    // Fetch order details
    $.get('/get_order_details/' + orderId)
        .done(function(response) {
            $('#orderDetailsContent').html(response);
        })
        .fail(function() {
            $('#orderDetailsContent').html('<div class="alert alert-danger">Failed to load order details</div>');
        });
};

window.editOrder = function(orderId) {
    if (typeof $ === 'undefined') {
        console.error('jQuery not loaded yet');
        return;
    }
    
    // Show loading state
    $('#editOrderModal').modal('show');
    
    // Fetch order details
    $.get('/get_order_details/' + orderId)
        .done(function(response) {
            // Parse the HTML response to extract order data
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = response;
            
            // Extract data from the parsed HTML
            const orderName = $(tempDiv).find('.order-name').text().trim();
            const link = $(tempDiv).find('.order-link a').attr('href') || '';
            const quantity = $(tempDiv).find('.order-quantity').text().trim();
            const note = $(tempDiv).find('.order-note').text().trim();
            
            // Populate the edit form
            $('#edit_order_id').val(orderId);
            $('#edit_order_name').val(orderName);
            $('#edit_link').val(link);
            $('#edit_quantity').val(quantity);
            $('#edit_note').val(note);
        })
        .fail(function() {
            $('#editOrderModal').modal('hide');
            showAlert('Failed to load order details for editing', 'danger');
        });
};

window.deleteOrder = function(orderId) {
    if (typeof $ === 'undefined') {
        console.error('jQuery not loaded yet');
        return;
    }
    
    $('#deleteOrderModal').modal('show');
    $('#delete_order_id').val(orderId);
};

// Function to initialize everything once jQuery is available
function initializeOrdersJS() {
    if (typeof $ === 'undefined') {
        // If jQuery isn't loaded yet, try again in 100ms
        setTimeout(initializeOrdersJS, 100);
        return;
    }

    // Helper functions
    function showAlert(message, type = 'success') {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        $('.container').first().prepend(alertHtml);
        
        // Auto-dismiss after 5 seconds
        setTimeout(function() {
            $('.alert').alert('close');
        }, 5000);
    }
    
    function setupAuthorSuggestions() {
        const authorInput = $("#authorSearch");
        const suggestionsList = $("#author_suggestions");
        
        authorInput.on("input focus", function() {
            const query = $(this).val();
            const lastQuery = query.split(',').pop().trim();
            
            if (lastQuery.length < 1) {
                suggestionsList.hide();
                return;
            }
            
            // Make AJAX request to search for usernames
            $.ajax({
                url: "/username_search",
                method: "POST",
                data: { text: lastQuery },
                success: function(response) {
                    if (response.length > 0) {
                        // Build suggestions list
                        let html = '';
                        response.forEach(function(user) {
                            html += `<a class="dropdown-item" href="#" data-username="${user[0]}">${user[0]}</a>`;
                        });
                        
                        suggestionsList.html(html);
                        suggestionsList.show();
                        
                        // Handle clicking on a suggestion
                        $(".dropdown-item", suggestionsList).on("click", function(e) {
                            e.preventDefault();
                            const username = $(this).data("username");
                            
                            // Get current input value and replace the last part
                            let currentValue = authorInput.val();
                            const parts = currentValue.split(',');
                            parts.pop(); // Remove the last part (what user was typing)
                            
                            // Add the selected username
                            if (parts.length > 0) {
                                currentValue = parts.join(',') + ', ' + username;
                            } else {
                                currentValue = username;
                            }
                            
                            authorInput.val(currentValue + ', ');
                            suggestionsList.hide();
                            authorInput.focus();
                            
                            // Trigger change to apply filters
                            authorInput.trigger('change');
                        });
                    } else {
                        suggestionsList.hide();
                    }
                }
            });
        });
        
        // Hide suggestions when clicking outside
        $(document).on("click", function(e) {
            if (!$(e.target).closest("#authorSearch, #author_suggestions").length) {
                suggestionsList.hide();
            }
        });
    }
    
    function initializeStatusSelects() {
        $('.status-select').off('change').on('change', function() {
            const orderId = $(this).data('order-id');
            const newStatus = $(this).val();
            
            $.post('/update_order_status', {
                order_id: orderId,
                status: newStatus
            })
            .done(function(response) {
                if (response.success) {
                    // Remove any existing success alerts before showing a new one
                    $('.alert-success').remove();
                } else {
                    showAlert('Failed to update order status: ' + (response.error || 'Unknown error'), 'danger');
                }
            })
            .fail(function() {
                showAlert('Failed to update order status', 'danger');
            });
        });
    }
    
    function getSessionData() {
        // Use window.sessionData if available, otherwise fallback to window variables
        if (window.sessionData) {
            return window.sessionData;
        }
        return {
            username: '',
            admin: false,
            orderManager: false
        };
    }
    
    // Main initialization
    $(document).ready(function() {
        const ITEMS_PER_PAGE = 10;
        
        // Set currentlyShown to initial value
        window.currentlyShown = ITEMS_PER_PAGE;
        
        // Store original orders data if table exists
        const ordersTableBody = $('#ordersTableBody');
        if (ordersTableBody.length) {
            // Apply filters automatically when any filter changes
            $("#orderSearch, #authorSearch, #statusFilter, #dateStart, #dateEnd").on("change keyup", function() {
                // Add a small delay to prevent too many requests while typing
                clearTimeout(window.filterTimeout);
                window.filterTimeout = setTimeout(function() {
                    window.applyAllFilters();
                }, 500);
            });
            
            // Reset filters button
            $("#resetFiltersBtn").on("click", function() {
                $("#orderSearch").val("");
                $("#authorSearch").val("");
                $("#statusFilter").val("");
                $("#dateStart").val("");
                $("#dateEnd").val("");
                window.applyAllFilters();
            });
            
            // Username suggestions for author search
            setupAuthorSuggestions();
        }

        // Fix the Show More button functionality
        $('#showMoreBtn').off('click').on('click', function() {
            const offset = $('.order-item').length;
            const searchTerm = $('#orderSearch').val();
            const authorTerm = $('#authorSearch').val();
            const status = $('#statusFilter').val();
            const dateStart = $('#dateStart').val();
            const dateEnd = $('#dateEnd').val();
            
            // Show loading state
            $(this).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...');
            $(this).prop('disabled', true);
            
            // Make AJAX request to load more orders
            $.get('/load_more_orders', {
                offset: offset,
                search: searchTerm,
                author: authorTerm,
                status: status,
                date_start: dateStart,
                date_end: dateEnd
            })
            .done(function(response) {
                if (response.success && response.orders.length > 0) {
                    // Append new orders to the table
                    response.orders.forEach(function(order, index) {
                        const sessionData = getSessionData();
                        const statusHtml = (sessionData.admin || sessionData.username === order.order_assignee) ?
                            `<select class="form-control status-select" data-order-id="${order.id}">
                                <option value="pending" ${order.status.toLowerCase() === 'pending' ? 'selected' : ''}>Pending</option>
                                <option value="ordered" ${order.status.toLowerCase() === 'ordered' ? 'selected' : ''}>Ordered</option>
                                <option value="rejected" ${order.status.toLowerCase() === 'rejected' ? 'selected' : ''}>Rejected</option>
                            </select>` :
                            order.status;
                        
                        const actionsHtml = `
                            <button class="btn btn-sm btn-info" onclick="window.showOrderDetails(${order.id})">Details</button>
                            ${sessionData.username === order.order_author ? `
                                <button class="btn btn-sm btn-warning" onclick="window.editOrder(${order.id})">Edit</button>
                                <button class="btn btn-sm btn-danger" onclick="window.deleteOrder(${order.id})">Delete</button>
                            ` : ''}`;
                        
                        const newRow = `
                            <tr class="order-item" data-status="${order.status.toLowerCase()}">
                                <td class="row-number text-center align-middle py-3">${offset + index + 1}</td>
                                <td class="align-middle py-3">${order.order_name}</td>
                                <td class="text-center align-middle py-3">${order.quantity}</td>
                                <td class="align-middle py-3">${order.order_assignee}</td>
                                <td class="align-middle py-3">${order.order_author}</td>
                                <td class="align-middle py-3">${statusHtml}</td>
                                <td class="align-middle py-3">${order.date}</td>
                                <td class="text-center align-middle py-3">${actionsHtml}</td>
                            </tr>`;
                        
                        $('#ordersTableBody').append(newRow);
                    });
                    
                    // Update button state
                    $('#showMoreBtn').html('<i class="bi bi-arrow-down-circle me-1"></i> Show More');
                    $('#showMoreBtn').prop('disabled', false);
                    
                    // Show button only if there are more orders to load
                    if (response.orders.length < ITEMS_PER_PAGE) {
                        $('#showMoreBtn').hide();
                    }
                    
                    // Initialize status selects for new rows
                    initializeStatusSelects();
                } else {
                    // No more orders to load
                    $('#showMoreBtn').hide();
                }
            })
            .fail(function() {
                // Reset button state
                $('#showMoreBtn').html('<i class="bi bi-arrow-down-circle me-1"></i> Show More');
                $('#showMoreBtn').prop('disabled', false);
                showAlert('Failed to load more orders', 'danger');
            });
        });
        
        // Initialize status select handlers
        initializeStatusSelects();
        
        // Set up save changes button for edit modal
        $('#saveOrderChanges').off('click').on('click', function() {
            const formData = new FormData(document.getElementById('editOrderForm'));
            
            $.ajax({
                url: '/update_order',
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function(response) {
                    if (response.success) {
                        $('#editOrderModal').modal('hide');
                        showAlert('Order updated successfully');
                        // Reload the page to show updated order
                        setTimeout(function() {
                            window.location.reload();
                        }, 1000);
                    } else {
                        showAlert('Failed to update order: ' + (response.error || 'Unknown error'), 'danger');
                    }
                },
                error: function() {
                    showAlert('Failed to update order', 'danger');
                }
            });
        });
        
        // Set up confirm delete button
        $('#confirmDeleteOrder').off('click').on('click', function() {
            const orderId = $('#delete_order_id').val();
            
            $.ajax({
                url: '/delete_order',
                type: 'POST',
                data: { order_id: orderId },
                success: function(response) {
                    if (response.success) {
                        $('#deleteOrderModal').modal('hide');
                        showAlert('Order deleted successfully');
                        // Reload the page to update the orders list
                        setTimeout(function() {
                            window.location.reload();
                        }, 1000);
                    } else {
                        showAlert('Failed to delete order: ' + (response.error || 'Unknown error'), 'danger');
                    }
                },
                error: function() {
                    showAlert('Failed to delete order', 'danger');
                }
            });
        });
    });
    
    // Define the applyAllFilters function on the window object
    window.applyAllFilters = function() {
        const searchTerm = $("#orderSearch").val().toLowerCase();
        const authorTerm = $("#authorSearch").val().toLowerCase();
        const status = $("#statusFilter").val();
        const dateStart = $("#dateStart").val();
        const dateEnd = $("#dateEnd").val();
        
        // Show loading state
        $('#ordersTableBody').html('<tr><td colspan="8" class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></td></tr>');
        
        // Reset to first page when applying filters
        $.get('/orders', {
            search: searchTerm,
            author: authorTerm,
            status: status,
            date_start: dateStart,
            date_end: dateEnd,
            format: 'json'  // Add this to indicate we want JSON response
        })
        .done(function(response) {
            // Clear the table body
            $('#ordersTableBody').empty();
            
            if (response.orders && response.orders.length > 0) {
                // Add new rows
                response.orders.forEach(function(order, index) {
                    const sessionData = getSessionData();
                    const statusHtml = (sessionData.username === order.order_assignee) ?
                        `<select class="form-control status-select" data-order-id="${order.id}">
                            <option value="pending" ${order.status.toLowerCase() === 'pending' ? 'selected' : ''}>Pending</option>
                            <option value="ordered" ${order.status.toLowerCase() === 'ordered' ? 'selected' : ''}>Ordered</option>
                            <option value="rejected" ${order.status.toLowerCase() === 'rejected' ? 'selected' : ''}>Rejected</option>
                        </select>` :
                        order.status;
                    
                    const actionsHtml = `
                        <button class="btn btn-sm btn-info" onclick="window.showOrderDetails(${order.id})">Details</button>
                        ${sessionData.username === order.order_author ? `
                            <button class="btn btn-sm btn-warning" onclick="window.editOrder(${order.id})">Edit</button>
                            <button class="btn btn-sm btn-danger" onclick="window.deleteOrder(${order.id})">Delete</button>
                        ` : ''}`;
                    
                    const newRow = `
                        <tr class="order-item" data-status="${order.status.toLowerCase()}">
                            <td class="row-number text-center align-middle py-3">${index + 1}</td>
                            <td class="align-middle py-3">${order.order_name}</td>
                            <td class="text-center align-middle py-3">${order.quantity}</td>
                            <td class="align-middle py-3">${order.order_assignee}</td>
                            <td class="align-middle py-3">${order.order_author}</td>
                            <td class="align-middle py-3">${statusHtml}</td>
                            <td class="align-middle py-3">${order.date}</td>
                            <td class="text-center align-middle py-3">${actionsHtml}</td>
                        </tr>`;
                    
                    $('#ordersTableBody').append(newRow);
                });
                
                // Initialize status selects for new rows
                initializeStatusSelects();
                
                // Show/hide "Show More" button
                if (response.orders.length === 10) {
                    $('#showMoreBtn').show();
                } else {
                    $('#showMoreBtn').hide();
                }
            } else {
                // No orders found
                $('#ordersTableBody').html('<tr><td colspan="8" class="text-center">No orders found</td></tr>');
                $('#showMoreBtn').hide();
            }
        })
        .fail(function(jqXHR, textStatus, errorThrown) {
            console.error('Filter request failed:', textStatus, errorThrown);
            showAlert('Failed to apply filters: ' + (errorThrown || 'Unknown error'), 'danger');
            $('#ordersTableBody').html('<tr><td colspan="8" class="text-center">Error loading orders</td></tr>');
        });
    };
}

// Start initialization
initializeOrdersJS();