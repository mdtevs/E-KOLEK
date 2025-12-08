# Pre-Deployment Checklist - Railway Deployment

## ⚠️ CRITICAL: Complete ALL items before deploying to Railway

### 🔧 Code Changes Required

- [ ] **1. Add WhiteNoise to settings.py**
  - Open: `eko/settings.py`
  - Find: `MIDDLEWARE = [`
  - Add after SecurityMiddleware: `'whitenoise.middleware.WhiteNoiseMiddleware',`
  - Add at bottom: `STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'`

- [ ] **2. Update Database Configuration in settings.py**
  - Open: `eko/settings.py`
  - Add at top: `import dj_database_url`
  - Replace DATABASES section with:
  ```python
  DATABASES = {
      'default': dj_database_url.config(
          default=config('DATABASE_URL', default=''),
          conn_max_age=600,
          conn_health_checks=True
      ) if config('DATABASE_URL', default='') else {
          'ENGINE': 'django.db.backends.postgresql',
          'NAME': config('DB_NAME'),
          'USER': config('DB_USER'),
          'PASSWORD': config('DB_PASSWORD'),
          'HOST': config('DB_HOST', default='localhost'),
          'PORT': config('DB_PORT', default='5432', cast=int),
          'CONN_MAX_AGE': 600,
          'OPTIONS': {'connect_timeout': 10},
      }
  }
  ```

- [ ] **3. Update requirements.txt**
  - Add all packages from `RAILWAY_PACKAGES.txt`
  - Or copy the entire file content to `requirements.txt`

- [ ] **4. Disable Google Drive for Railway** (Recommended)
  - In your production `.env` or Railway variables: `USE_GOOGLE_DRIVE=False`
  - Reason: OAuth flow doesn't work well in Railway environment

### 📁 Files Created (Verify They Exist)

- [x] `Procfile` - Railway startup commands
- [x] `runtime.txt` - Python version specification
- [x] `railway.json` - Railway deployment configuration
- [x] `RAILWAY_DEPLOYMENT_GUIDE.md` - Complete deployment guide
- [x] `RAILWAY_PACKAGES.txt` - Required packages list

### 🗄️ Database Migration (Local Testing)

- [ ] **5. Test Migration to ekolek_cenro** (Local Only)
  ```powershell
  # Set your PostgreSQL password first
  $env:PGPASSWORD = "renz123"
  
  # Run migration script
  .\migrate_to_ekolek_cenro.ps1
  ```

- [ ] **6. Verify Local Database Works**
  ```powershell
  python manage.py runserver
  # Test all features: login, admin, uploads, etc.
  ```

### 🔐 Environment Variables Preparation

- [ ] **7. Generate New SECRET_KEY for Production**
  ```powershell
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
  - Save this - you'll add to Railway variables
  - ⚠️ NEVER reuse your development SECRET_KEY

- [ ] **8. Prepare Railway Environment Variables**
  - Copy template below and fill in values
  - You'll paste these in Railway Dashboard → Variables

### 🚀 GitHub Preparation

- [ ] **9. Review .gitignore**
  - Verify `.env` is NOT committed
  - Verify `google-drive-*.json` files are NOT committed
  - Verify `media/` and `logs/` are ignored

- [ ] **10. Commit and Push**
  ```powershell
  git add .
  git status  # Verify no sensitive files
  git commit -m "Prepare for Railway deployment"
  git push origin main
  ```

### 🌐 Railway Setup

- [ ] **11. Create Railway Project**
  - Go to https://railway.app
  - Create new project
  - Connect to GitHub repository

- [ ] **12. Add PostgreSQL Plugin**
  - Click "+ New"
  - Select "Database" → "PostgreSQL"
  - Railway will provide `DATABASE_URL`

- [ ] **13. Add Redis Plugin**
  - Click "+ New"
  - Select "Database" → "Redis"
  - Railway will provide `REDIS_URL`

- [ ] **14. Configure Environment Variables**
  - Go to Variables tab
  - Add all variables from template below

- [ ] **15. Deploy**
  - Railway will auto-deploy from GitHub
  - Monitor logs for errors

### ✅ Post-Deployment Verification

- [ ] **16. Check Deployment Status**
  - Website loads: `https://<your-app>.railway.app`
  - No error pages

- [ ] **17. Test Core Features**
  - [ ] Homepage loads
  - [ ] Admin login works: `/admin/`
  - [ ] User login works
  - [ ] Static files load (CSS/JS)
  - [ ] Database queries work

- [ ] **18. Test Background Services**
  - [ ] Send test email (OTP)
  - [ ] Send test SMS
  - [ ] Check Celery logs

- [ ] **19. Security Check**
  - [ ] Verify `DEBUG=False` (check Railway logs)
  - [ ] Verify HTTPS is active
  - [ ] Test CSRF protection

---

## 📋 Railway Environment Variables Template

Copy this template and fill in your values:

```
# ===== CORE DJANGO =====
DJANGO_SECRET_KEY=<paste-new-secret-key-here>
DJANGO_DEBUG=False
ALLOWED_HOSTS=<your-app>.railway.app,.railway.app
SITE_URL=https://<your-app>.railway.app

# ===== DATABASE (PROVIDED BY RAILWAY) =====
# DATABASE_URL is automatically set by Railway PostgreSQL plugin
# No need to set DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

# ===== SECURITY =====
CSRF_TRUSTED_ORIGINS=https://<your-app>.railway.app
CORS_ALLOWED_ORIGINS=https://<your-app>.railway.app

# ===== EMAIL =====
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=ekolekcenro@gmail.com
EMAIL_HOST_PASSWORD=aeslhefyknzkuhet
DEFAULT_FROM_EMAIL=ekolekcenro@gmail.com

# ===== SMS & OTP =====
SMS_ENABLED=True
SMS_API_URL=https://www.iprogsms.com/api/v1/sms_messages
SMS_API_TOKEN=561bedeeb04ee035c27dfc92edf670f9bb5a0e51
SMS_API_TIMEOUT=10
SMS_PROVIDER=2
OTP_EXPIRY_MINUTES=5
OTP_MAX_ATTEMPTS=3
OTP_RESEND_COOLDOWN_SECONDS=60

# ===== JWT =====
JWT_ACCESS_TOKEN_LIFETIME_HOURS=1
JWT_REFRESH_TOKEN_LIFETIME_DAYS=30

# ===== GOOGLE DRIVE (DISABLED) =====
USE_GOOGLE_DRIVE=False

# ===== CELERY (USE RAILWAY REDIS) =====
# CELERY_BROKER_URL will use REDIS_URL from Railway Redis plugin
# CACHE_BACKEND=django.core.cache.backends.redis.RedisCache
# CACHE_LOCATION will use REDIS_URL from Railway Redis plugin
```

---

## 🔧 Code Changes Script

If you want to apply changes automatically, run these commands:

### Add WhiteNoise to MIDDLEWARE (Manual Edit Required)
Open `eko/settings.py` and modify the MIDDLEWARE list.

### Update requirements.txt
```powershell
# Copy packages to requirements.txt
Get-Content RAILWAY_PACKAGES.txt | Select-String -Pattern "^[a-zA-Z]" | Out-File requirements.txt -Encoding utf8
```

---

## ⚠️ Common Issues & Solutions

### Issue: Static files not loading
**Solution**: Verify WhiteNoise is installed and configured

### Issue: Database connection error
**Solution**: Check that Railway PostgreSQL plugin is added and `DATABASE_URL` is available

### Issue: Port binding error
**Solution**: Ensure Procfile uses `$PORT` variable (already configured)

### Issue: Celery not working
**Solution**: Create separate Railway services for Celery worker and beat

### Issue: Google Drive errors
**Solution**: Set `USE_GOOGLE_DRIVE=False` on Railway

---

## 📞 Need Help?

- Railway Docs: https://docs.railway.app
- Django Deployment: https://docs.djangoproject.com/en/5.2/howto/deployment/
- Check Railway logs for detailed error messages

---

**Once you complete this checklist, you're ready to deploy! 🚀**
