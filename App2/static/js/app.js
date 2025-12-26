// Test that JavaScript is loading
console.log('=== APP.JS LOADED ===');

// Application State
const state = {
    factories: [],
    regions: [],
    cameras: [],
    defectTypes: [],
    currentPage: 1,
    perPage: 8,
    filters: {
        region: '',
        factory: '',
        camera: '',
        prediction: '',
        defect_type: '',
        search: '',
        date_from: '',
        date_to: ''
    }
};

// Initialize app on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    // Set current date in header
    updateHeaderDate();
    
    // Load factories and populate dropdowns
    await loadFactories();
    
    // Load all filter options (defect types, etc.)
    await loadFilterOptions();
    
    // Setup event listeners
    setupEventListeners();
    
    // Load initial data
    loadInspections();
    
    console.log('[DEBUG] App initialization complete');
}

function updateHeaderDate() {
    const dateElement = document.getElementById('currentDate');
    const now = new Date();
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    dateElement.textContent = now.toLocaleDateString('en-US', options);
}

async function loadFactories() {
    try {
        const response = await fetch('/api/factories');
        const data = await response.json();
        
        state.factories = data.factories;
        
        // Extract unique regions and cameras
        state.regions = [...new Set(data.factories.map(f => f.region))].sort();
        
        const allCameras = data.factories.flatMap(f => f.cameras || []);
        state.cameras = [...new Set(allCameras)].sort();
        
        // Populate dropdowns
        populateRegionSelect();
        populateFactorySelect();
        populateCameraSelect();
        
    } catch (error) {
        console.error('Failed to load factories:', error);
        showError('Failed to load factory data. Please refresh the page.');
    }
}

async function loadFilterOptions() {
    try {
        const response = await fetch('/api/filter-options');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.defect_types || data.defect_types.length === 0) {
            console.warn('No defect types returned from API');
            return;
        }
        
        state.defectTypes = data.defect_types;
        
        // Populate defect types dropdown with all possible values
        populateDefectSelect(state.defectTypes);
        
    } catch (error) {
        console.error('Failed to load filter options:', error);
    }
}

function populateRegionSelect() {
    const select = document.getElementById('regionSelect');
    select.innerHTML = '<option value="">All Regions</option>';
    
    state.regions.forEach(region => {
        const option = document.createElement('option');
        option.value = region;
        option.textContent = region;
        select.appendChild(option);
    });
}

function populateFactorySelect(filterByRegion = null) {
    const select = document.getElementById('factorySelect');
    select.innerHTML = '<option value="">All Factories</option>';
    
    let factories = state.factories;
    if (filterByRegion) {
        factories = factories.filter(f => f.region === filterByRegion);
    }
    
    factories.forEach(factory => {
        const option = document.createElement('option');
        option.value = factory.factory_id;
        option.textContent = factory.factory_id;
        select.appendChild(option);
    });
}

function populateCameraSelect() {
    const select = document.getElementById('cameraSelect');
    select.innerHTML = '<option value="">All Cameras</option>';
    
    state.cameras.forEach(camera => {
        const option = document.createElement('option');
        option.value = camera;
        option.textContent = camera;
        select.appendChild(option);
    });
}

function populateDefectSelect(defectTypes) {
    const select = document.getElementById('defectSelect');
    select.innerHTML = '<option value="">All</option>';
    
    if (!defectTypes || defectTypes.length === 0) {
        return;
    }
    
    defectTypes.forEach(defect => {
        if (defect) {
            const option = document.createElement('option');
            option.value = defect;
            option.textContent = defect;
            select.appendChild(option);
        }
    });
}

function setupEventListeners() {
    // Region change should filter factories
    document.getElementById('regionSelect').addEventListener('change', (e) => {
        const region = e.target.value;
        populateFactorySelect(region);
        document.getElementById('factorySelect').value = '';
    });
    
    // Apply filters button
    document.getElementById('applyFilters').addEventListener('click', () => {
        state.currentPage = 1;
        collectFilters();
        loadInspections();
    });
    
    // Reset filters button
    document.getElementById('resetFilters').addEventListener('click', () => {
        resetFilters();
    });
    
    // Per page change
    document.getElementById('perPageSelect').addEventListener('change', (e) => {
        state.perPage = parseInt(e.target.value);
        state.currentPage = 1;
        collectFilters();
        loadInspections();
    });
    
    // Pagination buttons
    document.getElementById('prevPage').addEventListener('click', () => {
        if (state.currentPage > 1) {
            state.currentPage--;
            loadInspections();
        }
    });
    
    document.getElementById('nextPage').addEventListener('click', () => {
        state.currentPage++;
        loadInspections();
    });
    
    // Enter key in search
    document.getElementById('searchInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            state.currentPage = 1;
            collectFilters();
            loadInspections();
        }
    });
}

function collectFilters() {
    state.filters = {
        region: document.getElementById('regionSelect').value,
        factory: document.getElementById('factorySelect').value,
        camera: document.getElementById('cameraSelect').value,
        prediction: document.getElementById('predictionSelect').value,
        defect_type: document.getElementById('defectSelect').value,
        search: document.getElementById('searchInput').value,
        date_from: document.getElementById('dateFrom').value,
        date_to: document.getElementById('dateTo').value
    };
}

function resetFilters() {
    // Reset all form elements
    document.getElementById('regionSelect').value = '';
    document.getElementById('factorySelect').value = '';
    document.getElementById('cameraSelect').value = '';
    document.getElementById('predictionSelect').value = '';
    document.getElementById('defectSelect').value = '';
    document.getElementById('searchInput').value = '';
    document.getElementById('dateFrom').value = '';
    document.getElementById('dateTo').value = '';
    document.getElementById('perPageSelect').value = '8';
    
    // Reset state
    state.currentPage = 1;
    state.perPage = 8;
    state.filters = {
        region: '',
        factory: '',
        camera: '',
        prediction: '',
        defect_type: '',
        search: '',
        date_from: '',
        date_to: ''
    };
    
    // Reload factories dropdown
    populateFactorySelect();
    
    // Reload data
    loadInspections();
}

async function loadInspections() {
    showLoading();
    hideError();
    
    try {
        // Build query parameters
        const params = new URLSearchParams({
            page: state.currentPage,
            per_page: state.perPage
        });
        
        // Add filters
        Object.entries(state.filters).forEach(([key, value]) => {
            if (value) {
                params.append(key, value);
            }
        });
        
        const response = await fetch(`/api/inspections?${params}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update stats
        updateStats(data.stats);
        
        // Render inspection cards
        renderInspections(data.inspections);
        
        // Update pagination
        updatePagination(data.pagination);
        
        hideLoading();
        
    } catch (error) {
        console.error('Failed to load inspections:', error);
        hideLoading();
        showError('Failed to load inspections. Please try again.');
    }
}

function updateStats(stats) {
    document.getElementById('totalCount').textContent = stats.total || 0;
    document.getElementById('filteredCount').textContent = stats.filtered || 0;
    document.getElementById('okCount').textContent = stats.ok_count || 0;
    document.getElementById('koCount').textContent = stats.ko_count || 0;
}

function renderInspections(inspections) {
    const grid = document.getElementById('inspectionGrid');
    grid.innerHTML = '';
    
    if (inspections.length === 0) {
        grid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #666; padding: 40px;">No inspections found matching your filters.</p>';
        return;
    }
    
    inspections.forEach(inspection => {
        const card = createInspectionCard(inspection);
        grid.appendChild(card);
    });
}

function createInspectionCard(inspection) {
    const card = document.createElement('div');
    card.className = 'inspection-card';
    
    const prediction = inspection.prediction;
    const borderClass = prediction === 'OK' ? 'border-ok' : 'border-ko';
    const statusClass = prediction === 'OK' ? 'ok' : 'ko';
    
    // Build image URL
    const imageUrl = `/api/image?path=${encodeURIComponent(inspection.image_path)}`;
    
    // Defect badge HTML
    const defectBadge = inspection.defect_type 
        ? `<div class="defect-badge">${inspection.defect_type}</div>`
        : '';
    
    // Format confidence as percentage
    const confidence = (inspection.confidence_score * 100).toFixed(1);
    
    card.innerHTML = `
        <div class="image-container ${borderClass}">
            <img src="${imageUrl}" alt="${inspection.inspection_id}" loading="lazy" 
                 onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%27400%27 height=%27300%27%3E%3Crect fill=%27%23f0f0f0%27 width=%27400%27 height=%27300%27/%3E%3Ctext fill=%27%23999%27 font-family=%27sans-serif%27 font-size=%2716%27 x=%2750%25%27 y=%2750%25%27 text-anchor=%27middle%27%3EImage not available%3C/text%3E%3C/svg%3E'">
            <div class="status-overlay ${statusClass}">${prediction}</div>
            ${defectBadge}
            <button class="download-btn" onclick="downloadImage('${imageUrl}', '${inspection.inspection_id}')" title="Download image">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
            </button>
        </div>
        <div class="inspection-id">${inspection.inspection_id}</div>
        <div class="meta-row">
            <span class="meta-label">Factory</span>
            <span class="meta-value">${inspection.factory_id}</span>
        </div>
        <div class="meta-row">
            <span class="meta-label">Camera</span>
            <span class="meta-value">${inspection.camera_id}</span>
        </div>
        <div class="meta-row">
            <span class="meta-label">Timestamp</span>
            <span class="meta-value">${inspection.timestamp}</span>
        </div>
        <div class="meta-row">
            <span class="meta-label">Confidence</span>
            <span class="meta-value">${confidence}%</span>
        </div>
        <div class="meta-row">
            <span class="meta-label">Inference</span>
            <span class="meta-value">${inspection.inference_time_ms}ms</span>
        </div>
        <div class="meta-row">
            <span class="meta-label">Model</span>
            <span class="meta-value">${inspection.model_version}</span>
        </div>
    `;
    
    return card;
}

function downloadImage(imageUrl, inspectionId) {
    // Create a temporary link and trigger download
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = `${inspectionId}.jpg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function updatePagination(pagination) {
    const paginationDiv = document.getElementById('pagination');
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');
    const pageInfo = document.getElementById('pageInfo');
    
    if (pagination.total_pages > 1) {
        paginationDiv.style.display = 'flex';
        
        prevBtn.disabled = pagination.page <= 1;
        nextBtn.disabled = pagination.page >= pagination.total_pages;
        
        pageInfo.textContent = `Page ${pagination.page} of ${pagination.total_pages}`;
    } else {
        paginationDiv.style.display = 'none';
    }
}

function showLoading() {
    document.getElementById('loadingSpinner').style.display = 'block';
    document.getElementById('inspectionGrid').style.opacity = '0.5';
}

function hideLoading() {
    document.getElementById('loadingSpinner').style.display = 'none';
    document.getElementById('inspectionGrid').style.opacity = '1';
}

function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

function hideError() {
    document.getElementById('errorMessage').style.display = 'none';
}

