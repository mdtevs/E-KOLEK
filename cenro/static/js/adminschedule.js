
	// Custom dropdown functions
	function toggleDropdown(dropdownId) {
		const dropdown = document.getElementById(dropdownId);
		dropdown.classList.toggle('show');
		
		// Close other dropdowns
		document.querySelectorAll('.dropdown-content').forEach(function(content) {
			if (content.id !== dropdownId) {
				content.classList.remove('show');
			}
		});
	}

	// Update selected text when checkboxes change
	function updateSelectedText(dropdownId, displayId) {
		const checkboxes = document.querySelectorAll(`#${dropdownId} input[type="checkbox"]:checked`);
		const display = document.getElementById(displayId);
		
		if (checkboxes.length === 0) {
			display.textContent = 'Select waste types...';
		} else if (checkboxes.length === 1) {
			display.textContent = checkboxes[0].value;
		} else {
			display.textContent = `${checkboxes.length} items selected`;
		}
	}

	// Add event listeners for checkboxes
	document.addEventListener('DOMContentLoaded', function() {
		// Add change listeners for waste types dropdown
		document.querySelectorAll('#wasteTypesDropdown input[type="checkbox"]').forEach(function(checkbox) {
			checkbox.addEventListener('change', function() {
				updateSelectedText('wasteTypesDropdown', 'selectedWasteTypes');
			});
		});

		// Add change listeners for edit waste types dropdown
		document.querySelectorAll('#editWasteTypesDropdown input[type="checkbox"]').forEach(function(checkbox) {
			checkbox.addEventListener('change', function() {
				updateSelectedText('editWasteTypesDropdown', 'editSelectedWasteTypes');
			});
		});
	});

	// Close dropdowns when clicking outside
	document.addEventListener('click', function(event) {
		if (!event.target.closest('.custom-dropdown')) {
			document.querySelectorAll('.dropdown-content').forEach(function(content) {
				content.classList.remove('show');
			});
		}
	});

	// Notification helper functions
function showSuccessNotification(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed; top: 20px; right: 20px;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white; padding: 1rem 1.5rem; border-radius: 12px;
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3); z-index: 9999;
        display: flex; align-items: center; gap: 12px; font-weight: 600;
        animation: slideIn 0.3s ease-out;
    `;
    notification.innerHTML = `<i class='bx bx-check-circle' style="font-size: 1.5rem;"></i><span>${message}</span>`;
    document.body.appendChild(notification);
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function showErrorNotification(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed; top: 20px; right: 20px;
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white; padding: 1rem 1.5rem; border-radius: 12px;
        box-shadow: 0 8px 24px rgba(239, 68, 68, 0.3); z-index: 9999;
        display: flex; align-items: center; gap: 12px; font-weight: 600;
        animation: slideIn 0.3s ease-out;
    `;
    notification.innerHTML = `<i class='bx bx-error-circle' style="font-size: 1.5rem;"></i><span>${message}</span>`;
    document.body.appendChild(notification);
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function openAddScheduleModal() {
  document.getElementById("addScheduleModal").style.display = "flex";
}

function closeAddScheduleModal() {
  document.getElementById("addScheduleModal").style.display = "none";
  // Reset checkboxes and display text
  document.querySelectorAll('#wasteTypesDropdown input[type="checkbox"]').forEach(function(checkbox) {
    checkbox.checked = false;
  });
  document.getElementById('selectedWasteTypes').textContent = 'Select waste types...';
}
function closeEditScheduleModal() {
  document.getElementById("editScheduleModal").style.display = "none";
  // Reset checkboxes and display text
  document.querySelectorAll('#editWasteTypesDropdown input[type="checkbox"]').forEach(function(checkbox) {
    checkbox.checked = false;
  });
  document.getElementById('editSelectedWasteTypes').textContent = 'Select waste types...';
}
function closeDeleteScheduleModal() {
  document.getElementById("deleteScheduleModal").style.display = "none";
}

// Wait for DOM to be ready before attaching event listeners
window.addEventListener('DOMContentLoaded', function() {
// Add Schedule
document.getElementById("addScheduleForm").addEventListener("submit", function (e) {
  e.preventDefault();
  
  // Show confirmation modal first
  showConfirmation(null, 'add', 'Schedule', function() {
    const form = document.getElementById("addScheduleForm");
    const data = new FormData(form);
    
    AdminUtils.fetchWithCSRF(window.DJANGO_URLS.addSchedule, {
      method: "POST",
      body: data
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        showSuccessNotification('Schedule added successfully!');
        setTimeout(() => location.reload(), 1500);
      } else {
        showErrorNotification('Failed to add schedule');
      }
    });
  });
});

document.getElementById("editScheduleForm").addEventListener("submit", function (e) {
  e.preventDefault();
  
  // Show confirmation modal first
  showConfirmation(null, 'update', 'Schedule', function() {
    const form = document.getElementById("editScheduleForm");
    const data = new FormData(form);
    data.append('id', document.getElementById("editScheduleId").value);
    
    AdminUtils.fetchWithCSRF(window.DJANGO_URLS.editSchedule, {
      method: "POST",
      body: data
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        showSuccessNotification('Schedule updated successfully!');
        setTimeout(() => location.reload(), 1500);
      } else {
        showErrorNotification('Failed to update schedule');
      }
    });
  });
});
}); // End DOMContentLoaded

// Global helper functions - must be outside DOMContentLoaded to be called from HTML
let scheduleToDelete = null;

function openEditScheduleModal(id) {
  // Get the row data from the table
  const row = document.querySelector(`button[onclick="openEditScheduleModal('${id}')"]`).closest('tr');
  
  // Set the schedule ID
  document.getElementById("editScheduleId").value = id;
  
  // Get barangay ID from data attribute (column 0)
  document.getElementById("editBarangay").value = row.children[0].dataset.barangayId;
  
  // Get day (column 1)
  document.getElementById("editDay").value = row.children[1].innerText.trim();
  
  // Get start time (column 2)
  document.getElementById("editStartTime").value = row.children[2].innerText.trim();
  
  // Get end time (column 3)
  document.getElementById("editEndTime").value = row.children[3].innerText.trim();
  
  // Handle checkbox selection for waste types (column 4)
  const wasteTypesText = row.children[4].innerText.trim();
  const wasteTypesArray = wasteTypesText.split(',').map(type => type.trim());
  
  // Clear all checkboxes first
  document.querySelectorAll('#editWasteTypesDropdown input[type="checkbox"]').forEach(function(checkbox) {
    checkbox.checked = false;
  });
  
  // Check the appropriate checkboxes
  document.querySelectorAll('#editWasteTypesDropdown input[type="checkbox"]').forEach(function(checkbox) {
    if (wasteTypesArray.includes(checkbox.value)) {
      checkbox.checked = true;
    }
  });
  
  // Update the display text
  updateSelectedText('editWasteTypesDropdown', 'editSelectedWasteTypes');
  
  // Get notes (column 5)
  const notesText = row.children[5].innerText.trim();
  document.getElementById("editNotes").value = notesText === '-' ? '' : notesText;
  
  // Show the modal
  document.getElementById("editScheduleModal").style.display = "flex";
}

function openDeleteScheduleModal(id) {
  scheduleToDelete = id;
  document.getElementById("deleteScheduleModal").style.display = "flex";
}

function closeDeleteScheduleModal() {
  document.getElementById("deleteScheduleModal").style.display = "none";
}

function confirmDeleteSchedule() {
  AdminUtils.fetchWithCSRF(window.DJANGO_URLS.deleteSchedule, {
    method: "POST",
    body: new URLSearchParams({id: scheduleToDelete})
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      showSuccessNotification('Schedule deleted successfully!');
      setTimeout(() => location.reload(), 1500);
    } else {
      showErrorNotification('Failed to delete schedule');
    }
  });
  closeDeleteScheduleModal();
}

	