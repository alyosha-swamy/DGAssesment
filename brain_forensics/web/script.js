// API endpoint (change if deployed elsewhere)
const API_BASE_URL = 'http://localhost:8080/api';

// DOM elements
const searchForm = document.getElementById('search-form');
const usernameInput = document.getElementById('username');
const platformSelect = document.getElementById('platform');
const analyzeButton = document.getElementById('analyze-btn');
const loadingIndicator = document.getElementById('loading');
const resultsContainer = document.getElementById('results-container');

// Initialize charts
let sentimentChart = null;

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Form submission
    searchForm.addEventListener('submit', handleFormSubmit);
});

// Handle form submission
async function handleFormSubmit(event) {
    event.preventDefault();
    
    const username = usernameInput.value.trim();
    const platform = platformSelect.value;
    
    if (!username) {
        alert('Please enter a username to analyze');
        return;
    }
    
    // Show loading indicator
    showLoading(true);
    
    try {
        // Call API
        const data = await analyzeUser(username, platform);
        
        // Display results
        displayResults(data);
    } catch (error) {
        // Handle error
        showError(error.message);
    } finally {
        // Hide loading indicator
        showLoading(false);
    }
}

// Call API to analyze user
async function analyzeUser(username, platform) {
    try {
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, platform })
        });
        
        if (!response.ok) {
            if (response.status === 404) {
                throw new Error('No social media data found for this user');
            }
            const errorData = await response.json();
            throw new Error(errorData.error || 'An error occurred while analyzing the user');
        }
        
        return await response.json();
    } catch (error) {
        if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
            throw new Error('Unable to connect to the server. Please make sure the server is running and try again.');
        }
        throw error;
    }
}

// Show/hide loading indicator
function showLoading(isLoading) {
    loadingIndicator.classList.toggle('d-none', !isLoading);
    analyzeButton.disabled = isLoading;
    resultsContainer.classList.toggle('d-none', isLoading);
}

// Show error message
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-danger alert-dismissible fade show';
    errorDiv.innerHTML = `
        <i class="bi bi-exclamation-triangle-fill me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Insert error message at the top of the main content
    const mainContent = document.querySelector('main');
    mainContent.insertBefore(errorDiv, mainContent.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

// Display results
function displayResults(data) {
    // Show results container
    resultsContainer.classList.remove('d-none');
    
    // Display user profile
    displayProfile(data);
    
    // Display sentiment analysis
    displaySentiment(data.sentiment_analysis);
    
    // Display anomalies
    displayAnomalies(data.anomalies);
    
    // Display network analysis
    displayNetwork(data.network_analysis);
    
    // Set report link
    setReportLink(data.report_path);
}

// Display user profile
function displayProfile(data) {
    const profile = data.profile;
    
    // Set profile fields
    document.getElementById('profile-username').textContent = data.username;
    document.getElementById('profile-platform').textContent = data.platform.charAt(0).toUpperCase() + data.platform.slice(1);
    document.getElementById('profile-created').textContent = profile.created_date || 'Unknown';
    document.getElementById('profile-followers').textContent = formatNumber(profile.followers);
    document.getElementById('profile-following').textContent = formatNumber(profile.following);
    document.getElementById('profile-bio').textContent = profile.bio || 'No bio provided';
    
    // Set verification badge
    const profileBadge = document.getElementById('profile-badge');
    if (profile.verified) {
        profileBadge.textContent = 'Verified';
        profileBadge.className = 'badge bg-success';
    } else {
        profileBadge.textContent = 'Not Verified';
        profileBadge.className = 'badge bg-secondary';
    }
    
    // Show suspicious account alert if applicable
    const profileAlert = document.getElementById('profile-alert');
    if (profile.is_suspicious) {
        profileAlert.classList.remove('d-none');
    } else {
        profileAlert.classList.add('d-none');
    }
}

// Display sentiment analysis
function displaySentiment(sentimentData) {
    // Update gauge
    updateSentimentGauge(sentimentData.average_sentiment);
    
    // Update sentiment distribution chart
    createSentimentChart(sentimentData.sentiment_distribution);
    
    // Update keywords
    displayKeywords(sentimentData.top_keywords);
}

// Update sentiment gauge
function updateSentimentGauge(value) {
    const gaugeFill = document.getElementById('gauge-fill');
    const gaugeText = document.getElementById('gauge-text');
    
    // Convert sentiment value (-1 to 1) to gauge rotation (0 to 180 degrees)
    // -1 = very negative = 0 degrees
    // 0 = neutral = 90 degrees
    // 1 = very positive = 180 degrees
    const rotation = ((value + 1) / 2) * 180;
    
    // Set gauge fill color based on sentiment
    let fillColor;
    if (value < -0.3) fillColor = '#dc3545'; // red for negative
    else if (value < 0.3) fillColor = '#6c757d'; // gray for neutral
    else fillColor = '#28a745'; // green for positive
    
    // Apply rotation and color
    gaugeFill.style.transform = `rotate(${rotation}deg)`;
    gaugeFill.style.backgroundColor = fillColor;
    
    // Update text
    gaugeText.textContent = value.toFixed(2);
}

// Create sentiment distribution chart
function createSentimentChart(distribution) {
    const ctx = document.getElementById('sentiment-chart');
    
    // Destroy existing chart if it exists
    if (sentimentChart) {
        sentimentChart.destroy();
    }
    
    const labels = Object.keys(distribution);
    const data = Object.values(distribution);
    
    // Create new chart
    sentimentChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels.map(label => label.charAt(0).toUpperCase() + label.slice(1)),
            datasets: [{
                data: data,
                backgroundColor: [
                    '#28a745', // positive - green
                    '#6c757d', // neutral - gray
                    '#dc3545'  // negative - red
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Display keywords
function displayKeywords(keywords) {
    const keywordsContainer = document.getElementById('keywords-container');
    keywordsContainer.innerHTML = '';
    
    if (!keywords || keywords.length === 0) {
        keywordsContainer.innerHTML = '<p class="text-muted">No keywords found</p>';
        return;
    }
    
    // Create keyword badges
    keywords.forEach(keyword => {
        const badge = document.createElement('span');
        badge.className = 'keyword-badge';
        badge.textContent = keyword;
        keywordsContainer.appendChild(badge);
    });
}

// Display anomalies
function displayAnomalies(anomalies) {
    const anomaliesContainer = document.getElementById('anomalies-container');
    const noAnomalies = document.getElementById('no-anomalies');
    
    anomaliesContainer.innerHTML = '';
    
    if (!anomalies || anomalies.length === 0) {
        noAnomalies.classList.remove('d-none');
        return;
    }
    
    noAnomalies.classList.add('d-none');
    
    // Create anomaly cards
    anomalies.forEach((anomaly, index) => {
        const col = document.createElement('div');
        col.className = 'col-md-6';
        
        const card = document.createElement('div');
        card.className = `anomaly-card severity-${anomaly.severity || 'medium'}`;
        
        const title = document.createElement('h5');
        title.textContent = `Anomaly ${index + 1}: ${anomaly.type}`;
        
        const description = document.createElement('p');
        description.textContent = anomaly.description;
        
        const severity = document.createElement('p');
        severity.className = 'mb-0';
        severity.innerHTML = `<strong>Severity:</strong> <span class="badge bg-${getSeverityColor(anomaly.severity)}">${(anomaly.severity || 'medium').toUpperCase()}</span>`;
        
        card.appendChild(title);
        card.appendChild(description);
        card.appendChild(severity);
        col.appendChild(card);
        anomaliesContainer.appendChild(col);
    });
}

// Display network analysis
function displayNetwork(networkData) {
    // Display network image
    const networkImage = document.getElementById('network-image');
    if (networkData.image) {
        networkImage.src = `data:image/png;base64,${networkData.image}`;
    } else {
        networkImage.src = '';
        networkImage.alt = 'No network data available';
    }
    
    // Display influential nodes
    displayInfluentialNodes(networkData.influential_nodes);
    
    // Display suspicious connections
    displaySuspiciousConnections(networkData.suspicious_connections);
}

// Display influential nodes
function displayInfluentialNodes(nodes) {
    const nodesContainer = document.getElementById('influential-nodes');
    nodesContainer.innerHTML = '';
    
    if (!nodes || nodes.length === 0) {
        nodesContainer.innerHTML = '<p class="text-muted">No influential nodes found</p>';
        return;
    }
    
    // Create node items
    nodes.forEach((node) => {
        const item = document.createElement('a');
        item.className = 'list-group-item list-group-item-action';
        
        // Calculate influence score (0-1)
        const influenceScore = (node.betweenness + node.eigenvector + node.pagerank) / 3;
        
        item.innerHTML = `
            <div class="d-flex w-100 justify-content-between">
                <h6 class="mb-1">${node.username}</h6>
                <small class="text-${node.is_suspicious ? 'danger' : 'muted'}">${node.is_suspicious ? 'Suspicious' : 'Normal'}</small>
            </div>
            <div class="d-flex align-items-center">
                <div class="progress flex-grow-1" style="height: 8px;">
                    <div class="progress-bar ${node.is_suspicious ? 'bg-danger' : 'bg-primary'}" 
                         role="progressbar" 
                         style="width: ${influenceScore * 100}%" 
                         aria-valuenow="${influenceScore * 100}" 
                         aria-valuemin="0" 
                         aria-valuemax="100"></div>
                </div>
                <small class="ms-2">${(influenceScore * 100).toFixed(0)}%</small>
            </div>
            <small>${node.platform} | ${formatNumber(node.followers)} followers</small>
        `;
        
        nodesContainer.appendChild(item);
    });
}

// Display suspicious connections
function displaySuspiciousConnections(connections) {
    const connectionsContainer = document.getElementById('suspicious-connections');
    connectionsContainer.innerHTML = '';
    
    if (!connections || connections.length === 0) {
        connectionsContainer.innerHTML = '<p class="text-muted">No suspicious connections found</p>';
        return;
    }
    
    // Create connection items
    connections.forEach((connection) => {
        const item = document.createElement('a');
        item.className = 'list-group-item list-group-item-action text-danger';
        
        item.innerHTML = `
            <div class="d-flex w-100 justify-content-between">
                <h6 class="mb-1">${connection.type}</h6>
                <small>${connection.size || ''}</small>
            </div>
            <p class="mb-1">${connection.description}</p>
        `;
        
        connectionsContainer.appendChild(item);
    });
}

// Set report link
function setReportLink(reportPath) {
    if (!reportPath) return;
    
    const reportLink = document.getElementById('report-link');
    
    // Extract filename from path
    const filename = reportPath.split('/').pop();
    
    // Set link to download report
    reportLink.href = `${API_BASE_URL}/reports/${filename}`;
}

// Helper: Format number with commas
function formatNumber(num) {
    if (num === undefined || num === null) return 'Unknown';
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Helper: Get severity color
function getSeverityColor(severity) {
    switch (severity) {
        case 'high': return 'danger';
        case 'medium': return 'warning';
        case 'low': return 'info';
        default: return 'secondary';
    }
} 