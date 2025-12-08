
    const togglePasswordBtn = document.getElementById('togglePassword');
    if (togglePasswordBtn) {
      togglePasswordBtn.addEventListener('click', function () {
        const passwordInput = document.getElementById('passwordInput');
        const eyeIcon = document.getElementById('eyeIcon');
        if (passwordInput.type === 'password') {
          passwordInput.type = 'text';
          eyeIcon.innerHTML = '<circle cx="12" cy="12" r="3"/><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/><line x1="4" y1="4" x2="20" y2="20" stroke="#dc2626" stroke-width="2"/>';
        } else {
          passwordInput.type = 'password';
          eyeIcon.innerHTML = '<path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/><circle cx="12" cy="12" r="3"/>';
        }
      });
    }

    document.querySelectorAll('form').forEach(form => {
      form.addEventListener('submit', function() {
        document.getElementById('loader').style.display = 'flex';
      });
    });

    function switchTab(tab) {
      const isCode = tab === 'code';
      document.getElementById("codeLogin").classList.toggle("active", isCode);
      document.getElementById("qrLogin").classList.toggle("active", !isCode);
      document.getElementById("codeTab").classList.toggle("active", isCode);
      document.getElementById("qrTab").classList.toggle("active", !isCode);
      if (!isCode) { startQrScanner(); }
      else if (window.qrReader) { window.qrReader.stop().catch(() => {}); window.qrReader = null; }
    }

    function showMessage(text, isError = false) {
      const msg = document.createElement('div');
      const bgColor = isError ? '#ef4444' : '#4ade80';
      msg.style.cssText = `position:fixed;top:20px;right:20px;background:${bgColor};color:white;padding:15px 20px;border-radius:8px;z-index:9999;font-weight:500;max-width:300px;`;
      msg.textContent = text;
      document.body.appendChild(msg);
      
      // Auto-remove after 4 seconds
      setTimeout(() => {
        if (msg.parentNode) msg.parentNode.removeChild(msg);
      }, 4000);
    }

    function startQrScanner() {
      if (window.qrReader) return;
      
      console.log('Starting QR scanner...');
      
      try {
        window.qrReader = new Html5Qrcode("qr-reader");
        
        window.qrReader.start(
          { facingMode: "environment" },
          { fps: 10, qrbox: { width: 260, height: 260 }, aspectRatio: 1 },
          qrCodeMessage => {
            console.log('QR Code detected:', qrCodeMessage.substring(0, 10) + '...');
            
            window.qrReader.stop(); 
            window.qrReader = null;
            document.getElementById('loader').style.display = 'flex';
            
            // Enhanced QR login with better error handling
            AppUtils.fetchWithCSRF(window.DJANGO_URLS.qrLogin, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ user_id: qrCodeMessage })
            })
            .then(res => {
              console.log('QR Login response status:', res.status);
              return res.json();
            })
            .then(data => {
              console.log('QR Login response data:', data);

              // If server sent OTP for verification, redirect to verify_otp page (same as code login)
              if (data.otp_sent) {
                // Keep loader visible during redirect
                showMessage('OTP sent to your phone. Redirecting to verification page...');
                // Redirect to the same OTP verification page as code login
                setTimeout(() => {
                  window.location.href = '/accounts/otp/verify/';
                }, 1000);
                return;
              }
              
              if (data.success) {
                console.log('QR Login successful for user:', data.user_name);
                console.log('Search method used:', data.search_method);
                
                // Show success message and keep loading during redirect
                showMessage(`Welcome ${data.user_name}! Redirecting...`);
                
                // Keep loading spinner visible during redirect
                // Redirect after brief delay (no popup needed)
                setTimeout(() => {
                  window.location.href = window.DJANGO_URLS.userDashboard;
                }, 1500);
                
              } else if (data.error) {
                // Hide loader only on errors
                document.getElementById('loader').style.display = 'none';
                console.error('QR Login failed:', data.error);
                showMessage(`Login failed: ${data.error}`, true);
                switchTab('code');
              } else {
                // Hide loader only on errors
                document.getElementById('loader').style.display = 'none';
                console.error('QR Login: Unexpected response format');
                showMessage("Unexpected response from server", true);
                switchTab('code');
              }
            })
            .catch(err => {
              document.getElementById('loader').style.display = 'none';
              console.error('QR Login network error:', err);
              showMessage("Network error during login. Please check your connection", true);
              switchTab('code');
            });
          },
          error => {
            console.warn('QR Scanner error (can be ignored):', error);
          }
        ).catch(err => { 
          console.error('QR Scanner start error:', err);
          showMessage("Camera error. Please allow camera access and try again", true);
        });
      } catch (err) {
        console.error('QR Scanner initialization error:', err);
        showMessage("Failed to initialize QR scanner. Please check camera permissions", true);
      }
    }

    document.addEventListener("DOMContentLoaded", () => {
      switchTab('code');
    });

   