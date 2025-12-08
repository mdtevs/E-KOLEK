/**
 * Admin Analytics Charts Configuration
 * Chart.js configurations for waste analytics dashboard
 * Handles: Doughnut charts, Bar charts, Line charts, and Monthly tracking
 */

/* ==================== CHART INITIALIZATION ==================== */

/**
 * Initialize all analytics charts with data from Django templates
 */
function initializeAnalyticsCharts() {
  // Parse chart data from Django (set by template)
  const wasteTypeData = window.WASTE_TYPE_DATA;
  const barangayData = window.BARANGAY_DATA;
  const wasteTypeBarData = window.WASTE_TYPE_BAR_DATA;
  const monthlyTrackingData = window.MONTHLY_TRACKING_DATA;

  // Color palette for charts
  const colorPalette = [
    '#667eea', '#764ba2', '#f093fb', '#4facfe',
    '#43e97b', '#38f9d7', '#fa709a', '#fee140',
    '#30cfd0', '#330867', '#a8edea', '#fed6e3'
  ];

  // Initialize each chart
  initWasteTypeDoughnutChart(wasteTypeData, colorPalette);
  initBarangayBarChart(barangayData);
  initWasteTypeComparisonChart(wasteTypeBarData);
  initMonthlyTrackingChart(monthlyTrackingData);
}

/* ==================== WASTE TYPE DOUGHNUT CHART ==================== */

/**
 * Initialize waste type distribution doughnut chart
 * @param {Object} wasteTypeData - Waste type data with labels, weights, counts
 * @param {Array} colorPalette - Array of color codes
 */
function initWasteTypeDoughnutChart(wasteTypeData, colorPalette) {
  const ctx = document.getElementById('wasteTypeChart');
  if (!ctx) return;

  new Chart(ctx.getContext('2d'), {
    type: 'doughnut',
    data: {
      labels: wasteTypeData.labels,
      datasets: [{
        data: wasteTypeData.weights,
        backgroundColor: colorPalette,
        borderWidth: 3,
        borderColor: '#fff',
        hoverBorderColor: '#fff',
        hoverBorderWidth: 4
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
            font: {
              size: 12,
              family: "'Poppins', sans-serif"
            },
            usePointStyle: true,
            pointStyle: 'circle'
          }
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          padding: 12,
          titleFont: {
            size: 14,
            weight: 'bold'
          },
          bodyFont: {
            size: 13
          },
          callbacks: {
            label: function(context) {
              const label = context.label || '';
              const value = context.parsed;
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const percentage = ((value / total) * 100).toFixed(1);
              return [
                `${label}: ${value.toFixed(2)} kg`,
                `${percentage}% of total`,
                `${wasteTypeData.counts[context.dataIndex]} transactions`
              ];
            }
          }
        }
      }
    }
  });
}

/* ==================== BARANGAY BAR CHART ==================== */

/**
 * Initialize barangay waste collection horizontal bar chart
 * @param {Object} barangayData - Barangay data with labels, weights, counts
 */
function initBarangayBarChart(barangayData) {
  const ctx = document.getElementById('barangayChart');
  if (!ctx) return;

  new Chart(ctx.getContext('2d'), {
    type: 'bar',
    data: {
      labels: barangayData.labels,
      datasets: [{
        label: 'Weight (kg)',
        data: barangayData.weights,
        backgroundColor: 'rgba(102, 126, 234, 0.85)',
        borderColor: 'rgba(102, 126, 234, 1)',
        borderWidth: 2,
        borderRadius: 8,
        barThickness: 35
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: true,
      scales: {
        x: {
          beginAtZero: true,
          grid: {
            color: 'rgba(0, 0, 0, 0.05)'
          },
          ticks: {
            callback: function(value) {
              return value.toFixed(0) + ' kg';
            },
            font: {
              size: 11
            }
          }
        },
        y: {
          grid: {
            display: false
          },
          ticks: {
            font: {
              size: 12,
              weight: '600'
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
          callbacks: {
            label: function(context) {
              return [
                `Weight: ${context.parsed.x.toFixed(2)} kg`,
                `Transactions: ${barangayData.counts[context.dataIndex]}`
              ];
            }
          }
        }
      }
    }
  });
}

/* ==================== WASTE TYPE COMPARISON CHART ==================== */

/**
 * Initialize waste type comparison dual-axis bar chart
 * @param {Object} wasteTypeBarData - Waste type data with labels, weights, transactions, points
 */
function initWasteTypeComparisonChart(wasteTypeBarData) {
  const ctx = document.getElementById('wasteTypeBarChart');
  if (!ctx) return;

  new Chart(ctx.getContext('2d'), {
    type: 'bar',
    data: {
      labels: wasteTypeBarData.labels,
      datasets: [
        {
          label: 'Total Weight (kg)',
          data: wasteTypeBarData.weights,
          backgroundColor: 'rgba(102, 126, 234, 0.8)',
          borderColor: 'rgba(102, 126, 234, 1)',
          borderWidth: 2,
          borderRadius: 6,
          yAxisID: 'y',
          order: 2
        },
        {
          label: 'Number of Transactions',
          data: wasteTypeBarData.transactions,
          backgroundColor: 'rgba(16, 185, 129, 0.8)',
          borderColor: 'rgba(16, 185, 129, 1)',
          borderWidth: 2,
          borderRadius: 6,
          yAxisID: 'y1',
          order: 1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      interaction: {
        mode: 'index',
        intersect: false
      },
      scales: {
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          beginAtZero: true,
          grid: {
            color: 'rgba(0, 0, 0, 0.05)'
          },
          ticks: {
            callback: function(value) {
              return value.toFixed(0) + ' kg';
            },
            font: {
              size: 11
            }
          },
          title: {
            display: true,
            text: 'Weight (kg)',
            font: {
              size: 12,
              weight: 'bold'
            },
            color: '#667eea'
          }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          beginAtZero: true,
          grid: {
            drawOnChartArea: false
          },
          ticks: {
            callback: function(value) {
              return value.toFixed(0);
            },
            font: {
              size: 11
            }
          },
          title: {
            display: true,
            text: 'Transactions',
            font: {
              size: 12,
              weight: 'bold'
            },
            color: '#10b981'
          }
        },
        x: {
          grid: {
            display: false
          },
          ticks: {
            font: {
              size: 11,
              weight: '600'
            }
          }
        }
      },
      plugins: {
        legend: {
          position: 'top',
          labels: {
            padding: 15,
            font: {
              size: 12,
              family: "'Poppins', sans-serif"
            },
            usePointStyle: true
          }
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
            afterLabel: function(context) {
              if (context.datasetIndex === 0) {
                return `Points: ${wasteTypeBarData.points[context.dataIndex].toFixed(0)}`;
              }
              return '';
            }
          }
        }
      }
    }
  });
}

/* ==================== MONTHLY TRACKING CHART ==================== */

/**
 * Initialize monthly waste tracking line chart with enhanced features
 * @param {Object} monthlyTrackingData - Monthly data with months, datasets, counts
 */
function initMonthlyTrackingChart(monthlyTrackingData) {
  const ctx = document.getElementById('monthlyTrackingChart');
  if (!ctx) return;

  // Professional gradient color palette for waste types
  const monthlyColorPalette = [
    { primary: '#667eea', gradient: 'rgba(102, 126, 234, 0.15)' },
    { primary: '#10b981', gradient: 'rgba(16, 185, 129, 0.15)' },
    { primary: '#f59e0b', gradient: 'rgba(245, 158, 11, 0.15)' },
    { primary: '#ef4444', gradient: 'rgba(239, 68, 68, 0.15)' },
    { primary: '#3b82f6', gradient: 'rgba(59, 130, 246, 0.15)' },
    { primary: '#ec4899', gradient: 'rgba(236, 72, 153, 0.15)' },
    { primary: '#8b5cf6', gradient: 'rgba(139, 92, 246, 0.15)' },
    { primary: '#14b8a6', gradient: 'rgba(20, 184, 166, 0.15)' },
    { primary: '#f97316', gradient: 'rgba(249, 115, 22, 0.15)' },
    { primary: '#06b6d4', gradient: 'rgba(6, 182, 212, 0.15)' },
    { primary: '#a855f7', gradient: 'rgba(168, 85, 247, 0.15)' },
    { primary: '#84cc16', gradient: 'rgba(132, 204, 22, 0.15)' },
  ];

  // Prepare enhanced datasets for monthly chart
  const monthlyDatasets = monthlyTrackingData.datasets.map((dataset, index) => {
    const colorScheme = monthlyColorPalette[index % monthlyColorPalette.length];
    return {
      label: dataset.label,
      data: dataset.data,
      borderColor: colorScheme.primary,
      backgroundColor: colorScheme.gradient,
      borderWidth: 3,
      tension: 0.4,
      fill: true,
      pointRadius: 6,
      pointHoverRadius: 10,
      pointBackgroundColor: colorScheme.primary,
      pointBorderColor: '#fff',
      pointBorderWidth: 3,
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: colorScheme.primary,
      pointHoverBorderWidth: 4,
      pointStyle: 'circle',
    };
  });

  // Create dynamic legend with totals
  const legendContainer = document.getElementById('monthlyChartLegend');
  if (legendContainer && monthlyTrackingData.datasets.length > 0) {
    monthlyTrackingData.datasets.forEach((dataset, index) => {
      const total = dataset.data.reduce((a, b) => a + b, 0);
      const colorScheme = monthlyColorPalette[index % monthlyColorPalette.length];
      const transactionTotal = dataset.counts ? dataset.counts.reduce((a, b) => a + b, 0) : 0;
      
      const legendItem = document.createElement('div');
      legendItem.className = 'legend-badge';
      legendItem.style.background = colorScheme.primary;
      legendItem.innerHTML = `
        ${dataset.label}: ${total.toFixed(1)} kg
        <span style="opacity: 0.8; font-size: 0.7rem;"> (${transactionTotal} transactions)</span>
      `;
      legendContainer.appendChild(legendItem);
    });
  }

  // Create the monthly tracking chart
  new Chart(ctx.getContext('2d'), {
    type: 'line',
    data: {
      labels: monthlyTrackingData.months,
      datasets: monthlyDatasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          backgroundColor: 'rgba(31, 41, 55, 0.96)',
          titleColor: '#fff',
          bodyColor: '#fff',
          padding: 16,
          borderColor: '#667eea',
          borderWidth: 2,
          displayColors: true,
          usePointStyle: true,
          titleFont: {
            size: 14,
            weight: 'bold'
          },
          bodyFont: {
            size: 13
          },
          callbacks: {
            title: function(context) {
              return `📅 ${context[0].label}`;
            },
            label: function(context) {
              const wasteType = context.dataset.label;
              const weight = context.parsed.y.toFixed(2);
              const datasetIndex = context.datasetIndex;
              const monthIndex = context.dataIndex;
              
              let transactionCount = 0;
              if (monthlyTrackingData.datasets[datasetIndex] && 
                  monthlyTrackingData.datasets[datasetIndex].counts) {
                transactionCount = monthlyTrackingData.datasets[datasetIndex].counts[monthIndex];
              }
              
              return [
                `${wasteType}: ${weight} kg`,
                `📊 Transactions: ${transactionCount}`
              ];
            },
            footer: function(context) {
              let total = 0;
              let totalTransactions = 0;
              context.forEach((item, idx) => {
                total += item.parsed.y;
                if (monthlyTrackingData.datasets[idx] && 
                    monthlyTrackingData.datasets[idx].counts) {
                  totalTransactions += monthlyTrackingData.datasets[idx].counts[item.dataIndex] || 0;
                }
              });
              return `\n━━━━━━━━━━━━━━━━\n💼 Total: ${total.toFixed(2)} kg\n📋 Total Transactions: ${totalTransactions}`;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Weight Collected (kg)',
            font: {
              size: 14,
              weight: '700'
            },
            padding: {top: 10, bottom: 15},
            color: '#374151'
          },
          ticks: {
            callback: function(value) {
              return value.toFixed(1) + ' kg';
            },
            font: {
              size: 12
            },
            color: '#6b7280'
          },
          grid: {
            color: 'rgba(0, 0, 0, 0.06)',
            drawBorder: false,
            lineWidth: 1
          }
        },
        x: {
          title: {
            display: true,
            text: 'Collection Period (Month)',
            font: {
              size: 14,
              weight: '700'
            },
            padding: {top: 15, bottom: 0},
            color: '#374151'
          },
          ticks: {
            font: {
              size: 11,
              weight: '600'
            },
            color: '#6b7280',
            maxRotation: 45,
            minRotation: 0
          },
          grid: {
            display: false
          }
        }
      },
      animation: {
        duration: 2500,
        easing: 'easeInOutQuart',
        onProgress: function(animation) {
          if (animation.currentStep === 1) {
            console.log('📊 Monthly tracking chart animation started');
          }
        },
        onComplete: function() {
          console.log('✅ Monthly tracking chart rendered successfully');
        }
      }
    }
  });
}

// Initialize charts when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  if (typeof Chart !== 'undefined') {
    initializeAnalyticsCharts();
  } else {
    console.error('Chart.js library not loaded');
  }
});
