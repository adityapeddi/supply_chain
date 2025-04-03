// Main JavaScript for Retail Inventory Optimization System

$(document).ready(function() {
    // Global alert function
    window.showAlert = function(message, type) {
        var alertHtml = '<div class="alert alert-' + type + ' alert-dismissible fade show" role="alert">' +
            message +
            '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' +
            '</div>';
        
        // Insert alert at the top of the page
        $('.container-fluid').prepend(alertHtml);
        
        // Auto-dismiss after 5 seconds
        setTimeout(function() {
            $('.alert').alert('close');
        }, 5000);
    };
    
    // Poll system status if system is running
    if (typeof systemRunning !== 'undefined' && systemRunning) {
        startStatusPolling();
    }
    
    // Function to poll system status
    function startStatusPolling() {
        var pollInterval = setInterval(function() {
            $.ajax({
                url: '/api/system/status',
                type: 'GET',
                success: function(response) {
                    if (!response.running) {
                        clearInterval(pollInterval);
                        $('#execute-btn').prop('disabled', false);
                        $('#execute-btn').html('<i class="fas fa-play me-1"></i> Execute System');
                        
                        if (response.error) {
                            showAlert('System execution completed with errors: ' + response.error, 'warning');
                        } else {
                            showAlert('System execution completed successfully!', 'success');
                            setTimeout(function() {
                                location.reload();
                            }, 1500);
                        }
                    }
                }
            });
        }, 2000);
    }
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    });
});
