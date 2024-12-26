function addToCart(id, name, price) {
    fetch("/api/carts", {
        method: "POST",
        body: JSON.stringify({
            "id": id,
            "name": name,
            "price": price
        }),
        headers: {
            "Content-Type": "application/json"
        }
    })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            // Cập nhật số lượng trong giỏ hàng
            let counters = document.getElementsByClassName('class-counter');
            for (let counter of counters) {
                counter.innerText = data.total_quantity;
            }

            // Cập nhật số lượng tồn kho trên trang index
            if (data.inventory_quantity !== undefined) {
                const inventoryText = document.querySelector(`[data-book-id="${id}"] .card-text:nth-child(3)`);
                if (inventoryText) {
                    inventoryText.textContent = `Còn lại: ${data.inventory_quantity}`;

                    // Cập nhật trạng thái nút đặt hàng
                    const orderBtn = document.querySelector(`[data-book-id="${id}"] .btn-danger`);
                    const disabledBtn = document.querySelector(`[data-book-id="${id}"] .btn-secondary`);

                    if (data.inventory_quantity <= 0) {
                        orderBtn.style.display = 'none';
                        disabledBtn.style.display = 'inline-block';
                    }
                }
            }
        });
}

function deleteCartItem(id) {
    if (confirm('Bạn có chắc muốn xóa sản phẩm này?')) {
        fetch(`/api/carts/${id}`, {
            method: 'DELETE'
        })
            .then(res => res.json())
            .then(data => {
                let d = document.getElementsByClassName('class-counter');
                for (let e of d) {
                    e.innerText = data.total_quantity;
                }
                window.location.reload();
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Có lỗi xảy ra');
            });
    }
}

function updateQuantity(id, newQuantity, price) {
    if (newQuantity < 1) {
        alert('Số lượng phải lớn hơn 0');
        return;
    }

    fetch(`/api/carts/${id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            quantity: parseInt(newQuantity)
        })
    })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                window.location.reload();
                return;
            }

            const row = document.querySelector(`tr[data-id="${id}"]`);

            // Cập nhật tổng số lượng và tổng tiền
            document.getElementById('total-quantity').textContent = data.cart_stats.total_quantity;
            document.getElementById('total-amount').textContent =
                new Intl.NumberFormat('vi-VN').format(data.cart_stats.total_amount);

            // Cập nhật thành tiền của sản phẩm
            const totalCell = row.querySelector('.product-total');
            totalCell.textContent = new Intl.NumberFormat('vi-VN').format(data.product_total) + ' VND';

            // Cập nhật số lượng tồn kho
            const inventorySpan = row.querySelector('.inventory-quantity');
            if (data.inventory_quantity !== undefined) {
                inventorySpan.textContent = data.inventory_quantity;

                // Cập nhật max của input
                const quantityInput = row.querySelector('.quantity-input');
                quantityInput.max = parseInt(newQuantity) + data.inventory_quantity;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Có lỗi xảy ra khi cập nhật số lượng!');
        });
}

function updateTotals() {
    let totalQuantity = 0;
    let totalAmount = 0;

    const rows = document.querySelectorAll('tr[data-id]');

    rows.forEach(row => {
        const quantity = parseInt(row.querySelector('.quantity-input').value);
        const price = parseFloat(row.getAttribute('data-price'));

        totalQuantity += quantity;
        totalAmount += price * quantity;
    });

    document.getElementById('total-quantity').textContent = totalQuantity;
    document.getElementById('total-amount').textContent = formatCurrency(totalAmount);
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('vi-VN').format(amount);
}

document.addEventListener('DOMContentLoaded', function () {
    updateTotals();
});