// Agent ordering customization
document.addEventListener('DOMContentLoaded', function() {
    // Custom order for agents to be displayed in the UI
    const desiredAgentOrder = [
        'Credit Officer – Pre-Sanction',        // pre_qualification
        'Customer Service Officer',             // application_assist
        'Officer – Loan Documentation',         // document_checker
        'Technical Officer – Property Valuation', // valuation
        'Assistant Manager – Credit Appraisal',  // credit_assessor
        'Manager – Credit Risk and Underwriting', // Underwriting
        'Deputy Manager – Customer Relationship', // customer_communication
        'Assistant Manager – Loan Processing',   // offer_generation
        'Manager – Compliance and Internal Control' // audit
    ];

    // Function to reorder agents within their categories without flattening
    function reorderAgentList() {
        const agentCategories = document.getElementById('agentCategories');
        if (!agentCategories) return;

        // Process each category separately
        const categoryDivs = agentCategories.querySelectorAll('.agent-category');
        
        categoryDivs.forEach(categoryDiv => {
            // Get all agents in this category
            const agentList = categoryDiv.querySelector('.agent-list');
            if (!agentList) return;
            
            const agentItems = Array.from(agentList.querySelectorAll('.agent-item'));
            
            // Skip if no agents found
            if (agentItems.length === 0) return;
            
            // Sort agents in this category based on desired order
            agentItems.sort((a, b) => {
                const nameA = a.querySelector('.agent-name').textContent;
                const nameB = b.querySelector('.agent-name').textContent;
                const indexA = desiredAgentOrder.indexOf(nameA);
                const indexB = desiredAgentOrder.indexOf(nameB);
                return indexA - indexB;
            });
            
            // Clear the agent list and append in new order
            agentList.innerHTML = '';
            agentItems.forEach(agentItem => {
                agentList.appendChild(agentItem);
                
                // Reattach click event
                const agentKey = agentItem.getAttribute('data-agent');
                agentItem.addEventListener('click', () => {
                    selectAgent(agentKey);
                });
            });
        });
    }

    // Periodically check if the agent list has been populated
    const agentListCheckInterval = setInterval(() => {
        const agentItems = document.querySelectorAll('.agent-item');
        if (agentItems.length > 0) {
            clearInterval(agentListCheckInterval);
            reorderAgentList();
        }
    }, 500);

    // Also try to reorder when an application is loaded
    const originalSwitchApplication = window.switchApplication;
    if (originalSwitchApplication) {
        window.switchApplication = function() {
            originalSwitchApplication.apply(this, arguments);
            
            // Wait a bit for the UI to update
            setTimeout(reorderAgentList, 500);
        };
    }

    // Handle case when agents are dynamically added
    // Create a mutation observer to detect changes to the DOM
    const observer = new MutationObserver(mutations => {
        mutations.forEach(mutation => {
            if (mutation.type === 'childList' && 
                document.querySelectorAll('.agent-item').length > 0) {
                reorderAgentList();
            }
        });
    });

    // Start observing the agent categories container for changes
    const agentCategoriesContainer = document.getElementById('agentCategories');
    if (agentCategoriesContainer) {
        observer.observe(agentCategoriesContainer, { childList: true, subtree: true });
    }
});
