function searchBooks() {
    const query = document.getElementById('searchInput').value.trim();
    console.log("Search query:", query); // Kiểm tra query

    if (!query) {
        document.getElementById('searchResultsBody').innerHTML = `
            <tr>
                <td colspan="4" class="text-center text-muted">
                    Nhập tên sách và bấm tìm kiếm
                </td>
            </tr>`;
        return;
    }

    fetch(`/api/books/search?q=${encodeURIComponent(query)}`)
        .then(res => res.json())
        .then(books => {
            console.log("Search results:", books); // Kiểm tra dữ liệu trả về
            const tbody = document.getElementById('searchResultsBody');
            if (books.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="4" class="text-center text-muted">
                            Không tìm thấy sách phù hợp
                        </td>
                    </tr>`;
                return;
            }
            tbody.innerHTML = books.map(book => `
                <tr>
                    <td>${book.name}</td>
                    <td class="text-end">${new Intl.NumberFormat('vi-VN').format(book.price)} VND</td>
                    <td class="text-center">
                        <span class="badge bg-${book.inventory > 0 ? 'success' : 'danger'}">
                            ${book.inventory}
                        </span>
                    </td>
                    <td class="text-center">
                        <button class="btn btn-sm btn-primary" 
                                onclick="addToReceipt(${book.id}, '${book.name}', ${book.price})"
                                ${book.inventory <= 0 ? 'disabled' : ''}>
                            <i class="bi bi-plus"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
        })
        .catch(err => {
            console.error('Error:', err);
            document.getElementById('searchResultsBody').innerHTML = `
                <tr>
                    <td colspan="4" class="text-center text-danger">
                        Có lỗi xảy ra khi tìm kiếm: ${err.message}
                    </td>
                </tr>`;
        });
}

function addToReceipt(id, name, price) {
    fetch('/api/receipt/add_book', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({id, name, price, quantity: 1})
    })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            updateReceiptUI(data.cart);
            searchBooks(); // Refresh search results for inventory update
        });
}

function updateQuantity(id, newQuantity) {
    if (newQuantity < 1) return;

    fetch('/api/receipt/update_quantity', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({id, quantity: newQuantity})
    })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            updateReceiptUI(data.cart);
            searchBooks(); // Refresh search results
        });
}

function removeFromReceipt(id) {
    if (confirm('Bạn có chắc muốn xóa sách này khỏi hóa đơn?')) {
        fetch(`/api/receipt/remove_book?id=${id}`, {
            method: 'DELETE'
        })
            .then(res => res.json())
            .then(data => {
                updateReceiptUI(data.cart);
                searchBooks(); // Refresh search results
            });
    }
}

function updateReceiptUI(cart) {
    const tbody = document.getElementById('receiptItems');
    const totalAmount = document.getElementById('totalAmount');
    let total = 0;

    if (!cart || Object.keys(cart).length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Chưa có sách trong hóa đơn</td></tr>';
        totalAmount.textContent = '0 VND';
        return;
    }

    tbody.innerHTML = Object.values(cart).map(item => {
        const itemTotal = item.price * item.quantity;
        total += itemTotal;
        return `
           <tr>
               <td>${item.name}</td>
               <td class="text-center">
                   <div class="input-group input-group-sm">
                       <button class="btn btn-outline-secondary btn-sm" onclick="updateQuantity(${item.id}, ${item.quantity - 1})">-</button>
                       <input type="number" class="form-control text-center" value="${item.quantity}" 
                              min="1" style="width: 50px"
                              onchange="updateQuantity(${item.id}, parseInt(this.value) || 1)">
                       <button class="btn btn-outline-secondary btn-sm" onclick="updateQuantity(${item.id}, ${item.quantity + 1})">+</button>
                   </div>
               </td>
               <td class="text-end">${new Intl.NumberFormat('vi-VN').format(itemTotal)} VND</td>
               <td>
                   <button class="btn btn-sm btn-danger" onclick="removeFromReceipt(${item.id})">
                       <i class="bi bi-x"></i>
                   </button>
               </td>
           </tr>
       `;
    }).join('');

    totalAmount.textContent = new Intl.NumberFormat('vi-VN').format(total) + ' VND';
}

function completeReceipt() {
    fetch('/api/receipt/complete', {
        method: 'POST'
    })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }

            document.getElementById('receiptDetails').innerHTML = `
           <div class="text-center mb-4">
               <i class="bi bi-check-circle-fill text-success" style="font-size: 48px;"></i>
               <h4 class="mt-3">Thanh toán thành công!</h4>
           </div>
           <div class="text-center">
               <p class="mb-1">Mã hóa đơn: <strong>#${data.receipt_id}</strong></p>
               <p class="mb-1">Tổng tiền: <strong>${new Intl.NumberFormat('vi-VN').format(data.total_amount)} VND</strong></p>
               <p class="mb-0">Thời gian: <strong>${new Date().toLocaleString('vi-VN')}</strong></p>
           </div>
       `;

            const receiptModal = new bootstrap.Modal(document.getElementById('receiptModal'));
            receiptModal.show();
        });
}

// Tự động focus vào ô tìm kiếm khi trang load xong
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('searchInput').focus();
});

// Bắt sự kiện Enter trong ô tìm kiếm
document.getElementById('searchInput').addEventListener('keyup', function (e) {
    if (e.key === 'Enter') {
        searchBooks();
    }
});