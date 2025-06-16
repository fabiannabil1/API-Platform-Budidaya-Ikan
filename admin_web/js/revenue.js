// Revenue analytics functionality
class Revenue {
    constructor() {
        this.orders = [];
        this.chart = null;
        this.currentPeriod = 'daily';
        this.autoUpdateInterval = null;
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
        
        // Set default date range
        this.setDefaultDateRange();
        
        // Load revenue data
        await this.loadRevenueData();
        
        // Start auto-update
        this.startAutoUpdate();
    }

    setupEventListeners() {
        // Tab links for period selection
        const tabLinks = document.querySelectorAll('.tab-link');
        tabLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchPeriod(e.target.dataset.period);
            });
        });

        // Apply filters button
        const applyFilters = document.getElementById('applyFilters');
        if (applyFilters) {
            applyFilters.addEventListener('click', () => this.applyFilters());
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

    setDefaultDateRange() {
        const today = new Date();
        const thirtyDaysAgo = new Date(today.getTime() - (30 * 24 * 60 * 60 * 1000));
        
        document.getElementById('startDate').value = thirtyDaysAgo.toISOString().split('T')[0];
        document.getElementById('endDate').value = today.toISOString().split('T')[0];
    }

    async loadRevenueData() {
        try {
            Modal.showLoading();
            const orders = await API.get('/orders');
            this.orders = orders.filter(order => 
                order.status === 'completed' || order.status === 'delivered'
            );
            
            this.updateStats();
            this.updateChart();
            this.updateRevenueTable();
            this.updateTopProducts();
        } catch (error) {
            console.error('Error loading revenue data:', error);
            this.showError('Gagal memuat data pendapatan');
        } finally {
            Modal.hideLoading();
        }
    }

    updateStats() {
        const today = new Date();
        const startOfToday = new Date(today.getFullYear(), today.getMonth(), today.getDate());
        const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);

        // Total revenue
        const totalRevenue = this.orders.reduce((sum, order) => sum + (order.total_amount || 0), 0);
        document.getElementById('totalRevenue').textContent = formatCurrency(totalRevenue);

        // Today's revenue
        const todayRevenue = this.orders
            .filter(order => new Date(order.created_at) >= startOfToday)
            .reduce((sum, order) => sum + (order.total_amount || 0), 0);
        document.getElementById('todayRevenue').textContent = formatCurrency(todayRevenue);

        // This month's revenue
        const monthRevenue = this.orders
            .filter(order => new Date(order.created_at) >= startOfMonth)
            .reduce((sum, order) => sum + (order.total_amount || 0), 0);
        document.getElementById('monthRevenue').textContent = formatCurrency(monthRevenue);

        // Average order value
        const avgOrderValue = this.orders.length > 0 ? totalRevenue / this.orders.length : 0;
        document.getElementById('avgOrderValue').textContent = formatCurrency(avgOrderValue);
    }

    switchPeriod(period) {
        this.currentPeriod = period;
        
        // Update active tab
        document.querySelectorAll('.tab-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-period="${period}"]`).classList.add('active');
        
        // Update chart period badge
        const periodTexts = {
            'daily': 'Harian',
            'monthly': 'Bulanan',
            'yearly': 'Tahunan'
        };
        document.getElementById('chartPeriod').textContent = periodTexts[period];
        
        // Update chart
        this.updateChart();
        this.updateRevenueTable();
    }

    updateChart() {
        const ctx = document.getElementById('revenueChart');
        if (!ctx) return;

        const chartData = this.prepareChartData();
        
        if (this.chart) {
            this.chart.destroy();
        }

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Pendapatan',
                    data: chartData.data,
                    borderColor: 'rgb(37, 99, 235)',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: 'rgb(37, 99, 235)',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
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
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: 'rgb(37, 99, 235)',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                return 'Pendapatan: ' + formatCurrency(context.parsed.y);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return formatCurrency(value);
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    prepareChartData() {
        const startDate = new Date(document.getElementById('startDate').value);
        const endDate = new Date(document.getElementById('endDate').value);
        const minAmount = parseFloat(document.getElementById('minAmount').value) || 0;

        // Filter orders by date range
        const filteredOrders = this.orders.filter(order => {
            const orderDate = new Date(order.created_at);
            return orderDate >= startDate && orderDate <= endDate && (order.total_amount || 0) >= minAmount;
        });

        const labels = [];
        const data = [];
        const revenueMap = new Map();

        // Group by period
        filteredOrders.forEach(order => {
            const orderDate = new Date(order.created_at);
            let key;

            switch (this.currentPeriod) {
                case 'daily':
                    key = orderDate.toISOString().split('T')[0];
                    break;
                case 'monthly':
                    key = `${orderDate.getFullYear()}-${String(orderDate.getMonth() + 1).padStart(2, '0')}`;
                    break;
                case 'yearly':
                    key = orderDate.getFullYear().toString();
                    break;
            }

            if (!revenueMap.has(key)) {
                revenueMap.set(key, 0);
            }
            revenueMap.set(key, revenueMap.get(key) + (order.total_amount || 0));
        });

        // Sort and prepare data
        const sortedEntries = Array.from(revenueMap.entries()).sort((a, b) => a[0].localeCompare(b[0]));
        
        sortedEntries.forEach(([period, revenue]) => {
            labels.push(this.formatPeriodLabel(period));
            data.push(revenue);
        });

        return { labels, data };
    }

    formatPeriodLabel(period) {
        switch (this.currentPeriod) {
            case 'daily':
                return new Date(period).toLocaleDateString('id-ID', {
                    day: 'numeric',
                    month: 'short'
                });
            case 'monthly':
                const [year, month] = period.split('-');
                return new Date(year, month - 1).toLocaleDateString('id-ID', {
                    month: 'long',
                    year: 'numeric'
                });
            case 'yearly':
                return period;
            default:
                return period;
        }
    }

    updateRevenueTable() {
        const chartData = this.prepareChartData();
        const tbody = document.getElementById('revenueTableBody');
        
        if (!tbody) return;

        if (chartData.labels.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center">Tidak ada data pendapatan</td>
                </tr>
            `;
            return;
        }

        const startDate = new Date(document.getElementById('startDate').value);
        const endDate = new Date(document.getElementById('endDate').value);
        const filteredOrders = this.orders.filter(order => {
            const orderDate = new Date(order.created_at);
            return orderDate >= startDate && orderDate <= endDate;
        });

        // Group orders by period for counting
        const periodOrderCounts = new Map();
        filteredOrders.forEach(order => {
            const orderDate = new Date(order.created_at);
            let key;

            switch (this.currentPeriod) {
                case 'daily':
                    key = orderDate.toISOString().split('T')[0];
                    break;
                case 'monthly':
                    key = `${orderDate.getFullYear()}-${String(orderDate.getMonth() + 1).padStart(2, '0')}`;
                    break;
                case 'yearly':
                    key = orderDate.getFullYear().toString();
                    break;
            }

            if (!periodOrderCounts.has(key)) {
                periodOrderCounts.set(key, 0);
            }
            periodOrderCounts.set(key, periodOrderCounts.get(key) + 1);
        });

        tbody.innerHTML = chartData.labels.map((label, index) => {
            const revenue = chartData.data[index];
            const orderCount = Array.from(periodOrderCounts.values())[index] || 0;
            const avgPerOrder = orderCount > 0 ? revenue / orderCount : 0;

            return `
                <tr>
                    <td>${label}</td>
                    <td>${orderCount} pesanan</td>
                    <td>${formatCurrency(revenue)}</td>
                    <td>${formatCurrency(avgPerOrder)}</td>
                </tr>
            `;
        }).join('');
    }

    updateTopProducts() {
        const productRevenue = new Map();
        const productSales = new Map();

        // Calculate revenue per product
        this.orders.forEach(order => {
            if (order.items) {
                order.items.forEach(item => {
                    const productName = item.product_name;
                    const revenue = (item.price || 0) * (item.quantity || 0);
                    const quantity = item.quantity || 0;

                    if (!productRevenue.has(productName)) {
                        productRevenue.set(productName, 0);
                        productSales.set(productName, 0);
                    }

                    productRevenue.set(productName, productRevenue.get(productName) + revenue);
                    productSales.set(productName, productSales.get(productName) + quantity);
                });
            }
        });

        // Sort by revenue
        const sortedProducts = Array.from(productRevenue.entries())
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10);

        const totalRevenue = Array.from(productRevenue.values()).reduce((sum, rev) => sum + rev, 0);
        const tbody = document.getElementById('topProductsTableBody');

        if (!tbody) return;

        if (sortedProducts.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center">Tidak ada data produk</td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = sortedProducts.map(([productName, revenue]) => {
            const sales = productSales.get(productName);
            const contribution = totalRevenue > 0 ? (revenue / totalRevenue * 100) : 0;

            return `
                <tr>
                    <td>${productName}</td>
                    <td>${sales} unit</td>
                    <td>${formatCurrency(revenue)}</td>
                    <td>${contribution.toFixed(1)}%</td>
                </tr>
            `;
        }).join('');
    }

    applyFilters() {
        this.updateChart();
        this.updateRevenueTable();
        this.updateTopProducts();
    }

    startAutoUpdate() {
        // Update every 30 seconds
        this.autoUpdateInterval = setInterval(() => {
            this.loadRevenueData();
        }, 30000);
    }

    stopAutoUpdate() {
        if (this.autoUpdateInterval) {
            clearInterval(this.autoUpdateInterval);
            this.autoUpdateInterval = null;
        }
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

    logout() {
        if (confirm('Apakah Anda yakin ingin logout?')) {
            this.stopAutoUpdate();
            Auth.removeToken();
            Auth.redirectToLogin();
        }
    }
}

// Initialize revenue analytics when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new Revenue();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.revenue) {
        window.revenue.stopAutoUpdate();
    }
});
