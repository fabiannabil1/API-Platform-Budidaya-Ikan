// Orders management functionality
class Orders {
    constructor() {
        this.orders = [];
        this.customerOrders = [];
        this.currentOrderId = null;
        this.init();
    }

    async init() {
        // Check authentication
        if (!Auth.isAuthenticated()) {
            Auth.redirectToLogin();
            return;
        }

        // Setup event listeners
        this.setupEventListeners();
        
        // Load orders
        await this.loadOrders();
    }

    setupEventListeners() {
        // Search input
        const searchInput = document.getElementById('searchOrder');
        if (searchInput) {
            searchInput.addEventListener('input', () => this.filterOrders());
        }

        // Status filter
        const statusFilter = document.getElementById('statusFilter');
        if (statusFilter) {
            statusFilter.addEventListener('change', () => this.filterOrders());
        }

        // Date filter
        const dateFilter = document.getElementById('dateFilter');
        if (dateFilter) {
            dateFilter.addEventListener('change', () => this.filterOrders());
        }

        // Sort select
        const sortSelect = document.getElementById('sortOrders');
        if (sortSelect) {
            sortSelect.addEventListener('change', () => this.filterOrders());
        }

        // Status form
        const statusForm = document.getElementById('statusForm');
        if (statusForm) {
            statusForm.addEventListener('submit', (e) => this.handleStatusUpdate(e));
        }

        // Update status button
        const updateStatusBtn = document.getElementById('updateStatusBtn');
        if (updateStatusBtn) {
            updateStatusBtn.addEventListener('click', () => this.showStatusModal());
        }

        // Logout button
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.logout();
            });
        }
    }

    async loadOrders() {
        try {
            Modal.showLoading();
            const orders = await API.get('/orders');
            this.orders = orders;
            this.updateStats();
            this.renderOrders();
            await this.loadCustomerOrderCounts();
        } catch (error) {
            console.error('Error loading orders:', error);
            this.showError('Gagal memuat data pesanan');
        } finally {
            Modal.hideLoading();
        }
    }

    updateStats() {
        // Total orders
        const totalOrders = document.getElementById('totalOrders');
        if (totalOrders) {
            totalOrders.textContent = this.orders.length.toLocaleString('id-ID');
        }

        // Pending orders
        const pendingOrders = document.getElementById('pendingOrders');
        if (pendingOrders) {
            const pending = this.orders.filter(order => order.status === 'pending').length;
            pendingOrders.textContent = pending.toLocaleString('id-ID');
        }

        // Completed orders
        const completedOrders = document.getElementById('completedOrders');
        if (completedOrders) {
            const completed = this.orders.filter(order => 
                order.status === 'completed' || order.status === 'delivered'
            ).length;
            completedOrders.textContent = completed.toLocaleString('id-ID');
        }

        // Active customers (unique users with orders)
        const activeCustomers = document.getElementById('activeCustomers');
        if (activeCustomers) {
            const uniqueCustomers = new Set(this.orders.map(order => order.user_id)).size;
            activeCustomers.textContent = uniqueCustomers.toLocaleString('id-ID');
        }
    }

    renderOrders() {
        const tbody = document.getElementById('ordersTableBody');
        if (!tbody) return;

        if (this.orders.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center">Tidak ada pesanan</td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = this.orders.map(order => `
            <tr>
                <td>#${order.id}</td>
                <td>
                    <div style="font-weight: 500;">${order.user_name || 'User'}</div>
                    <div style="font-size: 12px; color: var(--text-light);">${order.user_phone || ''}</div>
                </td>
                <td>${formatDate(order.created_at)}</td>
                <td>${formatCurrency(order.total_amount || 0)}</td>
                <td>
                    <span class="badge ${this.getStatusBadgeClass(order.status)}">
                        ${this.getStatusText(order.status)}
                    </span>
                </td>
                <td>
                    <div class="d-flex gap-2">
                        <button class="btn btn-sm btn-primary" onclick="orders.showOrderDetail(${order.id})">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-warning" onclick="orders.showStatusModal(${order.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    async loadCustomerOrderCounts() {
        try {
            // Group orders by customer
            const customerMap = new Map();
            
            this.orders.forEach(order => {
                const customerId = order.user_id;
                const customerName = order.user_name || 'User';
                const customerPhone = order.user_phone || '';
                
                if (!customerMap.has(customerId)) {
                    customerMap.set(customerId, {
                        name: customerName,
                        phone: customerPhone,
                        orderCount: 0,
                        totalAmount: 0,
                        lastStatus: null,
                        lastOrderDate: null
                    });
                }
                
                const customer = customerMap.get(customerId);
                customer.orderCount++;
                customer.totalAmount += order.total_amount || 0;
                
                // Update last order info
                if (!customer.lastOrderDate || new Date(order.created_at) > new Date(customer.lastOrderDate)) {
                    customer.lastStatus = order.status;
                    customer.lastOrderDate = order.created_at;
                }
            });

            // Convert to array and sort by order count
            this.customerOrders = Array.from(customerMap.values())
                .sort((a, b) => b.orderCount - a.orderCount);

            this.renderCustomerOrders();
        } catch (error) {
            console.error('Error loading customer order counts:', error);
        }
    }

    renderCustomerOrders() {
        const tbody = document.getElementById('customerOrdersTableBody');
        if (!tbody) return;

        if (this.customerOrders.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center">Tidak ada data pelanggan</td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = this.customerOrders.map(customer => `
            <tr>
                <td>
                    <div style="font-weight: 500;">${customer.name}</div>
                    <div style="font-size: 12px; color: var(--text-light);">${customer.phone}</div>
                </td>
                <td>${customer.orderCount} pesanan</td>
                <td>${formatCurrency(customer.totalAmount)}</td>
                <td>
                    <span class="badge ${this.getStatusBadgeClass(customer.lastStatus)}">
                        ${this.getStatusText(customer.lastStatus)}
                    </span>
                </td>
            </tr>
        `).join('');
    }

    async showOrderDetail(orderId) {
        try {
            Modal.showLoading();
            const order = await API.get(`/orders/${orderId}`);
            this.currentOrderId = orderId;
            
            const orderDetails = document.getElementById('orderDetails');
            if (orderDetails) {
                orderDetails.innerHTML = `
                    <div class="order-detail">
                        <div class="row">
                            <div class="col">
                                <h4>Informasi Pesanan</h4>
                                <p><strong>ID Pesanan:</strong> #${order.id}</p>
                                <p><strong>Tanggal:</strong> ${formatDate(order.created_at)}</p>
                                <p><strong>Status:</strong> 
                                    <span class="badge ${this.getStatusBadgeClass(order.status)}">
                                        ${this.getStatusText(order.status)}
                                    </span>
                                </p>
                            </div>
                            <div class="col">
                                <h4>Informasi Pelanggan</h4>
                                <p><strong>Nama:</strong> ${order.user_name || 'User'}</p>
                                <p><strong>Telepon:</strong> ${order.user_phone || '-'}</p>
                                <p><strong>Alamat:</strong> ${order.address || '-'}</p>
                            </div>
                        </div>
                        
                        <h4>Detail Produk</h4>
                        <div class="table-container">
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>Produk</th>
                                        <th>Harga</th>
                                        <th>Jumlah</th>
                                        <th>Subtotal</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${order.items ? order.items.map(item => `
                                        <tr>
                                            <td>${item.product_name}</td>
                                            <td>${formatCurrency(item.price)}</td>
                                            <td>${item.quantity}</td>
                                            <td>${formatCurrency(item.price * item.quantity)}</td>
                                        </tr>
                                    `).join('') : '<tr><td colspan="4">Tidak ada detail produk</td></tr>'}
                                </tbody>
                                <tfoot>
                                    <tr>
                                        <th colspan="3">Total</th>
                                        <th>${formatCurrency(order.total_amount || 0)}</th>
                                    </tr>
                                </tfoot>
                            </table>
                        </div>
                    </div>
                `;
            }
            
            Modal.show('orderModal');
        } catch (error) {
            console.error('Error loading order detail:', error);
            this.showError('Gagal memuat detail pesanan');
        } finally {
            Modal.hideLoading();
        }
    }

    showStatusModal(orderId = null) {
        if (orderId) {
            this.currentOrderId = orderId;
            const order = this.orders.find(o => o.id === orderId);
            if (order) {
                document.getElementById('newStatus').value = order.status;
            }
        }
        
        document.getElementById('statusOrderId').value = this.currentOrderId;
        Modal.hide('orderModal');
        Modal.show('statusModal');
    }

    async handleStatusUpdate(e) {
        e.preventDefault();
        const form = e.target;
        const orderId = form.statusOrderId.value;
        const newStatus = form.status.value;

        try {
            Modal.showLoading();
            await API.put(`/orders/${orderId}/status`, { status: newStatus });
            Modal.hide('statusModal');
            await this.loadOrders();
            this.showSuccess('Status pesanan berhasil diperbarui');
        } catch (error) {
            console.error('Error updating order status:', error);
            this.showError('Gagal memperbarui status pesanan');
        } finally {
            Modal.hideLoading();
        }
    }

    filterOrders() {
        const searchTerm = document.getElementById('searchOrder').value.toLowerCase();
        const statusFilter = document.getElementById('statusFilter').value;
        const dateFilter = document.getElementById('dateFilter').value;
        const sortBy = document.getElementById('sortOrders').value;

        let filteredOrders = [...this.orders];

        // Apply search filter
        if (searchTerm) {
            filteredOrders = filteredOrders.filter(order => 
                order.id.toString().includes(searchTerm) ||
                (order.user_name && order.user_name.toLowerCase().includes(searchTerm)) ||
                (order.user_phone && order.user_phone.includes(searchTerm))
            );
        }

        // Apply status filter
        if (statusFilter) {
            filteredOrders = filteredOrders.filter(order => order.status === statusFilter);
        }

        // Apply date filter
        if (dateFilter) {
            const filterDate = new Date(dateFilter);
            filteredOrders = filteredOrders.filter(order => {
                const orderDate = new Date(order.created_at);
                return orderDate.toDateString() === filterDate.toDateString();
            });
        }

        // Apply sorting
        switch (sortBy) {
            case 'date_asc':
                filteredOrders.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
                break;
            case 'date_desc':
                filteredOrders.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
                break;
            case 'amount_asc':
                filteredOrders.sort((a, b) => (a.total_amount || 0) - (b.total_amount || 0));
                break;
            case 'amount_desc':
                filteredOrders.sort((a, b) => (b.total_amount || 0) - (a.total_amount || 0));
                break;
        }

        // Update the orders table with filtered results
        const originalOrders = this.orders;
        this.orders = filteredOrders;
        this.renderOrders();
        this.orders = originalOrders; // Restore original data
    }

    getStatusBadgeClass(status) {
        const statusClasses = {
            'pending': 'badge-warning',
            'processing': 'badge-info',
            'shipped': 'badge-primary',
            'delivered': 'badge-success',
            'cancelled': 'badge-danger',
            'completed': 'badge-success'
        };
        return statusClasses[status] || 'badge-secondary';
    }

    getStatusText(status) {
        const statusTexts = {
            'pending': 'Menunggu',
            'processing': 'Diproses',
            'shipped': 'Dikirim',
            'delivered': 'Terkirim',
            'cancelled': 'Dibatalkan',
            'completed': 'Selesai'
        };
        return statusTexts[status] || status;
    }

    showError(message) {
        let errorDiv = document.querySelector('.error-message');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            document.querySelector('.page-header').insertAdjacentElement('afterend', errorDiv);
        }
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';

        setTimeout(() => {
            if (errorDiv) {
                errorDiv.style.display = 'none';
            }
        }, 5000);
    }

    showSuccess(message) {
        let successDiv = document.querySelector('.success-message');
        if (!successDiv) {
            successDiv = document.createElement('div');
            successDiv.className = 'success-message';
            document.querySelector('.page-header').insertAdjacentElement('afterend', successDiv);
        }
        successDiv.textContent = message;
        successDiv.style.display = 'block';

        setTimeout(() => {
            if (successDiv) {
                successDiv.style.display = 'none';
            }
        }, 5000);
    }

    logout() {
        if (confirm('Apakah Anda yakin ingin logout?')) {
            Auth.removeToken();
            Auth.redirectToLogin();
        }
    }
}

// Add additional CSS for order details
const orderDetailStyles = `
    .order-detail .row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 24px;
        margin-bottom: 24px;
    }
    
    .order-detail h4 {
        color: var(--text-dark);
        margin-bottom: 16px;
        font-size: 16px;
        font-weight: 600;
    }
    
    .order-detail p {
        margin-bottom: 8px;
        font-size: 14px;
    }
    
    @media (max-width: 768px) {
        .order-detail .row {
            grid-template-columns: 1fr;
        }
    }
`;

// Add styles to head if not already present
if (!document.getElementById('orderDetailStyles')) {
    const styleSheet = document.createElement('style');
    styleSheet.id = 'orderDetailStyles';
    styleSheet.textContent = orderDetailStyles;
    document.head.appendChild(styleSheet);
}

// Initialize orders management when DOM is loaded
let orders;
document.addEventListener('DOMContentLoaded', () => {
    orders = new Orders();
});
