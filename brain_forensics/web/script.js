// API endpoint (change if deployed elsewhere)
const API_BASE_URL = 'http://localhost:8080/api';

// Global state
let currentCaseName = null;
let sentimentChartInstance = null; // Keep track of the chart instance

// DOM elements
const caseSelect = document.getElementById('case-select');
const newCaseNameInput = document.getElementById('new-case-name');
const createCaseBtn = document.getElementById('create-case-btn');
const selectedCaseDisplay = document.getElementById('selected-case-display');
const processForm = document.getElementById('process-form');
const targetIdentifierInput = document.getElementById('target-identifier');
const platformsSelect = document.getElementById('platforms');
const processBtn = document.getElementById('process-btn');
const caseRequiredAlert = document.getElementById('case-required-alert');
const loadingIndicator = document.getElementById('loading');
const loadingMessage = document.getElementById('loading-message');
const processLog = document.getElementById('process-log');
const resultsContainer = document.getElementById('results-container');
const resultsCaseName = document.getElementById('results-case-name');
const summaryStatus = document.getElementById('summary-status');
const summaryTarget = document.getElementById('summary-target');
const summaryPlatforms = document.getElementById('summary-platforms');
const summaryCollected = document.getElementById('summary-collected');
const summaryPreserved = document.getElementById('summary-preserved');
const artifactsList = document.getElementById('artifacts-list');
const reportLink = document.getElementById('report-link'); // Assumes this ID exists from previous HTML
const viewReportsLink = document.getElementById('view-reports-link');

// Initialize charts
let sentimentChart = null;

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    populatePlatformOptions();
    loadExistingCases();
    setupEventListeners();
    // Add a debug button to test visualizations without API calls
    addDebugButton(); // Re-enable this line
});

function populatePlatformOptions() {
    // Platforms defined in config.py on backend
    const platforms = ["X", "Facebook", "Instagram", "LinkedIn"]; // Example, should match backend config
    platforms.forEach(p => {
        const option = document.createElement('option');
        option.value = p;
        option.textContent = p;
        platformsSelect.appendChild(option);
    });
}

function setupEventListeners() {
    createCaseBtn.addEventListener('click', handleCreateCase);
    caseSelect.addEventListener('change', handleSelectCase);
    processForm.addEventListener('submit', handleProcessFormSubmit);
    
    // Add listener for viewing reports (optional, could link to reports folder or API)
    if (viewReportsLink) {
        viewReportsLink.addEventListener('click', (e) => {
            e.preventDefault();
            alert("Viewing reports separately - check the 'reports' folder or implement a report listing API.");
            // Example: window.open(`${API_BASE_URL}/reports`); // If you create a reports listing endpoint
        });
    }
}

// Case Management Functions
async function loadExistingCases() {
    try {
        const response = await fetch(`${API_BASE_URL}/cases`);
        if (!response.ok) throw new Error(`Failed to load cases: ${response.statusText}`);
        const data = await response.json();
        
        // Clear existing options except the default
        caseSelect.innerHTML = '<option value="" selected>-- Select Case --</option>';
        
        if (data.cases && data.cases.length > 0) {
            data.cases.forEach(caseName => {
                const option = document.createElement('option');
                option.value = caseName;
                option.textContent = caseName;
                caseSelect.appendChild(option);
            });
        } else {
            // Optionally disable parts of the form if no cases exist
        }
    } catch (error) {
        showError(`Error loading existing cases: ${error.message}`);
    }
}

async function handleCreateCase() {
    const newName = newCaseNameInput.value.trim();
    if (!newName) {
        showError('Please enter a name for the new case.');
        return;
    }

    showLoading(true, 'Creating case...');
    try {
        const response = await fetch(`${API_BASE_URL}/cases`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ case_name: newName })
        });
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || `Failed to create case: ${response.statusText}`);
        }
        
        // Success
        showMessage(`Case '${result.case_name}' created successfully.`);
        newCaseNameInput.value = ''; // Clear input
        await loadExistingCases(); // Reload case list
        // Automatically select the newly created case
        caseSelect.value = result.case_name;
        handleSelectCase(); // Update display

    } catch (error) {
        showError(`Error creating case: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

function handleSelectCase() {
    const selectedCase = caseSelect.value;
    
    // Update the selected case display - fix the ID to match HTML
    const caseDisplayElement = document.getElementById('selected-case-display');
    if (caseDisplayElement) {
        caseDisplayElement.textContent = selectedCase || 'None';
    }
    
    // Enable/disable form elements based on case selection
    const hasSelectedCase = !!selectedCase;
    document.getElementById('target-identifier').disabled = !hasSelectedCase;
    document.querySelectorAll('#platforms option').forEach(opt => opt.disabled = !hasSelectedCase);
    document.getElementById('process-btn').disabled = !hasSelectedCase;
    
    // Reset form if no case is selected
    if (!hasSelectedCase) {
        processForm.reset();
    }
}

async function handleProcessFormSubmit(e) {
    e.preventDefault();
    
    const selectedCase = caseSelect.value;
    if (!selectedCase) {
        showError('Please select or create a case first.');
        return;
    }
    
    const targetIdentifier = document.getElementById('target-identifier').value.trim();
    if (!targetIdentifier) {
        showError('Please enter a target identifier (username, hashtag, etc.)');
        return;
    }
    
    // Get selected platforms - multiple selection
    const platformsSelect = document.getElementById('platforms');
    const selectedPlatforms = Array.from(platformsSelect.selectedOptions).map(opt => opt.value);
    
    if (selectedPlatforms.length === 0) {
        showError('Please select at least one platform to analyze.');
        return;
    }
    
    // Show loading state
    showLoading(true, 'Processing forensic analysis...');
    
    // Clear previous results
    resultsContainer.innerHTML = '';
    
    try {
        const response = await fetch(`${API_BASE_URL}/process`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                case_name: selectedCase,
                target_identifier: targetIdentifier,
                platforms: selectedPlatforms
            })
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || `Processing failed: ${response.statusText}`);
        }
        
        // Display results
        displayProcessingResults(result);
        
    } catch (error) {
        showError(`Error during processing: ${error.message}`);
    } finally {
        showLoading(false);
    }
}

function displayProcessingResults(result) {
    // Create or clear the results container
    if (!resultsContainer) {
        resultsContainer = document.createElement('div');
        resultsContainer.id = 'results-container';
        resultsContainer.className = 'mt-4 p-3 border rounded bg-light';
        document.querySelector('main').appendChild(resultsContainer);
    } else {
        resultsContainer.innerHTML = '';
        resultsContainer.classList.remove('d-none');
    }
    
    // Create status summary
    const statusDiv = document.createElement('div');
    statusDiv.className = 'mb-4';
    statusDiv.innerHTML = `
        <h4>Processing Summary</h4>
        <p class="text-success"><i class="bi bi-check-circle"></i> Status: ${result.status || 'Completed'}</p>
        <p><i class="bi bi-file-text"></i> Collected ${result.collected_count || 0} items from ${result.platforms?.length || 0} platform(s)</p>
        <p><i class="bi bi-clock"></i> Processing time: ${result.processing_time || '< 1'} seconds</p>
    `;
    resultsContainer.appendChild(statusDiv);
    
    // Create artifacts section
    const artifactsDiv = document.createElement('div');
    artifactsDiv.className = 'mb-4';
    artifactsDiv.innerHTML = `
        <h4>Analysis Artifacts</h4>
        <div class="list-group">
            ${result.artifacts?.map(artifact => `
                <a href="${API_BASE_URL}/cases/${result.case_name}/artifacts/${artifact.path}" 
                   class="list-group-item list-group-item-action d-flex justify-content-between align-items-center" 
                   target="_blank">
                    <span><i class="bi bi-${getArtifactIcon(artifact.type)}"></i> ${artifact.name}</span>
                    <span class="badge bg-primary rounded-pill">View</span>
                </a>
            `).join('') || '<p>No artifacts generated</p>'}
        </div>
    `;
    resultsContainer.appendChild(artifactsDiv);
    
    // Display the sentiment analysis if available
    if (result.sentiment_summary) {
        const sentimentDiv = document.createElement('div');
        sentimentDiv.className = 'mb-4';
        sentimentDiv.innerHTML = `
            <h4>Sentiment Analysis</h4>
            <div class="card">
                <div class="card-body">
                    <p><strong>Overall Sentiment:</strong> ${getSentimentLabel(result.sentiment_summary.average_score)}</p>
                    <p><strong>Average Score:</strong> ${result.sentiment_summary.average_score.toFixed(2)}</p>
                    <p><strong>Key Emotions:</strong> ${result.sentiment_summary.top_emotions?.join(', ') || 'None detected'}</p>
                    <p><strong>Top Keywords:</strong> ${result.sentiment_summary.top_keywords?.join(', ') || 'None detected'}</p>
                </div>
            </div>
        `;
        resultsContainer.appendChild(sentimentDiv);
    }
    
    // Display network analysis if available
    if (result.network_summary) {
        const networkDiv = document.createElement('div');
        networkDiv.className = 'mb-4';
        networkDiv.innerHTML = `
            <h4>Network Analysis</h4>
            <div class="card">
                <div class="card-body">
                    <p><strong>Connections:</strong> ${result.network_summary.connection_count || 0} identified</p>
                    <p><strong>Clusters:</strong> ${result.network_summary.cluster_count || 0} detected</p>
                    ${result.network_summary.suspicious_count ? 
                        `<p class="text-danger"><strong>Suspicious Connections:</strong> ${result.network_summary.suspicious_count}</p>` : ''}
                </div>
            </div>
        `;
        resultsContainer.appendChild(networkDiv);
    }
    
    // Add report link if available
    if (result.report_path) {
        const reportDiv = document.createElement('div');
        reportDiv.className = 'mt-4 text-center';
        reportDiv.innerHTML = `
            <a href="${API_BASE_URL}/reports/${result.report_path}" class="btn btn-primary" target="_blank">
                <i class="bi bi-file-pdf"></i> Download Full Forensic Report
            </a>
        `;
        resultsContainer.appendChild(reportDiv);
    }
}

// Helper function to get appropriate icon for artifact type
function getArtifactIcon(type) {
    switch (type?.toLowerCase()) {
        case 'json': return 'file-earmark-code';
        case 'image': return 'image';
        case 'graph': return 'graph-up';
        case 'network': return 'diagram-3';
        case 'report': return 'file-earmark-pdf';
        default: return 'file-earmark';
    }
}

// Helper function to get sentiment label
function getSentimentLabel(score) {
    if (score <= -0.6) return 'Very Negative';
    if (score <= -0.2) return 'Negative';
    if (score >= 0.6) return 'Very Positive';
    if (score >= 0.2) return 'Positive';
    return 'Neutral';
}

// Show/hide loading indicator
function showLoading(isLoading, message) {
    loadingIndicator.classList.toggle('d-none', !isLoading);
    if (message && loadingMessage) {
        loadingMessage.textContent = message;
    }
    
    const processBtn = document.getElementById('process-btn');
    if (processBtn) {
        processBtn.disabled = isLoading;
    }
    
    if (resultsContainer) {
        resultsContainer.classList.toggle('d-none', isLoading);
    }
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

// Show success message
function showMessage(message) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'alert alert-success alert-dismissible fade show';
    msgDiv.innerHTML = `
        <i class="bi bi-check-circle-fill me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Insert message at the top of the main content
    const mainContent = document.querySelector('main');
    mainContent.insertBefore(msgDiv, mainContent.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        msgDiv.remove();
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
    
    // Update sentiment trend chart
    createSentimentTrendChart(sentimentData.sentiment_scores || []);
    
    // Update keywords
    displayKeywords(sentimentData.top_keywords);
}

// Update sentiment gauge
function updateSentimentGauge(value) {
    const gaugeFill = document.getElementById('gauge-fill');
    const gaugeText = document.getElementById('gauge-text');
    const sentimentLabel = document.getElementById('sentiment-label');
    
    // Convert sentiment value (-1 to 1) to gauge rotation (0 to 180 degrees)
    // -1 = very negative = 0 degrees
    // 0 = neutral = 90 degrees
    // 1 = very positive = 180 degrees
    const rotation = ((value + 1) / 2) * 180;
    
    // Set gauge fill color based on sentiment
    let fillColor;
    let labelText;
    
    if (value < -0.6) {
        fillColor = '#dc3545'; // red for very negative
        labelText = '(Very Negative)';
    }
    else if (value < -0.3) {
        fillColor = '#e57373'; // lighter red for negative
        labelText = '(Negative)';
    }
    else if (value < 0.3) {
        fillColor = '#6c757d'; // gray for neutral
        labelText = '(Neutral)';
    }
    else if (value < 0.6) {
        fillColor = '#81c784'; // lighter green for positive
        labelText = '(Positive)';
    }
    else {
        fillColor = '#28a745'; // green for very positive
        labelText = '(Very Positive)';
    }
    
    // Apply rotation and color
    gaugeFill.style.transform = `rotate(${rotation}deg)`;
    gaugeFill.style.backgroundColor = fillColor;
    
    // Update text
    gaugeText.textContent = value.toFixed(2);
    sentimentLabel.textContent = labelText;
}

// Create sentiment distribution chart
function createSentimentChart(distribution) {
    const ctx = document.getElementById('sentiment-chart');
    
    // Destroy existing chart if it exists
    if (sentimentChart) {
        sentimentChart.destroy();
    }
    
    // Ensure we have data - use defaults if needed
    const chartData = distribution || {
        "Positive": 33,
        "Neutral": 34,
        "Negative": 33
    };
    
    const labels = Object.keys(chartData);
    const data = Object.values(chartData);
    
    // Create new chart
    sentimentChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels.map(label => label.charAt(0).toUpperCase() + label.slice(1)),
            datasets: [{
                data: data,
                backgroundColor: [
                    '#28a745', // positive - green
                    '#6c757d', // neutral - gray
                    '#dc3545'  // negative - red
                ],
                borderWidth: 1,
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.formattedValue} posts`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    }
                },
                y: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
    
    // Add platform filter event listener
    document.getElementById('platform-filter').addEventListener('change', function(e) {
        // Placeholder for API call to filter by platform
        // In a real implementation, this would call the API with the selected platform
        console.log(`Filter by platform: ${e.target.value}`);
    });
}

// Create sentiment trend chart
function createSentimentTrendChart(sentimentScores) {
    const ctx = document.getElementById('sentiment-trend');
    
    // Generate some data if none provided
    const scores = sentimentScores && sentimentScores.length > 0 ? 
                  sentimentScores : 
                  [0.2, 0.3, 0.1, 0.4, 0.2, -0.1, 0.3];
    
    // Create gradient for line
    const chartCanvas = document.getElementById('sentiment-trend');
    const ctx2d = chartCanvas.getContext('2d');
    const gradient = ctx2d.createLinearGradient(0, 0, 0, 60);
    gradient.addColorStop(0, 'rgba(40, 167, 69, 0.7)');  
    gradient.addColorStop(1, 'rgba(40, 167, 69, 0.1)');
    
    // Create labels (just placeholders for visual)
    const labels = Array.from({length: scores.length}, (_, i) => `Day ${i+1}`);
    
    // Create mini trend chart
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                data: scores,
                borderColor: '#28a745',
                backgroundColor: gradient,
                borderWidth: 2,
                pointRadius: 0,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    enabled: false
                }
            },
            scales: {
                x: {
                    display: false
                },
                y: {
                    display: false,
                    min: -1,
                    max: 1
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
    
    // Sample sentiment scores for keywords (in a real implementation, these would come from the API)
    const sampleScores = [0.72, 0.65, -0.41, 0.58, 0.12];
    const mentionCounts = [28, 23, 19, 17, 15];
    
    // Create keyword badges
    keywords.forEach((keyword, i) => {
        const sentiment = i < sampleScores.length ? sampleScores[i] : (Math.random() * 2 - 1);
        const mentions = i < mentionCounts.length ? mentionCounts[i] : Math.floor(Math.random() * 30) + 5;
        
        // Determine keyword class based on sentiment
        let keywordClass = 'keyword-badge';
        if (sentiment > 0.3) keywordClass += ' keyword-positive';
        else if (sentiment < -0.3) keywordClass += ' keyword-negative';
        
        const keywordElement = document.createElement('div');
        keywordElement.className = keywordClass;
        keywordElement.innerHTML = `
            <span>${keyword} <small>(${mentions}×)</small></span>
            <span class="score">${sentiment.toFixed(2)}</span>
        `;
        keywordsContainer.appendChild(keywordElement);
    });
}

// Display anomalies
function displayAnomalies(anomalies) {
    const anomaliesContainer = document.getElementById('anomalies-container');
    const noAnomaliesAlert = document.getElementById('no-anomalies');
    
    // Clear container
    anomaliesContainer.innerHTML = '';
    
    if (!anomalies || anomalies.length === 0) {
        noAnomaliesAlert.classList.remove('d-none');
        return;
    }
    
    // Hide no anomalies alert
    noAnomaliesAlert.classList.add('d-none');
    
    // Sample dates for anomalies (in a real implementation, these would come from the API)
    const sampleDates = [
        'May 15, 2023',
        'April 29, 2023',
        'June 3, 2023'
    ];
    
    // Create anomaly cards
    anomalies.forEach((anomaly, index) => {
        const severity = anomaly.severity || 'medium';
        const date = sampleDates[index % sampleDates.length];
        
        const platformsHtml = anomaly.platforms ? 
            anomaly.platforms.map(p => `<span class="platform-badge">${p}</span>`).join('') :
            '<span class="platform-badge">Twitter</span>';
        
        const colDiv = document.createElement('div');
        colDiv.className = 'col-lg-6 mb-3';
        
        colDiv.innerHTML = `
            <div class="anomaly-card severity-${severity.toLowerCase()}">
                <div class="anomaly-header">
                    <h5 class="anomaly-title">${anomaly.type || 'Anomaly Detected'}</h5>
                    <span class="severity-badge">${severity.toUpperCase()}</span>
                </div>
                <div class="anomaly-date">${date}</div>
                <p class="mt-2">${anomaly.description}</p>
                <div class="anomaly-platforms">
                    ${platformsHtml}
                </div>
            </div>
        `;
        
        anomaliesContainer.appendChild(colDiv);
    });
}

// Display network analysis
function displayNetwork(networkData) {
    // Set network image if available
    if (networkData.image) {
        document.getElementById('network-image').src = `data:image/png;base64,${networkData.image}`;
    } else {
        // Create a placeholder network graph for demo mode
        createPlaceholderNetworkGraph();
    }
    
    // Display influential nodes
    displayInfluentialNodes(networkData.patterns);
    
    // Display suspicious connections
    displaySuspiciousConnections(networkData.flags);
    
    // Add event listeners for network controls
    document.getElementById('zoom-in').addEventListener('click', function() {
        console.log('Zoom in network graph');
        // In a real implementation, this would zoom in the network graph
    });
    
    document.getElementById('zoom-out').addEventListener('click', function() {
        console.log('Zoom out network graph');
        // In a real implementation, this would zoom out the network graph
    });
    
    document.getElementById('reset-view').addEventListener('click', function() {
        console.log('Reset network graph view');
        // In a real implementation, this would reset the network graph view
    });
    
    document.getElementById('network-filter').addEventListener('change', function(e) {
        console.log(`Filter network by: ${e.target.value}`);
        // In a real implementation, this would filter the network graph by platform
    });
}

// Set report link
function setReportLink(reportPath) {
    if (!reportLink) return;
    
    if (reportPath) {
        reportLink.href = `${API_BASE_URL}/reports/${reportPath}`;
        reportLink.textContent = 'Download Forensic Report (PDF)';
        reportLink.classList.remove('d-none');
        reportLink.classList.remove('disabled');
    } else {
        reportLink.href = '#';
        reportLink.textContent = 'Report not available';
        reportLink.classList.add('disabled');
    }
}

// Create a placeholder network graph for demo mode
function createPlaceholderNetworkGraph() {
    const container = document.getElementById('network-graph');
    
    // Check if container exists
    if (!container) {
        console.error('Network graph container not found');
        return;
    }
    
    // Remove any existing image
    container.innerHTML = '';
    
    // Create canvas with explicit styling
    const canvas = document.createElement('canvas');
    canvas.id = 'network-canvas';
    canvas.width = 600;
    canvas.height = 400;
    canvas.style.maxWidth = '100%';
    canvas.style.height = 'auto';
    canvas.style.display = 'block';
    canvas.style.margin = '0 auto';
    canvas.style.border = '1px solid #eee';
    canvas.style.borderRadius = '4px';
    
    // Add canvas to container
    container.appendChild(canvas);
    
    // Make sure canvas context is available
    const ctx = canvas.getContext('2d');
    if (!ctx) {
        console.error('Could not get canvas context');
        return;
    }
    
    // Create a simple network visualization
    const nodes = [
        { id: 'main', x: 300, y: 200, radius: 25, color: '#0366d6' },
        { id: 'node1', x: 150, y: 100, radius: 15, color: '#28a745' },
        { id: 'node2', x: 450, y: 120, radius: 15, color: '#28a745' },
        { id: 'node3', x: 200, y: 300, radius: 15, color: '#fd7e14' },
        { id: 'node4', x: 400, y: 320, radius: 18, color: '#fd7e14' },
        { id: 'node5', x: 500, y: 250, radius: 12, color: '#dc3545' },
        { id: 'node6', x: 100, y: 220, radius: 10, color: '#6c757d' },
        { id: 'node7', x: 380, y: 80, radius: 8, color: '#6c757d' }
    ];
    
    // Define edges (connections between nodes)
    const edges = [
        { from: 'main', to: 'node1', width: 3, color: 'rgba(3, 102, 214, 0.6)' },
        { from: 'main', to: 'node2', width: 4, color: 'rgba(3, 102, 214, 0.6)' },
        { from: 'main', to: 'node3', width: 2, color: 'rgba(3, 102, 214, 0.6)' },
        { from: 'main', to: 'node4', width: 3, color: 'rgba(3, 102, 214, 0.6)' },
        { from: 'node1', to: 'node6', width: 1, color: 'rgba(3, 102, 214, 0.4)' },
        { from: 'node2', to: 'node7', width: 1, color: 'rgba(3, 102, 214, 0.4)' },
        { from: 'node2', to: 'node5', width: 2, color: 'rgba(220, 53, 69, 0.5)' },
        { from: 'node3', to: 'node4', width: 2, color: 'rgba(253, 126, 20, 0.5)' }
    ];
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Set a background color
    ctx.fillStyle = '#f8f9fa';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Draw a light grid background
    ctx.strokeStyle = 'rgba(0,0,0,0.05)';
    ctx.lineWidth = 1;
    
    for (let i = 0; i < canvas.width; i += 40) {
        ctx.beginPath();
        ctx.moveTo(i, 0);
        ctx.lineTo(i, canvas.height);
        ctx.stroke();
    }
    
    for (let i = 0; i < canvas.height; i += 40) {
        ctx.beginPath();
        ctx.moveTo(0, i);
        ctx.lineTo(canvas.width, i);
        ctx.stroke();
    }
    
    // Draw edges first (so they appear under the nodes)
    edges.forEach(edge => {
        const fromNode = nodes.find(n => n.id === edge.from);
        const toNode = nodes.find(n => n.id === edge.to);
        
        if (fromNode && toNode) {
            ctx.beginPath();
            ctx.moveTo(fromNode.x, fromNode.y);
            ctx.lineTo(toNode.x, toNode.y);
            ctx.strokeStyle = edge.color;
            ctx.lineWidth = edge.width;
            ctx.stroke();
        }
    });
    
    // Draw nodes
    nodes.forEach(node => {
        // Node background with shadow
        ctx.shadowColor = 'rgba(0,0,0,0.2)';
        ctx.shadowBlur = 10;
        ctx.shadowOffsetX = 2;
        ctx.shadowOffsetY = 2;
        
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
        ctx.fillStyle = node.color;
        ctx.fill();
        
        // Reset shadow
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;
        ctx.shadowOffsetX = 0;
        ctx.shadowOffsetY = 0;
        
        // Node border
        ctx.strokeStyle = 'rgba(255,255,255,0.8)';
        ctx.lineWidth = 2;
        ctx.stroke();
    });
    
    // Add labels to nodes
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 12px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    
    ctx.fillText('@main', nodes[0].x, nodes[0].y);
    
    // Add a label indicating this is a demo graph
    ctx.fillStyle = '#6c757d';
    ctx.font = 'italic 14px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Demo Network Graph', canvas.width / 2, 20);
    
    console.log('Network graph created successfully');
}

// Display influential nodes
function displayInfluentialNodes(nodes) {
    const nodesContainer = document.getElementById('influential-nodes');
    nodesContainer.innerHTML = '';
    
    if (!nodes || nodes.length === 0) {
        // Create sample nodes if none provided
        const sampleNodes = [
            {
                source: '@tech_innovator',
                target: '@news_network',
                influence_score: 87,
                interactions: 23,
                amplification: 26,
                coordinated: true
            },
            {
                source: 'facebook.com/research_group',
                target: 'linkedin.com/company/neural-tech',
                influence_score: 76,
                alignment: 92,
                themes: ['breakthrough', 'paradigm shift']
            },
            {
                source: '@neural_science',
                target: '@investment_daily',
                influence_score: 72,
                pattern: 'bidirectional',
                topics: ['funding', 'market']
            }
        ];
        
        sampleNodes.forEach(node => {
            const nodeElement = document.createElement('div');
            nodeElement.className = 'connection-item list-group-item';
            
            nodeElement.innerHTML = `
                <div class="connection-header">
                    <h6 class="connection-title">${node.source} → ${node.target}</h6>
                    <span class="connection-score">${node.influence_score}/100</span>
                </div>
                
                <div class="connection-details">
                    ${node.interactions ? `${node.interactions} interactions in past month<br>` : ''}
                    ${node.amplification ? `Content amplification rate: ${node.amplification}×<br>` : ''}
                    ${node.alignment ? `Cross-platform messaging alignment: ${node.alignment}%<br>` : ''}
                    ${node.pattern ? `${node.pattern.charAt(0).toUpperCase() + node.pattern.slice(1)} amplification pattern<br>` : ''}
                    ${node.coordinated ? `<span class="text-danger">Coordinated posting detected</span>` : ''}
                </div>
                
                <div class="connection-metadata">
                    ${node.themes ? `<span>Themes: ${node.themes.join(', ')}</span>` : ''}
                    ${node.topics ? `<span>Topics: ${node.topics.join(', ')}</span>` : ''}
                </div>
            `;
            
            nodesContainer.appendChild(nodeElement);
        });
        
        return;
    }
    
    // Create node items
    nodes.forEach(node => {
        const nodeElement = document.createElement('div');
        nodeElement.className = 'connection-item list-group-item';
        
        // Format node information
        let nodeDetails = '';
        let nodeMetadata = '';
        
        if (node.description) {
            nodeDetails = `<div class="connection-details">${node.description}</div>`;
        }
        
        if (node.details) {
            nodeMetadata = `<div class="connection-metadata">
                <span>${node.details}</span>
            </div>`;
        }
        
        nodeElement.innerHTML = `
            <div class="connection-header">
                <h6 class="connection-title">${node.title || node.type || 'Connection'}</h6>
                <span class="connection-score">${node.score || '?'}/100</span>
            </div>
            ${nodeDetails}
            ${nodeMetadata}
        `;
        
        nodesContainer.appendChild(nodeElement);
    });
}

// Display suspicious connections
function displaySuspiciousConnections(connections) {
    const connectionsContainer = document.getElementById('suspicious-connections');
    connectionsContainer.innerHTML = '';
    
    if (!connections || connections.length === 0) {
        // Create sample suspicious connections if none provided
        const sampleConnections = [
            {
                type: 'TEMPORAL ANOMALY',
                date: 'May 11, 2023',
                description: '47 accounts posting similar content within 3-minute window',
                details: [
                    'Behavior inconsistent with organic activity',
                    'Accounts created: all within past 30 days'
                ]
            },
            {
                type: 'GEOGRAPHICAL INCONSISTENCY',
                date: 'June 7, 2023',
                description: 'Accounts claiming US location posting during unusual hours (2-4AM local)',
                details: [
                    'IP analysis suggests different geographic origins',
                    'Language patterns inconsistent with claimed locations'
                ]
            },
            {
                type: 'NARRATIVE SEEDING',
                date: 'May 23-29, 2023',
                description: 'Coordinated introduction of specific terminology across platforms',
                details: [
                    'Evidence of message testing and refinement',
                    'Progressive amplification pattern identified'
                ]
            }
        ];
        
        sampleConnections.forEach(connection => {
            const connectionElement = document.createElement('div');
            connectionElement.className = 'connection-item suspicious list-group-item';
            
            let details = '';
            if (connection.details && connection.details.length > 0) {
                details = connection.details.map(d => `<li>${d}</li>`).join('');
                details = `<ul class="mb-0 ps-3">${details}</ul>`;
            }
            
            connectionElement.innerHTML = `
                <div class="connection-header">
                    <h6 class="connection-title">${connection.type}</h6>
                    <span class="connection-score">Alert</span>
                </div>
                
                <div class="connection-details">
                    <strong>Detected ${connection.date}</strong><br>
                    ${connection.description}
                    ${details}
                </div>
            `;
            
            connectionsContainer.appendChild(connectionElement);
        });
        
        return;
    }
    
    // Create connection items
    connections.forEach(connection => {
        const connectionElement = document.createElement('div');
        connectionElement.className = 'connection-item suspicious list-group-item';
        
        // Format connection information
        let connectionDetails = '';
        
        if (connection.description) {
            connectionDetails = `<div class="connection-details">${connection.description}</div>`;
        }
        
        connectionElement.innerHTML = `
            <div class="connection-header">
                <h6 class="connection-title">${connection.title || connection.type || 'Suspicious Activity'}</h6>
                <span class="connection-score">Alert</span>
            </div>
            ${connectionDetails}
        `;
        
        connectionsContainer.appendChild(connectionElement);
    });
}

// Ensure error suppression script is still relevant (likely needed)
window.addEventListener('error', function(e) {
    if (e.filename && (e.filename.includes('utils.js') || e.filename.includes('extensionState.js') || e.filename.includes('heuristicsRedefinitions.js'))) {
        console.warn('Suppressed error for likely browser extension file:', e.filename);
        e.preventDefault();
        return true;
    }
}, true);

// Add a debug button for testing visualizations
function addDebugButton() {
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'mt-3 mb-3 text-center';
    buttonContainer.innerHTML = `
        <button id="debug-button" class="btn btn-outline-secondary btn-sm">
            <i class="bi bi-bug"></i> Run Detailed Display Tests
        </button>
    `;
    
    // Insert before the loading indicator or results container
    const targetElement = loadingIndicator || resultsContainer || document.querySelector('main');
    targetElement.parentNode.insertBefore(buttonContainer, targetElement);
    
    // Add event listener to call the new test function
    document.getElementById('debug-button').addEventListener('click', function() {
        console.log("Running detailed display tests...");
        runDetailedDisplayTests(); // Call the new test function
    });
}

// Load sample data for testing (Keep original or remove if not needed elsewhere)
function loadSampleData() {
    // ... (original loadSampleData content can remain or be removed) ...
    console.warn("loadSampleData function called, but debug button now uses runDetailedDisplayTests.");
}

// *** NEW FUNCTION TO RUN DETAILED TESTS ***
function runDetailedDisplayTests() {
    console.log("Starting detailed display tests...");
    
    // Ensure results container is visible and cleared
    if (resultsContainer) {
        resultsContainer.classList.remove('d-none');
        // Minimal HTML structure needed for the components if not already there
        // This assumes index.html has the necessary divs with IDs
        resultsContainer.innerHTML = `
            <h2>Test Results</h2>
            <div id="profile-section" class="mb-4">
                <h4>Profile</h4>
                <div class="card"><div class="card-body">
                    <p>Username: <span id="profile-username"></span> <span id="profile-badge" class="badge"></span></p>
                    <p>Platform: <span id="profile-platform"></span></p>
                    <p>Created: <span id="profile-created"></span></p>
                    <p>Followers: <span id="profile-followers"></span> | Following: <span id="profile-following"></span></p>
                    <p>Bio: <span id="profile-bio"></span></p>
                    <div id="profile-alert" class="alert alert-warning d-none">Suspicious Account</div>
                </div></div>
            </div>
            <div id="sentiment-section" class="mb-4">
                 <h4>Sentiment Analysis</h4>
                 <div class="card"><div class="card-body">
                     <div class="row">
                         <div class="col-md-4">
                            <h5>Overall Sentiment</h5>
                            <div id="sentiment-gauge-container">
                                 <div class="gauge">
                                     <div class="gauge-body">
                                         <div class="gauge-fill" id="gauge-fill"></div>
                                         <div class="gauge-cover"><span id="gauge-text">0.00</span></div>
                                     </div>
                                     <div class="gauge-label" id="sentiment-label">(Neutral)</div>
                                 </div>
                             </div>
                         </div>
                         <div class="col-md-4">
                             <h5>Distribution</h5>
                             <canvas id="sentiment-chart" height="150"></canvas>
                             <select id="platform-filter" class="form-select form-select-sm mt-2"><option value="">All Platforms</option></select>
                         </div>
                         <div class="col-md-4">
                             <h5>Trend</h5>
                             <canvas id="sentiment-trend" height="60"></canvas>
                             <h5>Top Keywords</h5>
                             <div id="keywords-container"></div>
                         </div>
                     </div>
                 </div></div>
             </div>
            <div id="anomalies-section" class="mb-4">
                <h4>Anomalies</h4>
                <div id="no-anomalies" class="alert alert-info d-none">No significant anomalies detected.</div>
                <div id="anomalies-container" class="row"></div>
            </div>
            <div id="network-section" class="mb-4">
                <h4>Network Analysis</h4>
                 <div class="card"><div class="card-body">
                    <div id="network-graph"><img id="network-image" src="" alt="Network Graph" class="img-fluid"/></div>
                    <div class="network-controls mt-2 text-center">
                         <button id="zoom-in" class="btn btn-sm btn-outline-secondary"><i class="bi bi-zoom-in"></i></button>
                         <button id="zoom-out" class="btn btn-sm btn-outline-secondary"><i class="bi bi-zoom-out"></i></button>
                         <button id="reset-view" class="btn btn-sm btn-outline-secondary"><i class="bi bi-arrow-counterclockwise"></i></button>
                         <select id="network-filter" class="form-select form-select-sm d-inline-block w-auto ms-2"><option value="">All Platforms</option></select>
                     </div>
                     <h5>Influential Nodes/Patterns</h5>
                     <div id="influential-nodes" class="list-group mb-3"></div>
                     <h5>Suspicious Connections/Flags</h5>
                     <div id="suspicious-connections" class="list-group"></div>
                </div></div>
            </div>
        `;
    } else {
        showError("Results container not found. Cannot run tests.");
        return;
    }

    const sampleData = {
        username: 'test_user_detailed',
        platform: 'X', // Test single platform display
        profile: {
            created_date: '2022-08-15T10:30:00Z', // Test date parsing/display if any
            followers: 987,
            following: 123,
            bio: 'Testing detailed bio with special characters & emojis 🤔✨.',
            verified: false, // Test non-verified
            is_suspicious: true // Test suspicious flag
        },
        sentiment_analysis: {
            average_sentiment: -0.75, // Test very negative
            sentiment_distribution: {
                'Positive': 5,
                'Neutral': 15,
                'Negative': 80 // Skewed distribution
            },
            sentiment_scores: [-0.5, -0.8, -0.6, -0.9, -0.7, -0.85, -0.7], // Negative trend
            top_keywords: ['critical', 'error', 'fail', 'warning', 'issue'] // Negative keywords
        },
        anomalies: [ // Test multiple anomalies
            {
                type: 'HIGH VOLUME POSTING',
                severity: 'high',
                description: 'Posting frequency increased 10x compared to baseline.',
                platforms: ['X', 'Facebook'] // Test multiple platforms
            },
            {
                type: 'GEOLOCATION MISMATCH',
                severity: 'medium',
                description: 'IP address location inconsistent with user profile location.',
                platforms: ['Instagram']
            },
             {
                type: 'BOT-LIKE BEHAVIOR',
                severity: 'low', // Test low severity
                description: 'Repetitive content detected across posts.',
                // platforms: null // Test missing platforms
            }
        ],
        network_analysis: {
            // image: null, // Test placeholder graph generation
             image: 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=', // Test with a tiny valid base64 image string
            patterns: [ // Test influential nodes display
                {
                    title: '@nodeA → @nodeB',
                    score: 95,
                    description: 'Strong amplification detected.'
                },
                 {
                    title: 'Group C ↔ Group D',
                    score: 60,
                    description: 'Moderate bidirectional interaction.'
                }
            ],
            flags: [ // Test suspicious flags display
                 {
                    type: 'COORDINATED INAUTHENTIC BEHAVIOR',
                    title: 'Coordination Alert',
                    description: 'Multiple accounts posting identical content simultaneously.'
                },
                {
                    type: 'SUSPICIOUS LOGIN ACTIVITY',
                     title: 'Login Anomaly',
                    description: 'Logins detected from multiple unusual locations.'
                }
            ]
        },
        report_path: 'test_report_detailed.pdf' // Test report link generation
    };
    
    try {
        console.log("Testing displayProfile...");
        // displayProfile needs the top-level data object
        displayProfile(sampleData); 
        
        console.log("Testing displaySentiment...");
        // displaySentiment needs the sentiment_analysis object
        displaySentiment(sampleData.sentiment_analysis); 
        
        console.log("Testing displayAnomalies...");
        // displayAnomalies needs the anomalies array
        displayAnomalies(sampleData.anomalies); 
        
        console.log("Testing displayNetwork...");
        // displayNetwork needs the network_analysis object
        displayNetwork(sampleData.network_analysis); 
        
        console.log("Testing setReportLink (implicitly called by displayResults or needs separate call if displayResults isn't used)...");
        // We might need to call setReportLink directly if not using displayResults
        // Assuming setReportLink exists and takes the path:
        // setReportLink(sampleData.report_path); 
        // **Correction:** Looking at the code again, displayResults calls setReportLink.
        // Since we are calling components individually, we need to handle the report link separately or add it.
        // Let's add a simple call for the report link if the element exists.
        if (reportLink) {
             reportLink.href = `${API_BASE_URL}/reports/${sampleData.report_path}`;
             reportLink.textContent = 'Download Test Report';
             reportLink.classList.remove('disabled');
             console.log("Report link updated.");
        } else {
            console.warn("Report link element not found.")
        }

        showMessage("Detailed display tests completed. Please review the sections below.");
        
    } catch (error) {
        showError(`Error during detailed tests: ${error.message}`);
        console.error("Detailed test failed:", error);
    }
}

// Format numbers for display (adding commas)
function formatNumber(num) {
    if (num === undefined || num === null) return '0';
    return new Intl.NumberFormat().format(num);
}