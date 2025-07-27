// Integration script for dashboard and applications page
document.addEventListener('DOMContentLoaded', function() {
    // This script runs on the dashboard page and helps with application loading
    
    // Check if BankingAgentSystem exists (we're on the dashboard page)
    if (typeof BankingAgentSystem !== 'undefined') {
        console.log('Dashboard integration: Enhancing URL parameter handling');
        
        // Add the getApplicationByCustomerId method to BankingAgentSystem prototype
        BankingAgentSystem.prototype.getApplicationByCustomerId = async function(customerId, applicationId) {
            if (!customerId) {
                this.showNotification('No customer ID provided', 'warning');
                return;
            }
            
            try {
                // Show loading state
                this.updateUIState('loading', `Loading application for Customer ${customerId}...`);
                
                // Search for application by customer ID and application ID if available
                let url = '';
                if (applicationId) {
                    url = `/api/applications/search?customer_id=${encodeURIComponent(customerId)}&application_id=${encodeURIComponent(applicationId)}&search_type=both`;
                } else {
                    url = `/api/applications/search?customer_id=${encodeURIComponent(customerId)}&search_type=customer_id`;
                }
                
                const response = await fetch(url);
                const data = await response.json();
                
                if (response.ok && data.success && data.application) {
                    this.showNotification(`Application found for Customer ${customerId}`, 'success');
                    
                    // Load the found application
                    this.currentApplication = data.application;
                    
                    // Update the application selector
                    this.updateApplicationSelector(data.application);
                    
                    // Populate the application data
                    this.loadApplicationData(data.application);
                    
                    // Update UI state to show application is loaded
                    this.updateUIState('application_loaded');
                    
                    return true;
                } else {
                    this.showNotification(data.error || `No application found for Customer ${customerId}`, 'error');
                    this.updateUIState('idle');
                    return false;
                }
                
            } catch (error) {
                console.error('Error searching application:', error);
                this.showNotification('Failed to search application. Please try again.', 'error');
                this.updateUIState('idle');
                return false;
            }
        };
        
        // Get URL parameters after defining the method
        const urlParams = new URLSearchParams(window.location.search);
        const applicationId = urlParams.get('application_id');
        const customerId = urlParams.get('customer_id');
        const autoload = urlParams.get('autoload');
        
        if (applicationId && customerId && autoload === 'true' && window.bankingSystem) {
            console.log(`Auto-loading application from applications page: ${applicationId}, Customer: ${customerId}`);
            
            // Show loading notification
            window.bankingSystem.showNotification(`Loading application for ${customerId}...`, 'info');
            
            // Load the application directly without needing any modal
            setTimeout(function() {
                // Try to load via the search API with both customer ID and application ID
                window.bankingSystem.getApplicationByCustomerId(customerId, applicationId)
                    .then(() => {
                        // Clean up the URL without reloading the page
                        window.history.replaceState({}, document.title, '/dashboard');
                    });
            }, 500);
        }
    }
});
