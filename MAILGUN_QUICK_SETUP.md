# SIMPLE FIX: Use Mailgun (Easier than SendGrid, Still Free)

## Why Mailgun is Better Than SendGrid:
- ✅ **5,000 free emails/month** (vs SendGrid's 100/day)
- ✅ **Simpler signup** (no phone verification)
- ✅ **Works immediately** on Railway
- ✅ **No sender verification needed** for your own domain

## Setup Steps (5 minutes):

### 1. Sign Up for Mailgun
Go to: https://signup.mailgun.com/new/signup
- Email: (your email)
- No credit card required
- Verify email

### 2. Get SMTP Credentials
After login:
1. Click "Sending" → "Domain Settings"
2. Click "SMTP" tab
3. You'll see:
   ```
   SMTP Hostname: smtp.mailgun.org
   Port: 587
   Username: postmaster@sandboxXXXX.mailgun.org
   Password: (shown on page)
   ```

### 3. Update Railway Variables

In Railway Dashboard → E-KOLEK → Variables:

```
EMAIL_BACKEND = django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST = smtp.mailgun.org
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = postmaster@sandboxXXXX.mailgun.org
EMAIL_HOST_PASSWORD = (your mailgun password)
DEFAULT_FROM_EMAIL = ekolekcenro@gmail.com
```

### 4. Done!

Emails will send immediately. No sender verification needed for sandbox domain.

---

## Alternative: Keep Trying Railway Support

If you really want Gmail SMTP, contact Railway:
https://railway.app/help

Ask: "Please enable outbound SMTP to smtp.gmail.com ports 587/465 for my project"

But Mailgun is faster and guaranteed to work! 🚀
