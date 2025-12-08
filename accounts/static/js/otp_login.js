/**
 * OTP Login Functionality for E-KOLEK
 * Handles SMS OTP sending and verification
 */

class OTPManager {
    constructor() {
        this.currentPhoneNumber = '';
        this.otpTimer = null;
        this.resendTimer = null;
        this.otpTimeLeft = 300; // 5 minutes
        this.resendTimeLeft = 60; // 1 minute
        
        this.initializeElements();
        this.bindEvents();
    }
    
    initializeElements() {
        // Form elements
        this.otpPhoneForm = document.getElementById('otpPhoneForm');
        this.otpVerifyForm = document.getElementById('otpVerifyForm');
        this.otpPhoneNumber = document.getElementById('otpPhoneNumber');
        this.otpCode = document.getElementById('otpCode');
        
        // Button elements
        this.sendOtpBtn = document.getElementById('sendOtpBtn');
        this.verifyOtpBtn = document.getElementById('verifyOtpBtn');
        this.resendOtpBtn = document.getElementById('resendOtpBtn');
        this.backToPhoneBtn = document.getElementById('backToPhoneBtn');
        
        // Display elements
        this.otpPhoneDisplay = document.getElementById('otpPhoneDisplay');
        this.otpTimer = document.getElementById('otpTimer');
        this.resendTimer = document.getElementById('resendTimer');
        
        // Step containers
        this.otpStep1 = document.getElementById('otpStep1');
        this.otpStep2 = document.getElementById('otpStep2');
    }
    
    bindEvents() {
        if (this.otpPhoneForm) {
            this.otpPhoneForm.addEventListener('submit', (e) => this.handleSendOTP(e));
        }
        
        if (this.otpVerifyForm) {
            this.otpVerifyForm.addEventListener('submit', (e) => this.handleVerifyOTP(e));
        }
        
        if (this.resendOtpBtn) {
            this.resendOtpBtn.addEventListener('click', () => this.handleResendOTP());
        }
        
        if (this.backToPhoneBtn) {
            this.backToPhoneBtn.addEventListener('click', () => this.goBackToPhone());
        }
        
        // Phone number formatting
        if (this.otpPhoneNumber) {
            this.otpPhoneNumber.addEventListener('input', (e) => this.formatPhoneNumber(e));
        }
        
        // OTP code formatting
        if (this.otpCode) {
            this.otpCode.addEventListener('input', (e) => this.formatOTPCode(e));
        }
    }
    
    formatPhoneNumber(event) {
        let value = event.target.value.replace(/\D/g, ''); // Remove non-digits
        
        // Limit to 11 digits for Philippine numbers
        if (value.length > 11) {
            value = value.substring(0, 11);
        }
        
        // Auto-add 0 prefix if user starts with 9
        if (value.length === 10 && value.startsWith('9')) {
            value = '0' + value;
        }
        
        event.target.value = value;
    }
    
    formatOTPCode(event) {
        let value = event.target.value.replace(/\D/g, ''); // Remove non-digits
        
        // Limit to 6 digits
        if (value.length > 6) {
            value = value.substring(0, 6);
        }
        
        event.target.value = value;
    }
    
    async handleSendOTP(event) {
        event.preventDefault();
        
        const phoneNumber = this.otpPhoneNumber.value.trim();
        
        if (!this.validatePhoneNumber(phoneNumber)) {
            this.showError('Please enter a valid 11-digit Philippine mobile number');
            return;
        }
        
        this.setLoading(this.sendOtpBtn, true, 'Sending OTP...');
        
        try {
            const response = await fetch(window.DJANGO_URLS.sendOtp, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.CSRF_TOKEN
                },
                body: JSON.stringify({
                    phone_number: phoneNumber
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentPhoneNumber = phoneNumber;
                this.showOTPStep2(phoneNumber);
                this.startOTPTimer();
                this.startResendTimer();
                this.showSuccess('OTP code sent to your phone number');
            } else {
                this.showError(data.message || 'Failed to send OTP');
            }
            
        } catch (error) {
            console.error('Send OTP error:', error);
            this.showError('Network error. Please check your connection and try again.');
        } finally {
            this.setLoading(this.sendOtpBtn, false, 'Send OTP Code');
        }
    }
    
    async handleVerifyOTP(event) {
        event.preventDefault();
        
        const otpCode = this.otpCode.value.trim();
        
        if (!this.validateOTPCode(otpCode)) {
            this.showError('Please enter a valid 6-digit OTP code');
            return;
        }
        
        this.setLoading(this.verifyOtpBtn, true, 'Verifying...');
        
        try {
            const response = await fetch(window.DJANGO_URLS.verifyOtp, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.CSRF_TOKEN
                },
                body: JSON.stringify({
                    phone_number: this.currentPhoneNumber,
                    otp_code: otpCode
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showSuccess('Login successful! Redirecting...');
                this.clearTimers();
                
                // Redirect to dashboard
                setTimeout(() => {
                    window.location.href = data.redirect_url || window.DJANGO_URLS.userDashboard;
                }, 1000);
                
            } else {
                this.showError(data.message || 'Invalid OTP code');
                
                // If no attempts remaining, go back to phone step
                if (data.attempts_remaining === 0) {
                    setTimeout(() => {
                        this.goBackToPhone();
                    }, 2000);
                }
            }
            
        } catch (error) {
            console.error('Verify OTP error:', error);
            this.showError('Network error. Please check your connection and try again.');
        } finally {
            this.setLoading(this.verifyOtpBtn, false, 'Verify & Login');
        }
    }
    
    async handleResendOTP() {
        if (!this.currentPhoneNumber) {
            this.showError('Phone number not found. Please start over.');
            return;
        }
        
        this.setLoading(this.resendOtpBtn, true, 'Resending...');
        
        try {
            const response = await fetch(window.DJANGO_URLS.sendOtp, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.CSRF_TOKEN
                },
                body: JSON.stringify({
                    phone_number: this.currentPhoneNumber
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showSuccess('New OTP code sent to your phone');
                this.startOTPTimer();
                this.startResendTimer();
                this.otpCode.value = ''; // Clear previous OTP
            } else {
                this.showError(data.message || 'Failed to resend OTP');
            }
            
        } catch (error) {
            console.error('Resend OTP error:', error);
            this.showError('Network error. Please try again.');
        } finally {
            this.setLoading(this.resendOtpBtn, false, 'Resend OTP');
        }
    }
    
    validatePhoneNumber(phoneNumber) {
        // Philippine mobile number validation
        const phoneRegex = /^09\d{9}$/;
        return phoneRegex.test(phoneNumber);
    }
    
    validateOTPCode(otpCode) {
        // 6-digit OTP validation
        const otpRegex = /^\d{6}$/;
        return otpRegex.test(otpCode);
    }
    
    showOTPStep2(phoneNumber) {
        this.otpStep1.classList.remove('active');
        this.otpStep2.classList.add('active');
        
        // Display formatted phone number
        const formatted = phoneNumber.replace(/(\d{4})(\d{3})(\d{4})/, '$1-$2-$3');
        this.otpPhoneDisplay.textContent = formatted;
        
        // Focus on OTP input
        setTimeout(() => {
            this.otpCode.focus();
        }, 100);
    }
    
    goBackToPhone() {
        this.otpStep2.classList.remove('active');
        this.otpStep1.classList.add('active');
        
        this.clearTimers();
        this.currentPhoneNumber = '';
        this.otpCode.value = '';
        
        // Focus on phone input
        setTimeout(() => {
            this.otpPhoneNumber.focus();
        }, 100);
    }
    
    startOTPTimer() {
        this.clearOTPTimer();
        this.otpTimeLeft = 300; // 5 minutes
        
        this.otpTimer = setInterval(() => {
            this.otpTimeLeft--;
            
            const minutes = Math.floor(this.otpTimeLeft / 60);
            const seconds = this.otpTimeLeft % 60;
            const timeDisplay = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            
            if (this.otpTimer) {
                this.otpTimer.textContent = `Code expires in ${timeDisplay}`;
            }
            
            if (this.otpTimeLeft <= 0) {
                this.clearOTPTimer();
                this.showError('OTP code expired. Please request a new one.');
                this.goBackToPhone();
            }
        }, 1000);
    }
    
    startResendTimer() {
        this.clearResendTimer();
        this.resendTimeLeft = 60; // 1 minute
        this.resendOtpBtn.disabled = true;
        
        this.resendTimer = setInterval(() => {
            this.resendTimeLeft--;
            
            if (this.resendTimer) {
                this.resendTimer.textContent = this.resendTimeLeft;
            }
            
            if (this.resendTimeLeft <= 0) {
                this.clearResendTimer();
                this.resendOtpBtn.disabled = false;
                this.resendOtpBtn.innerHTML = 'Resend OTP';
            }
        }, 1000);
    }
    
    clearTimers() {
        this.clearOTPTimer();
        this.clearResendTimer();
    }
    
    clearOTPTimer() {
        if (this.otpTimer) {
            clearInterval(this.otpTimer);
            this.otpTimer = null;
        }
    }
    
    clearResendTimer() {
        if (this.resendTimer) {
            clearInterval(this.resendTimer);
            this.resendTimer = null;
        }
    }
    
    setLoading(button, isLoading, loadingText) {
        if (isLoading) {
            button.disabled = true;
            button.originalText = button.textContent;
            button.textContent = loadingText;
        } else {
            button.disabled = false;
            button.textContent = button.originalText || button.textContent;
        }
    }
    
    showError(message) {
        this.showMessage(message, 'error');
    }
    
    showSuccess(message) {
        this.showMessage(message, 'success');
    }
    
    showMessage(message, type) {
        // Remove existing messages
        const existingMessages = document.querySelectorAll('.otp-message');
        existingMessages.forEach(msg => msg.remove());
        
        // Create new message
        const messageDiv = document.createElement('div');
        messageDiv.className = `otp-message otp-${type}`;
        messageDiv.textContent = message;
        
        // Insert message
        const activeStep = document.querySelector('.otp-step.active');
        if (activeStep) {
            activeStep.insertBefore(messageDiv, activeStep.firstChild);
        }
        
        // Auto-remove success messages
        if (type === 'success') {
            setTimeout(() => {
                messageDiv.remove();
            }, 3000);
        }
    }
}

// Enhanced tab switching function to include OTP
function switchTab(tabName) {
    // Hide all sections
    document.getElementById('codeLogin').classList.remove('active');
    document.getElementById('qrLogin').classList.remove('active');
    document.getElementById('otpLogin').classList.remove('active');
    
    // Remove active class from all tabs
    document.getElementById('codeTab').classList.remove('active');
    document.getElementById('qrTab').classList.remove('active');
    document.getElementById('otpTab').classList.remove('active');
    
    // Show selected section and activate tab
    if (tabName === 'code') {
        document.getElementById('codeLogin').classList.add('active');
        document.getElementById('codeTab').classList.add('active');
    } else if (tabName === 'qr') {
        document.getElementById('qrLogin').classList.add('active');
        document.getElementById('qrTab').classList.add('active');
        
        // Initialize QR scanner if needed
        if (typeof initializeQRScanner === 'function') {
            initializeQRScanner();
        }
    } else if (tabName === 'otp') {
        document.getElementById('otpLogin').classList.add('active');
        document.getElementById('otpTab').classList.add('active');
    }
}

// Initialize OTP Manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if OTP elements exist
    if (document.getElementById('otpLogin')) {
        window.otpManager = new OTPManager();
    }
});
