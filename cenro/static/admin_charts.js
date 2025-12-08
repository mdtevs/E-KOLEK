/**
 * Admin Dashboard Charts
 * Initializes Chart.js charts for the admin landing page
 */

document.addEventListener('DOMContentLoaded', function() {
    // User Growth Chart - Doughnut
    const userCtx = document.getElementById('userGrowthChart');
    if (userCtx) {
        const totalUsers = parseInt(userCtx.dataset.totalUsers) || 0;
        const pendingUsers = parseInt(userCtx.dataset.pendingUsers) || 0;
        
        new Chart(userCtx, {
            type: 'doughnut',
            data: {
                labels: ['Approved Users', 'Pending Approval'],
                datasets: [{
                    data: [totalUsers, pendingUsers],
                    backgroundColor: [
                        'rgba(102, 126, 234, 0.8)',
                        'rgba(255, 159, 64, 0.8)'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            font: { size: 12 }
                        }
                    }
                }
            }
        });
    }

    // Waste Collection Impact Chart - Bar chart for better visibility
    const wasteCtx = document.getElementById('wasteCollectionChart');
    if (wasteCtx) {
        const totalWaste = parseFloat(wasteCtx.dataset.totalWaste) || 0;
        const wasteCount = parseInt(wasteCtx.dataset.wasteCount) || 0;
        const wasteThisMonth = parseFloat(wasteCtx.dataset.wasteThisMonth) || 0;
        
        // Calculate average per transaction
        const avgPerTransaction = wasteCount > 0 ? parseFloat((totalWaste / wasteCount).toFixed(2)) : 0;
        
        console.log('Waste Chart Data:', {
            totalWaste,
            wasteCount,
            wasteThisMonth,
            avgPerTransaction
        });
        
        new Chart(wasteCtx, {
            type: 'bar',
            data: {
                labels: ['Total Collected', 'This Month', 'Avg per Transaction'],
                datasets: [{
                    label: 'Waste (kg)',
                    data: [totalWaste, wasteThisMonth, avgPerTransaction],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(245, 158, 11, 0.8)'
                    ],
                    borderColor: [
                        'rgba(16, 185, 129, 1)',
                        'rgba(59, 130, 246, 1)',
                        'rgba(245, 158, 11, 1)'
                    ],
                    borderWidth: 2,
                    borderRadius: 8,
                    hoverBackgroundColor: [
                        'rgba(16, 185, 129, 1)',
                        'rgba(59, 130, 246, 1)',
                        'rgba(245, 158, 11, 1)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value.toFixed(1) + ' kg';
                            },
                            font: {
                                size: 11
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                size: 10
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleFont: {
                            size: 13,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: 12
                        },
                        callbacks: {
                            label: function(context) {
                                return 'Weight: ' + context.parsed.y.toFixed(2) + ' kg';
                            }
                        }
                    }
                }
            }
        });
    }

    // Rewards Activity Chart - Pie
    const rewardsCtx = document.getElementById('rewardsChart');
    if (rewardsCtx) {
        const activeRewards = parseInt(rewardsCtx.dataset.activeRewards) || 0;
        const totalRedemptions = parseInt(rewardsCtx.dataset.totalRedemptions) || 0;
        
        new Chart(rewardsCtx, {
            type: 'pie',
            data: {
                labels: ['Active Rewards', 'Total Redemptions'],
                datasets: [{
                    data: [activeRewards, totalRedemptions],
                    backgroundColor: [
                        'rgba(240, 147, 251, 0.8)',
                        'rgba(67, 233, 123, 0.8)'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            font: { size: 12 }
                        }
                    }
                }
            }
        });
    }
});
