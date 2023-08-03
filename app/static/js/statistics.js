function loadChart(ctx, labels, data, type, colors, borderColors) {
        new Chart(ctx, {
            type: type,
            data: {
              labels: labels,
              datasets: [{
                label: 'Doanh thu',
                data: data,
                borderWidth: 1,
                backgroundColor: borderColors
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