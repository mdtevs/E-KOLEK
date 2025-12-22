/**
 * Games Management JavaScript
 * Uses unified confirmation modal system for all confirmations
 * Uses notification system for success/error messages
 */

let choiceCount = 2;

// Notification helper functions
function showSuccessNotification(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3);
        z-index: 9999;
        display: flex;
        align-items: center;
        gap: 12px;
        font-weight: 600;
        animation: slideIn 0.3s ease-out;
    `;
    notification.innerHTML = `
        <i class='bx bx-check-circle' style="font-size: 1.5rem;"></i>
        <span>${message}</span>
    `;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function showErrorNotification(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(239, 68, 68, 0.3);
        z-index: 9999;
        display: flex;
        align-items: center;
        gap: 12px;
        font-weight: 600;
        animation: slideIn 0.3s ease-out;
    `;
    notification.innerHTML = `
        <i class='bx bx-error-circle' style="font-size: 1.5rem;"></i>
        <span>${message}</span>
    `;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Initialize Color Picker
function initializeColorPicker(previewId, inputId, textInputId) {
    const preview = document.getElementById(previewId);
    const colorInput = document.getElementById(inputId);
    const textInput = document.getElementById(textInputId);
    
    if (!preview || !colorInput || !textInput) return;
    
    // Set initial color
    preview.style.backgroundColor = colorInput.value;
    
    // Position the hidden color input inside the preview circle
    preview.style.position = 'relative';
    colorInput.style.position = 'absolute';
    colorInput.style.top = '0';
    colorInput.style.left = '0';
    colorInput.style.width = '100%';
    colorInput.style.height = '100%';
    colorInput.style.opacity = '0';
    colorInput.style.cursor = 'pointer';
    
    // Move the color input inside the preview circle for better positioning
    if (colorInput.parentElement !== preview) {
        preview.appendChild(colorInput);
    }
    
    // Update preview and text when color picker changes
    colorInput.addEventListener('input', (e) => {
        const color = e.target.value.toUpperCase();
        preview.style.backgroundColor = color;
        textInput.value = color;
    });
    
    // Also handle change event for better compatibility
    colorInput.addEventListener('change', (e) => {
        const color = e.target.value.toUpperCase();
        preview.style.backgroundColor = color;
        textInput.value = color;
    });
    
    // Update preview and color picker when text input changes
    textInput.addEventListener('input', (e) => {
        let color = e.target.value.trim();
        // Add # if missing
        if (color && !color.startsWith('#')) {
            color = '#' + color;
        }
        // Validate hex color format
        if (/^#[0-9A-Fa-f]{6}$/.test(color)) {
            preview.style.backgroundColor = color;
            colorInput.value = color;
            textInput.style.borderColor = '#e5e7eb';
        } else if (color.length === 7) {
            textInput.style.borderColor = '#ef4444';
        }
    });
    
    // Format on blur
    textInput.addEventListener('blur', (e) => {
        let color = e.target.value.trim().toUpperCase();
        if (color && !color.startsWith('#')) {
            color = '#' + color;
        }
        if (/^#[0-9A-Fa-f]{6}$/.test(color)) {
            textInput.value = color;
            textInput.style.borderColor = '#e5e7eb';
        } else {
            // Reset to current color if invalid
            textInput.value = colorInput.value.toUpperCase();
            textInput.style.borderColor = '#e5e7eb';
        }
    });
}

// Apply dynamic colors to category displays
document.addEventListener('DOMContentLoaded', function() {
    const colorDisplays = document.querySelectorAll('.color-display');
    colorDisplays.forEach(function(element) {
        const color = element.getAttribute('data-color');
        element.style.backgroundColor = color;
    });
    
    // Apply colors to circle displays
    const circleDisplays = document.querySelectorAll('.color-circle-display');
    circleDisplays.forEach(function(element) {
        const color = element.getAttribute('data-color');
        if (color) {
            element.style.backgroundColor = color;
        }
    });
    
    // Initialize color pickers
    initializeColorPicker('categoryColorPreview', 'categoryColor', 'categoryColorText');
    
    // Initialize tab persistence
    if (window.TabPersistence) {
        window.TabPersistence.init({
            tabButtonsSelector: '.tab-btn',
            tabContentsSelector: '.tab-content',
            activeClass: 'active'
        });
    }
    
    // Initialize Category Form
    const categoryForm = document.getElementById('categoryForm');
    if (categoryForm) {
        categoryForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show confirmation modal
            showConfirmation(e, 'add', 'Category', async function() {
                const formData = new FormData();
                formData.append('csrfmiddlewaretoken', window.CSRF_TOKEN);
                formData.append('name', document.getElementById('categoryName').value);
                // Get color from the text input (which can be manually edited)
                const colorValue = document.getElementById('categoryColorText').value || document.getElementById('categoryColor').value;
                formData.append('color_hex', colorValue);
                formData.append('icon_name', document.getElementById('categoryIcon').value);
                formData.append('description', document.getElementById('categoryDescription').value);
                
                try {
                    const response = await fetch(window.DJANGO_URLS.addCategory, {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        showSuccessNotification('Category added successfully!');
                        setTimeout(() => location.reload(), 1500);
                    } else {
                        showErrorNotification('Failed to add category');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    showErrorNotification('Error: ' + error.message);
                }
            });
        });
    }
    
    // Initialize Item Form
    const itemForm = document.getElementById('itemForm');
    if (itemForm) {
        itemForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show confirmation modal
            showConfirmation(e, 'add', 'Item', async function() {
                const formData = new FormData();
                formData.append('csrfmiddlewaretoken', window.CSRF_TOKEN);
                formData.append('name', document.getElementById('itemName').value);
                formData.append('emoji', document.getElementById('itemEmoji').value);
                formData.append('category', document.getElementById('itemCategory').value);
                formData.append('points', document.getElementById('itemPoints').value);
                formData.append('difficulty_level', document.getElementById('itemDifficulty').value);
                formData.append('is_active', document.getElementById('itemActive').checked);
                
                try {
                    const response = await fetch(window.DJANGO_URLS.addItem, {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        showSuccessNotification('Item added successfully!');
                        setTimeout(() => location.reload(), 1500);
                    } else {
                        showErrorNotification('Failed to add item');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    showErrorNotification('Error: ' + error.message);
                }
            });
        });
    }
    
    // Initialize Question Form
    const questionForm = document.getElementById('questionForm');
    if (questionForm) {
        questionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show confirmation modal
            showConfirmation(e, 'add', 'Question', async function() {
                const questionText = document.getElementById('questionText').value;
                const questionPoints = document.getElementById('questionPoints').value;
                const choiceTexts = Array.from(document.querySelectorAll('.choice-text')).map(input => input.value);
                const correctChoiceIndex = document.querySelector('input[name="correctChoice"]:checked').value;
                
                const formData = new FormData();
                formData.append('csrfmiddlewaretoken', window.CSRF_TOKEN);
                formData.append('question_text', questionText);
                formData.append('question_points', questionPoints);
                formData.append('choices', JSON.stringify(choiceTexts));
                formData.append('correct_choice', correctChoiceIndex);
                
                try {
                    const response = await fetch(window.DJANGO_URLS.addQuestion, {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        showSuccessNotification('Question added successfully!');
                        setTimeout(() => location.reload(), 1500);
                    } else {
                        showErrorNotification('Failed to add question');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    showErrorNotification('Error: ' + error.message);
                }
            });
        });
    }
});

// Tab functionality with persistence
function openTab(evt, tabName) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tab-content");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("tab-btn");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].classList.remove("active");
    }
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.classList.add("active");
    
    // Save tab state for persistence
    if (window.TabPersistence) {
        window.TabPersistence.saveTabState(tabName);
    }
}

function addChoice() {
    const container = document.getElementById('choicesContainer');
    const choiceDiv = document.createElement('div');
    choiceDiv.className = 'choice-group';
    choiceDiv.innerHTML = `
        <input type="text" class="choice-input choice-text" placeholder="Choice ${choiceCount + 1}" required>
        <label>
            <input type="radio" name="correctChoice" value="${choiceCount}" class="correct-checkbox" required>
            Mark as correct answer
        </label>
        <button type="button" onclick="removeChoice(this)" class="btn-remove">Remove</button>
    `;
    container.appendChild(choiceDiv);
    choiceCount++;
}

function removeChoice(button) {
    button.parentElement.remove();
}

async function deleteCategory(categoryId) {
    // Show confirmation modal
    showConfirmation(null, 'delete', 'Category', async function() {
        try {
            const response = await fetch(window.DJANGO_URLS.deleteCategory.replace('/0/', `/${categoryId}/`), {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': window.CSRF_TOKEN
                }
            });
            
            if (response.ok) {
                showSuccessNotification('Category deleted successfully!');
                setTimeout(() => location.reload(), 1500);
            } else {
                showErrorNotification('Failed to delete category');
            }
        } catch (error) {
            console.error('Error:', error);
            showErrorNotification('Error: ' + error.message);
        }
    });
}

async function deleteItem(itemId) {
    // Show confirmation modal
    showConfirmation(null, 'delete', 'Item', async function() {
        try {
            const response = await fetch(window.DJANGO_URLS.deleteItem.replace('/0/', `/${itemId}/`), {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': window.CSRF_TOKEN
                }
            });
            
            if (response.ok) {
                showSuccessNotification('Item deleted successfully!');
                setTimeout(() => location.reload(), 1500);
            } else {
                showErrorNotification('Failed to delete item');
            }
        } catch (error) {
            console.error('Error:', error);
            showErrorNotification('Error: ' + error.message);
        }
    });
}

async function deleteQuestion(questionId) {
    // Show confirmation modal
    showConfirmation(null, 'delete', 'Question', async function() {
        try {
            const response = await fetch(window.DJANGO_URLS.deleteQuestion.replace('/0/', `/${questionId}/`), {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': window.CSRF_TOKEN
                }
            });
            
            if (response.ok) {
                showSuccessNotification('Question deleted successfully!');
                setTimeout(() => location.reload(), 1500);
            } else {
                showErrorNotification('Failed to delete question');
            }
        } catch (error) {
            console.error('Error:', error);
            showErrorNotification('Error: ' + error.message);
        }
    });
}

// Add animations for notifications
if (!document.getElementById('notification-animations')) {
    const style = document.createElement('style');
    style.id = 'notification-animations';
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(400px);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}
