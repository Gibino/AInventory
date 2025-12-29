/**
 * Controle de Inventário Doméstico
 * Frontend Application with ML predictions, theme system, and barcode scanning
 */

const API_URL = '';
// Auth Check
if (!localStorage.getItem('access_token')) {
    window.location.href = 'login.html';
}

// Function to handle fetch with auth
async function fetchWithAuth(url, options = {}) {
    const token = localStorage.getItem('access_token');
    const headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`
    };

    const response = await fetch(url, { ...options, headers });

    if (response.status === 401) {
        localStorage.removeItem('access_token');
        window.location.href = 'login.html';
        return null;
    }
    return response;
}

let currentLang = localStorage.getItem('app-language') || navigator.language || 'pt-BR';
let translations = {};


// ====== State Management ======
let items = [];
let categories = [];
let shoppingList = [];
let selectedCategoryId = null;
let itemToDelete = null;
let videoStream = null;
let currentUser = null; // Store user profile

// ====== Localization System ======

async function loadTranslations(lang) {
    try {
        // Fallback to en-US if specific locale not found, or just try to load
        // Use pt-BR if lang starts with pt, else en-US
        const targetLang = lang.startsWith('pt') ? 'pt-BR' : 'en-US';
        const response = await fetch(`locales/${targetLang}.json`);
        translations = await response.json();
        currentLang = targetLang;
        localStorage.setItem('app-language', targetLang);
        updateLanguageButtons(targetLang);
        applyTranslations();
        // Re-render components to update dynamic text
        renderCategories();
        renderItems();
        updateStats();
    } catch (err) {
        console.error("Error loading translations:", err);
    }
}

function t(key, params = {}) {
    let text = translations[key] || key;
    Object.entries(params).forEach(([param, value]) => {
        text = text.replace(`{${param}}`, value);
    });
    return text;
}

function applyTranslations() {
    document.title = t('app_title');

    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.dataset.i18n;
        if (translations[key]) {
            el.textContent = translations[key];
        }
    });

    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.dataset.i18nPlaceholder;
        if (translations[key]) {
            el.placeholder = translations[key];
        }
    });

    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.dataset.i18nTitle;
        if (translations[key]) {
            el.title = translations[key];
        }
    });

    // Specific placeholder updates for dynamic hints
    const nameInput = document.getElementById('name');
    if (nameInput) {
        nameInput.placeholder = t('unit_kg') === 'kg' ? "Ex: Arroz, Feijão..." : "Ex: Rice, Beans...";
    }
}

function updateLanguageButtons(lang) {
    document.querySelectorAll('[data-lang]').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.lang === lang);
    });
}

// Language Switcher Listeners are set up in init() to include DB persistence

// ====== DOM Elements ======
const itemsGrid = document.getElementById('items-grid');
const categoriesList = document.getElementById('categories-list');
const itemModal = document.getElementById('item-modal');
const shoppingModal = document.getElementById('shopping-modal');
const deleteModal = document.getElementById('delete-modal');
const scannerModal = document.getElementById('scanner-modal');
const settingsPanel = document.getElementById('settings-panel');
const itemForm = document.getElementById('item-form');
const addItemBtn = document.getElementById('add-item-btn');
const toggleListBtn = document.getElementById('toggle-list-btn');
const settingsBtn = document.getElementById('settings-btn');

// ====== Theme System ======

/**
 * Initialize theme based on system preference or saved preference
 */
function initTheme() {
    const savedTheme = localStorage.getItem('theme-preference') || 'auto';
    applyTheme(savedTheme);
    updateThemeButtons(savedTheme);
}

/**
 * Apply the selected theme
 */
function applyTheme(preference) {
    const body = document.body;

    if (preference === 'auto') {
        // Use system preference
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        body.classList.toggle('light-mode', !prefersDark);
    } else if (preference === 'light') {
        body.classList.add('light-mode');
    } else {
        body.classList.remove('light-mode');
    }

    localStorage.setItem('theme-preference', preference);
}

/**
 * Update theme button states
 */
function updateThemeButtons(activeTheme) {
    document.querySelectorAll('.segment-btn[data-theme]').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.theme === activeTheme);
    });
}

// Listen for system theme changes
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    const savedTheme = localStorage.getItem('theme-preference');
    if (savedTheme === 'auto') {
        applyTheme('auto');
    }
});

// ====== Smart Increment Logic ======

/**
 * Get increment step based on unit type
 * Discrete units (un, pacotes) = 1
 * Continuous units (kg, g, ml) = 0.5
 */
function getIncrementStep(unit) {
    const discreteUnits = ['un', 'pacotes', 'l'];
    return discreteUnits.includes(unit.toLowerCase()) ? 1 : 0.5;
}

// ====== API Functions ======

async function fetchItems() {
    try {
        const response = await fetchWithAuth(`${API_URL}/items`);
        if (!response) return;
        items = await response.json();
    } catch (err) {
        console.error("Erro ao buscar itens:", err);
        showToast("Erro ao carregar itens", "error");
    }
}

async function fetchCategories() {
    try {
        const response = await fetchWithAuth(`${API_URL}/categories`);
        if (!response) return;
        categories = await response.json();

        // Populate select in form
        const select = document.getElementById('category');
        select.innerHTML = categories.map(c => `<option value="${c.id}">${c.icon} ${c.name}</option>`).join('');
    } catch (err) {
        console.error("Erro ao buscar categorias:", err);
    }
}

async function fetchShoppingList() {
    try {
        const response = await fetchWithAuth(`${API_URL}/shopping-list`);
        if (!response) return;
        shoppingList = await response.json();
        renderShoppingList();
    } catch (err) {
        console.error("Erro ao buscar lista de compras:", err);
    }
}

async function fetchPrediction(itemId) {
    try {
        const response = await fetchWithAuth(`${API_URL}/items/${itemId}/purchase-prediction`);
        if (!response) return null;
        return await response.json();
    } catch (err) {
        console.error("Erro ao buscar previsão:", err);
        return null;
    }
}

// ====== Rendering Functions ======

function renderItems() {
    let filteredItems = selectedCategoryId
        ? items.filter(i => i.category_id == selectedCategoryId)
        : items;

    if (filteredItems.length === 0) {
        itemsGrid.innerHTML = `
            <div class="empty-state" style="grid-column: 1/-1; text-align: center; padding: 60px 20px;">
                <div style="font-size: 4rem; margin-bottom: 20px;">📦</div>
                <h3 style="color: var(--text-secondary); margin-bottom: 10px;">${t('msg_empty_items')}</h3>
                <p style="color: var(--text-muted);">${t('msg_click_to_add')}</p>
            </div>
        `;
        return;
    }

    itemsGrid.innerHTML = filteredItems.map(item => {
        const percent = Math.min((item.current_quantity / item.minimum_quantity) * 100, 100);
        let colorVar = '--accent-green';
        let urgency = 'ok';

        if (item.current_quantity < item.minimum_quantity && item.current_quantity > 0) {
            colorVar = '--accent-yellow';
            urgency = 'attention';
        }
        if (item.current_quantity <= 0) {
            colorVar = '--accent-red';
            urgency = 'critical';
        }

        const step = getIncrementStep(item.unit);
        const difficultyLabel = item.acquisition_difficulty === 0 ? t('difficulty_easy') :
            item.acquisition_difficulty === 5 ? t('difficulty_medium') : t('difficulty_hard');

        return `
            <div class="item-card" data-id="${item.id}">
                <span class="item-badge">${item.category?.icon || '📦'}</span>
                <div class="item-title">${item.name}</div>
                <span class="item-category">${item.category?.name || 'Sem categoria'}</span>
                
                <div class="quantity-control">
                    <button class="q-btn" onclick="updateQuantity(${item.id}, -${step})">−</button>
                    <span class="q-value">${formatQuantity(item.current_quantity)} ${item.unit}</span>
                    <button class="q-btn" onclick="updateQuantity(${item.id}, ${step})">+</button>
                </div>

                <label style="color: var(--text-muted); font-size: 0.8rem;">${t('label_min_qty')}: ${formatQuantity(item.minimum_quantity)} ${item.unit}</label>
                <div class="progress-container">
                    <div class="progress-bar" style="width: ${percent}%; background: var(${colorVar})"></div>
                </div>
                
                <div class="prediction-badge ${urgency}" id="prediction-${item.id}">
                    ${item.current_quantity <= 0 ? `⚡ ${t('status_no_stock')}` :
                (urgency === 'ok' ? `✓ ${t('section_stock')}` :
                    urgency === 'attention' ? `⚠ ${t('section_attention')}` : `⚡ ${t('section_critical')}`)} 
                    · ${difficultyLabel}
                </div>
                
                <div class="item-actions">
                    <button onclick="confirmDelete(${item.id}, '${escapeHtml(item.name)}')" class="btn-delete" title="Excluir item">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
                    <button onclick="editItem(${item.id})" class="btn-secondary w-100">Editar</button>
                </div>
            </div>
        `;
    }).join('');

    // Load predictions for items
    loadPredictions(filteredItems);
}

async function loadPredictions(items) {
    for (const item of items) {
        const prediction = await fetchPrediction(item.id);
        if (prediction) {
            const badge = document.getElementById(`prediction-${item.id}`);
            if (badge) {
                if (prediction.needs_tracking) {
                    badge.className = 'prediction-badge learning';
                    badge.innerHTML = `📊 ${t('status_learning')}`;
                } else if (item.current_quantity <= 0) {
                    badge.className = 'prediction-badge critical';
                    badge.innerHTML = `⚡ ${t('status_no_stock')}`;
                } else if (prediction.days_remaining < 999) {
                    const daysText = prediction.days_remaining <= 0
                        ? t('status_no_stock')
                        : `${Math.round(prediction.days_remaining)} ${t('text_days_remaining')}`;
                    badge.className = `prediction-badge ${prediction.urgency}`;
                    badge.innerHTML = `${prediction.urgency === 'critical' ? '⚡' : prediction.urgency === 'attention' ? '⚠' : '✓'} ${daysText}`;
                }
            }
        }
    }
}

function formatQuantity(qty) {
    return Number.isInteger(qty) ? qty : qty.toFixed(1);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function renderCategories() {
    categoriesList.innerHTML = `
        <div class="category-chip ${!selectedCategoryId ? 'active' : ''}" onclick="filterByCategory(null)">Todos</div>
    ` + categories.map(c => `
        <div class="category-chip ${selectedCategoryId == c.id ? 'active' : ''}" onclick="filterByCategory(${c.id})">
            ${c.icon} ${c.name}
        </div>
    `).join('');
}

function renderShoppingList() {
    const listContent = document.getElementById('shopping-list-content');

    if (shoppingList.length === 0) {
        listContent.innerHTML = `
            <div style="text-align: center; padding: 40px 20px;">
                <div style="font-size: 3rem; margin-bottom: 16px;">🎉</div>
                <p style="color: var(--text-secondary);">${t('msg_empty_list')}</p>
            </div>
        `;
        return;
    }

    listContent.innerHTML = shoppingList.map(item => `
        <div class="shopping-item ${item.urgency}">
            <div>
                <strong>${item.name}</strong>
                <small>
                    Faltam: ${formatQuantity(item.needed)} ${item.unit} (Mín: ${item.minimum_quantity})
                    ${item.days_remaining ? ` · ~${Math.round(item.days_remaining)} dias` : ''}
                </small>
            </div>
            <div class="urgency-badge">
                ${item.urgency === 'critical' ? '🔴 Faltando' : '⚠️ Baixo'}
            </div>
        </div>
    `).join('');
}

function updateStats() {
    const critical = items.filter(i => i.current_quantity <= 0).length;
    const attention = items.filter(i => i.current_quantity < i.minimum_quantity && i.current_quantity > 0).length;
    const ok = items.filter(i => i.current_quantity >= i.minimum_quantity).length;

    document.querySelector('#stat-ok .stat-value').innerText = ok;
    document.querySelector('#stat-attention .stat-value').innerText = attention;
    document.querySelector('#stat-critical .stat-value').innerText = critical;
}

// ====== Actions ======

function filterByCategory(id) {
    selectedCategoryId = id;
    renderCategories();
    renderItems();
}

async function updateQuantity(id, delta) {
    const item = items.find(i => i.id === id);
    if (!item) return;

    const newQty = Math.max(0, item.current_quantity + delta);

    // Optimistic update
    item.current_quantity = newQty;

    // Don't re-render full items grid to keep UI stable during clicks
    // Just update specific element if possible or simple re-render
    renderItems();
    updateStats();

    // Check for low stock toast
    if (newQty <= item.minimum_quantity && (item.current_quantity + delta) > item.minimum_quantity) {
        showToast(t('toast_low_stock', { name: item.name }), 'warning');
    }

    try {
        const response = await fetchWithAuth(`${API_URL}/items/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ current_quantity: newQty })
        });

        if (response.ok) {
            const updated = await response.json();
            items = items.map(i => i.id === id ? updated : i);
            // Silent refresh - no visible update needed
        } else {
            // Revert on error
            await fetchItems();
            renderItems();
            updateStats();
        }
    } catch (err) {
        console.error("Erro ao atualizar quantidade:", err);
        // Revert on error
        await fetchItems();
        renderItems();
        updateStats();
    }
}

// ====== Delete Functionality ======

function confirmDelete(id, name) {
    itemToDelete = id;
    document.getElementById('delete-item-name').textContent = name;

    // Update modal text dynamically
    const container = document.querySelector('.delete-confirm-content');
    const p = container.querySelector('p');
    if (p) {
        // We reconstruct the message because the structure uses a strong tag in the middle
        p.innerHTML = t('modal_delete_text', { name: `<strong id="delete-item-name">${name}</strong>` });
    }

    deleteModal.classList.add('active');
}

async function executeDelete() {
    if (!itemToDelete) return;

    try {
        const response = await fetchWithAuth(`${API_URL}/items/${itemToDelete}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            items = items.filter(i => i.id !== itemToDelete);
            renderItems();
            updateStats();
            showToast(t('toast_item_deleted'), "success");
        } else {
            showToast(t('toast_error_delete'), "error");
        }
    } catch (err) {
        console.error("Erro ao deletar item:", err);
        showToast("Erro ao remover item", "error");
    }

    closeDeleteModal();
}

function closeDeleteModal() {
    itemToDelete = null;
    deleteModal.classList.remove('active');
}

// ====== Modal Logic ======

addItemBtn.onclick = () => {
    document.getElementById('modal-title').innerText = t('modal_new_item');
    itemForm.reset();
    document.getElementById('item-id').value = '';
    // Reset difficulty to Easy
    document.querySelector('input[name="difficulty"][value="0"]').checked = true;
    itemModal.classList.add('active');
};

toggleListBtn.onclick = () => {
    fetchShoppingList();
    shoppingModal.classList.add('active');
};

settingsBtn.onclick = () => {
    settingsPanel.classList.add('active');
};

// Close handlers
document.querySelectorAll('.close-btn').forEach(btn => {
    btn.onclick = (e) => {
        const modal = e.target.closest('.modal');
        if (modal) {
            // If closing scanner modal, properly stop the camera and reopen item modal
            if (modal.id === 'scanner-modal') {
                stopScanner();
                itemModal.classList.add('active'); // Reopen item modal like Cancelar does
            } else {
                modal.classList.remove('active');
            }
        }

        const panel = e.target.closest('.side-panel');
        if (panel) panel.classList.remove('active');
    };
});

document.getElementById('close-settings').onclick = () => {
    settingsPanel.classList.remove('active');
};

document.querySelector('.side-panel-overlay')?.addEventListener('click', () => {
    settingsPanel.classList.remove('active');
});

window.onclick = (event) => {
    if (event.target.classList.contains('modal')) {
        // Prevent closing item modal on outside click to avoid data loss
        if (event.target.id === 'item-modal') {
            return;
        }

        event.target.classList.remove('active');
        if (event.target === scannerModal) {
            stopScanner();
            itemModal.classList.add('active');
        }
    }
};

// Delete modal buttons
document.getElementById('cancel-delete-btn').onclick = closeDeleteModal;
document.getElementById('confirm-delete-btn').onclick = executeDelete;

// Theme buttons
document.querySelectorAll('.segment-btn').forEach(btn => {
    btn.onclick = (e) => {
        // Handle click on SVG or span inside button
        const targetBtn = e.target.closest('.segment-btn');
        if (!targetBtn || !targetBtn.dataset.theme) return;

        const theme = targetBtn.dataset.theme;
        applyTheme(theme);
        updateThemeButtons(theme);
    };
});

// ====== Form Submission ======

itemForm.onsubmit = async (e) => {
    e.preventDefault();
    const itemId = document.getElementById('item-id').value;

    const difficultyInput = document.querySelector('input[name="difficulty"]:checked');
    const usageRateInput = document.getElementById('usage_rate');

    const data = {
        name: document.getElementById('name').value,
        category_id: parseInt(document.getElementById('category').value),
        unit: document.getElementById('unit').value,
        current_quantity: parseFloat(document.getElementById('current_quantity').value),
        minimum_quantity: parseFloat(document.getElementById('minimum_quantity').value),
        notes: document.getElementById('notes').value,
        acquisition_difficulty: parseInt(difficultyInput?.value || 0),
        usage_period: document.getElementById('usage_period').value
    };

    // Only include usage_rate if provided
    if (usageRateInput.value) {
        data.usage_rate = parseFloat(usageRateInput.value);
    }

    try {
        let response;
        if (itemId) {
            response = await fetchWithAuth(`${API_URL}/items/${itemId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        } else {
            response = await fetchWithAuth(`${API_URL}/items`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        }

        if (response.ok) {
            await fetchItems();
            renderItems();
            updateStats();
            itemModal.classList.remove('active');
            showToast(itemId ? t('toast_item_updated') : t('toast_item_added'), "success");
        } else {
            showToast(t('toast_error_save'), "error");
        }
    } catch (err) {
        console.error("Erro ao salvar item:", err);
        showToast(t('toast_error_save'), "error");
    }
};

function editItem(id) {
    const item = items.find(i => i.id === id);
    if (!item) return;

    document.getElementById('modal-title').innerText = t('modal_edit_item');
    document.getElementById('item-id').value = item.id;
    document.getElementById('name').value = item.name;
    document.getElementById('category').value = item.category_id;
    document.getElementById('unit').value = item.unit;
    document.getElementById('current_quantity').value = item.current_quantity;
    document.getElementById('minimum_quantity').value = item.minimum_quantity;
    document.getElementById('notes').value = item.notes || '';

    // Set difficulty
    const diffValue = item.acquisition_difficulty || 0;
    const diffInput = document.querySelector(`input[name="difficulty"][value="${diffValue}"]`);
    if (diffInput) diffInput.checked = true;

    // Set usage rate
    document.getElementById('usage_rate').value = item.usage_rate || '';
    document.getElementById('usage_period').value = item.usage_period || 'daily';

    itemModal.classList.add('active');
}

// ====== Barcode Scanner ======

document.getElementById('scan-barcode-btn').onclick = () => {
    startScanner();
};

async function startScanner() {
    try {
        itemModal.classList.remove('active');
        scannerModal.classList.add('active');

        const video = document.getElementById('scanner-video');
        videoStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment' }
        });
        video.srcObject = videoStream;

        updateScannerStatus('', '');
    } catch (err) {
        console.error("Erro ao acessar câmera:", err);
        updateScannerStatus('Erro ao acessar câmera. Verifique as permissões.', 'error');
    }
}

function stopScanner() {
    // Stop all video tracks
    if (videoStream) {
        videoStream.getTracks().forEach(track => {
            track.stop();
        });
        videoStream = null;
    }

    // Clear the video element's source
    const video = document.getElementById('scanner-video');
    if (video) {
        video.srcObject = null;
        video.load(); // Reset the video element
    }

    // Clear scanner status
    updateScannerStatus('', '');

    // Close the modal
    scannerModal.classList.remove('active');
}

document.getElementById('cancel-scan-btn').onclick = () => {
    stopScanner();
    itemModal.classList.add('active');
};

document.getElementById('capture-btn').onclick = async () => {
    const video = document.getElementById('scanner-video');
    const canvas = document.getElementById('scanner-canvas');
    const ctx = canvas.getContext('2d');

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);

    const imageData = canvas.toDataURL('image/jpeg', 0.8);
    const base64Data = imageData.split(',')[1];

    updateScannerStatus(t('status_identifying'), 'loading');

    try {
        const response = await fetchWithAuth(`${API_URL}/barcode/identify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image_base64: base64Data })
        });

        const result = await response.json();

        if (result.success) {
            updateScannerStatus(t('status_success', { name: result.product_name }), 'success');

            // Auto-fill form
            setTimeout(() => {
                stopScanner();

                document.getElementById('name').value = result.product_name || '';

                // Find matching category
                if (result.suggested_category) {
                    const categoryMatch = categories.find(c =>
                        c.name.toLowerCase() === result.suggested_category.toLowerCase()
                    );
                    if (categoryMatch) {
                        document.getElementById('category').value = categoryMatch.id;
                    }
                }

                if (result.suggested_unit) {
                    document.getElementById('unit').value = result.suggested_unit;
                }

                itemModal.classList.add('active');
            }, 1500);
        } else {
            updateScannerStatus(result.error || t('status_error'), 'error');
        }
    } catch (err) {
        console.error("Erro ao identificar produto:", err);
        updateScannerStatus(t('status_error'), 'error');
    }
};

function updateScannerStatus(message, type) {
    const status = document.getElementById('scanner-status');
    status.textContent = message;
    status.className = 'scanner-status';
    if (type) status.classList.add(type);
}

// ====== Shopping List ======

document.getElementById('copy-list-btn').onclick = () => {
    const text = shoppingList.map(i => `- ${i.name}: ${formatQuantity(i.needed)} ${i.unit}`).join('\n');
    navigator.clipboard.writeText(`${t('modal_shopping_list')}:\n\n${text}`);
    showToast(t('toast_list_copied'), 'success');
};

// ====== Toast Notifications ======

function showToast(message, type = 'info') {
    // Remove existing toasts
    document.querySelectorAll('.toast').forEach(t => t.remove());

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span>${type === 'success' ? '✓' : type === 'error' ? '✕' : type === 'warning' ? '⚠' : 'ℹ'}</span>
        <span>${message}</span>
    `;

    // Add toast styles if not present
    if (!document.getElementById('toast-styles')) {
        const style = document.createElement('style');
        style.id = 'toast-styles';
        style.textContent = `
            .toast {
                position: fixed;
                bottom: 24px;
                left: 50%;
                transform: translateX(-50%);
                padding: 14px 24px;
                border-radius: var(--radius-lg);
                background: var(--bg-secondary);
                color: var(--text-primary);
                box-shadow: var(--shadow-lg);
                display: flex;
                align-items: center;
                gap: 10px;
                z-index: 10000;
                animation: toastSlide 0.3s ease;
                border: 1px solid var(--border-light);
            }
            .toast-success { border-color: var(--accent-green); }
            .toast-success span:first-child { color: var(--accent-green); }
            .toast-error { border-color: var(--accent-red); }
            .toast-error span:first-child { color: var(--accent-red); }
            .toast-warning { border-color: var(--accent-yellow); }
            .toast-warning span:first-child { color: var(--accent-yellow); }
            @keyframes toastSlide {
                from { transform: translateX(-50%) translateY(20px); opacity: 0; }
                to { transform: translateX(-50%) translateY(0); opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    }

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(-50%) translateY(20px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ====== Settings Persistence ======

function loadSettings() {
    // Load notification settings
    const notifyLowStock = localStorage.getItem('notify-low-stock') !== 'false';
    const notifyReminders = localStorage.getItem('notify-reminders') !== 'false';
    document.getElementById('notify-low-stock').checked = notifyLowStock;
    document.getElementById('notify-reminders').checked = notifyReminders;
}

function saveSettings() {
    localStorage.setItem('notify-low-stock', document.getElementById('notify-low-stock').checked);
    localStorage.setItem('notify-reminders', document.getElementById('notify-reminders').checked);
}

// Settings change handlers
// API key handler removed
document.getElementById('notify-low-stock')?.addEventListener('change', saveSettings);
document.getElementById('notify-reminders')?.addEventListener('change', saveSettings);

// ====== Initialization ======

async function init() {
    await loadUserProfile(); // Load profile first to get prefs

    // Fallback or Apply Prefs
    if (currentUser) {
        if (currentUser.language_preference) currentLang = currentUser.language_preference;
        if (currentUser.theme_preference) applyTheme(currentUser.theme_preference);
    } else {
        initTheme(); // Default auto
    }

    await loadTranslations(currentLang);
    loadSettings();
    setupEventListeners(); // Attach new listeners

    await Promise.all([fetchCategories(), fetchItems()]);
    renderCategories();
    renderItems();
    updateStats();
}

// Start the application
// === User Profile Functions ===
async function loadUserProfile() {
    const response = await fetchWithAuth(`${API_URL}/users/me`);
    if (response && response.ok) {
        currentUser = await response.json();
    }
}

async function updateUserProfile(profileData) {
    const response = await fetchWithAuth(`${API_URL}/users/me`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profileData)
    });

    if (response && response.ok) {
        currentUser = await response.json();

        // Apply new preferences immediately
        if (profileData.language_preference) {
            currentLang = profileData.language_preference;
            loadTranslations(currentLang);
        }
        if (profileData.theme_preference) {
            applyTheme(profileData.theme_preference);
        }

        showToast('Perfil atualizado com sucesso!', 'success');
        return true;
    } else {
        showToast('Erro ao atualizar perfil', 'error');
        return false;
    }
}

function applyTheme(theme) {
    const body = document.body;
    body.classList.remove('light-mode', 'dark-mode');

    if (theme === 'system' || theme === 'auto') {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
            body.classList.add('light-mode');
        }
    } else if (theme === 'light') {
        body.classList.add('light-mode');
    } else if (theme === 'dark') {
        body.classList.add('dark-mode');
    }

    localStorage.setItem('theme-preference', theme);
    updateThemeButtons(theme);
}

// === Category Management ===
async function createCategory(categoryData) {
    const response = await fetchWithAuth(`${API_URL}/categories`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(categoryData)
    });

    if (response && response.ok) {
        await fetchCategories(); // Reload list
        renderCategories();
        return await response.json();
    } else {
        const err = await response.json();
        alert(err.detail || 'Erro ao criar categoria');
        return null;
    }
}

// === Sharing ===
function shareShoppingList(items) {
    if (!items || items.length === 0) return;

    const title = currentLang === 'pt-BR' ? 'Lista de Compras 🏠' : 'Shopping List 🏠';
    let text = '';

    items.forEach(item => {
        const checkbox = item.urgency === 'critical' ? '🔴' : '🟡';
        text += `${checkbox} ${item.name} (${item.needed} ${item.unit})\n`;
    });

    text += `\nShared via AInventory`;

    if (navigator.share) {
        navigator.share({
            title: title,
            text: text
        }).catch(err => console.log('Error sharing:', err));
    } else {
        // Fallback to clipboard
        navigator.clipboard.writeText(text).then(() => {
            showToast(t('msg_list_copied'), 'success');
        });
    }
}

// === Event Listeners Setup (New) ===
function setupEventListeners() {
    // Profile & Settings
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.removeItem('access_token');
            window.location.href = 'login.html';
        });
    }

    const editProfileBtn = document.getElementById('edit-profile-btn');
    if (editProfileBtn) {
        editProfileBtn.addEventListener('click', () => {
            if (currentUser) {
                if (document.getElementById('profile-name')) document.getElementById('profile-name').value = currentUser.display_name || '';
                if (document.getElementById('profile-phone')) document.getElementById('profile-phone').value = currentUser.phone_number || '';
            }
            settingsPanel.classList.remove('active');
            document.getElementById('profile-modal').classList.add('active');
        });
    }

    const profileForm = document.getElementById('profile-form');
    if (profileForm) {
        profileForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                display_name: document.getElementById('profile-name').value,
                phone_number: document.getElementById('profile-phone').value,
            };
            const pw = document.getElementById('profile-password').value;
            if (pw) data.password = pw;

            const success = await updateUserProfile(data);
            if (success) {
                document.getElementById('profile-modal').classList.remove('active');
            }
        });
    }

    // Theme & Lang Persistence (Augment existing logic)
    // We already have listeners for changes, we just need to Add the PUT call
    // Logic: Listener below captures the click and applies theme. We add another listener to save to DB.

    document.querySelectorAll('[data-theme]').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            if (!currentUser) return;
            // Get theme from the closest button (in case click on icon)
            const target = e.target.closest('[data-theme]');
            if (!target) return;
            const theme = target.dataset.theme;

            await fetchWithAuth(`${API_URL}/users/me`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ theme_preference: theme })
            });
        });
    });

    document.querySelectorAll('[data-lang]').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const target = e.target.closest('[data-lang]');
            if (!target) return;
            const lang = target.dataset.lang;

            // Apply translations immediately
            await loadTranslations(lang);

            // Save preference to DB if logged in
            if (currentUser) {
                await fetchWithAuth(`${API_URL}/users/me`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ language_preference: lang })
                });
            }
        });
    });

    // Category
    const addCatBtn = document.getElementById('add-category-btn');
    if (addCatBtn) {
        addCatBtn.addEventListener('click', () => {
            document.getElementById('category-form').reset();
            document.getElementById('category-modal').classList.add('active');
        });
    }

    const catForm = document.getElementById('category-form');
    if (catForm) {
        catForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                name: document.getElementById('cat-name').value,
                icon: document.getElementById('cat-icon').value,
                color: document.getElementById('cat-color').value
            };
            const newCat = await createCategory(data);
            if (newCat) {
                document.getElementById('category-modal').classList.remove('active');
            }
        });
    }

    // Share List
    const shareBtn = document.getElementById('share-list-btn');
    if (shareBtn) {
        shareBtn.addEventListener('click', async () => {
            await fetchShoppingList(); // Refresh list first
            shareShoppingList(shoppingList);
        });
    }

    // API Token Copy
    const copyTokenBtn = document.getElementById('copy-token-btn');
    if (copyTokenBtn) {
        copyTokenBtn.addEventListener('click', () => {
            const token = localStorage.getItem('access_token');
            if (token) {
                navigator.clipboard.writeText(token);
                showToast(t('toast_token_copied'), 'success');
            }
        });
    }

    // Emoji Picker
    initEmojiPicker();
}

// ====== Emoji Picker ======

let currentEmojiCategory = 'food_drink';

function initEmojiPicker() {
    const trigger = document.getElementById('emoji-picker-trigger');
    const modal = document.getElementById('emoji-picker-modal');
    const closeBtn = document.getElementById('close-emoji-picker');
    const searchInput = document.getElementById('emoji-search');

    if (!trigger || !modal) return;

    // Open picker
    trigger.addEventListener('click', () => {
        modal.classList.add('active');
        renderEmojiCategories();
        renderEmojis(currentEmojiCategory);
        searchInput?.focus();
    });

    // Close picker
    closeBtn?.addEventListener('click', () => {
        modal.classList.remove('active');
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });

    // Search
    searchInput?.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        if (query) {
            renderSearchResults(query);
        } else {
            renderEmojis(currentEmojiCategory);
        }
    });
}

function renderEmojiCategories() {
    const container = document.getElementById('emoji-categories');
    if (!container || typeof EMOJI_DATA === 'undefined') return;

    const categories = Object.entries(EMOJI_DATA).filter(([key, cat]) => cat.emojis?.length > 0 || key === 'frequently_used');

    container.innerHTML = categories.map(([key, cat]) => {
        const label = cat.label?.[currentLang] || cat.label?.['en-US'] || key;
        return `<button class="emoji-category-btn ${key === currentEmojiCategory ? 'active' : ''}" data-category="${key}">${label}</button>`;
    }).join('');

    // Add click handlers
    container.querySelectorAll('.emoji-category-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            currentEmojiCategory = btn.dataset.category;
            container.querySelectorAll('.emoji-category-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            renderEmojis(currentEmojiCategory);
        });
    });
}

function renderEmojis(categoryKey) {
    const container = document.getElementById('emoji-grid-container');
    if (!container || typeof EMOJI_DATA === 'undefined') return;

    const category = EMOJI_DATA[categoryKey];
    if (!category) return;

    const label = category.label?.[currentLang] || category.label?.['en-US'] || categoryKey;
    const emojis = category.emojis || [];

    if (emojis.length === 0) {
        container.innerHTML = `<div class="emoji-grid-section"><p style="color: var(--text-muted); text-align: center; padding: 20px;">No emojis in this category</p></div>`;
        return;
    }

    container.innerHTML = `
        <div class="emoji-grid-section">
            <div class="emoji-grid-label">${label}</div>
            <div class="emoji-grid">
                ${emojis.map(emoji => `<button class="emoji-btn" data-emoji="${emoji}">${emoji}</button>`).join('')}
            </div>
        </div>
    `;

    // Add click handlers
    container.querySelectorAll('.emoji-btn').forEach(btn => {
        btn.addEventListener('click', () => selectEmoji(btn.dataset.emoji));
    });
}

function renderSearchResults(query) {
    const container = document.getElementById('emoji-grid-container');
    if (!container || typeof EMOJI_DATA === 'undefined') return;

    // Simple search across all categories
    const allEmojis = [];
    Object.values(EMOJI_DATA).forEach(cat => {
        if (cat.emojis) allEmojis.push(...cat.emojis);
    });

    // For now, just show all emojis (real search would need emoji names/keywords)
    const searchLabel = currentLang.startsWith('pt') ? 'Resultados' : 'Results';

    container.innerHTML = `
        <div class="emoji-grid-section">
            <div class="emoji-grid-label">${searchLabel}</div>
            <div class="emoji-grid">
                ${allEmojis.slice(0, 64).map(emoji => `<button class="emoji-btn" data-emoji="${emoji}">${emoji}</button>`).join('')}
            </div>
        </div>
    `;

    container.querySelectorAll('.emoji-btn').forEach(btn => {
        btn.addEventListener('click', () => selectEmoji(btn.dataset.emoji));
    });
}

function selectEmoji(emoji) {
    // Update the hidden input and preview
    const input = document.getElementById('cat-icon');
    const preview = document.getElementById('cat-icon-preview');

    if (input) input.value = emoji;
    if (preview) preview.textContent = emoji;

    // Add to frequently used
    if (typeof addToFrequentlyUsed === 'function') {
        addToFrequentlyUsed(emoji);
    }

    // Close modal
    document.getElementById('emoji-picker-modal')?.classList.remove('active');
}

init();


