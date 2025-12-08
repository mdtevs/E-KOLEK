# MAKING GMAIL SMTP WORK ON RAILWAY - INVESTIGATION GUIDE

## Current Status

Railway CLI test showed ports 587 and 465 both work, but the Django app can't connect.

## Why This Happens

Railway has **different network policies** for:
1. ✅ **Interactive CLI sessions** (`railway run`) - Full network access
2. ❌ **Web service containers** - Restricted outbound SMTP

## Solutions to Try (In Order)

### Solution 1: Enable Railway Private Networking

Railway may require enabling private networking for SMTP:

1. Railway Dashboard → Your Project → Settings
2. Look for "Private Networking" or "Network Settings"
3. Enable outbound SMTP connections

### Solution 2: Use Railway's Network Service Reference

Check if Railway provides internal SMTP relay:

```bash
# Test from Railway container
railway run python debug_smtp.py
```

This will show exactly which ports are blocked.

### Solution 3: Contact Railway Support (Most Likely Needed)

Railway blocks SMTP by default for security. You need to request whitelist:

**Email Railway Support:**
- To: support@railway.app
- Subject: "Request SMTP Port Access for E-KOLEK Project"
- Body:
```
Hi Railway Team,

I'm developing E-KOLEK, a waste management system that needs to send:
- OTP verification emails
- Password reset emails  
- Schedule update notifications to users
- Admin notifications

Could you please enable outbound SMTP access (ports 587/465) for my project?

Project: E-KOLEK
Service: e-kolek-production.up.railway.app
Email provider: Gmail SMTP (smtp.gmail.com)
Use case: Transactional emails for waste management app

Thank you!
```

### Solution 4: Check Gmail "Less Secure Apps" Setting

Even though ports work, Gmail might be blocking Railway's IP:

1. Go to: https://myaccount.google.com/security
2. Check "Less secure app access"
3. OR generate App-Specific Password:
   - Google Account → Security → 2-Step Verification
   - App passwords → Mail → Generate
   - Use this password instead

### Solution 5: Debug Exact Error

Run the diagnostic script on Railway:

```bash
railway run python debug_smtp.py
```

This will show:
- Which ports are actually blocked
- DNS resolution status
- Exact error messages
- Network policy restrictions

## Testing Steps

1. **Deploy debug script:**
```bash
git add debug_smtp.py accounts/email_backend.py
git commit -m "Add SMTP debugging and remove third-party services"
git push origin master
```

2. **Wait for Railway deployment** (~2 min)

3. **Run diagnostic:**
```bash
railway run python debug_smtp.py
```

4. **Check results:**
   - If all ports blocked → Contact Railway support
   - If ports open but auth fails → Check password
   - If everything passes → Issue is in Django settings

## Expected Outcome

Most likely: Railway blocks SMTP for web services, but support can whitelist your project.

Alternative: Use App-Specific Password if Gmail is blocking Railway IPs.
