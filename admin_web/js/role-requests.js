// Global variable to store current request being processed
let currentRequestId = null;

// Load role change requests when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Ensure API_BASE_URL is set correctly
    if (!window.API_BASE_URL) {
        window.API_BASE_URL = 'https://efishery.acerkecil.my.id/api';
    }
    console.log('Using API Base URL:', window.API_BASE_URL);
    
    checkAdminAuth();
    loadRoleRequests();
});

// Debug: Log API configuration
console.log('Role requests page loaded');
console.log('API class available:', typeof API !== 'undefined');
console.log('Auth class available:', typeof Auth !== 'undefined');

async function loadRoleRequests() {
    try {
        console.log('API Base URL:', window.API_BASE_URL || 'Not available');
        console.log('Loading role requests...');
        
        const data = await API.get('/role-change/requests');
        console.log('Role requests data:', data);
        updateRequestsTable(data.data);
        updateStats(data.data);
    } catch (error) {
        console.error('Error loading role requests:', error);
        console.error('Error details:', {
            message: error.message,
            stack: error.stack
        });
        showError('Gagal memuat data permintaan: ' + error.message);
    }
}

// Update the requests table with data
function updateRequestsTable(requests) {
    const tbody = document.getElementById('roleRequestsTable');
    const statusFilter = document.getElementById('statusFilter').value;
    
    // Filter requests if status filter is set
    const filteredRequests = statusFilter ? 
        requests.filter(req => req.status === statusFilter) : 
        requests;

    tbody.innerHTML = filteredRequests.length ? 
        filteredRequests.map(request => `
            <tr>
                <td>${request.id}</td>
                <td>${request.name}</td>
                <td>${request.phone}</td>
                <td>${request.reason}</td>
                <td>${new Date(request.requested_at).toLocaleString('id-ID')}</td>
                <td>
                    <span class="status-badge ${request.status}">
                        ${getStatusLabel(request.status)}
                    </span>
                </td>
                <td>
                    ${request.status === 'pending' ? `
                        <button class="btn btn-sm btn-success" onclick="showApprovalModal(${request.id}, '${request.name}', '${request.reason}')">
                            <i class="fas fa-check"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="showRejectionModal(${request.id}, '${request.name}', '${request.reason}')">
                            <i class="fas fa-times"></i>
                        </button>
                    ` : ''}
                </td>
            </tr>
        `).join('') : 
        '<tr><td colspan="7" class="text-center">Tidak ada data permintaan</td></tr>';
}

// Update statistics
function updateStats(requests) {
    const stats = requests.reduce((acc, req) => {
        acc[req.status]++;
        return acc;
    }, { pending: 0, approved: 0, rejected: 0 });

    document.getElementById('pendingCount').textContent = stats.pending;
    document.getElementById('approvedCount').textContent = stats.approved;
    document.getElementById('rejectedCount').textContent = stats.rejected;
}

// Show approval confirmation modal
function showApprovalModal(requestId, name, reason) {
    currentRequestId = requestId;
    document.getElementById('approveUserName').textContent = name;
    document.getElementById('approveUserReason').textContent = reason;
    document.getElementById('approvalModal').style.display = 'block';
}

// Show rejection modal
function showRejectionModal(requestId, name, reason) {
    currentRequestId = requestId;
    document.getElementById('rejectUserName').textContent = name;
    document.getElementById('rejectUserReason').textContent = reason;
    document.getElementById('rejectionReason').value = '';
    document.getElementById('rejectionModal').style.display = 'block';
}

// Close modal
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
    currentRequestId = null;
}

async function approveRequest() {
    if (!currentRequestId) return;

    try {
        await API.put(`/role-change/${currentRequestId}/approve`);
        showSuccess('Permintaan berhasil disetujui');
        closeModal('approvalModal');
        loadRoleRequests();
    } catch (error) {
        console.error('Error:', error);
        showError('Gagal menyetujui permintaan');
    }
}

async function rejectRequest() {
    if (!currentRequestId) return;

    const reason = document.getElementById('rejectionReason').value.trim();
    if (!reason) {
        showError('Alasan penolakan harus diisi');
        return;
    }

    try {
        await API.put(`/role-change/${currentRequestId}/reject`, { reason });
        showSuccess('Permintaan berhasil ditolak');
        closeModal('rejectionModal');
        loadRoleRequests();
    } catch (error) {
        console.error('Error:', error);
        showError('Gagal menolak permintaan');
    }
}

// Filter requests
function filterRequests() {
    loadRoleRequests();
}

// Helper function to get status label
function getStatusLabel(status) {
    const labels = {
        pending: 'Menunggu',
        approved: 'Disetujui',
        rejected: 'Ditolak'
    };
    return labels[status] || status;
}

// Show success message
function showSuccess(message) {
    // Implement your success notification here
    alert(message);
}

// Show error message
function showError(message) {
    // Implement your error notification here
    alert(message);
}

async function checkAdminAuth() {
    if (!Auth.isAuthenticated()) {
        window.location.href = 'index.html';
        return;
    }

    try {
        await API.get('/role-change/requests');
    } catch (error) {
        console.error('Auth Error:', error);
        window.location.href = 'index.html';
    }
}
