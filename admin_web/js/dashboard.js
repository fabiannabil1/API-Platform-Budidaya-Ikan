// Dashboard functionality
class Dashboard {
    constructor() {
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
        
        // Load dashboard data
        await this.loadDashboardData();
    }

    setupEventListeners() {
        // Logout button
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.logout();
            });
        }

        // Mobile sidebar toggle (if needed)
        const sidebarToggle = document.getElementById('sidebarToggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                const sidebar = document.getElementById('sidebar');
                sidebar.classList.toggle('open');
            });
        }
    }

    async loadDashboardData() {
        try {
            Modal.showLoading();
            
            // Load all dashboard data concurrently
            const [products, orders, users, revenue, roleRequests] = await Promise.allSettled([
                this.loadProducts(),
                this.loadOrders(),
                this.loadUsers(),
                this.calculateRevenue(),
                this.loadRoleRequests()
            ]);

            // Update stats
            this.updateStats({
                products: products.status === 'fulfilled' ? products.value : [],
                orders: orders.status === 'fulfilled' ? orders.value : [],
                users: users.status === 'fulfilled' ? users.value : [],
                revenue: revenue.status === 'fulfilled' ? revenue.value : 0,
                roleRequests: roleRequests.status === 'fulfilled' ? roleRequests.value : []
            });

            // Load recent activity
            await this.loadRecentActivity();

        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError('Gagal memuat data dashboard');
        } finally {
            Modal.hideLoading();
        }
    }

    async loadProducts() {
        try {
            return await API.get('/products');
        } catch (error) {
            console.error('Error loading products:', error);
            return [];
        }
    }

    async loadOrders() {
        try {
            return await API.get('/orders');
        } catch (error) {
            console.error('Error loading orders:', error);
            return [];
        }
    }

    async loadUsers() {
        try {
            return await API.get('/profiles');
        } catch (error) {
            console.error('Error loading users:', error);
            return [];
        }
    }

    async calculateRevenue() {
        try {
            const orders = await API.get('/orders');
            return orders
                .filter(order => order.status === 'completed' || order.status === 'delivered')
                .reduce((total, order) => total + (order.total_amount || 0), 0);
        } catch (error) {
            console.error('Error calculating revenue:', error);
            return 0;
        }
    }

    async loadRoleRequests() {
        try {
            const response = await API.get('/role-change/requests');
            // Handle the nested data structure from the API
            return response.data || response || [];
        } catch (error) {
            console.error('Error loading role requests:', error);
            return [];
        }
    }

    updateStats(data) {
        // Update product count
        const totalProducts = document.getElementById('totalProducts');
        if (totalProducts) {
            totalProducts.textContent = data.products.length.toLocaleString('id-ID');
        }

        // Update order count
        const totalOrders = document.getElementById('totalOrders');
        if (totalOrders) {
            totalOrders.textContent = data.orders.length.toLocaleString('id-ID');
        }

        // Update user count
        const totalUsers = document.getElementById('totalUsers');
        if (totalUsers) {
            totalUsers.textContent = data.users.length.toLocaleString('id-ID');
        }

        // Update revenue
        const totalRevenue = document.getElementById('totalRevenue');
        if (totalRevenue) {
            totalRevenue.textContent = formatCurrency(data.revenue);
        }

        // Update pending role requests
        const pendingRoleRequests = document.getElementById('pendingRoleRequests');
        if (pendingRoleRequests) {
            const pendingCount = data.roleRequests.filter(req => req.status === 'pending').length;
            pendingRoleRequests.textContent = pendingCount.toLocaleString('id-ID');
        }
    }

    async loadRecentActivity() {
        try {
            // Get recent orders for activity
            const orders = await API.get('/orders');
            const recentOrders = orders
                .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
                .slice(0, 10);

            const activityTableBody = document.getElementById('recentActivity');
            if (activityTableBody) {
                if (recentOrders.length === 0) {
                    activityTableBody.innerHTML = `
                        <tr>
                            <td colspan="3" class="text-center">Tidak ada aktivitas terbaru</td>
                        </tr>
                    `;
                } else {
                    activityTableBody.innerHTML = recentOrders.map(order => `
                        <tr>
                            <td>${formatDate(order.created_at)}</td>
                            <td>Pesanan #${order.id} - ${order.user_name || 'User'}</td>
                            <td>
                                <span class="badge ${this.getStatusBadgeClass(order.status)}">
                                    ${this.getStatusText(order.status)}
                                </span>
                            </td>
                        </tr>
                    `).join('');
                }
            }
        } catch (error) {
            console.error('Error loading recent activity:', error);
            const activityTableBody = document.getElementById('recentActivity');
            if (activityTableBody) {
                activityTableBody.innerHTML = `
                    <tr>
                        <td colspan="3" class="text-center">Gagal memuat aktivitas terbaru</td>
                    </tr>
                `;
            }
        }
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
        // Create or update error message
        let errorDiv = document.getElementById('dashboardError');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.id = 'dashboardError';
            errorDiv.className = 'error-message';
            document.querySelector('.main-content').insertBefore(errorDiv, document.querySelector('.page-header').nextSibling);
        }
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';

        // Auto hide after 5 seconds
        setTimeout(() => {
            if (errorDiv) {
                errorDiv.style.display = 'none';
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

// Add badge styles to CSS if not already present
const badgeStyles = `
    .badge {
        display: inline-block;
        padding: 4px 8px;
        font-size: 12px;
        font-weight: 500;
        border-radius: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-primary { background-color: var(--primary-blue); color: white; }
    .badge-secondary { background-color: var(--gray-400); color: white; }
    .badge-success { background-color: var(--success-color); color: white; }
    .badge-warning { background-color: var(--warning-color); color: white; }
    .badge-danger { background-color: var(--error-color); color: white; }
    .badge-info { background-color: var(--accent-blue); color: white; }
`;

// Add styles to head if not already present
if (!document.getElementById('badgeStyles')) {
    const styleSheet = document.createElement('style');
    styleSheet.id = 'badgeStyles';
    styleSheet.textContent = badgeStyles;
    document.head.appendChild(styleSheet);
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new Dashboard();
});

// Auto refresh dashboard data every 30 seconds
setInterval(() => {
    if (Auth.isAuthenticated()) {
        const dashboard = new Dashboard();
        dashboard.loadDashboardData();
    }
}, 30000);
