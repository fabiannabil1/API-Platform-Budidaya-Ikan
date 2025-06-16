// Chat functionality
class Chat {
    constructor() {
        this.users = [];
        this.orders = [];
        this.messages = new Map(); // userId -> messages[]
        this.selectedUserId = null;
        this.updateInterval = null;
        this.currentUserId = null; // Store current admin user ID
        this.init();
    }

    async init() {
        // Check authentication
        if (!Auth.isAuthenticated()) {
            Auth.redirectToLogin();
            return;
        }

        // Get current user ID from JWT token
        await this.getCurrentUserId();

        // Setup event listeners
        this.setupEventListeners();
        
        // Load initial data
        await this.loadData();
        
        // Start auto-update
        this.startAutoUpdate();
    }

    setupEventListeners() {
        // User filter tabs
        document.querySelectorAll('.tab-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.filterUsers(e.target.dataset.filter);
            });
        });

        // Search users
        const searchInput = document.getElementById('searchUsers');
        if (searchInput) {
            searchInput.addEventListener('input', () => this.filterUsers());
        }

        // Sort users
        const sortSelect = document.getElementById('sortUsers');
        if (sortSelect) {
            sortSelect.addEventListener('change', () => this.filterUsers());
        }

        // Message form
        const messageForm = document.getElementById('messageForm');
        if (messageForm) {
            messageForm.addEventListener('submit', (e) => this.handleSendMessage(e));
        }

        // Refresh chat button
        const refreshBtn = document.getElementById('refreshChat');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshChat());
        }

        // Clear chat button
        const clearBtn = document.getElementById('clearChat');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearChat());
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

    async loadData() {
        try {
            Modal.showLoading();
            
            // Load users and orders concurrently
            const [users, orders] = await Promise.all([
                API.get('/profiles'),
                API.get('/orders')
            ]);
            
            this.users = users;
            this.orders = orders;
            
            // Update UI
            this.updateUsersList();
            this.updateChatStats();
        } catch (error) {
            console.error('Error loading data:', error);
            this.showError('Gagal memuat data');
        } finally {
            Modal.hideLoading();
        }
    }

    updateUsersList() {
        const usersList = document.getElementById('chatUsersList');
        if (!usersList) return;

        if (this.users.length === 0) {
            usersList.innerHTML = `
                <div class="text-center" style="padding: 20px; color: var(--text-light);">
                    Tidak ada pengguna
                </div>
            `;
            return;
        }

        // Update user count
        document.getElementById('userCount').textContent = this.users.length;

        // Get user order counts
        const userOrderCounts = new Map();
        this.orders.forEach(order => {
            const userId = order.user_id;
            userOrderCounts.set(userId, (userOrderCounts.get(userId) || 0) + 1);
        });

        usersList.innerHTML = this.users.map(user => `
            <div class="chat-user-item ${this.selectedUserId === user.id ? 'active' : ''}" 
                 onclick="chat.selectUser(${user.id})">
                <div class="d-flex justify-between align-center">
                    <div>
                        <div class="chat-user-name">${user.name || 'User'}</div>
                        <div class="chat-user-phone">${user.phone || ''}</div>
                    </div>
                    ${userOrderCounts.has(user.id) ? `
                        <span class="badge badge-primary">
                            ${userOrderCounts.get(user.id)} pesanan
                        </span>
                    ` : ''}
                </div>
            </div>
        `).join('');
    }

    async selectUser(userId) {
        this.selectedUserId = userId;
        const user = this.users.find(u => u.id === userId);
        console.log(`Selected userId: ${userId}, user phone: ${user ? user.phone : 'undefined'}`);
        
        // Update UI
        this.updateUsersList();
        document.getElementById('selectedUserName').textContent = user.name || 'User';
        document.getElementById('selectedUserPhone').textContent = user.phone || '';
        document.getElementById('chatInput').style.display = 'block';
        document.getElementById('clearChat').style.display = 'block';
        
        // Load messages
        await this.loadMessages(userId);
    }

    async loadMessages(userId) {
        try {
            const response = await API.get(`/chats/${userId}`);
            // The API returns {chat_id, messages}
            const messages = response.messages || [];
            this.messages.set(userId, messages);
            this.renderMessages();
        } catch (error) {
            console.error('Error loading messages:', error);
            this.showError('Gagal memuat pesan');
        }
    }

    async getCurrentUserId() {
        try {
            // Decode JWT token to get current user ID
            const token = Auth.getToken();
            if (token) {
                // Simple JWT decode (for production, use a proper JWT library)
                const payload = JSON.parse(atob(token.split('.')[1]));
                this.currentUserId = parseInt(payload.sub || payload.identity);
                console.log('Current admin user ID:', this.currentUserId);
            }
        } catch (error) {
            console.error('Error getting current user ID:', error);
            // Fallback: try to get from API
            try {
                const response = await API.get('/profiles/me');
                this.currentUserId = response.id;
            } catch (apiError) {
                console.error('Error getting user ID from API:', apiError);
                this.currentUserId = null;
            }
        }
    }

    renderMessages() {
        const messagesBody = document.getElementById('chatMessagesBody');
        if (!messagesBody || !this.selectedUserId) return;

        const messages = this.messages.get(this.selectedUserId) || [];
        
        if (messages.length === 0) {
            messagesBody.innerHTML = `
                <div class="text-center" style="padding: 40px; color: var(--text-light);">
                    <i class="fas fa-comments" style="font-size: 48px; margin-bottom: 16px; opacity: 0.3;"></i>
                    <p>Belum ada percakapan</p>
                </div>
            `;
            return;
        }

        messagesBody.innerHTML = messages.map(message => {
            // Compare with current admin user ID instead of hardcoded 1
            const isSent = this.currentUserId && (message.sender_id === this.currentUserId);
            console.log(`Message sender_id: ${message.sender_id}, current user: ${this.currentUserId}, isSent: ${isSent}`);
            
            return `
                <div class="chat-message ${isSent ? 'sent' : 'received'}">
                    <div class="chat-message-content">
                        ${message.message}
                    </div>
                    <div class="chat-message-time">
                        ${formatDate(message.sent_at)}
                    </div>
                </div>
            `;
        }).join('');

        // Scroll to bottom
        messagesBody.scrollTop = messagesBody.scrollHeight;
    }

    async handleSendMessage(e) {
        e.preventDefault();
        if (!this.selectedUserId) return;

        const messageInput = document.getElementById('messageText');
        const content = messageInput.value.trim();
        
        if (!content) return;

        const receiverUser = this.users.find(u => u.id === this.selectedUserId);
        const receiverPhone = receiverUser ? receiverUser.phone : null;
        console.log(`Sending message to receiver_phone: ${receiverPhone}, content: ${content}`);

        try {
            await API.post('/chats/send', {
                receiver_phone: receiverPhone,
                message: content
            });

            // Clear input
            messageInput.value = '';

            // Refresh messages
            await this.loadMessages(this.selectedUserId);
        } catch (error) {
            console.error('Error sending message:', error);
            this.showError('Gagal mengirim pesan');
        }
    }

    filterUsers(filter = null) {
        const searchTerm = document.getElementById('searchUsers').value.toLowerCase();
        const sortBy = document.getElementById('sortUsers').value;
        
        if (filter) {
            document.querySelectorAll('.tab-link').forEach(link => {
                link.classList.toggle('active', link.dataset.filter === filter);
            });
        } else {
            filter = document.querySelector('.tab-link.active').dataset.filter;
        }

        let filteredUsers = [...this.users];

        // Apply search filter
        if (searchTerm) {
            filteredUsers = filteredUsers.filter(user => 
                (user.name && user.name.toLowerCase().includes(searchTerm)) ||
                (user.phone && user.phone.includes(searchTerm))
            );
        }

        // Apply user type filter
        if (filter === 'with-orders') {
            const userIdsWithOrders = new Set(this.orders.map(order => order.user_id));
            filteredUsers = filteredUsers.filter(user => userIdsWithOrders.has(user.id));
        }

        // Apply sorting
        switch (sortBy) {
            case 'name_asc':
                filteredUsers.sort((a, b) => (a.name || '').localeCompare(b.name || ''));
                break;
            case 'name_desc':
                filteredUsers.sort((a, b) => (b.name || '').localeCompare(a.name || ''));
                break;
            case 'recent_chat':
                // Sort by most recent message
                filteredUsers.sort((a, b) => {
                    const aMessages = this.messages.get(a.id) || [];
                    const bMessages = this.messages.get(b.id) || [];
                    const aLatest = aMessages.length ? new Date(aMessages[aMessages.length - 1].sent_at) : new Date(0);
                    const bLatest = bMessages.length ? new Date(bMessages[bMessages.length - 1].sent_at) : new Date(0);
                    return bLatest - aLatest;
                });
                break;
            case 'most_orders':
                // Sort by number of orders
                const orderCounts = new Map();
                this.orders.forEach(order => {
                    orderCounts.set(order.user_id, (orderCounts.get(order.user_id) || 0) + 1);
                });
                filteredUsers.sort((a, b) => 
                    (orderCounts.get(b.id) || 0) - (orderCounts.get(a.id) || 0)
                );
                break;
        }

        // Update users list with filtered results
        const originalUsers = this.users;
        this.users = filteredUsers;
        this.updateUsersList();
        this.users = originalUsers;
    }

    async refreshChat() {
        if (this.selectedUserId) {
            await this.loadMessages(this.selectedUserId);
        }
    }

    clearChat() {
        if (!this.selectedUserId || !confirm('Apakah Anda yakin ingin menghapus riwayat chat ini?')) {
            return;
        }

        this.messages.set(this.selectedUserId, []);
        this.renderMessages();
    }

    updateChatStats() {
        // Total chats (unique conversations)
        const totalChats = this.messages.size;
        document.getElementById('totalChats').textContent = totalChats;

        // Total messages
        const totalMessages = Array.from(this.messages.values())
            .reduce((sum, messages) => sum + messages.length, 0);
        document.getElementById('totalMessages').textContent = totalMessages;

        // Today's messages
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const todayMessages = Array.from(this.messages.values())
            .reduce((sum, messages) => sum + messages.filter(m => 
                new Date(m.sent_at) >= today
            ).length, 0);
        document.getElementById('todayMessages').textContent = todayMessages;

        // Active chats (with messages in last 24 hours)
        const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000);
        const activeChats = Array.from(this.messages.entries())
            .filter(([_, messages]) => messages.some(m => 
                new Date(m.sent_at) >= yesterday
            )).length;
        document.getElementById('activeChats').textContent = activeChats;
    }

    startAutoUpdate() {
        // Update every 5 seconds
        this.updateInterval = setInterval(() => {
            if (this.selectedUserId) {
                this.loadMessages(this.selectedUserId);
            }
        }, 5000);
    }

    stopAutoUpdate() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
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

// Initialize chat when DOM is loaded
let chat;
document.addEventListener('DOMContentLoaded', () => {
    chat = new Chat();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.chat) {
        window.chat.stopAutoUpdate();
    }
});
