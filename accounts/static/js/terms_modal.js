/**
 * Terms and Conditions Modal Handler for Registration Pages
 * Fetches and displays both English and Tagalog terms
 */

// Open Terms Modal
function openTermsModal() {
    const modal = document.getElementById('termsModal');
    modal.style.display = 'flex';
    loadTermsAndConditions();
}

// Close Terms Modal
function closeTermsModal() {
    const modal = document.getElementById('termsModal');
    modal.style.display = 'none';
}

// Load Terms and Conditions from API
function loadTermsAndConditions() {
    const loadingMessage = document.getElementById('termsLoadingMessage');
    const termsContent = document.getElementById('termsContent');
    const errorMessage = document.getElementById('termsErrorMessage');
    
    // Show loading
    loadingMessage.style.display = 'block';
    termsContent.style.display = 'none';
    errorMessage.style.display = 'none';
    
    // Fetch terms from API
    fetch('/api/terms/active/')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load terms');
            }
            return response.json();
        })
        .then(data => {
            loadingMessage.style.display = 'none';
            
            if (data.success && data.terms) {
                displayTerms(data.terms.english, data.terms.tagalog);
                termsContent.style.display = 'block';
            } else {
                errorMessage.style.display = 'block';
            }
        })
        .catch(error => {
            console.error('Error loading terms:', error);
            loadingMessage.style.display = 'none';
            errorMessage.style.display = 'block';
        });
}

// Display Terms Content
function displayTerms(englishTerms, tagalogTerms) {
    // Display English Terms
    const englishSection = document.getElementById('englishTermsSection');
    if (englishTerms) {
        const englishTitle = document.getElementById('englishTermsTitle');
        const englishVersion = document.getElementById('englishTermsVersion');
        const englishText = document.getElementById('englishTermsText');
        
        if (englishTitle) englishTitle.textContent = englishTerms.title;
        if (englishVersion) englishVersion.textContent = englishTerms.version;
        if (englishText) englishText.textContent = englishTerms.content;
        
        if (englishSection) englishSection.style.display = 'block';
    } else {
        if (englishSection) englishSection.style.display = 'none';
    }
    
    // Display Tagalog Terms
    const tagalogSection = document.getElementById('tagalogTermsSection');
    if (tagalogTerms) {
        const tagalogTitle = document.getElementById('tagalogTermsTitle');
        const tagalogVersion = document.getElementById('tagalogTermsVersion');
        const tagalogText = document.getElementById('tagalogTermsText');
        
        if (tagalogTitle) tagalogTitle.textContent = tagalogTerms.title;
        if (tagalogVersion) tagalogVersion.textContent = tagalogTerms.version;
        if (tagalogText) tagalogText.textContent = tagalogTerms.content;
        
        if (tagalogSection) tagalogSection.style.display = 'none'; // Start with English visible
    } else {
        if (tagalogSection) tagalogSection.style.display = 'none';
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // View Terms button
    const viewTermsBtn = document.getElementById('viewTermsBtn');
    if (viewTermsBtn) {
        viewTermsBtn.addEventListener('click', function(e) {
            e.preventDefault();
            openTermsModal();
        });
    }
    
    // Close modal when clicking outside
    const modal = document.getElementById('termsModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeTermsModal();
            }
        });
    }
});
