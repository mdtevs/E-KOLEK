/**
 * Admin Quiz Questions JavaScript
 * Handles quiz question CRUD operations (Create, Read, Update, Delete)
 */

// Notification helper functions
function showSuccessNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'custom-notification success';
    notification.innerHTML = `
        <i class='bx bx-check-circle'></i>
        <span>${message}</span>
    `;
    document.body.appendChild(notification);
    setTimeout(() => notification.classList.add('show'), 100);
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function showErrorNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'custom-notification error';
    notification.innerHTML = `
        <i class='bx bx-error-circle'></i>
        <span>${message}</span>
    `;
    document.body.appendChild(notification);
    setTimeout(() => notification.classList.add('show'), 100);
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Global quiz configuration
let QUIZ_CONFIG = {};

/**
 * Edit a quiz question
 * @param {string} questionId - ID of the question to edit
 * @param {HTMLElement} button - Button element containing question data
 */
function editQuestion(questionId, button) {
    if (!button) {
        showErrorNotification('Question data not found.');
        return;
    }
    
    document.getElementById('questionId').value = questionId;
    document.getElementById('questionText').value = button.dataset.questionText || '';
    document.getElementById('optionA').value = button.dataset.optionA || '';
    document.getElementById('optionB').value = button.dataset.optionB || '';
    document.getElementById('optionC').value = button.dataset.optionC || '';
    document.getElementById('optionD').value = button.dataset.optionD || '';
    document.getElementById('correctAnswer').value = button.dataset.correctAnswer || '';
    document.getElementById('pointsReward').value = button.dataset.points || '10';
    document.getElementById('order').value = button.dataset.order || '1';
    document.getElementById('explanation').value = button.dataset.explanation || '';
    
    document.getElementById('saveButtonText').textContent = 'Update Question';
    document.getElementById('cancelEdit').style.display = 'inline-block';
    
    // Scroll to form
    document.querySelector('.quiz-form').scrollIntoView({ behavior: 'smooth' });
}

/**
 * Cancel editing mode and reset form
 */
function cancelEdit() {
    document.getElementById('questionForm').reset();
    document.getElementById('questionId').value = '';
    document.getElementById('saveButtonText').textContent = 'Add Question';
    document.getElementById('cancelEdit').style.display = 'none';
    document.getElementById('order').value = QUIZ_CONFIG.questionsCount + 1;
}

/**
 * Toggle question active status
 * @param {string} questionId - ID of the question to toggle
 */
function toggleQuestion(questionId) {
    const formData = new FormData();
    formData.append('csrfmiddlewaretoken', QUIZ_CONFIG.csrfToken);
    formData.append('question_id', questionId);
    
    fetch(QUIZ_CONFIG.urls.toggleQuestion, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccessNotification(data.message);
            setTimeout(() => location.reload(), 1500);
        } else {
            showErrorNotification('Error: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showErrorNotification('An error occurred while toggling the question.');
    });
}

/**
 * Delete a quiz question
 * @param {string} questionId - ID of the question to delete
 */
function deleteQuestion(questionId) {
    if (!confirm('Are you sure you want to delete this question? This action cannot be undone.')) {
        return;
    }
    
    const formData = new FormData();
    formData.append('csrfmiddlewaretoken', QUIZ_CONFIG.csrfToken);
    formData.append('question_id', questionId);
    
    fetch(QUIZ_CONFIG.urls.deleteQuestion, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccessNotification(data.message);
            setTimeout(() => location.reload(), 1500);
        } else {
            showErrorNotification('Error: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showErrorNotification('An error occurred while deleting the question.');
    });
}

/**
 * Initialize quiz questions functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get configuration from hidden element
    const dataElement = document.getElementById('django-data');
    if (!dataElement) {
        console.error('Django data element not found');
        return;
    }
    
    QUIZ_CONFIG = {
        csrfToken: dataElement.dataset.csrfToken,
        videoId: dataElement.dataset.videoId,
        questionsCount: parseInt(dataElement.dataset.questionsCount) || 0,
        urls: {
            addQuestion: dataElement.dataset.addUrl,
            editQuestion: dataElement.dataset.editUrl,
            deleteQuestion: dataElement.dataset.deleteUrl,
            toggleQuestion: dataElement.dataset.toggleUrl
        }
    };
    
    // Set initial order value
    const orderInput = document.getElementById('order');
    if (orderInput) {
        orderInput.value = QUIZ_CONFIG.questionsCount + 1;
    }
    
    // Attach cancel edit button listener
    const cancelBtn = document.getElementById('cancelEdit');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', cancelEdit);
    }
    
    // Attach event listeners for action buttons
    document.addEventListener('click', function(e) {
        const target = e.target.closest('[data-action]');
        if (!target) return;
        
        const action = target.dataset.action;
        const questionId = target.dataset.questionId;
        
        switch(action) {
            case 'edit':
                editQuestion(questionId, target);
                break;
            case 'toggle':
                toggleQuestion(questionId);
                break;
            case 'delete':
                deleteQuestion(questionId);
                break;
        }
    });
    
    // Form submission handler
    const questionForm = document.getElementById('questionForm');
    if (questionForm) {
        questionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const questionId = document.getElementById('questionId').value;
            const isEdit = questionId !== '';
            
            const formData = new FormData();
            formData.append('csrfmiddlewaretoken', QUIZ_CONFIG.csrfToken);
            formData.append('video_id', QUIZ_CONFIG.videoId);
            formData.append('question_text', document.getElementById('questionText').value);
            formData.append('option_a', document.getElementById('optionA').value);
            formData.append('option_b', document.getElementById('optionB').value);
            formData.append('option_c', document.getElementById('optionC').value);
            formData.append('option_d', document.getElementById('optionD').value);
            formData.append('correct_answer', document.getElementById('correctAnswer').value);
            formData.append('points_reward', document.getElementById('pointsReward').value);
            formData.append('order', document.getElementById('order').value);
            formData.append('explanation', document.getElementById('explanation').value);
            
            if (isEdit) {
                formData.append('question_id', questionId);
            }
            
            const url = isEdit ? QUIZ_CONFIG.urls.editQuestion : QUIZ_CONFIG.urls.addQuestion;
            
            fetch(url, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showSuccessNotification(data.message);
                    setTimeout(() => location.reload(), 1500);
                } else {
                    showErrorNotification('Error: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showErrorNotification('An error occurred while saving the question.');
            });
        });
    }
});
