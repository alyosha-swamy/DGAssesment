/**
 * Social Media Analysis Visualization Tool
 * This simplified app loads and displays preloaded data about social media activity
 */

// DOM Elements
const datasetSelect = document.getElementById('dataset-select');
const visualizationType = document.getElementById('visualization-type');
const visualizeBtn = document.getElementById('visualize-btn');
const loadingIndicator = document.getElementById('loading');
const resultsContainer = document.getElementById('results-container');

// Templates
const networkTemplate = document.getElementById('network-template');
const sentimentTemplate = document.getElementById('sentiment-template');
const timelineTemplate = document.getElementById('timeline-template');

// Charts
let sentimentChart = null;
let sentimentTrendChart = null;
let timelineChart = null;

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    
    // Automatically visualize the default dataset (user1)
    setTimeout(() => {
        visualizeData();
    }, 500);
});

function setupEventListeners() {
    // Visualize button
    visualizeBtn.addEventListener('click', () => {
        visualizeData();
    });
    
    // Dataset selection change
    datasetSelect.addEventListener('change', () => {
        // Optional: Auto-visualize on dataset change
        // visualizeData();
    });
}

function visualizeData() {
    // Get selected dataset
    const datasetId = datasetSelect.value;
    const selectedVisualization = visualizationType.value;
    
    // Show loading
    showLoading(true);
    
    // Clear results container
    resultsContainer.innerHTML = '';
    
    // Load dataset
    currentDataset = PRELOADED_DATA[datasetId];
    
    // Create header with dataset info
    createDatasetHeader(currentDataset.meta);
    
    // Generate visualizations based on selection
    if (selectedVisualization === 'all' || selectedVisualization === 'network') {
        createNetworkVisualization(currentDataset.network);
    }
    
    if (selectedVisualization === 'all' || selectedVisualization === 'sentiment') {
        createSentimentVisualization(currentDataset.sentiment);
    }
    
    if (selectedVisualization === 'all' || selectedVisualization === 'timeline') {
        createTimelineVisualization(currentDataset.timeline);
    }
    
    // Hide loading
    showLoading(false);
}

// Create dataset header with metadata
function createDatasetHeader(meta) {
    const header = document.createElement('div');
    header.className = 'dataset-header mb-4';
    header.innerHTML = `
        <h2>${meta.name}</h2>
        <p class="text-muted">${meta.description}</p>
        <div class="badge bg-secondary">${meta.dataPoints.toLocaleString()} data points</div>
    `;
    resultsContainer.appendChild(header);
}

// Create network visualization
function createNetworkVisualization(networkData) {
    // Clone template
    const networkSection = document.importNode(networkTemplate.content, true);
    
    // Append to results container
    resultsContainer.appendChild(networkSection);
    
    // Get the network graph container
    const networkGraph = document.getElementById('network-graph');
    
    // Create canvas for network graph
    const canvas = document.createElement('canvas');
    canvas.id = 'network-canvas';
    canvas.width = 600;
    canvas.height = 400;
    canvas.style.maxWidth = '100%';
    networkGraph.appendChild(canvas);
    
    // Draw network graph using canvas
    drawNetworkGraph(canvas, networkData);
    
    // Populate key nodes
    const nodesContainer = document.getElementById('influential-nodes');
    networkData.keyNodes.forEach(node => {
        const nodeElement = document.createElement('div');
        nodeElement.className = `list-group-item ${node.suspicious ? 'border-danger' : ''}`;
        
        nodeElement.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <h6 class="mb-1">${node.title}</h6>
                <span class="badge bg-${node.suspicious ? 'danger' : 'primary'} rounded-pill">${node.score}/100</span>
            </div>
            <p class="mb-1">${node.description}</p>
        `;
        
        nodesContainer.appendChild(nodeElement);
    });
    
    // Add network controls functionality
    document.getElementById('zoom-in').addEventListener('click', () => {
        zoomNetwork(1.2);
    });
    
    document.getElementById('zoom-out').addEventListener('click', () => {
        zoomNetwork(0.8);
    });
    
    document.getElementById('reset-view').addEventListener('click', () => {
        resetNetworkView();
    });
}

// Draw network graph on canvas
function drawNetworkGraph(canvas, networkData) {
    const ctx = canvas.getContext('2d');
    
    // Scale and positions
    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#f8f9fa';
    ctx.fillRect(0, 0, width, height);
    
    // Draw a light grid background
    ctx.strokeStyle = 'rgba(0,0,0,0.05)';
    ctx.lineWidth = 1;
    
    for (let i = 0; i < width; i += 40) {
        ctx.beginPath();
        ctx.moveTo(i, 0);
        ctx.lineTo(i, height);
        ctx.stroke();
    }
    
    for (let i = 0; i < height; i += 40) {
        ctx.beginPath();
        ctx.moveTo(0, i);
        ctx.lineTo(width, i);
        ctx.stroke();
    }
    
    // Node positions (calculated with a simple force-directed layout approach)
    const nodePositions = {};
    
    // Simple placement algorithm
    const radius = Math.min(width, height) * 0.35;
    
    // Set central node in the middle
    nodePositions['central'] = { x: centerX, y: centerY };
    
    // Place other nodes in a circle around it
    const otherNodes = networkData.nodes.filter(n => n.id !== 'central');
    otherNodes.forEach((node, i) => {
        const angle = (i / otherNodes.length) * Math.PI * 2;
        const nodeRadius = radius * (0.5 + (node.size / 30));
        
        nodePositions[node.id] = {
            x: centerX + Math.cos(angle) * nodeRadius,
            y: centerY + Math.sin(angle) * nodeRadius
        };
    });
    
    // Draw edges first (so they appear underneath nodes)
    ctx.strokeStyle = 'rgba(0,0,0,0.2)';
    networkData.edges.forEach(edge => {
        // Skip if we don't have positions for source or target
        if (!nodePositions[edge.source] || !nodePositions[edge.target]) return;
        
        const sourcePos = nodePositions[edge.source];
        const targetPos = nodePositions[edge.target];
        
        // Color based on edge type
        let edgeColor;
        switch(edge.type) {
            case 'coordinated':
                edgeColor = 'rgba(220, 53, 69, 0.6)'; // Red for suspicious coordination
                break;
            case 'mention':
                edgeColor = 'rgba(13, 110, 253, 0.5)'; // Blue for mentions
                break;
            case 'used_hashtag':
                edgeColor = 'rgba(25, 135, 84, 0.5)'; // Green for hashtag usage
                break;
            case 'cooccurrence':
                edgeColor = 'rgba(255, 193, 7, 0.5)'; // Yellow for co-occurrence
                break;
            default:
                edgeColor = 'rgba(108, 117, 125, 0.4)'; // Gray default
        }
        
        ctx.strokeStyle = edgeColor;
        ctx.lineWidth = edge.weight / 4 || 1;
        
        ctx.beginPath();
        ctx.moveTo(sourcePos.x, sourcePos.y);
        ctx.lineTo(targetPos.x, targetPos.y);
        ctx.stroke();
    });
    
    // Draw nodes
    networkData.nodes.forEach(node => {
        const pos = nodePositions[node.id];
        if (!pos) return;
        
        // Determine node color based on type
        let nodeColor;
        switch(node.type) {
            case 'account':
                nodeColor = '#0d6efd'; // Blue for accounts
                break;
            case 'hashtag':
                nodeColor = '#198754'; // Green for hashtags
                break;
            case 'topic':
            case 'subtopic':
                nodeColor = '#6610f2'; // Purple for topics
                break;
            default:
                nodeColor = '#6c757d'; // Gray default
        }
        
        // Node shadow
        ctx.shadowColor = 'rgba(0,0,0,0.2)';
        ctx.shadowBlur = 5;
        ctx.shadowOffsetX = 2;
        ctx.shadowOffsetY = 2;
        
        // Draw node
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, node.size / 2, 0, Math.PI * 2);
        ctx.fillStyle = nodeColor;
        ctx.fill();
        
        // Remove shadow for node border
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;
        ctx.shadowOffsetX = 0;
        ctx.shadowOffsetY = 0;
        
        // Node border
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 2;
        ctx.stroke();
        
        // Node label
        ctx.fillStyle = '#212529';
        ctx.font = '10px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        
        // Label with background
        const label = node.label;
        const textWidth = ctx.measureText(label).width + 6;
        const textHeight = 16;
        
        ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
        ctx.fillRect(
            pos.x - textWidth / 2, 
            pos.y + node.size / 2 + 2, 
            textWidth, 
            textHeight
        );
        
        ctx.fillStyle = '#212529';
        ctx.fillText(
            label, 
            pos.x, 
            pos.y + node.size / 2 + 4
        );
    });
}

// Network zoom function
function zoomNetwork(factor) {
    console.log(`Zoom network by factor ${factor}`);
    // In a real implementation, this would scale the network graph
}

// Reset network view
function resetNetworkView() {
    console.log('Reset network view');
    // In a real implementation, this would reset the network graph view
}

// Create sentiment visualization
function createSentimentVisualization(sentimentData) {
    // Clone template
    const sentimentSection = document.importNode(sentimentTemplate.content, true);
    
    // Append to results container
    resultsContainer.appendChild(sentimentSection);
    
    // Update sentiment gauge
    updateSentimentGauge(sentimentData.average);
    
    // Create sentiment distribution chart
    createSentimentDistributionChart(sentimentData.distribution);
    
    // Create sentiment trend chart
    createSentimentTrendChart(sentimentData.trend);
    
    // Display keywords
    displayKeywords(sentimentData.keywords);
}

// Update sentiment gauge
function updateSentimentGauge(value) {
    const gaugeFill = document.getElementById('gauge-fill');
    const gaugeText = document.getElementById('gauge-text');
    const sentimentLabel = document.getElementById('sentiment-label');
    
    // Convert sentiment value (-1 to 1) to gauge rotation (0 to 180 degrees)
    const rotation = ((value + 1) / 2) * 180;
    
    // Set gauge fill color based on sentiment
    let fillColor;
    let labelText;
    
    if (value < -0.6) {
        fillColor = '#dc3545'; // Red for very negative
        labelText = '(Very Negative)';
    }
    else if (value < -0.2) {
        fillColor = '#fd7e14'; // Orange for negative
        labelText = '(Negative)';
    }
    else if (value < 0.2) {
        fillColor = '#6c757d'; // Gray for neutral
        labelText = '(Neutral)';
    }
    else if (value < 0.6) {
        fillColor = '#198754'; // Green for positive
        labelText = '(Positive)';
    }
    else {
        fillColor = '#198754'; // Darker green for very positive
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
function createSentimentDistributionChart(distribution) {
    const ctx = document.getElementById('sentiment-chart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (sentimentChart) {
        sentimentChart.destroy();
    }
    
    // Prepare data
    const labels = Object.keys(distribution);
    const data = Object.values(distribution);
    
    // Create chart
    sentimentChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Sentiment Distribution',
                data: data,
                backgroundColor: [
                    '#198754', // Green for positive
                    '#6c757d', // Gray for neutral
                    '#dc3545'  // Red for negative
                ],
                borderColor: [
                    '#198754',
                    '#6c757d',
                    '#dc3545'
                ],
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Create sentiment trend chart
function createSentimentTrendChart(trendData) {
    const ctx = document.getElementById('sentiment-trend').getContext('2d');
    
    // Destroy existing chart if it exists
    if (sentimentTrendChart) {
        sentimentTrendChart.destroy();
    }
    
    // Prepare data
    const labels = Array.from({ length: trendData.length }, (_, i) => `${i+1}`);
    
    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 60);
    gradient.addColorStop(0, 'rgba(25, 135, 84, 0.7)');
    gradient.addColorStop(1, 'rgba(25, 135, 84, 0.1)');
    
    // Create chart
    sentimentTrendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Sentiment Trend',
                data: trendData,
                borderColor: '#198754',
                backgroundColor: gradient,
                tension: 0.4,
                fill: true,
                pointRadius: 0
            }]
        },
        options: {
            plugins: {
                legend: {
                    display: false
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
    const container = document.getElementById('keywords-container');
    
    keywords.forEach(keyword => {
        const keywordElement = document.createElement('div');
        
        // Determine class based on sentiment score
        let colorClass = '';
        if (keyword.score > 0.3) {
            colorClass = 'text-success';
        } else if (keyword.score < -0.3) {
            colorClass = 'text-danger';
        }
        
        keywordElement.className = `keyword mb-1 d-flex justify-content-between ${colorClass}`;
        keywordElement.innerHTML = `
            <span>${keyword.word} <small>(${keyword.count}×)</small></span>
            <span>${keyword.score.toFixed(2)}</span>
        `;
        
        container.appendChild(keywordElement);
    });
}

// Create timeline visualization
function createTimelineVisualization(timelineData) {
    // Clone template
    const timelineSection = document.importNode(timelineTemplate.content, true);
    
    // Append to results container
    resultsContainer.appendChild(timelineSection);
    
    // Create timeline chart
    createTimelineChart(timelineData);
    
    // Display key events
    displayKeyEvents(timelineData.events);
    
    // Add event listener for timeline metric change
    document.getElementById('timeline-metric').addEventListener('change', (e) => {
        updateTimelineChart(timelineData, e.target.value);
    });
}

// Create timeline chart
function createTimelineChart(timelineData) {
    const ctx = document.getElementById('timeline-chart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (timelineChart) {
        timelineChart.destroy();
    }
    
    // Default to posts metric
    updateTimelineChart(timelineData, 'posts');
}

// Update timeline chart with selected metric
function updateTimelineChart(timelineData, metric) {
    const ctx = document.getElementById('timeline-chart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (timelineChart) {
        timelineChart.destroy();
    }
    
    // Prepare data
    const labels = timelineData.dates;
    const data = timelineData.metrics[metric];
    
    // Determine color based on metric
    let color;
    let label;
    
    switch(metric) {
        case 'posts':
            color = '#0d6efd'; // Blue
            label = 'Post Volume';
            break;
        case 'engagement':
            color = '#fd7e14'; // Orange
            label = 'Engagement';
            break;
        case 'reach':
            color = '#6610f2'; // Purple
            label = 'Reach';
            break;
        default:
            color = '#6c757d'; // Gray
            label = 'Activity';
    }
    
    // Create chart
    timelineChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                borderColor: color,
                backgroundColor: color + '20',
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.raw.toLocaleString()}`;
                        }
                    }
                }
            }
        }
    });
}

// Display key events
function displayKeyEvents(events) {
    const container = document.getElementById('key-events');
    
    events.forEach(event => {
        const eventElement = document.createElement('div');
        
        // Add suspicious class if applicable
        const isSuspicious = event.suspicious === true;
        
        eventElement.className = `list-group-item ${isSuspicious ? 'border-danger' : ''}`;
        eventElement.innerHTML = `
            <div class="d-flex justify-content-between">
                <h6 class="mb-1 ${isSuspicious ? 'text-danger' : ''}">${event.title}</h6>
                <small>${event.date}</small>
            </div>
            <p class="mb-0">${event.description}</p>
        `;
        
        container.appendChild(eventElement);
    });
}

// Show/hide loading indicator
function showLoading(isLoading) {
    loadingIndicator.classList.toggle('d-none', !isLoading);
}

// Show error message
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-danger mt-3';
    errorDiv.textContent = message;
    resultsContainer.prepend(errorDiv);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
} 