
function openEditRewardCategoryModal(id, name, desc) {
  document.getElementById('editCategoryId').value = id;
  document.getElementById('editCategoryName').value = name;
  document.getElementById('editCategoryDesc').value = desc;
  document.getElementById('editRewardCategoryForm').action = '/admincontrol/edit-reward-category/' + id + '/';
  document.getElementById('editRewardCategoryModal').style.display = 'flex';
}
function openEditWasteTypeModal(id, name, points) {
  document.getElementById('editWasteId').value = id;
  document.getElementById('editWasteName').value = name;
  
  // Format points to remove unnecessary decimals (e.g., 3.00 → 3, 3.50 → 3.5)
  const formattedPoints = window.formatPointsDisplay ? window.formatPointsDisplay(points) : points;
  document.getElementById('editWastePoints').value = formattedPoints;
  
  document.getElementById('editWasteTypeForm').action = '/admincontrol/edit-waste-type/' + id + '/';
  document.getElementById('editWasteTypeModal').style.display = 'flex';
}

// Tab switching function with persistence
function openTab(evt, tabName) {
  var i, tabcontent, tablinks;
  
  // Hide all tab content
  tabcontent = document.getElementsByClassName("tab-content");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }
  
  // Remove active class from all tab buttons
  tablinks = document.getElementsByClassName("tab-button");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].classList.remove("active");
  }
  
  // Show the selected tab and mark button as active
  document.getElementById(tabName).style.display = "block";
  evt.currentTarget.classList.add("active");
  
  // Save tab state for persistence
  if (window.TabPersistence) {
    window.TabPersistence.saveTabState(tabName);
  }
}

// Initialize tab persistence on page load
document.addEventListener('DOMContentLoaded', function() {
  if (window.TabPersistence) {
    window.TabPersistence.init({
      tabButtonsSelector: '.tab-button',
      tabContentsSelector: '.tab-content',
      activeClass: 'active'
    });
  }
});
