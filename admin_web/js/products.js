// Products management functionality
class Products {
    constructor() {
        this.products = [];
        this.currentProductId = null;
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
        
        // Load products
        await this.loadProducts();
    }

    setupEventListeners() {
        // Add product button
        const addProductBtn = document.getElementById('addProductBtn');
        if (addProductBtn) {
            addProductBtn.addEventListener('click', () => this.showProductModal());
        }

        // Product form
        const productForm = document.getElementById('productForm');
        if (productForm) {
            productForm.addEventListener('submit', (e) => this.handleProductSubmit(e));
        }

        // Image file input
        const imageInput = document.getElementById('productImage');
        if (imageInput) {
            imageInput.addEventListener('change', (e) => this.handleImagePreview(e));
        }

        // Search input
        const searchInput = document.getElementById('searchProduct');
        if (searchInput) {
            searchInput.addEventListener('input', () => this.filterProducts());
        }

        // Stock filter
        const stockFilter = document.getElementById('stockFilter');
        if (stockFilter) {
            stockFilter.addEventListener('change', () => this.filterProducts());
        }

        // Sort select
        const sortSelect = document.getElementById('sortProducts');
        if (sortSelect) {
            sortSelect.addEventListener('change', () => this.filterProducts());
        }

        // Logout button
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.logout();
            });
        }

        // Delete confirmation
        const confirmDelete = document.getElementById('confirmDelete');
        if (confirmDelete) {
            confirmDelete.addEventListener('click', () => this.deleteProduct());
        }
    }

    handleImagePreview(e) {
        const file = e.target.files[0];
        const previewImg = document.getElementById('previewImg');
        
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                previewImg.src = e.target.result;
                previewImg.style.display = 'block';
            };
            reader.readAsDataURL(file);
        } else {
            previewImg.style.display = 'none';
        }
    }

    async loadProducts() {
        try {
            Modal.showLoading();
            const products = await API.get('/products');
            this.products = products;
            this.renderProducts();
        } catch (error) {
            console.error('Error loading products:', error);
            this.showError('Gagal memuat data produk');
        } finally {
            Modal.hideLoading();
        }
    }

    renderProducts() {
        const tbody = document.getElementById('productsTableBody');
        if (!tbody) return;

        if (this.products.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center">Tidak ada produk</td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = this.products.map(product => `
            <tr>
                <td>
                    <img src="${product.image_url || 'placeholder.jpg'}" 
                         alt="${product.name}" 
                         style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;">
                </td>
                <td>
                    <div style="font-weight: 500;">${product.name}</div>
                    <div style="font-size: 12px; color: var(--text-light);">${product.description || ''}</div>
                </td>
                <td>${formatCurrency(product.price)}</td>
                <td>${product.stock}</td>
                <td>
                    <span class="badge ${this.getStockBadgeClass(product.stock)}">
                        ${this.getStockStatus(product.stock)}
                    </span>
                </td>
                <td>
                    <div class="d-flex gap-2">
                        <button class="btn btn-sm btn-primary" onclick="products.showProductModal(${product.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="products.showDeleteModal(${product.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    getStockBadgeClass(stock) {
        if (stock <= 0) return 'badge-danger';
        if (stock < 5) return 'badge-warning';
        return 'badge-success';
    }

    getStockStatus(stock) {
        if (stock <= 0) return 'Habis';
        if (stock < 5) return 'Menipis';
        return 'Tersedia';
    }

    showProductModal(productId = null) {
        this.currentProductId = productId;
        const modal = document.getElementById('productModal');
        const title = document.getElementById('modalTitle');
        const form = document.getElementById('productForm');
        const previewImg = document.getElementById('previewImg');

        if (productId) {
            const product = this.products.find(p => p.id === productId);
            if (product) {
                title.textContent = 'Edit Produk';
                form.productId.value = product.id;
                form.name.value = product.name;
                form.description.value = product.description || '';
                form.price.value = product.price;
                form.stock.value = product.stock;
                document.getElementById('productImageUrl').value = product.image_url || '';
                
                // Show current image if exists
                if (product.image_url) {
                    previewImg.src = product.image_url;
                    previewImg.style.display = 'block';
                } else {
                    previewImg.style.display = 'none';
                }
            }
        } else {
            title.textContent = 'Tambah Produk';
            form.reset();
            form.productId.value = '';
            previewImg.style.display = 'none';
        }

        Modal.show('productModal');
    }

    async handleProductSubmit(e) {
        e.preventDefault();
        const form = e.target;
        const imageFile = document.getElementById('productImage').files[0];
        const imageUrl = document.getElementById('productImageUrl').value;

        // Create FormData for multipart/form-data
        const formData = new FormData();
        formData.append('name', form.name.value);
        formData.append('description', form.description.value);
        formData.append('price', form.price.value);
        formData.append('stock', form.stock.value);

        // Add image file or URL
        if (imageFile) {
            formData.append('image', imageFile);
        } else if (imageUrl) {
            formData.append('image_url', imageUrl);
        }

        try {
            Modal.showLoading();
            
            if (this.currentProductId) {
                await this.uploadProduct(`/products/${this.currentProductId}`, formData, 'PUT');
            } else {
                await this.uploadProduct('/products', formData, 'POST');
            }

            Modal.hide('productModal');
            await this.loadProducts();
            this.showSuccess(this.currentProductId ? 'Produk berhasil diperbarui' : 'Produk berhasil ditambahkan');
        } catch (error) {
            console.error('Error saving product:', error);
            this.showError('Gagal menyimpan produk');
        } finally {
            Modal.hideLoading();
        }
    }

    async uploadProduct(url, formData, method) {
        const token = Auth.getToken();
        const response = await fetch(`${API_BASE_URL}${url}`, {
            method: method,
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Request failed');
        }

        return response.json();
    }

    showDeleteModal(productId) {
        this.currentProductId = productId;
        Modal.show('deleteModal');
    }

    async deleteProduct() {
        if (!this.currentProductId) return;

        try {
            Modal.showLoading();
            await API.delete(`/products/${this.currentProductId}`);
            Modal.hide('deleteModal');
            await this.loadProducts();
            this.showSuccess('Produk berhasil dihapus');
        } catch (error) {
            console.error('Error deleting product:', error);
            this.showError('Gagal menghapus produk');
        } finally {
            Modal.hideLoading();
            this.currentProductId = null;
        }
    }

    filterProducts() {
        const searchTerm = document.getElementById('searchProduct').value.toLowerCase();
        const stockFilter = document.getElementById('stockFilter').value;
        const sortBy = document.getElementById('sortProducts').value;

        let filteredProducts = [...this.products];

        // Apply search filter
        if (searchTerm) {
            filteredProducts = filteredProducts.filter(product => 
                product.name.toLowerCase().includes(searchTerm) ||
                (product.description && product.description.toLowerCase().includes(searchTerm))
            );
        }

        // Apply stock filter
        switch (stockFilter) {
            case 'in':
                filteredProducts = filteredProducts.filter(p => p.stock > 0);
                break;
            case 'out':
                filteredProducts = filteredProducts.filter(p => p.stock <= 0);
                break;
            case 'low':
                filteredProducts = filteredProducts.filter(p => p.stock > 0 && p.stock < 5);
                break;
        }

        // Apply sorting
        switch (sortBy) {
            case 'name_asc':
                filteredProducts.sort((a, b) => a.name.localeCompare(b.name));
                break;
            case 'name_desc':
                filteredProducts.sort((a, b) => b.name.localeCompare(a.name));
                break;
            case 'price_asc':
                filteredProducts.sort((a, b) => a.price - b.price);
                break;
            case 'price_desc':
                filteredProducts.sort((a, b) => b.price - a.price);
                break;
            case 'stock_asc':
                filteredProducts.sort((a, b) => a.stock - b.stock);
                break;
            case 'stock_desc':
                filteredProducts.sort((a, b) => b.stock - a.stock);
                break;
        }

        // Update the products table with filtered results
        const tbody = document.getElementById('productsTableBody');
        if (tbody) {
            if (filteredProducts.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center">Tidak ada produk yang sesuai dengan filter</td>
                    </tr>
                `;
            } else {
                this.products = filteredProducts;
                this.renderProducts();
            }
        }
    }

    showError(message) {
        // Create or update error message
        let errorDiv = document.querySelector('.error-message');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            document.querySelector('.page-header').insertAdjacentElement('afterend', errorDiv);
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

    showSuccess(message) {
        // Create or update success message
        let successDiv = document.querySelector('.success-message');
        if (!successDiv) {
            successDiv = document.createElement('div');
            successDiv.className = 'success-message';
            document.querySelector('.page-header').insertAdjacentElement('afterend', successDiv);
        }
        successDiv.textContent = message;
        successDiv.style.display = 'block';

        // Auto hide after 5 seconds
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

// Initialize products management when DOM is loaded
let products;
document.addEventListener('DOMContentLoaded', () => {
    products = new Products();
});
