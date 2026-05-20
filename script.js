// Global state
let currentPage = 'dashboard';
let medicines = [];
let customers = [];
let transactions = [];
let notifications = [];

// API helper function
async function apiCall(endpoint, method = 'GET', data = null) {
    try {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(/api${endpoint}, options);
        
        if (!response.ok) {
            throw new Error(HTTP error! status: ${response.status});
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        showToast('API call failed: ' + error.message, 'error');
        throw error;
    }
}

// Toast notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toast-message');
    
    toastMessage.textContent = message;
    toast.className = toast ${type};
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Modal functions
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.add('show');
}

function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.remove('show');
}

// Navigation
function switchPage(pageName) {
    // Update navigation
    // ===== navigation click handler (TOP) =====
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', e => {
        e.preventDefault();
        const pageName = link.getAttribute('data-page');
        switchPage(pageName);
    });
});

function switchPage(pageName) {
    // Remove active class from all nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });

    // Add active to clicked link
    document.querySelectorAll(`[data-page="${pageName}"]`).forEach(link => {
        link.classList.add('active');
    });

    // Show selected page, hide others
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
        if (page.id === pageName + '-page') {
            page.classList.add('active');
        }
    });
}

    // Update header title
    const pageTitle = document.getElementById('page-title');
    pageTitle.textContent = pageName.charAt(0).toUpperCase() + pageName.slice(1);

    // Hide all header buttons
    document.querySelectorAll('.header-actions button').forEach(btn => {
        btn.style.display = 'none';
    });

    // Show specific buttons per page
    if (pageName === 'billing') {
        document.getElementById('new-sale-btn').style.display = 'inline-flex';
    } else if (pageName === 'inventory') {
        document.getElementById('add-medicine-btn').style.display = 'inline-flex';
    } else if (pageName === 'customers') {
        document.getElementById('add-customer-btn').style.display = 'inline-flex';
    }
}
    
    currentPage = pageName;
    
    // Load page data
    loadPageData();
}

// Load page specific data
async function loadPageData() {
    try {
        switch(currentPage) {
            case 'dashboard':
                await loadDashboardData();
                break;
            case 'inventory':
                await loadMedicines();
                break;
            case 'billing':
                await loadTransactions();
                break;
            case 'customers':
                await loadCustomers();
                break;
            case 'notifications':
                await loadNotifications();
                break;
            case 'reports':
                await loadReports();
                break;
        }
    } catch (error) {
        console.error(Error loading ${currentPage} data:, error);
    }
}

// Dashboard functions
async function loadDashboardData() {
    try {
        const stats = await apiCall('/dashboard/stats');
        
        document.getElementById('total-medicines').textContent = stats.totalMedicines;
        document.getElementById('low-stock-items').textContent = stats.lowStockItems;
        document.getElementById('total-customers').textContent = stats.totalCustomers;
        document.getElementById('todays-sales').textContent = $${stats.todaysSales.toFixed(2)};
        
        // Load recent transactions
        const recentTransactions = await apiCall('/transactions');
        renderRecentTransactions(recentTransactions.slice(0, 5));
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

function renderRecentTransactions(transactionsList) {
    const tbody = document.querySelector('#recent-transactions-table tbody');
    tbody.innerHTML = '';
    
    if (transactionsList.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #6b7280;">No recent transactions</td></tr>';
        return;
    }
    
    transactionsList.forEach(transaction => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${transaction.customer_name || 'N/A'}</td>
            <td>${transaction.medicine_name || 'N/A'}</td>
            <td>${transaction.quantity}</td>
            <td>$${parseFloat(transaction.total_amount).toFixed(2)}</td>
            <td>${new Date(transaction.created_at).toLocaleDateString()}</td>
            <td><span class="status-badge status-success">${transaction.status}</span></td>
        `;
        tbody.appendChild(row);
    });
}

// Inventory functions
async function loadMedicines() {
    try {
        medicines = await apiCall('/medicines');
        renderMedicinesTable();
    } catch (error) {
        console.error('Error loading medicines:', error);
    }
}

function renderMedicinesTable() {
    const tbody = document.querySelector('#medicines-table tbody');
    tbody.innerHTML = '';
    
    medicines.forEach(medicine => {
        const row = document.createElement('tr');
        const isLowStock = medicine.current_stock <= medicine.min_stock_level;
        const isExpiringSoon = new Date(medicine.expiry_date) <= new Date(Date.now() + 30 * 24 * 60 * 60 * 1000); // 30 days
        
        let statusClass = 'status-success';
        let statusText = 'In Stock';
        
        if (isLowStock) {
            statusClass = 'status-warning';
            statusText = 'Low Stock';
        }
        if (isExpiringSoon) {
            statusClass = 'status-danger';
            statusText = 'Expiring Soon';
        }
        
        row.innerHTML = `
            <td>${medicine.name}</td>
            <td>${medicine.manufacturer}</td>
            <td>${medicine.category}</td>
            <td>${medicine.current_stock}</td>
            <td>$${parseFloat(medicine.price_per_unit).toFixed(2)}</td>
            <td>${new Date(medicine.expiry_date).toLocaleDateString()}</td>
            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
        `;
        tbody.appendChild(row);
    });
}

// Transaction functions
async function loadTransactions() {
    try {
        transactions = await apiCall('/transactions');
        renderTransactionsTable();
        
        // Also load medicines and customers for new sale modal
        if (medicines.length === 0) {
            medicines = await apiCall('/medicines');
        }
        if (customers.length === 0) {
            customers = await apiCall('/customers');
        }
        populateMedicineSelect();
    } catch (error) {
        console.error('Error loading transactions:', error);
    }
}

function renderTransactionsTable() {
    const tbody = document.querySelector('#transactions-table tbody');
    tbody.innerHTML = '';
    
    transactions.forEach(transaction => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${transaction.customer_name || 'N/A'}</td>
            <td>${transaction.medicine_name || 'N/A'}</td>
            <td>${transaction.quantity}</td>
            <td>$${parseFloat(transaction.unit_price).toFixed(2)}</td>
            <td>$${parseFloat(transaction.total_amount).toFixed(2)}</td>
            <td>${new Date(transaction.created_at).toLocaleDateString()}</td>
            <td><span class="status-badge ${transaction.sms_notification_sent ? 'status-success' : 'status-warning'}">${transaction.sms_notification_sent ? 'Sent' : 'Pending'}</span></td>
        `;
        tbody.appendChild(row);
    });
}

function populateMedicineSelect() {
    const medicineSelect = document.getElementById('medicine-select');
    medicineSelect.innerHTML = '<option value="">Select Medicine</option>';
    
    medicines.forEach(medicine => {
        if (medicine.current_stock > 0) {
            const option = document.createElement('option');
            option.value = medicine.id;
            option.textContent = ${medicine.name} - $${medicine.price_per_unit} (Stock: ${medicine.current_stock});
            option.setAttribute('data-price', medicine.price_per_unit);
            option.setAttribute('data-stock', medicine.current_stock);
            medicineSelect.appendChild(option);
        }
    });
}

// Customer functions
async function loadCustomers() {
    try {
        customers = await apiCall('/customers');
        renderCustomersTable();
    } catch (error) {
        console.error('Error loading customers:', error);
    }
}

function renderCustomersTable() {
    const tbody = document.querySelector('#customers-table tbody');
    tbody.innerHTML = '';
    
    customers.forEach(customer => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${customer.name}</td>
            <td>${customer.phone}</td>
            <td>${customer.email || 'N/A'}</td>
            <td>${customer.address || 'N/A'}</td>
            <td>${new Date(customer.created_at).toLocaleDateString()}</td>
        `;
        tbody.appendChild(row);
    });
}

// Notification functions
async function loadNotifications() {
    try {
        notifications = await apiCall('/notifications');
        renderNotificationsTable();
    } catch (error) {
        console.error('Error loading notifications:', error);
    }
}

function renderNotificationsTable() {
    const tbody = document.querySelector('#notifications-table tbody');
    tbody.innerHTML = '';
    
    notifications.forEach(notification => {
        const row = document.createElement('tr');
        const typeIcon = notification.type === 'sms' ? 'fas fa-sms' : 'fas fa-phone';
        const statusClass = notification.status === 'sent' ? 'status-success' : 'status-warning';
        
        row.innerHTML = `
            <td><i class="${typeIcon}"></i> ${notification.type.toUpperCase()}</td>
            <td>${notification.customer_name || 'N/A'}</td>
            <td>${notification.message}</td>
            <td><span class="status-badge ${statusClass}">${notification.status}</span></td>
            <td>${notification.sent_at ? new Date(notification.sent_at).toLocaleString() : 'Not sent'}</td>
        `;
        tbody.appendChild(row);
    });
}

// Reports functions
async function loadReports() {
    try {
        const transactionData = await apiCall('/transactions');
        
        // Calculate stats
        const totalSales = transactionData.reduce((sum, t) => sum + parseFloat(t.total_amount), 0);
        const totalTransactions = transactionData.length;
        const averageSale = totalTransactions > 0 ? totalSales / totalTransactions : 0;
        
        document.getElementById('total-sales').textContent = $${totalSales.toFixed(2)};
        document.getElementById('total-transactions').textContent = totalTransactions;
        document.getElementById('average-sale').textContent = $${averageSale.toFixed(2)};
        
        // Top medicines
        const medicineStats = {};
        transactionData.forEach(transaction => {
            const medicineName = transaction.medicine_name;
            if (!medicineStats[medicineName]) {
                medicineStats[medicineName] = { quantity: 0, revenue: 0 };
            }
            medicineStats[medicineName].quantity += transaction.quantity;
            medicineStats[medicineName].revenue += parseFloat(transaction.total_amount);
        });
        
        const topMedicines = Object.entries(medicineStats)
            .sort(([,a], [,b]) => b.revenue - a.revenue)
            .slice(0, 5);
        
        renderTopMedicines(topMedicines);
        
    } catch (error) {
        console.error('Error loading reports:', error);
    }
}

function renderTopMedicines(topMedicinesList) {
    const container = document.getElementById('top-medicines-list');
    container.innerHTML = '';
    
    if (topMedicinesList.length === 0) {
        container.innerHTML = '<p style="color: #6b7280; text-align: center;">No sales data available</p>';
        return;
    }
    
    topMedicinesList.forEach(([name, stats]) => {
        const div = document.createElement('div');
        div.className = 'report-stat';
        div.innerHTML = `
            <span class="label">${name}</span>
            <span class="value">$${stats.revenue.toFixed(2)}</span>
        `;
        container.appendChild(div);
    });
}

// Form handlers
function handleAddMedicine(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    
    const medicineData = {
        name: formData.get('name'),
        manufacturer: formData.get('manufacturer'),
        category: formData.get('category'),
        currentStock: parseInt(formData.get('currentStock')),
        minStockLevel: parseInt(formData.get('minStockLevel')),
        pricePerUnit: parseFloat(formData.get('pricePerUnit')),
        expiryDate: formData.get('expiryDate'),
        batchNumber: formData.get('batchNumber'),
        description: formData.get('description') || ''
    };
    
    apiCall('/medicines', 'POST', medicineData)
        .then(() => {
            showToast('Medicine added successfully!');
            hideModal('add-medicine-modal');
            event.target.reset();
            loadMedicines();
        })
        .catch(error => {
            showToast('Error adding medicine: ' + error.message, 'error');
        });
}

function handleAddCustomer(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    
    const customerData = {
        name: formData.get('name'),
        phone: formData.get('phone'),
        email: formData.get('email') || null,
        address: formData.get('address') || null
    };
    
    apiCall('/customers', 'POST', customerData)
        .then(() => {
            showToast('Customer added successfully!');
            hideModal('add-customer-modal');
            event.target.reset();
            loadCustomers();
        })
        .catch(error => {
            showToast('Error adding customer: ' + error.message, 'error');
        });
}

function handleNewSale(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    
    const customerPhone = formData.get('customerPhone');
    const medicineId = formData.get('medicineId');
    const quantity = parseInt(formData.get('quantity'));
    
    // Find or create customer
    let customer = customers.find(c => c.phone === customerPhone);
    
    const medicine = medicines.find(m => m.id === medicineId);
    if (!medicine) {
        showToast('Selected medicine not found', 'error');
        return;
    }
    
    if (quantity > medicine.current_stock) {
        showToast('Insufficient stock available', 'error');
        return;
    }
    
    const unitPrice = parseFloat(medicine.price_per_unit);
    const totalAmount = unitPrice * quantity;
    
    const processTransaction = (customerId) => {
        const transactionData = {
            customerId: customerId,
            medicineId: medicineId,
            quantity: quantity,
            unitPrice: unitPrice.toString(),
            totalAmount: totalAmount.toString(),
            status: 'completed',
            smsNotificationSent: true,
            voiceCallScheduled: false
        };
        
        apiCall('/transactions', 'POST', transactionData)
            .then(() => {
                showToast('Sale completed successfully! SMS notification sent.');
                hideModal('new-sale-modal');
                event.target.reset();
                document.getElementById('sale-summary').style.display = 'none';
                loadTransactions();
                if (currentPage === 'dashboard') {
                    loadDashboardData();
                }
            })
            .catch(error => {
                showToast('Error completing sale: ' + error.message, 'error');
            });
    };
    
    if (customer) {
        processTransaction(customer.id);
    } else {
        // Create new customer first
        const customerData = {
            name: 'New Customer',
            phone: customerPhone,
            email: null,
            address: null
        };
        
        apiCall('/customers', 'POST', customerData)
            .then(newCustomer => {
                customers.push(newCustomer);
                processTransaction(newCustomer.id);
            })
            .catch(error => {
                showToast('Error creating customer: ' + error.message, 'error');
            });
    }
}

// Sale calculation
function updateSaleSummary() {
    const medicineSelect = document.getElementById('medicine-select');
    const quantityInput = document.querySelector('input[name="quantity"]');
    const saleSummary = document.getElementById('sale-summary');
    
    if (medicineSelect.value && quantityInput.value) {
        const selectedOption = medicineSelect.options[medicineSelect.selectedIndex];
        const unitPrice = parseFloat(selectedOption.getAttribute('data-price'));
        const quantity = parseInt(quantityInput.value);
        const totalAmount = unitPrice * quantity;
        
        document.getElementById('unit-price').textContent = $${unitPrice.toFixed(2)};
        document.getElementById('sale-quantity').textContent = quantity;
        document.getElementById('total-amount').textContent = $${totalAmount.toFixed(2)};
        
        saleSummary.style.display = 'block';
    } else {
        saleSummary.style.display = 'none';
    }
}

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    // Navigation event listeners
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const page = this.getAttribute('data-page');
            switchPage(page);
        });
    });
    
    // Modal event listeners
    document.querySelectorAll('.close, .close-modal').forEach(element => {
        element.addEventListener('click', function() {
            const modal = this.closest('.modal');
            modal.classList.remove('show');
        });
    });
    
    // Button event listeners
    document.getElementById('add-medicine-btn').addEventListener('click', () => showModal('add-medicine-modal'));
    document.getElementById('add-customer-btn').addEventListener('click', () => showModal('add-customer-modal'));
    document.getElementById('new-sale-btn').addEventListener('click', () => showModal('new-sale-modal'));
    
    // Form event listeners
    document.getElementById('add-medicine-form').addEventListener('submit', handleAddMedicine);
    document.getElementById('add-customer-form').addEventListener('submit', handleAddCustomer);
    document.getElementById('new-sale-form').addEventListener('submit', handleNewSale);
    
    // Sale calculation listeners
    document.getElementById('medicine-select').addEventListener('change', updateSaleSummary);
    document.querySelector('input[name="quantity"]').addEventListener('input', updateSaleSummary);
    
    // Close modals when clicking outside
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.remove('show');
            }
        });
    });
    
    // Load initial data
    switchPage('dashboard');
});