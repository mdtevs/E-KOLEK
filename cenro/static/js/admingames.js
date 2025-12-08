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

// Apply dynamic colors to category displays
document.addEventListener('DOMContentLoaded', function() {
    const colorDisplays = document.querySelectorAll('.color-display');
    colorDisplays.forEach(function(element) {
        const color = element.getAttribute('data-color');
        element.style.backgroundColor = color;
    });
    
    // Initialize tab persistence
    if (window.TabPersistence) {
        window.TabPersistence.init({
            tabButtonsSelector: '.tab-btn',
            tabContentsSelector: '.tab-content',
            activeClass: 'active'
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

// Category Form
document.getElementById('categoryForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Show confirmation modal
    showConfirmation(e, 'add', 'Category', async function() {
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', window.CSRF_TOKEN);
        formData.append('name', document.getElementById('categoryName').value);
        formData.append('color_hex', document.getElementById('categoryColor').value);
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

// Item Form
document.getElementById('itemForm').addEventListener('submit', function(e) {
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

// Question Form
document.getElementById('questionForm').addEventListener('submit', function(e) {
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

// Add CSS animations if not already present
if (!document.getElementById('games-animations')) {
    const style = document.createElement('style');
    style.id = 'games-animations';
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
