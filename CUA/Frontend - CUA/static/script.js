class CustomerLookup {
    constructor() {
        this.currentStep = 1;
        this.sessionId = null;
        this.statusInterval = null;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Step 1: Customer ID
        document.getElementById('nextStep1').addEventListener('click', () => {
            this.validateAndNextStep1();
        });

        // Step 2: Credentials
        document.getElementById('backStep1').addEventListener('click', () => {
            this.goToStep(1);
        });

        document.getElementById('startLookup').addEventListener('click', () => {
            this.startLookupProcess();
        });

        // Step 3: Results actions
        document.getElementById('newLookup').addEventListener('click', () => {
            this.resetToStep1();
        });

        document.getElementById('retryLookup').addEventListener('click', () => {
            this.startLookupProcess();
        });

        // Enter key handlers
        document.getElementById('customerId').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.validateAndNextStep1();
        });

        document.getElementById('username').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') document.getElementById('password').focus();
        });

        document.getElementById('password').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.startLookupProcess();
        });
    }

    validateAndNextStep1() {
        const customerId = document.getElementById('customerId').value.trim();
        
        if (!customerId) {
            this.showError('Please enter a Customer ID');
            return;
        }

        if (customerId.length < 3) {
            this.showError('Customer ID must be at least 3 characters');
            return;
        }

        this.goToStep(2);
    }

    goToStep(step) {
        // Hide all steps
        document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
        
        // Show target step
        document.getElementById(`step${step}`).classList.add('active');
        this.currentStep = step;

        // Focus on first input of the step
        const stepElement = document.getElementById(`step${step}`);
        const firstInput = stepElement.querySelector('input');
        if (firstInput && step !== 3) {
            setTimeout(() => firstInput.focus(), 100);
        }
    }

    async startLookupProcess() {
        const customerId = document.getElementById('customerId').value.trim();
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value.trim();

        if (!customerId || !username || !password) {
            this.showError('All fields are required');
            return;
        }

        // Go to processing step
        this.goToStep(3);
        this.showLoadingSection();

        try {
            // Start the lookup process
            const response = await fetch('/api/start-lookup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    customer_id: customerId,
                    username: username,
                    password: password
                })
            });

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Failed to start lookup');
            }

            this.sessionId = data.session_id;
            this.startStatusPolling();

        } catch (error) {
            this.showError(error.message);
        }
    }

    startStatusPolling() {
        this.statusInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/status/${this.sessionId}`);
                const data = await response.json();

                if (!data.success) {
                    throw new Error(data.error || 'Status check failed');
                }

                if (data.status === 'completed') {
                    this.stopStatusPolling();
                    
                    if (data.result.error) {
                        this.showError(data.result.error);
                    } else {
                        this.showResults(data.result);
                    }
                } else {
                    // Update status message
                    this.updateStatusMessage(data.message || 'Processing...');
                }

            } catch (error) {
                this.stopStatusPolling();
                this.showError(error.message);
            }
        }, 2000); // Poll every 2 seconds
    }

    stopStatusPolling() {
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
            this.statusInterval = null;
        }
    }

    updateStatusMessage(message) {
        document.getElementById('statusMessage').textContent = message;
    }

    showLoadingSection() {
        document.getElementById('loadingSection').style.display = 'block';
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('errorSection').style.display = 'none';
    }

    showResults(result) {
        document.getElementById('loadingSection').style.display = 'none';
        document.getElementById('errorSection').style.display = 'none';
        
        // Populate results
        document.getElementById('resultCustomerId').textContent = result.customer_id;
        document.getElementById('resultCrmRef').textContent = result.crm_ref;
        
        document.getElementById('resultsSection').style.display = 'block';
        
        // Add success animation
        const resultCard = document.querySelector('.result-card');
        resultCard.style.animation = 'fadeIn 0.5s ease-in';
    }

    showError(message) {
        this.stopStatusPolling();
        
        document.getElementById('loadingSection').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'none';
        
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('errorSection').style.display = 'block';
    }

    resetToStep1() {
        this.stopStatusPolling();
        this.sessionId = null;
        
        // Clear all inputs
        document.getElementById('customerId').value = '';
        document.getElementById('username').value = '';
        document.getElementById('password').value = '';
        
        // Go back to step 1
        this.goToStep(1);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new CustomerLookup();
});

// Handle page unload to clean up polling
window.addEventListener('beforeunload', () => {
    if (window.customerLookup && window.customerLookup.statusInterval) {
        clearInterval(window.customerLookup.statusInterval);
    }
});
