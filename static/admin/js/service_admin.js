django.jQuery(function($) {
    function updateServiceFields() {
        var serviceType = $('#id_service_type').val();
        var serviceFields = {
            'cleaning': ['cleaning_option'],
            'maintenance': ['maintenance_option'],
            'gardening': ['gardening_option'],
            'automation': ['automation_option'],
            'security': ['security_option']
        };

        // Hide all service-specific fields first
        $('.field-cleaning_option, .field-maintenance_option, .field-gardening_option, .field-automation_option, .field-security_option').hide();

        // Show only the relevant field
        if (serviceType in serviceFields) {
            serviceFields[serviceType].forEach(function(field) {
                $('.field-' + field).show();
            });
        }
    }

    // Update fields when service type changes
    $('#id_service_type').on('change', updateServiceFields);

    // Initial update
    updateServiceFields();
}); 