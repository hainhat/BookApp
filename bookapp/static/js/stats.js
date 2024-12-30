function drawChart(id = 'myChart', type = 'bar', labels, data, title = 'Số lượng') {
    const ctx = document.getElementById(id);
    new Chart(ctx, {
        type: type,
        data: {
            labels: labels,
            datasets: [{
                label: title,
                data: data,
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}