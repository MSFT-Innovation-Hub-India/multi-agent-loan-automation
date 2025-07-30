// Multi-Agent Banking System JavaScript
class BankingAgentSystem {
    constructor() {
        this.socket = null;
        this.currentApplication = null;
        this.currentAgent = null;
        this.applications = [];
        this.agentCategories = {};
        this.agents = {};
        this.sessionId = null;
        this.isConnected = false;
        
        this.init();
    }

    init() {
        this.initializeEventListeners();
        this.loadApplications();
        this.updateConnectionStatus('Connected', 'success');
        
        // Check for application ID and customer ID in URL parameters
        this.checkUrlParameters();
    }
    
    checkUrlParameters() {
        const urlParams = new URLSearchParams(window.location.search);
        const applicationId = urlParams.get('application_id');
        const customerId = urlParams.get('customer_id');
        
        if (applicationId && customerId) {
            console.log(`Loading application from URL parameters: ${applicationId}, Customer: ${customerId}`);
            this.loadApplicationFromUrl(applicationId, customerId);
        }
    }
    
    async loadApplicationFromUrl(applicationId, customerId) {
        try {
            // Show loading state
            this.updateUIState('loading', 'Loading application...');
            
            // Search for application by ID and customer ID
            const response = await fetch(`/api/applications/search?application_id=${applicationId}&customer_id=${customerId}&search_type=both`);
            const data = await response.json();
            
            if (data.success && data.application) {
                console.log('Application loaded successfully from URL parameters:', data.application.id);
                this.loadApplicationData(data.application);
                
                // Clean up the URL without reloading the page
                window.history.replaceState({}, document.title, '/');
            } else {
                this.showNotification('Application not found', 'error');
                this.updateUIState('idle');
            }
        } catch (error) {
            console.error('Error loading application from URL:', error);
            this.showNotification('Failed to load application', 'error');
            this.updateUIState('idle');
        }
    }
    
    // Removed socket initialization for now - using HTTP requests instead
    initializeEventListeners() {
        // Chat form submission
        document.getElementById('chatForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });
        
        // Modal events - close when clicking outside
        window.onclick = (event) => {
            // Modal handling code for future modals
        };
        
        // Escape key to close modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                // Close any open modal
                const openModals = document.querySelectorAll('.modal-overlay.show');
                openModals.forEach(modal => {
                    this.closeModal(modal.id);
                });
            }
        });
    }
    
    updateConnectionStatus(status, type = 'info') {
        // Update connection status indicator if it exists
        const statusIndicator = document.getElementById('connectionStatus');
        if (statusIndicator) {
            statusIndicator.textContent = status;
            statusIndicator.className = `connection-status ${type}`;
        }
        console.log(`Connection Status: ${status}`);
    }

    async loadApplications() {
        try {
            const response = await fetch('/api/applications');
            const data = await response.json();
            
            this.applications = data.applications || [];
            this.agentCategories = data.agent_categories || {};
            this.agents = data.agents || {};
            
            this.populateApplicationSelect();
            this.populateAgentCategories();
            
        } catch (error) {
            console.error('Error loading applications:', error);
            this.showNotification('Failed to load applications', 'error');
        }
    }
    
    populateApplicationSelect() {
        const select = document.getElementById('applicationSelect');
        if (!select) return;
        
        // Clear existing options except the first one
        while (select.children.length > 1) {
            select.removeChild(select.lastChild);
        }
        
        // Add applications
        this.applications.forEach(app => {
            const option = document.createElement('option');
            option.value = app.id;
            option.textContent = `${app.customer_id} - ${app.id}`;
            select.appendChild(option);
        });
    }
    populateAgentCategories() {
        const container = document.getElementById('agentCategories');
        if (!container) return;
        
        container.innerHTML = '';
        
        Object.entries(this.agentCategories).forEach(([categoryKey, category]) => {
            const categoryDiv = document.createElement('div');
            categoryDiv.className = 'agent-category expanded';
            categoryDiv.innerHTML = `
                <div class="category-header" style="background: ${category.color}20; border-left: 4px solid ${category.color}"
                     onclick="toggleAgentCategory('${categoryKey}')">
                    <div class="category-info">
                        <span class="category-name">${category.name}</span>
                        <small class="category-description">${category.description}</small>
                    </div>
                    <i class="fas fa-chevron-up"></i>
                </div>
                <div class="agent-list" id="agents-${categoryKey}">
                    ${Object.entries(category.agents).map(([agentKey, agent]) => `
                        <div class="agent-item" onclick="selectAgent('${agentKey}')" data-agent="${agentKey}">
                            <div class="agent-icon" style="background: ${agent.color}20; color: ${agent.color}">
                                ${agent.icon}
                            </div>
                            <div class="agent-details">
                                <div class="agent-name">${agent.name}</div>
                                <div class="agent-description">${agent.description}</div>
                                <div class="agent-capabilities">
                                    ${agent.capabilities?.slice(0, 2).map(cap => `<span class="capability-tag">${cap}</span>`).join('') || ''}
                                </div>
                            </div>
                            <div class="agent-status-indicator ${agent.status}">
                                <i class="fas fa-circle"></i>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
            container.appendChild(categoryDiv);
        });
    }
    
    populateWorkflowCategories(application) {
        const container = document.getElementById('workflowCategories');
        if (!container || !application) return;
        
        container.innerHTML = '';
        
        // Group steps by category
        const categorizedSteps = {};
        application.steps.forEach((step, index) => {
            if (!categorizedSteps[step.category]) {
                categorizedSteps[step.category] = [];
            }
            categorizedSteps[step.category].push({...step, index});
        });
        
        // Create category sections
        Object.entries(categorizedSteps).forEach(([categoryKey, steps]) => {
            const category = this.agentCategories[categoryKey];
            if (!category) return;
            
            const categoryDiv = document.createElement('div');
            categoryDiv.className = 'category-section expanded';
            categoryDiv.innerHTML = `
                <div class="category-header ${categoryKey.toLowerCase().replace('_', '-')}" 
                     onclick="toggleCategory('${categoryKey}')">
                    <span>${category.name}</span>
                    <i class="fas fa-chevron-up"></i>
                </div>
                <div class="category-steps">
                    ${steps.map(step => this.createStepHTML(step)).join('')}
                </div>
            `;
            container.appendChild(categoryDiv);
        });
        
        // Update overall progress
        this.updateOverallProgress(application);
    }
    
    createStepHTML(step) {
        const progressPercent = step.progress || 0;
        const agentBadges = step.assigned_agents.map(agent => 
            `<span class="agent-badge">${agent}</span>`
        ).join('');
        
        return `
            <div class="workflow-step ${step.status}" data-step="${step.index}">
                <div class="step-header">
                    <div class="step-name">${step.name}</div>
                    <div class="step-status ${step.status}">${step.status}</div>
                </div>
                <div class="step-description">${step.description}</div>
                ${step.assigned_agents.length > 0 ? `
                    <div class="step-agents">${agentBadges}</div>
                ` : ''}
                <div class="step-progress">
                    <div class="step-progress-bar">
                        <div class="step-progress-fill" style="width: ${progressPercent}%"></div>
                    </div>
                </div>
                ${step.notes.length > 0 ? `
                    <div class="step-notes">
                        ${step.notes.slice(-1).map(note => `
                            <div class="step-note">
                                <small>${note.agent}: ${note.note}</small>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    updateOverallProgress(application) {
        const progressFill = document.getElementById('overallProgress');
        const progressText = document.getElementById('progressText');
        const appInfo = document.getElementById('applicationInfo');
        
        if (progressFill && progressText && appInfo) {
            const progress = application.overall_progress || 0;
            progressFill.style.width = `${progress}%`;
            progressText.textContent = `${Math.round(progress)}% Complete`;
            appInfo.style.display = 'block';
        }
    }
    switchApplication() {
        const select = document.getElementById('applicationSelect');
        const applicationId = select.value;
        
        if (!applicationId) {
            this.currentApplication = null;
            this.showWelcomeCard();
            this.updateWorkflowProgress(0);
            document.getElementById('applicationStatus').innerHTML = `
                <div class="no-app-selected">
                    <i class="fas fa-inbox"></i>
                    <p>No application selected</p>
                    <button class="select-app-btn" onclick="createNewApplication()">Create New Application</button>
                </div>
            `;
            return;
        }
        
        this.currentApplication = this.applications.find(app => app.id === applicationId);
        
        if (this.currentApplication) {
            // Set workflow progress to 96%
            this.updateWorkflowProgress(96);
            this.populateWorkflowCategories(this.currentApplication);
            this.populateChatMessages(this.currentApplication.messages || []);
            this.updateApplicationStatus();
        }
    }

    updateWorkflowProgress(percentage) {
        // Update the circular progress indicator
        const progressCircle = document.getElementById('progressCircle');
        const progressPercentage = document.getElementById('progressPercentage');
        
        if (progressCircle && progressPercentage) {
            const circumference = 2 * Math.PI * 18; // radius is 18
            const offset = circumference - (percentage / 100) * circumference;
            
            progressCircle.style.strokeDasharray = circumference;
            progressCircle.style.strokeDashoffset = offset;
            progressPercentage.textContent = `${Math.round(percentage)}%`;
        }
        
        // Update any other progress indicators
        const progressFill = document.getElementById('overallProgress');
        const progressText = document.getElementById('progressText');
        
        if (progressFill) {
            progressFill.style.width = `${percentage}%`;
        }
        
        if (progressText) {
            progressText.textContent = `${Math.round(percentage)}% Complete`;
        }
    }

    updateApplicationStatus(application) {
        const statusContainer = document.getElementById('applicationStatus');
        // Use provided application or fall back to currentApplication
        const app = application || this.currentApplication;
        
        if (statusContainer && app) {
            statusContainer.innerHTML = `
                <div class="app-status-card">
                    <div class="status-header">
                        <h4>${app.customer_id}</h4>
                        <span class="status-badge ${app.status}">${app.status}</span>
                    </div>
                    <div class="status-details">
                        <div class="detail-item">
                            <span class="label">Application ID:</span>
                            <span class="value">${app.id}</span>
                        </div>
                        <div class="detail-item">
                            <span class="label">Created:</span>
                            <span class="value">${new Date(app.created_at).toLocaleDateString()}</span>
                        </div>
                        <div class="detail-item">
                            <span class="label">Priority:</span>
                            <span class="value priority-${app.priority || 'normal'}">${app.priority || 'normal'}</span>
                        </div>
                    </div>
                </div>
            `;
        }
    }
    
    populateChatMessages(messages) {
        const container = document.getElementById('chatMessages');
        const welcomeMessage = container.querySelector('.welcome-message');
        
        // Clear previous messages but keep welcome message
        container.innerHTML = '';
        if (welcomeMessage) {
            container.appendChild(welcomeMessage);
        }
        
        messages.forEach(message => {
            this.addMessageToChat(message, false);
        });
        
        this.scrollToBottom();
    }
    
    selectAgent(agentKey) {
        // Remove previous selection
        document.querySelectorAll('.agent-item').forEach(item => {
            item.classList.remove('selected');
        });
        
        // Add selection to clicked agent
        const agentElement = document.querySelector(`[data-agent="${agentKey}"]`);
        if (agentElement) {
            agentElement.classList.add('selected');
        }
        
        this.currentAgent = agentKey;
        const agent = this.agents[agentKey];
        
        if (agent) {
            // Hide welcome card when agent is selected
            this.hideWelcomeCard();
            
            // Update active agent display
            const activeAgent = document.getElementById('activeAgent');
            if (activeAgent) {
                activeAgent.innerHTML = `
                    <div class="agent-avatar" style="background: ${agent.color}20; color: ${agent.color}">
                        ${agent.icon}
                    </div>
                    <div class="agent-info">
                        <h4>${agent.name}</h4>
                        <span>${agent.description}</span>
                        <div class="agent-capabilities">
                            ${agent.capabilities?.slice(0, 3).map(cap => `<span class="capability-tag">${cap}</span>`).join('') || ''}
                        </div>
                    </div>
                    <div class="agent-status-badge ${agent.status}">
                        <i class="fas fa-circle"></i>
                        ${agent.status}
                    </div>
                `;
            }
            
            // Show welcome message for the agent
            this.addAgentWelcomeMessage(agent);
            
            // Show quick suggestions for the agent
            this.showQuickSuggestions(agentKey);
            
            this.showNotification(`Connected to ${agent.name}`, 'success');
        }
    }

    hideWelcomeCard() {
        const welcomeCard = document.getElementById('welcomeCard');
        if (welcomeCard) {
            welcomeCard.style.display = 'none';
        }
    }

    showWelcomeCard() {
        const welcomeCard = document.getElementById('welcomeCard');
        if (welcomeCard) {
            welcomeCard.style.display = 'block';
        }
    }

    addAgentWelcomeMessage(agent) {
        const container = document.getElementById('chatMessages');
        
        // Remove any existing welcome messages from agents
        const existingWelcome = container.querySelector('.agent-welcome-message');
        if (existingWelcome) {
            existingWelcome.remove();
        }
        
        const welcomeDiv = document.createElement('div');
        welcomeDiv.className = 'message agent agent-welcome-message';
        welcomeDiv.innerHTML = `
            <div class="agent-avatar" style="background: ${agent.color}20; color: ${agent.color}">
                ${agent.icon}
            </div>
            <div class="message-content">
                <div class="message-header">
                    <span class="agent-name">${agent.name}</span>
                    <span class="message-time">${new Date().toLocaleTimeString()}</span>
                </div>
                <div class="agent-welcome">
                    <h4>Hello! I'm your ${agent.name}</h4>
                    <p>${agent.description}</p>
                    <div class="agent-capabilities-welcome">
                        <strong>I can help you with:</strong>
                        <ul>
                            ${agent.capabilities?.map(cap => `<li>${cap}</li>`).join('') || '<li>General assistance</li>'}
                        </ul>
                    </div>
                    <p><em>Type a message below to start our conversation!</em></p>
                </div>
            </div>
        `;
        
        container.appendChild(welcomeDiv);
        this.scrollToBottom();
    }
    
    switchAgent() {
        const selector = document.getElementById('agentSelector');
        this.currentAgent = selector.value;
        
        if (this.currentAgent) {
            const agent = this.agents[this.currentAgent];
            if (agent) {
                const currentAgent = document.getElementById('currentAgent');
                currentAgent.innerHTML = `
                    <span class="agent-icon">${agent.icon}</span>
                    <span class="agent-name">${agent.name}</span>
                `;
            }
        }
    }
    async sendMessage() {
        const input = document.getElementById('messageInput');
        const message = input.value.trim();
        
        if (!message) return;
        
        if (!this.currentAgent) {
            this.showNotification('Please select an agent first', 'warning');
            return;
        }
        
        // Remove agent welcome message when user starts chatting
        const welcomeMessage = document.querySelector('.agent-welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        // Add user message to chat
        const userMessage = {
            id: 'user-' + Date.now(),
            type: 'user',
            content: message,
            timestamp: new Date().toISOString(),
            agent: this.currentAgent,
            agent_name: this.agents[this.currentAgent]?.name || 'Unknown Agent'
        };
        
        this.addMessageToChat(userMessage, true);
        
        // Clear input and show loading
        input.value = '';
        this.showTypingIndicator();
        
        try {
            if (!this.currentApplication) {
                this.showNotification('No application data loaded', 'warning');
                this.removeTypingIndicator();
                return;
            }

            // Send message to server via HTTP
            const response = await fetch('/api/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    application_id: this.currentApplication.id,
                    message: message,
                    agent_type: this.currentAgent
                })
            });
            
            const data = await response.json();
            
            this.removeTypingIndicator();
            
            if (response.ok) {
                // Add agent response to chat
                const agentMessage = {
                    id: 'agent-' + Date.now(),
                    type: 'agent',
                    content: data.response,
                    timestamp: new Date().toISOString(),
                    agent: data.agent,
                    agent_name: data.agent_name
                };
                
                this.addMessageToChat(agentMessage, true);
                
                // Update application if provided
                if (data.application) {
                    this.handleApplicationUpdate(data.application);
                }
            } else {
                this.showNotification('Error: ' + (data.error || 'Failed to send message'), 'error');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.removeTypingIndicator();
            this.showNotification('Failed to send message', 'error');
        }
    }
    
    addMessageToChat(message, animate = true) {
        const container = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.type}`;
        if (animate) messageDiv.classList.add('fade-in');
        
        const agent = this.agents[message.agent] || {};
        const timestamp = new Date(message.timestamp).toLocaleTimeString();
        
        if (message.type === 'user') {
            messageDiv.innerHTML = `
                <div class="message-content">
                    <div class="message-header">
                        <span class="user-name">You → ${agent.name || 'Unknown Agent'}</span>
                        <span class="message-time">${timestamp}</span>
                    </div>
                    <div class="message-text">${this.formatMessage(message.content)}</div>
                </div>
                <div class="user-avatar">
                    <i class="fas fa-user"></i>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="agent-avatar" data-icon="${agent.icon || '🤖'}">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="message-content">
                    <div class="message-header">
                        <span class="agent-name">${message.agent_name || 'Agent'}</span>
                        <span class="message-time">${timestamp}</span>
                    </div>
                    <div class="message-text">${this.formatMessage(message.content)}</div>
                </div>
            `;
        }
        
        container.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    formatMessage(content) {
        // Check if the content already contains HTML table
        if (content.includes('<table class="agent-logs-table">')) {
            // For content with HTML tables, only format markdown outside of HTML tags
            let isInsideHtmlTag = false;
            const parts = content.split(/(<[^>]*>)/);
            
            return parts.map(part => {
                if (part.startsWith('<')) {
                    isInsideHtmlTag = !part.startsWith('</') && !part.endsWith('/>');
                    return part; // Return HTML tags as they are
                } else if (part.endsWith('>')) {
                    isInsideHtmlTag = false;
                    return part; // Return HTML tags as they are
                } else if (!isInsideHtmlTag) {
                    // Apply markdown formatting only to non-HTML content
                    return part
                        .replace(/\n/g, '<br>')
                        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                        .replace(/\*(.*?)\*/g, '<em>$1</em>')
                        .replace(/`(.*?)`/g, '<code>$1</code>')
                        .replace(/₹([\d,]+\.?\d*)/g, '<span class="currency">₹$1</span>');
                } else {
                    return part; // Return content inside HTML tags as it is
                }
            }).join('');
        } else {
            // For regular content without HTML, apply all formatting
            return content
                .replace(/\n/g, '<br>')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/`(.*?)`/g, '<code>$1</code>')
                .replace(/₹([\d,]+\.?\d*)/g, '<span class="currency">₹$1</span>');
        }
    }
    
    showTypingIndicator() {
        const container = document.getElementById('chatMessages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message agent typing-indicator';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="agent-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        
        container.appendChild(typingDiv);
        this.scrollToBottom();
    }
    
    removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }
    
    handleMessageResponse(data) {
        this.removeTypingIndicator();
        
        const agentMessage = {
            id: 'agent-' + Date.now(),
            type: 'agent',
            content: data.response,
            timestamp: new Date().toISOString(),
            agent: data.agent,
            agent_name: data.agent_name,
            icon: data.icon
        };
        
        this.addMessageToChat(agentMessage, true);
    }
    
    handleApplicationUpdate(application) {
        // Update the current application
        const index = this.applications.findIndex(app => app.id === application.id);
        if (index !== -1) {
            this.applications[index] = application;
        } else {
            this.applications.push(application);
        }
        
        // Update UI if this is the current application
        if (this.currentApplication && this.currentApplication.id === application.id) {
            this.currentApplication = application;
            this.populateWorkflowCategories(application);
        }
        
        // Update application selector
        this.populateApplicationSelect();
    }
    
    scrollToBottom() {
        const container = document.getElementById('chatMessages');
        container.scrollTop = container.scrollHeight;
    }

    clearChat() {
        const container = document.getElementById('chatMessages');
        const welcomeMessage = container.querySelector('.welcome-message');
        container.innerHTML = '';
        if (welcomeMessage) {
            container.appendChild(welcomeMessage);
        }
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('show');
            setTimeout(() => {
                modal.style.display = 'none';
            }, 300);
        }
    }

    showAuditTrail() {
        if (!this.currentApplication) {
            // If there's no application, show a more friendly message
            this.showNotification('No application data loaded', 'info');
            return;
        }
        
        const modal = document.createElement('div');
        modal.className = 'audit-modal';
        modal.innerHTML = `
            <div class="audit-modal-content">
                <div class="audit-modal-header">
                    <h3><i class="fas fa-history"></i> Audit Trail - ${this.currentApplication.customer_id}</h3>
                    <button class="close-btn" onclick="this.closest('.audit-modal').remove()">&times;</button>
                </div>
                <div class="audit-modal-body">
                    ${this.currentApplication.audit_trail?.map(entry => `
                        <div class="audit-entry">
                            <div class="audit-timestamp">${new Date(entry.timestamp).toLocaleString()}</div>
                            <div class="audit-action">${entry.action}</div>
                            <div class="audit-agent">Agent: ${entry.agent}</div>
                            <div class="audit-details">${entry.details}</div>
                        </div>
                    `).join('') || '<p>No audit entries found.</p>'}
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        modal.style.display = 'block';
    }    // Methods for getting application data are now handled through the applications page
    // and the dashboard-integration.js functionality

    updateApplicationSelector(application) {
        const appSelect = document.getElementById('applicationSelect');
        if (appSelect && application) {
            // Check if option already exists
            const existingOption = Array.from(appSelect.options).find(opt => opt.value === application.id);
            if (!existingOption) {
                const option = document.createElement('option');
                option.value = application.id;
                option.textContent = `${application.customer_id} - ${application.id} (${application.status})`;
                appSelect.appendChild(option);
            }
            appSelect.value = application.id;
        }
    }

    loadApplicationData(application) {
        // Set the current application
        this.currentApplication = application;

        // Update application status panel
        this.updateApplicationStatus(application);
        
        // Update workflow progress
        this.updateWorkflowProgress(application.overall_progress || 96);
        
        // Load messages if any
        if (application.messages && application.messages.length > 0) {
            this.populateChatMessages(application.messages);
        }
        
        // Update overall progress
        this.updateOverallProgress(application);

        // Set the UI state to application_loaded
        this.updateUIState('application_loaded');
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${this.getNotificationIcon(type)}"></i>
                <span>${message}</span>
            </div>
        `;
        
        // Add to body
        document.body.appendChild(notification);
        
        // Show notification
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    getNotificationIcon(type) {
        switch (type) {
            case 'success': return 'check-circle';
            case 'error': return 'exclamation-circle';
            case 'warning': return 'exclamation-triangle';
            default: return 'info-circle';
        }
    }

    toggleAgentPanel() {
        const sidebar = document.querySelector('.enhanced-sidebar');
        if (sidebar) {
            sidebar.classList.toggle('collapsed');
        }
    }

    updateUIState(state, message = '') {
        const loadingOverlay = document.getElementById('loadingOverlay');
        
        switch (state) {
            case 'loading':
                // Show loading overlay with message
                if (loadingOverlay) {
                    const loadingText = loadingOverlay.querySelector('.loading-text');
                    if (loadingText) {
                        loadingText.textContent = message || 'Loading...';
                    }
                    loadingOverlay.style.display = 'flex';
                }
                break;
                
            case 'idle':
            case 'application_loaded':
                // Hide loading overlay
                if (loadingOverlay) {
                    loadingOverlay.style.display = 'none';
                }
                
                // For application_loaded, update UI elements to reflect loaded state
                if (state === 'application_loaded') {
                    // Enable agent selection
                    const agentContainer = document.querySelector('.agent-list');
                    if (agentContainer) {
                        agentContainer.classList.remove('disabled');
                    }
                    
                    // Update the chat interface to show it's ready
                    const chatInterface = document.getElementById('chatInterface');
                    if (chatInterface) {
                        chatInterface.classList.add('application-loaded');
                    }
                    
                    // Show application info
                    const appInfo = document.getElementById('applicationInfo');
                    if (appInfo) {
                        appInfo.style.display = 'block';
                    }
                    
                    // If we have a current application, update the UI with its details
                    if (this.currentApplication) {
                        this.updateApplicationStatus(this.currentApplication);
                        this.updateOverallProgress(this.currentApplication);
                    }
                }
                break;
                
            default:
                // Default is to hide loading overlay
                if (loadingOverlay) {
                    loadingOverlay.style.display = 'none';
                }
                break;
        }
    }
    
    showQuickSuggestions(agentKey) {
        const suggestionsContainer = document.getElementById('quickSuggestions');
        const buttonsContainer = document.getElementById('suggestionsButtons');
        
        if (!suggestionsContainer || !buttonsContainer) return;
        
        // Define suggestions for each agent type
        const suggestions = {
            'document_checker': [
                { text: 'Get the details', icon: 'fas fa-info-circle', class: 'primary-action' },
                { text: 'Show me the updates', icon: 'fas fa-sync-alt', class: '' },
                { text: 'Send the mail for missing documents', icon: 'fas fa-envelope', class: 'email-action' }
            ],
            'default': [
                { text: 'Get the details', icon: 'fas fa-info-circle', class: 'primary-action' },
                { text: 'Show me updates', icon: 'fas fa-sync-alt', class: '' },
                { text: 'Let\'s look on the updates', icon: 'fas fa-search', class: '' }
            ]
        };
        
        // Get suggestions for the current agent or use default
        const agentSuggestions = suggestions[agentKey] || suggestions['default'];
        
        // Clear previous suggestions
        buttonsContainer.innerHTML = '';
        
        // Create suggestion buttons
        agentSuggestions.forEach(suggestion => {
            const button = document.createElement('button');
            button.className = `suggestion-btn ${suggestion.class}`;
            button.innerHTML = `
                <i class="${suggestion.icon}"></i>
                ${suggestion.text}
            `;
            button.onclick = () => this.useSuggestion(suggestion.text);
            buttonsContainer.appendChild(button);
        });
        
        // Show the suggestions container
        suggestionsContainer.style.display = 'block';
    }
    
    hideQuickSuggestions() {
        const suggestionsContainer = document.getElementById('quickSuggestions');
        if (suggestionsContainer) {
            suggestionsContainer.style.display = 'none';
        }
    }
    
    useSuggestion(text) {
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            messageInput.value = text;
            messageInput.focus();
            
            // Optionally, auto-send the suggestion
            this.sendMessage();
        }
    }
}

// Initialize the system when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.bankingSystem = new BankingAgentSystem();
});

// Global function to select an agent - calls the class method
function selectAgent(agentKey) {
    if (window.bankingSystem) {
        window.bankingSystem.selectAgent(agentKey);
    }
}

// Global function to toggle agent category
function toggleAgentCategory(categoryKey) {
    const categoryElement = document.querySelector(`#agents-${categoryKey}`).closest('.agent-category');
    if (categoryElement) {
        categoryElement.classList.toggle('expanded');
        const icon = categoryElement.querySelector('.category-header i');
        if (icon) {
            icon.classList.toggle('fa-chevron-up');
            icon.classList.toggle('fa-chevron-down');
        }
    }
}

// Global function to toggle category in workflow
function toggleCategory(categoryKey) {
    const categoryElement = document.querySelector(`.category-section.${categoryKey.toLowerCase().replace('_', '-')}`);
    if (categoryElement) {
        categoryElement.classList.toggle('expanded');
        const icon = categoryElement.querySelector('.category-header i');
        if (icon) {
            icon.classList.toggle('fa-chevron-up');
            icon.classList.toggle('fa-chevron-down');
        }
    }
}
