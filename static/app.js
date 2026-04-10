// Ollama Server Web UI

const API_BASE = '';

// State
let models = [];
let config = {};
let modelToDelete = null;

// DOM Elements
const statusEl = document.getElementById('status');
const statusTextEl = document.getElementById('status-text');
const ollamaUrlEl = document.getElementById('ollama-url');
const modelCountEl = document.getElementById('model-count');
const modelsListEl = document.getElementById('models-list');
const pullModelInput = document.getElementById('pull-model-input');
const pullModelBtn = document.getElementById('pull-model-btn');
const refreshModelsBtn = document.getElementById('refresh-models-btn');
const pullProgressEl = document.getElementById('pull-progress');
const settingsForm = document.getElementById('settings-form');
const settingsOllamaUrl = document.getElementById('settings-ollama-url');
const settingsServerPort = document.getElementById('settings-server-port');
const settingsStatus = document.getElementById('settings-status');
const confirmModal = document.getElementById('confirm-modal');
const deleteModelNameEl = document.getElementById('delete-model-name');
const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
const cancelDeleteBtn = document.getElementById('cancel-delete-btn');

// Initialize
document.addEventListener('DOMContentLoaded', init);

async function init() {
    await loadConfig();
    await checkStatus();
    await loadModels();
    
    // Event listeners
    pullModelBtn.addEventListener('click', pullModel);
    refreshModelsBtn.addEventListener('click', loadModels);
    settingsForm.addEventListener('submit', saveSettings);
    confirmDeleteBtn.addEventListener('click', confirmDelete);
    cancelDeleteBtn.addEventListener('click', closeModal);
    
    // Check status periodically
    setInterval(checkStatus, 30000);
}

async function loadConfig() {
    try {
        const response = await fetch(`${API_BASE}/api/config`);
        config = await response.json();
        settingsOllamaUrl.value = config.ollama_url || '';
        settingsServerPort.value = config.server_port || '';
    } catch (error) {
        console.error('Failed to load config:', error);
    }
}

async function checkStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/status`);
        const data = await response.json();
        
        if (data.ollama.connected) {
            statusEl.className = 'status connected';
            statusTextEl.textContent = 'Connected';
            ollamaUrlEl.textContent = data.ollama.url;
            modelCountEl.textContent = data.ollama.model_count;
        } else {
            statusEl.className = 'status disconnected';
            statusTextEl.textContent = 'Disconnected';
            ollamaUrlEl.textContent = data.ollama.url;
            modelCountEl.textContent = '-';
        }
    } catch (error) {
        statusEl.className = 'status disconnected';
        statusTextEl.textContent = 'Error';
        console.error('Failed to check status:', error);
    }
}

async function loadModels() {
    modelsListEl.innerHTML = '<p class="loading">Loading models...</p>';
    
    try {
        const response = await fetch(`${API_BASE}/api/tags`);
        const data = await response.json();
        models = data.models || [];
        renderModels();
    } catch (error) {
        modelsListEl.innerHTML = '<p class="loading">Failed to load models</p>';
        console.error('Failed to load models:', error);
    }
}

function renderModels() {
    if (models.length === 0) {
        modelsListEl.innerHTML = '<p class="loading">No models found. Pull a model to get started.</p>';
        return;
    }
    
    modelsListEl.innerHTML = models.map(model => {
        const size = formatSize(model.size);
        const modified = formatDate(model.modified_at);
        return `
            <div class="model-item">
                <div class="model-info">
                    <span class="model-name">${model.name}</span>
                    <span class="model-meta">${size} • ${modified}</span>
                </div>
                <div class="model-actions">
                    <button class="btn small danger" onclick="showDeleteModal('${model.name}')">Delete</button>
                </div>
            </div>
        `;
    }).join('');
}

async function pullModel() {
    const modelName = pullModelInput.value.trim();
    if (!modelName) return;
    
    pullModelBtn.disabled = true;
    pullProgressEl.classList.remove('hidden');
    const progressText = pullProgressEl.querySelector('.progress-text');
    const progressFill = pullProgressEl.querySelector('.progress-fill');
    
    progressText.textContent = `Pulling ${modelName}...`;
    progressFill.style.width = '0%';
    
    try {
        const response = await fetch(`${API_BASE}/api/pull`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: modelName }),
        });
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const lines = decoder.decode(value).split('\n').filter(Boolean);
            for (const line of lines) {
                try {
                    const data = JSON.parse(line);
                    if (data.status) {
                        progressText.textContent = data.status;
                    }
                    if (data.completed && data.total) {
                        const percent = Math.round((data.completed / data.total) * 100);
                        progressFill.style.width = `${percent}%`;
                    }
                    if (data.error) {
                        progressText.textContent = `Error: ${data.error}`;
                    }
                } catch (e) {
                    // Ignore parse errors
                }
            }
        }
        
        progressText.textContent = 'Pull complete!';
        progressFill.style.width = '100%';
        pullModelInput.value = '';
        await loadModels();
        await checkStatus();
        
        setTimeout(() => {
            pullProgressEl.classList.add('hidden');
        }, 2000);
        
    } catch (error) {
        progressText.textContent = `Error: ${error.message}`;
        console.error('Failed to pull model:', error);
    } finally {
        pullModelBtn.disabled = false;
    }
}

function showDeleteModal(modelName) {
    modelToDelete = modelName;
    deleteModelNameEl.textContent = modelName;
    confirmModal.classList.remove('hidden');
}

function closeModal() {
    confirmModal.classList.add('hidden');
    modelToDelete = null;
}

async function confirmDelete() {
    if (!modelToDelete) return;
    
    confirmDeleteBtn.disabled = true;
    
    try {
        await fetch(`${API_BASE}/api/delete`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: modelToDelete }),
        });
        
        await loadModels();
        await checkStatus();
    } catch (error) {
        console.error('Failed to delete model:', error);
        alert(`Failed to delete model: ${error.message}`);
    } finally {
        confirmDeleteBtn.disabled = false;
        closeModal();
    }
}

async function saveSettings(e) {
    e.preventDefault();
    
    const updates = {
        ollama_url: settingsOllamaUrl.value.trim(),
        server_port: parseInt(settingsServerPort.value, 10),
    };
    
    try {
        const response = await fetch(`${API_BASE}/api/config`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates),
        });
        
        config = await response.json();
        settingsStatus.textContent = 'Saved!';
        
        // Refresh status with new config
        await checkStatus();
        await loadModels();
        
        setTimeout(() => {
            settingsStatus.textContent = '';
        }, 2000);
        
    } catch (error) {
        settingsStatus.textContent = 'Save failed';
        console.error('Failed to save settings:', error);
    }
}

// Helpers
function formatSize(bytes) {
    if (!bytes) return '-';
    const gb = bytes / (1024 * 1024 * 1024);
    if (gb >= 1) return `${gb.toFixed(1)} GB`;
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(0)} MB`;
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString();
}
