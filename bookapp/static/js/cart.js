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
    }).then(res => res.json()).then(data => {
        let counters = document.getElementsByClassName('class-counter');
        for (let counter of counters) {
            counter.innerText = data.total_quantity;
        }

        if (data.inventory_quantity !== undefined) {
            const bookDiv = document.querySelector(`[data-book-id="${id}"]`);
            if (bookDiv) {
                const inventorySpan = bookDiv.querySelector('.inventory-quantity');
                if (inventorySpan) {
                    inventorySpan.textContent = data.inventory_quantity;
                }

                if (data.inventory_quantity <= 0) {
                    const orderBtn = bookDiv.querySelector('.btn-danger');
                    const disabledBtn = document.createElement('button');
                    disabledBtn.className = 'btn btn-secondary';
                    disabledBtn.disabled = true;
                    disabledBtn.textContent = 'Hết hàng';
                    orderBtn.replaceWith(disabledBtn);
                }
            }
        }
    });
}

function updateCart(id, quantity) {
    if (quantity < 1) {
        alert("Số lượng phải lớn hơn 0.");
        location.reload();
        return;
    }
    fetch(`/api/carts/${id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            quantity: parseInt(quantity)
        })
    }).then(res => res.json()).then(data => {
        let counters = document.getElementsByClassName('class-counter');
        for (let counter of counters) {
            counter.innerText = data.cart_stats.total_quantity;
        }
        document.getElementById('total-amount').textContent = data.cart_stats.total_amount.toLocaleString('en') + ' VND';

        if (data.inventory_quantity !== undefined) {
            const row = document.getElementById(`product${id}`);
            const inventorySpan = row.querySelector('.inventory-quantity');
            if (inventorySpan) {
                inventorySpan.textContent = data.inventory_quantity;
            }
        }
    });
}

function deleteCart(id) {
    if (confirm('Bạn có chắc muốn xóa sản phẩm này?')) {
        fetch(`/api/carts/${id}`, {
            method: 'DELETE'
        }).then(res => res.json()).then(data => {
            let counters = document.getElementsByClassName('class-counter');
            for (let counter of counters) {
                counter.innerText = data.total_quantity;
            }
            location.reload();
        });
    }
}