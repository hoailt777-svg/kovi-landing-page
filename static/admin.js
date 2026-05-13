// Global state
let currentEditingProduct = null;
let currentEditingCustomer = null;
let currentEditingOrder = null;

// Tab switching
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        const tab = e.target.dataset.tab;
        switchTab(tab);
    });
});

function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Deactivate all buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName).classList.add('active');
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // Load data
    if (tabName === 'products') loadProducts();
    if (tabName === 'customers') loadCustomers();
    if (tabName === 'orders') loadOrders();
}

// ========== PRODUCTS ==========

function loadProducts() {
    fetch('/api/products')
        .then(r => r.json())
        .then(products => {
            const tbody = document.getElementById('products-tbody');
            tbody.innerHTML = '';
            
            if (products.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="empty-message">Chưa có sản phẩm nào</td></tr>';
                return;
            }
            
            products.forEach(p => {
                const row = `
                    <tr>
                        <td>${p.id}</td>
                        <td><strong>${p.name}</strong></td>
                        <td>${p.price.toLocaleString()} đ</td>
                        <td><span class="quantity-badge">${p.quantity_available}</span></td>
                        <td>${p.description || '-'}</td>
                        <td>
                            <div class="action-btn">
                                <button class="btn btn-edit" onclick="editProduct(${p.id})">✏️ Sửa</button>
                                <button class="btn btn-delete" onclick="deleteProduct(${p.id})">🗑️ Xóa</button>
                            </div>
                        </td>
                    </tr>
                `;
                tbody.innerHTML += row;
            });
        })
        .catch(err => showAlert('Lỗi tải sản phẩm: ' + err, 'error'));
}

function openProductModal() {
    currentEditingProduct = null;
    document.getElementById('productId').value = '';
    document.getElementById('productName').value = '';
    document.getElementById('productPrice').value = '';
    document.getElementById('productQuantity').value = '';
    document.getElementById('productDescription').value = '';
    document.getElementById('productModalTitle').textContent = 'Thêm Sản Phẩm';
    document.getElementById('productModal').style.display = 'block';
}

function closeProductModal() {
    document.getElementById('productModal').style.display = 'none';
}

function editProduct(id) {
    fetch(`/api/products`)
        .then(r => r.json())
        .then(products => {
            const product = products.find(p => p.id === id);
            currentEditingProduct = id;
            document.getElementById('productId').value = product.id;
            document.getElementById('productName').value = product.name;
            document.getElementById('productPrice').value = product.price;
            document.getElementById('productQuantity').value = product.quantity_available;
            document.getElementById('productDescription').value = product.description || '';
            document.getElementById('productModalTitle').textContent = 'Chỉnh Sửa Sản Phẩm';
            document.getElementById('productModal').style.display = 'block';
        });
}

function deleteProduct(id) {
    if (confirm('Bạn chắc chắn muốn xóa sản phẩm này?')) {
        fetch(`/api/products/${id}`, { method: 'DELETE' })
            .then(r => r.json())
            .then(() => {
                showAlert('Xóa sản phẩm thành công!', 'success');
                loadProducts();
            })
            .catch(err => showAlert('Lỗi: ' + err, 'error'));
    }
}

document.getElementById('productForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const data = {
        name: document.getElementById('productName').value,
        price: parseFloat(document.getElementById('productPrice').value),
        quantity_available: parseInt(document.getElementById('productQuantity').value),
        description: document.getElementById('productDescription').value
    };
    
    const url = currentEditingProduct ? `/api/products/${currentEditingProduct}` : '/api/products';
    const method = currentEditingProduct ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
        .then(r => r.json())
        .then(() => {
            showAlert(currentEditingProduct ? 'Cập nhật sản phẩm thành công!' : 'Thêm sản phẩm thành công!', 'success');
            closeProductModal();
            loadProducts();
        })
        .catch(err => showAlert('Lỗi: ' + err, 'error'));
});

// ========== CUSTOMERS ==========

function loadCustomers() {
    fetch('/api/customers')
        .then(r => r.json())
        .then(customers => {
            const tbody = document.getElementById('customers-tbody');
            tbody.innerHTML = '';
            
            if (customers.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="empty-message">Chưa có khách hàng nào</td></tr>';
                return;
            }
            
            customers.forEach(c => {
                const row = `
                    <tr>
                        <td>${c.id}</td>
                        <td><strong>${c.name}</strong></td>
                        <td>${c.phone || '-'}</td>
                        <td>${c.zalo || '-'}</td>
                        <td>${c.email || '-'}</td>
                        <td>${c.address || '-'}</td>
                        <td>
                            <div class="action-btn">
                                <button class="btn btn-edit" onclick="editCustomer(${c.id})">✏️ Sửa</button>
                                <button class="btn btn-delete" onclick="deleteCustomer(${c.id})">🗑️ Xóa</button>
                            </div>
                        </td>
                    </tr>
                `;
                tbody.innerHTML += row;
            });
        })
        .catch(err => showAlert('Lỗi tải khách hàng: ' + err, 'error'));
}

function openCustomerModal() {
    currentEditingCustomer = null;
    document.getElementById('customerId').value = '';
    document.getElementById('customerName').value = '';
    document.getElementById('customerPhone').value = '';
    document.getElementById('customerZalo').value = '';
    document.getElementById('customerEmail').value = '';
    document.getElementById('customerAddress').value = '';
    document.getElementById('customerModalTitle').textContent = 'Thêm Khách Hàng';
    document.getElementById('customerModal').style.display = 'block';
}

function closeCustomerModal() {
    document.getElementById('customerModal').style.display = 'none';
}

function editCustomer(id) {
    fetch(`/api/customers`)
        .then(r => r.json())
        .then(customers => {
            const customer = customers.find(c => c.id === id);
            currentEditingCustomer = id;
            document.getElementById('customerId').value = customer.id;
            document.getElementById('customerName').value = customer.name;
            document.getElementById('customerPhone').value = customer.phone || '';
            document.getElementById('customerZalo').value = customer.zalo || '';
            document.getElementById('customerEmail').value = customer.email || '';
            document.getElementById('customerAddress').value = customer.address || '';
            document.getElementById('customerModalTitle').textContent = 'Chỉnh Sửa Khách Hàng';
            document.getElementById('customerModal').style.display = 'block';
        });
}

function deleteCustomer(id) {
    if (confirm('Bạn chắc chắn muốn xóa khách hàng này?')) {
        fetch(`/api/customers/${id}`, { method: 'DELETE' })
            .then(r => r.json())
            .then(() => {
                showAlert('Xóa khách hàng thành công!', 'success');
                loadCustomers();
            })
            .catch(err => showAlert('Lỗi: ' + err, 'error'));
    }
}

document.getElementById('customerForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const data = {
        name: document.getElementById('customerName').value,
        phone: document.getElementById('customerPhone').value,
        zalo: document.getElementById('customerZalo').value,
        email: document.getElementById('customerEmail').value,
        address: document.getElementById('customerAddress').value
    };
    
    const url = currentEditingCustomer ? `/api/customers/${currentEditingCustomer}` : '/api/customers';
    const method = currentEditingCustomer ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
        .then(r => r.json())
        .then(() => {
            showAlert(currentEditingCustomer ? 'Cập nhật khách hàng thành công!' : 'Thêm khách hàng thành công!', 'success');
            closeCustomerModal();
            loadCustomers();
        })
        .catch(err => showAlert('Lỗi: ' + err, 'error'));
});

// ========== ORDERS ==========

function loadOrders() {
    fetch('/api/orders')
        .then(r => r.json())
        .then(orders => {
            const tbody = document.getElementById('orders-tbody');
            tbody.innerHTML = '';
            
            if (orders.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" class="empty-message">Chưa có đơn hàng nào</td></tr>';
                return;
            }
            
            orders.forEach(o => {
                const activateBtn = o.status === 'pending' ? `<button class="btn btn-success" onclick="activateOrder(${o.id})">💰 Kích hoạt</button>` : '';
                const row = `
                    <tr>
                        <td>${o.id}</td>
                        <td><strong>${o.customer_name}</strong></td>
                        <td>${o.product_name}</td>
                        <td>${o.quantity}</td>
                        <td>${o.total_amount.toLocaleString()} đ</td>
                        <td><span class="status-badge status-${o.status}">${getStatusText(o.status)}</span></td>
                        <td>${new Date(o.order_date).toLocaleDateString('vi-VN')}</td>
                        <td>
                            <div class="action-btn">
                                ${activateBtn}
                                <button class="btn btn-edit" onclick="editOrder(${o.id})">✏️ Sửa</button>
                                <button class="btn btn-delete" onclick="deleteOrder(${o.id})">🗑️ Xóa</button>
                            </div>
                        </td>
                    </tr>
                `;
                tbody.innerHTML += row;
            });
        })
        .catch(err => showAlert('Lỗi tải đơn hàng: ' + err, 'error'));
}

function activateOrder(id) {
    if (confirm('Xác nhận kích hoạt thanh toán thành công cho đơn hàng này?')) {
        fetch(`/api/orders/${id}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'success' })
        })
        .then(r => r.json())
        .then(res => {
            if (res.success) {
                showAlert('Đơn hàng đã được kích hoạt thành công!', 'success');
                loadOrders();
            } else {
                showAlert('Lỗi: ' + res.message, 'error');
            }
        })
        .catch(err => showAlert('Lỗi: ' + err, 'error'));
    }
}

function getStatusText(status) {
    const statusMap = {
        'pending': '⏳ Chờ xác nhận',
        'confirmed': '✅ Đã xác nhận',
        'shipped': '📦 Đã gửi',
        'success': '💰 Đã thanh toán',
        'completed': '✔️ Hoàn thành',
        'cancelled': '❌ Hủy'
    };
    return statusMap[status] || status;
}

function openOrderModal() {
    currentEditingOrder = null;
    document.getElementById('orderId').value = '';
    document.getElementById('orderCustomer').value = '';
    document.getElementById('orderProduct').value = '';
    document.getElementById('orderQuantity').value = '1';
    document.getElementById('orderTotal').value = '';
    document.getElementById('orderStatus').value = 'pending';
    document.getElementById('orderModalTitle').textContent = 'Thêm Đơn Hàng';
    
    // Load customers
    fetch('/api/customers')
        .then(r => r.json())
        .then(customers => {
            const select = document.getElementById('orderCustomer');
            select.innerHTML = '<option value="">-- Chọn khách hàng --</option>';
            customers.forEach(c => {
                select.innerHTML += `<option value="${c.id}">${c.name} (${c.phone})</option>`;
            });
        });
    
    // Load products
    fetch('/api/products')
        .then(r => r.json())
        .then(products => {
            const select = document.getElementById('orderProduct');
            select.innerHTML = '<option value="">-- Chọn sản phẩm --</option>';
            products.forEach(p => {
                select.innerHTML += `<option value="${p.id}" data-price="${p.price}" data-qty="${p.quantity_available}">${p.name} (${p.price.toLocaleString()} đ)</option>`;
            });
        });
    
    document.getElementById('orderModal').style.display = 'block';
}

function closeOrderModal() {
    document.getElementById('orderModal').style.display = 'none';
}

function updateOrderPrice() {
    const productSelect = document.getElementById('orderProduct');
    const quantity = parseInt(document.getElementById('orderQuantity').value) || 0;
    
    if (productSelect.value) {
        const option = productSelect.selectedOptions[0];
        const price = parseFloat(option.dataset.price);
        const availableQty = parseInt(option.dataset.qty);
        
        if (quantity > availableQty && !currentEditingOrder) {
            showAlert(`Không đủ hàng. Còn lại: ${availableQty}`, 'error');
            document.getElementById('orderQuantity').value = availableQty;
        }
        
        const total = price * quantity;
        document.getElementById('orderTotal').value = total;
    }
}

function editOrder(id) {
    fetch(`/api/orders`)
        .then(r => r.json())
        .then(orders => {
            const order = orders.find(o => o.id === id);
            currentEditingOrder = id;
            
            // Load customers
            fetch('/api/customers')
                .then(r => r.json())
                .then(customers => {
                    const select = document.getElementById('orderCustomer');
                    select.innerHTML = '';
                    customers.forEach(c => {
                        select.innerHTML += `<option value="${c.id}" ${c.id === order.customer_id ? 'selected' : ''}>${c.name}</option>`;
                    });
                });
            
            // Load products
            fetch('/api/products')
                .then(r => r.json())
                .then(products => {
                    const select = document.getElementById('orderProduct');
                    select.innerHTML = '';
                    products.forEach(p => {
                        select.innerHTML += `<option value="${p.id}" data-price="${p.price}" data-qty="${p.quantity_available}" ${p.id === order.product_id ? 'selected' : ''}>${p.name}</option>`;
                    });
                });
            
            document.getElementById('orderId').value = order.id;
            document.getElementById('orderQuantity').value = order.quantity;
            document.getElementById('orderTotal').value = order.total_amount;
            document.getElementById('orderStatus').value = order.status;
            document.getElementById('orderModalTitle').textContent = 'Chỉnh Sửa Đơn Hàng';
            document.getElementById('orderModal').style.display = 'block';
        });
}

function deleteOrder(id) {
    if (confirm('Bạn chắc chắn muốn xóa đơn hàng này? Số lượng sản phẩm sẽ được hoàn lại.')) {
        fetch(`/api/orders/${id}`, { method: 'DELETE' })
            .then(r => r.json())
            .then(() => {
                showAlert('Xóa đơn hàng thành công!', 'success');
                loadOrders();
                loadProducts(); // Refresh products to update quantity
            })
            .catch(err => showAlert('Lỗi: ' + err, 'error'));
    }
}

document.getElementById('orderForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const data = {
        customer_id: parseInt(document.getElementById('orderCustomer').value),
        product_id: parseInt(document.getElementById('orderProduct').value),
        quantity: parseInt(document.getElementById('orderQuantity').value),
        total_amount: parseFloat(document.getElementById('orderTotal').value),
        status: document.getElementById('orderStatus').value
    };
    
    const url = currentEditingOrder ? `/api/orders/${currentEditingOrder}` : '/api/orders';
    const method = currentEditingOrder ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
        .then(r => r.json())
        .then((result) => {
            if (result.error) {
                showAlert('Lỗi: ' + result.error, 'error');
            } else {
                showAlert(currentEditingOrder ? 'Cập nhật đơn hàng thành công!' : 'Thêm đơn hàng thành công!', 'success');
                closeOrderModal();
                loadOrders();
                loadProducts();
            }
        })
        .catch(err => showAlert('Lỗi: ' + err, 'error'));
});

// Utilities
function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    document.body.insertBefore(alertDiv, document.body.firstChild);
    
    setTimeout(() => alertDiv.remove(), 3000);
}

// Close modal when clicking outside
window.onclick = function(event) {
    let modal = document.getElementById('productModal');
    if (event.target === modal) modal.style.display = 'none';
    
    modal = document.getElementById('customerModal');
    if (event.target === modal) modal.style.display = 'none';
    
    modal = document.getElementById('orderModal');
    if (event.target === modal) modal.style.display = 'none';
}

// Load products on page load
loadProducts();
