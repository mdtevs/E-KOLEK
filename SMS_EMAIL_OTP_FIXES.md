# 🔧 SMS, OTP & EMAIL SERVICE FIXES

## 📋 ISSUES FOUND:

### 1. ❌ Railway Redis Not Configured
- Redis service exists but `REDIS_URL` environment variable NOT set
- Celery can't connect to message broker
- Email tasks queue but never execute

### 2. ❌ Celery Worker Not Running on Railway
- No worker process in Procfile
- Email tasks accumulate but never processed
- OTP emails never sent

### 3. ⚠️ SMS Service Configured but Not Tested
- API token present: `561bedeeb04ee035c27dfc92edf670f9bb5a0e51`
- iProg Tech API endpoint configured
- Need to verify token validity

### 4. ⚠️ Email Fallback Not Working
- Code has fallback to direct sending when Celery unavailable
- But Gmail SMTP may need App Password verification

---

## ✅ SOLUTION 1: Configure Railway Redis (CRITICAL)

### Step 1: Get Redis URL from Railway

```powershell
railway link
railway service
```

Select **Redis** service, then run:

```powershell
railway variables --service Redis
```

Look for `REDIS_URL` or `DATABASE_URL` from Redis service.

### Step 2: Add REDIS_URL to E-KOLEK Service

Go to Railway Dashboard:
1. Click **E-KOLEK** service
2. Click **Variables** tab
3. Click **+ New Variable**
4. Add:
   - **Variable:** `REDIS_URL`
   - **Value:** `${{Redis.REDIS_URL}}` ← This references Redis service URL

**OR** use Railway CLI:

```powershell
railway variables --service E-KOLEK
railway link --service E-KOLEK
railway variables set REDIS_URL='${{Redis.REDIS_URL}}'
```

---

## ✅ SOLUTION 2: Add Celery Worker to Railway

### Option A: Update Procfile (Multi-Process)

Current Procfile runs only web process. We need to add worker process.

**⚠️ Railway Free Tier Limitation:** Railway free tier allows 1 service. We need to run both web and worker in the SAME process using a process manager.

### Option B: Use Celery in Same Process (Recommended for Railway Free Tier)

We'll modify the setup to run Celery worker alongside gunicorn.

**Create `start.sh` script:**

```bash
#!/bin/bash
# Start script for Railway deployment

echo "🚀 Starting E-KOLEK..."

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Start Celery worker in background
celery -A eko worker --loglevel=info --detach --logfile=/tmp/celery-worker.log

# Start Gunicorn web server
gunicorn eko.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --log-level debug --access-logfile - --error-logfile -
```

**Update Procfile:**

```
web: bash start.sh
```

### Option C: Use Celery Beat for Scheduled Tasks (Optional)

If you need scheduled tasks:

```bash
celery -A eko beat --loglevel=info --detach &
celery -A eko worker --loglevel=info --detach &
gunicorn eko.wsgi:application --bind 0.0.0.0:$PORT
```

---

## ✅ SOLUTION 3: Email Service Fallback (Immediate Fix)

The code already has fallback to direct SMTP when Celery unavailable. Let's verify Gmail setup:

### Test Gmail SMTP Locally:

```python
python manage.py shell
```

```python
from django.core.mail import send_mail
from django.conf import settings

# Test email sending
result = send_mail(
    subject='E-KOLEK Test Email',
    message='This is a test email from E-KOLEK',
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=['your-test-email@gmail.com'],  # YOUR EMAIL HERE
    fail_silently=False
)

print(f"Email sent: {result}")
```

If this fails with "Authentication failed", you need:
1. Enable 2-Factor Authentication on `ekolekcenro@gmail.com`
2. Generate App Password at: https://myaccount.google.com/apppasswords
3. Update `EMAIL_HOST_PASSWORD` with the new App Password

---

## ✅ SOLUTION 4: SMS Service Testing

### Test SMS API:

```python
python manage.py shell
```

```python
from accounts.otp_service import send_otp

# Test SMS sending (use YOUR phone number)
result = send_otp('09171234567', 'Your E-KOLEK OTP is: :otp')

print(f"SMS Result: {result}")
print(f"Success: {result.get('success')}")
print(f"OTP Code: {result.get('data', {}).get('otp_code')}")
```

If it fails:
- Check API token validity with iProg Tech
- Verify account has SMS credits
- Check phone number format (must be 639XXXXXXXXX)

---

## ✅ SOLUTION 5: Enable OTP Email Fallback (Production-Ready)

If Celery/Redis too complex for now, we can make email OTP work WITHOUT Celery using direct SMTP:

**Modify `email_otp_service.py` to prioritize direct sending:**

The code already has this logic! Just ensure:
1. Gmail SMTP credentials are correct
2. App Password is valid
3. `EMAIL_BACKEND` is set to `django.core.mail.backends.smtp.EmailBackend`

---

## 🎯 QUICK FIX FOR RAILWAY (Choose One):

### Option A: Disable Celery, Use Direct Sending (Fastest)

No Redis/Celery needed. Emails sent directly via SMTP.

**Update Railway Variables:**
```
# Remove REDIS_URL (or leave empty)
# Email will use direct SMTP fallback
```

**No code changes needed!** Your `email_otp_service.py` already handles this:
```python
if use_celery:
    # Try Celery
else:
    # Fallback to direct sending (THIS WILL BE USED)
```

### Option B: Full Celery Setup (Best for Production)

Follow Solution 1 + Solution 2:
1. Add `REDIS_URL=${{Redis.REDIS_URL}}` to E-KOLEK service
2. Update Procfile with `start.sh` script
3. Deploy

---

## 📝 STEP-BY-STEP IMPLEMENTATION:

### For Local Development:

1. **Start Redis:**
   ```powershell
   .\run_redis.bat
   ```

2. **Start Celery Worker:**
   ```powershell
   .\run_celery.bat
   ```

3. **Start Django:**
   ```powershell
   python manage.py runserver
   ```

### For Railway Production (Quick Fix):

1. **Verify Gmail App Password**
2. **Test email sending works without Celery** (fallback mode)
3. **SMS should work already** (no dependencies)

### For Railway Production (Full Solution):

1. **Add REDIS_URL variable** (as shown in Solution 1)
2. **Create `start.sh` script** (as shown in Solution 2)
3. **Update Procfile**
4. **Git commit and push**
5. **Railway auto-redeploys**

---

## 🧪 TESTING:

### Test Email OTP:
```python
from accounts.email_otp_service import send_otp

result = send_otp('your-email@gmail.com', purpose='verification')
print(result)
```

### Test SMS OTP:
```python
from accounts.otp_service import send_otp

result = send_otp('09171234567')
print(result)
```

### Test Celery (if configured):
```python
from accounts.tasks import test_celery_task

task = test_celery_task.delay("Hello from Celery!")
print(f"Task ID: {task.id}")
print(f"Task Status: {task.status}")
```

---

## 🚨 TROUBLESHOOTING:

### Email Not Sending:
1. Check Gmail credentials in .env
2. Generate new App Password if needed
3. Check logs: `railway logs --service E-KOLEK`

### SMS Not Sending:
1. Verify API token with iProg Tech
2. Check account has credits
3. Test with different phone number
4. Check logs for HTTP errors

### Celery Not Working:
1. Verify REDIS_URL is set
2. Check worker logs: `cat /tmp/celery-worker.log` (on Railway)
3. Ensure Redis service is running

### Redis Connection Failed:
1. Verify Redis service is running in Railway
2. Check REDIS_URL format: `redis://...`
3. Ensure E-KOLEK can reach Redis (internal network)

---

## 💡 RECOMMENDATIONS:

1. **For Now (Quickest):** Use direct email sending (no Celery) - Already works!
2. **For Production:** Setup Celery + Redis properly (better scalability)
3. **For SMS:** Test API token validity - May need to contact iProg Tech
4. **For Testing:** Use local Redis + Celery worker in development

---

## 📞 NEXT STEPS:

1. Choose Quick Fix (Option A) or Full Solution (Option B)
2. Implement chosen solution
3. Test email OTP sending
4. Test SMS OTP sending
5. Verify on Railway production

Let me know which approach you prefer!
