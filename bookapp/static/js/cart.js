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
            let d = document.getElementsByClassName('class-counter');
            for (let e of d) {
                e.innerText = data.total_quantity
            }
        })
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
            document.getElementById('total-quantity').textContent = data.cart_stats.total_quantity;
            document.getElementById('total-amount').textContent =
                new Intl.NumberFormat('vi-VN').format(data.cart_stats.total_amount);
            const row = document.querySelector(`tr[data-id="${id}"]`);
            const totalCell = row.querySelector('.product-total');
            totalCell.textContent = new Intl.NumberFormat('vi-VN').format(data.product_total) + ' VND';
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Có lỗi xảy ra');
            window.location.reload();
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