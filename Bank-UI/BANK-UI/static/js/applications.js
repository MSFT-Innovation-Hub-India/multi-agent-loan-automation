document.addEventListener('DOMContentLoaded', function() {
    // Fetch applications from the server or use dummy data
    try {
        fetchApplications();
    } catch (error) {
        console.error("Error fetching applications, using dummy data instead", error);
        useDummyApplications();
    }

    // Setup socket connection if needed
    setupSocketConnection();
});

function fetchApplications() {
    // First try to fetch real applications from the server
    fetch('/api/applications')
        .then(response => response.json())
        .then(data => {
            if (data.applications && data.applications.length > 0) {
                displayApplications(data.applications);
            } else {
                // If no real applications, use dummy ones
                useDummyApplications();
            }
        })
        .catch(error => {
            console.error('Error fetching applications:', error);
            useDummyApplications();
        });
}

function useDummyApplications() {
    // Create dummy applications for demonstration with data structure matching main dashboard expectations
    const dummyApplications = [
        {
            id: 'APP10001',
            customer_id: 'CUST0001',
            created_at: new Date(2025, 6, 7, 9, 15).toISOString(),
            overall_progress: 25,
            loan_amount: 150000,
            loan_purpose: 'Home Purchase',
            status: 'In Progress',
            messages: [],
            current_agent: 'document_checker',
            agent_progress: {
                'application_assist': 100,
                'document_checker': 30,
                'pre_qualification': 0,
                'Underwriting': 0,
                'credit_assessor': 0,
                'valuation': 0,
                'audit': 0,
                'customer_communication': 0,
                'offer_generation': 0
            }
        },
        {
            id: 'APP10002',
            customer_id: 'CUST0002',
            created_at: new Date(2025, 6, 7, 10, 30).toISOString(),
            overall_progress: 15,
            loan_amount: 75000,
            loan_purpose: 'Vehicle Purchase',
            status: 'In Progress',
            messages: [],
            current_agent: 'application_assist',
            agent_progress: {
                'application_assist': 60,
                'document_checker': 0,
                'pre_qualification': 0,
                'Underwriting': 0,
                'credit_assessor': 0,
                'valuation': 0,
                'audit': 0,
                'customer_communication': 0,
                'offer_generation': 0
            }
        },
        {
            id: 'APP10003',
            customer_id: 'CUST0003',
            created_at: new Date(2025, 6, 8, 11, 45).toISOString(),
            overall_progress: 90,
            loan_amount: 200000,
            loan_purpose: 'Business Expansion',
            status: 'Approved',
            messages: [],
            current_agent: 'offer_generation',
            agent_progress: {
                'application_assist': 100,
                'document_checker': 100,
                'pre_qualification': 100,
                'Underwriting': 100,
                'credit_assessor': 100,
                'valuation': 100,
                'audit': 100,
                'customer_communication': 100,
                'offer_generation': 80
            }
        },
        {
            id: 'APP10004',
            customer_id: 'CUST0004',
            created_at: new Date(2025, 6, 8, 14, 20).toISOString(),
            overall_progress: 100,
            loan_amount: 50000,
            loan_purpose: 'Education Loan',
            status: 'Completed',
            messages: [],
            current_agent: null,
            agent_progress: {
                'application_assist': 100,
                'document_checker': 100,
                'pre_qualification': 100,
                'Underwriting': 100,
                'credit_assessor': 100,
                'valuation': 100,
                'audit': 100,
                'customer_communication': 100,
                'offer_generation': 100
            }
        },
        {
            id: 'APP10005',
            customer_id: 'CUST0005',
            created_at: new Date(2025, 6, 9, 9, 0).toISOString(),
            overall_progress: 65,
            loan_amount: 120000,
            loan_purpose: 'Home Renovation',
            status: 'In Progress',
            messages: [],
            current_agent: 'credit_assessor',
            agent_progress: {
                'application_assist': 100,
                'document_checker': 100,
                'pre_qualification': 100,
                'Underwriting': 100,
                'credit_assessor': 50,
                'valuation': 0,
                'audit': 0,
                'customer_communication': 0,
                'offer_generation': 0
            }
        },
        {
            id: 'APP10006',
            customer_id: 'CUST0006',
            created_at: new Date(2025, 6, 9, 16, 15).toISOString(),
            overall_progress: 40,
            loan_amount: 80000,
            loan_purpose: 'Debt Consolidation',
            status: 'In Progress',
            messages: [],
            current_agent: 'pre_qualification',
            agent_progress: {
                'application_assist': 100,
                'document_checker': 100,
                'pre_qualification': 30,
                'Underwriting': 0,
                'credit_assessor': 0,
                'valuation': 0,
                'audit': 0,
                'customer_communication': 0,
                'offer_generation': 0
            }
        }
    ];
    
    displayApplications(dummyApplications);
}

function displayApplications(applications) {
    const pendingContainer = document.getElementById('pending-applications');
    const reviewedContainer = document.getElementById('reviewed-applications');
    
    // Clear loading messages
    pendingContainer.innerHTML = '';
    reviewedContainer.innerHTML = '';
    
    // Counters for each category
    let pendingCount = 0;
    let reviewedCount = 0;
    
    // Check if we have applications
    if (!applications || applications.length === 0) {
        pendingContainer.innerHTML = '<div class="empty-message">No pending applications found</div>';
        reviewedContainer.innerHTML = '<div class="empty-message">No reviewed applications found</div>';
        return;
    }
    
    // Process applications
    applications.forEach(app => {
        // Determine if application is reviewed or pending
        // For demo purposes, we're using overall_progress > 75 as the criterion for "reviewed"
        const isReviewed = app.overall_progress > 75;
        const targetContainer = isReviewed ? reviewedContainer : pendingContainer;
        const statusClass = isReviewed ? 'reviewed' : 'pending';
        const statusText = isReviewed ? 'Reviewed' : 'Pending Review';
        const statusIcon = isReviewed ? 'check-circle' : 'clock';
        
        // Create application card
        const appCard = document.createElement('div');
        appCard.className = `application-card ${statusClass}`;
        appCard.dataset.appId = app.id;
        appCard.dataset.customerId = app.customer_id;
        
        // Format date in Indian format (DD/MM/YYYY)
        const createdDate = new Date(app.created_at);
        const day = String(createdDate.getDate()).padStart(2, '0');
        const month = String(createdDate.getMonth() + 1).padStart(2, '0');
        const year = createdDate.getFullYear();
        const hours = createdDate.getHours();
        const minutes = String(createdDate.getMinutes()).padStart(2, '0');
        const ampm = hours >= 12 ? 'pm' : 'am';
        const formattedHours = hours % 12 || 12; // Convert to 12-hour format
        const formattedDate = `${day}/${month}/${year} ${formattedHours}:${minutes} ${ampm}`;
        
        // Format loan amount with Indian currency (INR)
        const formattedAmount = new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(app.loan_amount);
        
        appCard.innerHTML = `
            <h3><i class="fas fa-user-circle"></i> <span class="customer-id">${app.customer_id}</span></h3>
            <div><strong>Application:</strong> <span class="app-id">${app.id}</span></div>
            <div><strong>Purpose:</strong> ${app.loan_purpose || 'Not specified'}</div>
            <div><strong>Amount:</strong> ${formattedAmount || 'Not specified'}</div>
            <div class="app-date"><i class="far fa-calendar-alt"></i> ${formattedDate}</div>
            <div class="app-status ${statusClass}"><i class="fas fa-${statusIcon}"></i> ${statusText}</div>
        `;
        
        // Add click event to load this application in the main page
        appCard.addEventListener('click', function() {
            loadApplication(app.id, app.customer_id);
        });
        
        // Append to appropriate container
        targetContainer.appendChild(appCard);
        
        // Increment counters
        if (isReviewed) {
            reviewedCount++;
        } else {
            pendingCount++;
        }
    });
    
    // If no applications in a category, show empty message
    if (pendingCount === 0) {
        pendingContainer.innerHTML = '<div class="empty-message">No pending applications found</div>';
    }
    
    if (reviewedCount === 0) {
        reviewedContainer.innerHTML = '<div class="empty-message">No reviewed applications found</div>';
    }
}

function loadApplication(applicationId, customerId) {
    console.log(`Loading application: ${applicationId}, Customer ID: ${customerId}`);
    
    // Show loading animation on the card
    const appCard = document.querySelector(`.application-card[data-app-id="${applicationId}"]`);
    if (appCard) {
        appCard.classList.add('loading-app');
        appCard.innerHTML += '<div class="loading-overlay"><i class="fas fa-spinner fa-spin"></i> Loading...</div>';
    }
    
    // First preload data for all agents by fetching CosmosDB data
    // This will ensure data is ready for all agents when redirected
    fetch(`/api/applications/search?application_id=${applicationId}&customer_id=${customerId}&search_type=both`)
        .then(response => response.json())
        .then(data => {
            console.log('Application data pre-loaded for all agents:', data.agent_details ? Object.keys(data.agent_details).length : 0);
            
            // Redirect to the dashboard page with the application ID and customer ID
            window.location.href = `/dashboard?application_id=${applicationId}&customer_id=${customerId}&autoload=true`;
        })
        .catch(error => {
            console.error('Error pre-loading application data:', error);
            // Still redirect even if there's an error
            window.location.href = `/dashboard?application_id=${applicationId}&customer_id=${customerId}&autoload=true`;
        });
}

function setupSocketConnection() {
    // Connect to Socket.IO server if needed
    const socket = io();
    
    socket.on('connect', function() {
        console.log('Connected to server');
    });
    
    // Listen for application updates if needed
    socket.on('application_updated', function(appData) {
        // You could refresh the applications list or update a specific card
        fetchApplications();
    });
}

function displayErrorMessage() {
    const pendingContainer = document.getElementById('pending-applications');
    const reviewedContainer = document.getElementById('reviewed-applications');
    
    const errorMessage = '<div class="error-message">Failed to load applications. Please try again later.</div>';
    pendingContainer.innerHTML = errorMessage;
    reviewedContainer.innerHTML = errorMessage;
}
