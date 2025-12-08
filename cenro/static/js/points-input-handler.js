/**
 * Points Input Handler
 * Allows decimal input but makes arrow keys increment/decrement by whole numbers (+1/-1)
 * while the step attribute allows manual decimal entry
 */

/**
 * Format points value for display (removes unnecessary decimals)
 * Examples: 3.00 → "3", 3.50 → "3.5", 10.75 → "10.75"
 */
function formatPointsDisplay(value) {
    if (value === null || value === undefined || value === '') {
        return '0';
    }
    
    const num = parseFloat(value);
    if (isNaN(num)) {
        return '0';
    }
    
    // Check if it's a whole number
    if (num === Math.floor(num)) {
        return Math.floor(num).toString();
    }
    
    // Return with minimal decimal places
    return num.toString();
}

// Export for use in other scripts
window.formatPointsDisplay = formatPointsDisplay;

document.addEventListener('DOMContentLoaded', function() {
    // Find all points input fields
    const pointsInputs = document.querySelectorAll('.points-input, input[type="number"][step="0.01"]');
    
    pointsInputs.forEach(input => {
        // Store the original step value
        const originalStep = input.getAttribute('step') || '0.01';
        
        // When user focuses on the input, temporarily change step to 1 for arrow keys
        input.addEventListener('focus', function() {
            this.setAttribute('step', '1');
        });
        
        // Handle arrow key presses for whole number increments
        input.addEventListener('keydown', function(e) {
            if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
                e.preventDefault();
                
                const currentValue = parseFloat(this.value) || 0;
                const min = parseFloat(this.getAttribute('min')) || 0;
                const max = parseFloat(this.getAttribute('max')) || Infinity;
                
                let newValue;
                if (e.key === 'ArrowUp') {
                    newValue = currentValue + 1;
                } else {
                    newValue = currentValue - 1;
                }
                
                // Respect min/max bounds
                if (newValue < min) newValue = min;
                if (newValue > max) newValue = max;
                
                // Update the value
                this.value = newValue;
                
                // Trigger change event
                this.dispatchEvent(new Event('change', { bubbles: true }));
                this.dispatchEvent(new Event('input', { bubbles: true }));
            }
        });
        
        // When user clicks the spinner buttons, increment/decrement by 1
        input.addEventListener('mousedown', function(e) {
            // Temporarily set step to 1 for spinner buttons
            this.setAttribute('step', '1');
            
            // After a short delay, restore the original step for decimal input
            setTimeout(() => {
                this.setAttribute('step', originalStep);
            }, 100);
        });
        
        // When input loses focus, restore original step and format value
        input.addEventListener('blur', function() {
            this.setAttribute('step', originalStep);
            
            // Format the value to remove unnecessary decimals
            const value = parseFloat(this.value);
            if (!isNaN(value)) {
                // If it's a whole number, show without decimals
                if (value === Math.floor(value)) {
                    this.value = Math.floor(value).toString();
                } else {
                    // Keep decimals but remove trailing zeros
                    this.value = value.toString();
                }
            }
        });
        
        // Handle manual input - allow decimals
        input.addEventListener('input', function() {
            // Restore decimal step when typing manually
            this.setAttribute('step', originalStep);
        });
    });
});

/**
 * Initialize points input handler for dynamically added inputs
 * Call this function after adding new input fields via JavaScript
 */
function initializePointsInputs(container) {
    const pointsInputs = container.querySelectorAll('.points-input, input[type="number"][step="0.01"]');
    
    pointsInputs.forEach(input => {
        const originalStep = input.getAttribute('step') || '0.01';
        
        input.addEventListener('focus', function() {
            this.setAttribute('step', '1');
        });
        
        input.addEventListener('keydown', function(e) {
            if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
                e.preventDefault();
                
                const currentValue = parseFloat(this.value) || 0;
                const min = parseFloat(this.getAttribute('min')) || 0;
                const max = parseFloat(this.getAttribute('max')) || Infinity;
                
                let newValue;
                if (e.key === 'ArrowUp') {
                    newValue = currentValue + 1;
                } else {
                    newValue = currentValue - 1;
                }
                
                if (newValue < min) newValue = min;
                if (newValue > max) newValue = max;
                
                this.value = newValue;
                this.dispatchEvent(new Event('change', { bubbles: true }));
                this.dispatchEvent(new Event('input', { bubbles: true }));
            }
        });
        
        input.addEventListener('mousedown', function(e) {
            this.setAttribute('step', '1');
            setTimeout(() => {
                this.setAttribute('step', originalStep);
            }, 100);
        });
        
        input.addEventListener('blur', function() {
            this.setAttribute('step', originalStep);
            const value = parseFloat(this.value);
            if (!isNaN(value)) {
                // Format to remove unnecessary decimals
                if (value === Math.floor(value)) {
                    this.value = Math.floor(value).toString();
                } else {
                    this.value = value.toString();
                }
            }
        });
        
        input.addEventListener('input', function() {
            this.setAttribute('step', originalStep);
        });
    });
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { initializePointsInputs };
}
