
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

        let choiceCount = 2;

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

        document.getElementById('questionForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Show confirmation modal before submitting
            showConfirmation(e, 'add', 'Question', async function() {
                const questionText = document.getElementById('questionText').value;
                const questionPoints = document.getElementById('questionPoints').value;
                const choiceTexts = Array.from(document.querySelectorAll('.choice-text')).map(input => input.value);
                const correctChoiceIndex = document.querySelector('input[name="correctChoice"]:checked').value;
                
                try {
                    // Use AdminUtils if available, fallback to manual method
                    let formData;
                    if (window.AdminUtils) {
                        formData = AdminUtils.createFormDataWithCSRF({
                            question_text: questionText,
                            question_points: questionPoints,
                            choices: choiceTexts,
                            correct_choice: correctChoiceIndex
                        });
                    } else {
                        // Fallback method
                        if (!window.CSRF_TOKEN) {
                            showErrorNotification('CSRF token not found. Please refresh the page.');
                            return;
                        }
                        
                        formData = new FormData();
                        formData.append('csrfmiddlewaretoken', window.CSRF_TOKEN);
                        formData.append('question_text', questionText);
                        formData.append('question_points', questionPoints);
                        formData.append('choices', JSON.stringify(choiceTexts));
                        formData.append('correct_choice', correctChoiceIndex);
                    }
                    
                    const response = await fetch(window.DJANGO_URLS.addQuestion, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': window.AdminUtils ? AdminUtils.getCSRFToken() : window.CSRF_TOKEN,
                        },
                        body: formData
                    });
                    
                    if (window.AdminUtils) {
                        await AdminUtils.handleResponse(response, 'Question added successfully!');
                        location.reload();
                    } else {
                        // Fallback error handling
                        if (response.ok) {
                            const result = await response.json();
                            showSuccessNotification('Question added successfully! Question ID: ' + result.question_id);
                            setTimeout(() => location.reload(), 1500);
                        } else {
                            const errorData = await response.json();
                            showErrorNotification('Error adding question: ' + (errorData.error || 'Unknown error'));
                            console.error('Server response:', errorData);
                        }
                    }
                } catch (error) {
                    showErrorNotification('Error: ' + error.message);
                    console.error('Fetch error:', error);
                }
            });
        });

        async function deleteQuestion(questionId) {
            if (confirm('Are you sure you want to delete this question?')) {
                try {
                    const response = await fetch(window.DJANGO_URLS.deleteQuestion.replace('0', questionId), {
                        method: 'DELETE',
                        headers: {
                            'X-CSRFToken': window.CSRF_TOKEN
                        }
                    });
                    
                    if (response.ok) {
                        showSuccessNotification('Question deleted successfully!');
                        setTimeout(() => location.reload(), 1500);
                    } else {
                        showErrorNotification('Error deleting question');
                    }
                } catch (error) {
                    showErrorNotification('Error: ' + error.message);
                }
            }
        }
  