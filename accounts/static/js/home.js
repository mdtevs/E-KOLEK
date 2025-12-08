/**
 * Home page functionality for E-KOLEK landing page
 */

(function() {
  'use strict';

  /**
   * Handle Get Started button click
   * Checks if user is authenticated and redirects accordingly
   */
  function handleGetStarted() {
    // Check if user is authenticated by checking for session/cookies
    // Since this is a public landing page, redirect to registration
    
    // Show loading state
    const buttons = document.querySelectorAll('.btn-primary');
    buttons.forEach(btn => {
      btn.style.opacity = '0.7';
      btn.style.cursor = 'wait';
    });

    // Redirect to registration page after brief delay for UX
    setTimeout(() => {
      window.location.href = '/accounts/register/';
    }, 200);
  }

  /**
   * Smooth scroll to sections
   */
  function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function(e) {
        const targetId = this.getAttribute('href');
        if (targetId === '#') return;
        
        const targetElement = document.querySelector(targetId);
        if (targetElement) {
          e.preventDefault();
          targetElement.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }
      });
    });
  }

  /**
   * Add scroll animations for better UX
   */
  function initScrollAnimations() {
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('fade-in-visible');
        }
      });
    }, observerOptions);

    // Observe benefit cards
    document.querySelectorAll('.benefit-card').forEach(card => {
      card.classList.add('fade-in');
      observer.observe(card);
    });
  }

  /**
   * Initialize mobile menu toggle (if needed in future)
   */
  function initMobileMenu() {
    // Placeholder for future mobile menu functionality
    // Can be expanded if hamburger menu is added
  }

  /**
   * Initialize all functionality when DOM is ready
   */
  document.addEventListener('DOMContentLoaded', function() {
    // Make handleGetStarted globally accessible
    window.handleGetStarted = handleGetStarted;
    
    // Initialize smooth scrolling
    initSmoothScroll();
    
    // Initialize scroll animations
    initScrollAnimations();
    
    // Initialize mobile menu
    initMobileMenu();

    console.log('E-KOLEK landing page initialized');
  });

  // Prevent back button issues (keep existing functionality)
  window.history.pushState(null, '', window.location.href);
  window.onpopstate = function() {
    window.history.go(1);
  };

})();
