// Main JavaScript for FYP Navigator

document.addEventListener('DOMContentLoaded', function() {
    // Enable tooltips everywhere
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // Enable popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    });
    
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Add required indicator to form labels
    document.querySelectorAll('form .form-label').forEach(function(label) {
        const input = document.getElementById(label.getAttribute('for'));
        if (input && input.hasAttribute('required')) {
            label.innerHTML += ' <span class="text-danger">*</span>';
        }
    });

    // Add nl2br functionality for display of text with line breaks
    document.querySelectorAll('[data-nl2br]').forEach(function(element) {
        element.innerHTML = element.innerHTML.replace(/\n/g, '<br>');
    });

    // Highlight current navigation link
    const currentPath = window.location.pathname;
    document.querySelectorAll('.navbar-nav .nav-link').forEach(function(link) {
        const href = link.getAttribute('href');
        if (href && currentPath.startsWith(href) && href !== '/') {
            link.classList.add('active');
        } else if (href === '/' && currentPath === '/') {
            link.classList.add('active');
        }
    });

    // Toggle password visibility
    document.querySelectorAll('.toggle-password').forEach(function(button) {
        button.addEventListener('click', function() {
            const passwordField = document.querySelector(button.getAttribute('data-target'));
            if (passwordField.type === 'password') {
                passwordField.type = 'text';
                button.innerHTML = '<i class="fas fa-eye-slash"></i>';
            } else {
                passwordField.type = 'password';
                button.innerHTML = '<i class="fas fa-eye"></i>';
            }
        });
    });
});

// Function to confirm dangerous actions
function confirmAction(message) {
    return confirm(message || 'Are you sure you want to proceed?');
}

// Add a Jinja2 template filter for nl2br (converting newlines to <br> tags)
if (typeof Jinja2 !== 'undefined') {
    Jinja2.addFilter('nl2br', function(str) {
        if (typeof str !== 'string') return '';
        return str.replace(/\n/g, '<br>');
    });
}
