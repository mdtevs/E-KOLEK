# Railway Deployment Guide - E-KOLEK System

## 📋 Pre-Deployment Analysis Complete

Your Django project has been thoroughly analyzed and is **production-ready** with the following configuration:

### ✅ Project Structure
- **Framework**: Django 5.2 with PostgreSQL
- **Apps**: accounts, cenro, game, learn, mobilelogin, ekoscan
- **Authentication**: Dual system (Web: Session + JWT for Mobile API)
- **Background Tasks**: Celery + Redis
- **Storage Options**: Local filesystem or Google Drive OAuth

---

## 🚨 CRITICAL ISSUES TO FIX BEFORE DEPLOYMENT

### 1. **Missing WhiteNoise for Static Files** ⚠️
Railway doesn't serve static files by default. You MUST add WhiteNoise.

**Issue**: Your `settings.py` doesn't have WhiteNoise configured.

**Required Changes**:
```python
# In eko/settings.py MIDDLEWARE (add after SecurityMiddleware)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ADD THIS LINE
    # ... rest of middleware
]

# At the bottom of settings.py
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### 2. **Google Drive Path Hardcoding** ⚠️
Your `.env` has Windows-specific paths that won't work on Railway:

**Current** (WRONG for Railway):
```
GOOGLE_DRIVE_OAUTH_CREDENTIALS_FILE=C:\Users\Lorenz\Documents\kolek - With OTP\kolek\google-drive-oauth-credentials.json
```

**Should be** (for Railway):
```
USE_GOOGLE_DRIVE=False  # Recommended for Railway
# OR use relative paths:
# GOOGLE_DRIVE_OAUTH_CREDENTIALS_FILE=/app/google-drive-oauth-credentials.json
```

**Recommendation**: Disable Google Drive for Railway and use Railway's persistent volumes instead.

### 3. **Procfile Missing** ⚠️
Railway needs a `Procfile` to know how to run your app.

---

## 📦 REQUIRED PIP PACKAGES FOR RAILWAY

Install these packages (you'll add to requirements.txt yourself):

```
Django==5.2
psycopg2-binary==2.9.9
python-decouple==3.8
djangorestframework==3.14.0
djangorestframework-simplejwt==5.3.1
django-cors-headers==4.3.1
django-csp==3.8
celery==5.3.4
django-celery-results==2.5.1
django-celery-beat==2.5.0
redis==5.0.1
gunicorn==21.2.0
whitenoise==6.6.0
cryptography==41.0.7
requests==2.31.0
Pillow==10.2.0
pandas==2.1.4
matplotlib==3.8.2
google-auth==2.25.2
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
google-api-python-client==2.111.0
```

**Why these packages?**
- `psycopg2-binary`: PostgreSQL adapter (Railway uses PostgreSQL)
- `gunicorn`: Production WSGI server (Railway requirement)
- `whitenoise`: Serves static files without Nginx
- `cryptography`: For session encryption in your code
- `google-*`: For Google Drive integration (if enabled)
- `pandas`, `matplotlib`: Used in analytics views
- `Pillow`: Image processing
- `requests`: SMS/OTP API calls

---

## 🔧 RAILWAY SETUP STEPS

### Step 1: Create Required Files

#### 1.1 Create `Procfile` (Railway startup commands)
Create file: `Procfile` (no extension)
```
web: gunicorn eko.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120
worker: celery -A eko worker --loglevel=info --concurrency=2
beat: celery -A eko beat --loglevel=info
```

**Note**: Railway will run the `web` process. For Celery, you'll need to create separate services.

#### 1.2 Create `runtime.txt` (Optional - Python version)
```
python-3.11.7
```

#### 1.3 Create `railway.json` (Optional - Railway configuration)
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn eko.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Step 2: Update `.gitignore`
Your `.gitignore` is already excellent! Verify these are included:
```
.env
.env.local
.env.production
google-drive-*.json
google-drive-*.pickle
media/
logs/
```

### Step 3: Push to GitHub
```bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

---

## 🗄️ DATABASE MIGRATION TO `ekolek_cenro`

### Option A: Create Fresh Database (Recommended for Railway)

**On Railway, you'll get a NEW PostgreSQL database automatically.**

1. **On Railway Dashboard**:
   - Add PostgreSQL plugin to your project
   - Railway will provide: `DATABASE_URL`

2. **Set Environment Variables on Railway**:
   ```
   DATABASE_URL=<provided by Railway>
   # Railway format: postgresql://user:password@host:port/database
   ```

3. **Run Migrations** (Railway will do this automatically if you add to build):
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

### Option B: Migrate Existing Data to `ekolek_cenro` (Local Testing First)

**Before deploying to Railway, test locally with new database:**

1. **Create New Database Locally**:
   ```sql
   -- Connect to PostgreSQL
   psql -U postgres
   
   -- Create new database
   CREATE DATABASE ekolek_cenro;
   GRANT ALL PRIVILEGES ON DATABASE ekolek_cenro TO postgres;
   ```

2. **Update Local `.env`**:
   ```
   DB_NAME=ekolek_cenro
   DB_USER=postgres
   DB_PASSWORD=renz123
   DB_HOST=localhost
   DB_PORT=5432
   ```

3. **Run Migrations**:
   ```bash
   python manage.py migrate
   ```

4. **Optional: Copy Data from Old Database**:
   ```bash
   # Dump old database
   pg_dump -U postgres cenro_db > backup.sql
   
   # Load into new database
   psql -U postgres ekolek_cenro < backup.sql
   ```

5. **Verify Everything Works Locally**:
   ```bash
   python manage.py runserver
   ```

---

## 🔐 RAILWAY ENVIRONMENT VARIABLES

Set these in Railway Dashboard → Project → Variables:

### Core Django Settings
```
DJANGO_SECRET_KEY=<generate new strong key - DO NOT reuse local key>
DJANGO_DEBUG=False
ALLOWED_HOSTS=<your-app>.railway.app,.railway.app
SITE_URL=https://<your-app>.railway.app
```

### Database (Automatically provided by Railway)
```
DATABASE_URL=<provided by Railway PostgreSQL plugin>
```

**Note**: When using `DATABASE_URL`, update `settings.py` to parse it:
```python
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default=''),
        conn_max_age=600
    )
}
```
**Add to requirements.txt**: `dj-database-url==2.1.0`

### Security Settings
```
CSRF_TRUSTED_ORIGINS=https://<your-app>.railway.app
CORS_ALLOWED_ORIGINS=https://<your-app>.railway.app
```

### Email Configuration
```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=ekolekcenro@gmail.com
EMAIL_HOST_PASSWORD=<your-gmail-app-password>
DEFAULT_FROM_EMAIL=ekolekcenro@gmail.com
```

### SMS/OTP Configuration
```
SMS_ENABLED=True
SMS_API_URL=https://www.iprogsms.com/api/v1/sms_messages
SMS_API_TOKEN=<your-token>
SMS_API_TIMEOUT=10
SMS_PROVIDER=2
OTP_EXPIRY_MINUTES=5
OTP_MAX_ATTEMPTS=3
OTP_RESEND_COOLDOWN_SECONDS=60
```

### JWT Settings
```
JWT_ACCESS_TOKEN_LIFETIME_HOURS=1
JWT_REFRESH_TOKEN_LIFETIME_DAYS=30
```

### Google Drive (Recommended: Disable for Railway)
```
USE_GOOGLE_DRIVE=False
```

### Celery & Redis (Railway Redis Plugin)
```
CELERY_BROKER_URL=redis://<provided by Railway Redis>
CACHE_BACKEND=django.core.cache.backends.redis.RedisCache
CACHE_LOCATION=redis://<provided by Railway Redis>
```

---

## 🚀 RAILWAY DEPLOYMENT WORKFLOW

### 1. Connect Railway to GitHub
1. Go to Railway.app
2. Create new project
3. Connect to your GitHub repository
4. Select the branch (e.g., `main`)

### 2. Add Services

#### Main Web Service (Django)
- Railway will auto-detect Django
- It will run `Procfile` → `web` command

#### PostgreSQL Service
- Click "+ New"
- Select "Database" → "PostgreSQL"
- Railway automatically provides `DATABASE_URL`

#### Redis Service (for Celery)
- Click "+ New"
- Select "Database" → "Redis"
- Railway provides `REDIS_URL`

#### Celery Worker Service (Optional - Separate Service)
- Click "+ New"
- Select "Empty Service"
- Connect same GitHub repo
- Set custom start command: `celery -A eko worker --loglevel=info`

#### Celery Beat Service (Optional)
- Click "+ New"
- Select "Empty Service"
- Connect same GitHub repo
- Set custom start command: `celery -A eko beat --loglevel=info`

### 3. Configure Build Command (Optional)
Railway auto-detects Python. To customize:

**Settings → Deploy → Build Command:**
```bash
python manage.py collectstatic --noinput && python manage.py migrate
```

### 4. Deploy
- Push to GitHub
- Railway auto-deploys
- Monitor logs in Railway dashboard

---

## ✅ POST-DEPLOYMENT CHECKLIST

### 1. Verify Deployment
- [ ] Website loads: `https://<your-app>.railway.app`
- [ ] Admin panel accessible: `/admin/`
- [ ] Static files load (CSS, JS, images)
- [ ] Media uploads work (if using Railway volumes)

### 2. Test Authentication
- [ ] Web login works (session-based)
- [ ] Mobile API login works (JWT)
- [ ] OTP sending works (SMS)
- [ ] Email OTP works

### 3. Test Background Tasks
- [ ] Celery worker is running (check logs)
- [ ] Email notifications send
- [ ] Scheduled tasks execute

### 4. Security Verification
- [ ] `DEBUG=False` confirmed
- [ ] SSL/HTTPS works
- [ ] Admin panel requires strong password
- [ ] CSRF protection active

### 5. Database
- [ ] Migrations applied
- [ ] Data accessible
- [ ] Create test user/admin

---

## 🐛 TROUBLESHOOTING

### Static Files Not Loading
**Solution**: Add WhiteNoise (see Critical Issues above)

### Database Connection Error
**Solution**: 
1. Verify Railway PostgreSQL is running
2. Check `DATABASE_URL` environment variable
3. Install `dj-database-url` package

### Celery Not Working
**Solution**:
1. Verify Railway Redis is running
2. Check `CELERY_BROKER_URL` environment variable
3. Create separate Celery worker service

### Port Binding Error
**Solution**: Railway provides `$PORT` variable. Gunicorn command uses `0.0.0.0:$PORT`

### Google Drive Errors
**Solution**: Set `USE_GOOGLE_DRIVE=False` on Railway (OAuth doesn't work well in cloud)

---

## 📊 RAILWAY COST ESTIMATION

- **Hobby Plan** (Free): Limited hours, suitable for testing
- **Developer Plan** ($5/month): Unlimited hours, suitable for small apps
- **Services Needed**:
  - 1x Web service (Django)
  - 1x PostgreSQL
  - 1x Redis
  - Optional: 2x Celery services

**Recommendation**: Start with Hobby plan, upgrade if needed.

---

## 🔒 SECURITY REMINDERS

1. **Never commit `.env` to GitHub** ✅ (your .gitignore is correct)
2. **Generate new `DJANGO_SECRET_KEY` for production**
3. **Use strong database password** (Railway generates this)
4. **Enable HTTPS** (Railway provides this automatically)
5. **Set `DEBUG=False`** in production
6. **Regularly update dependencies** (security patches)
7. **Monitor logs** for suspicious activity
8. **Backup database regularly** (Railway provides backups)

---

## 📞 NEXT STEPS

1. **Install required packages** (add to requirements.txt)
2. **Create Procfile, runtime.txt, railway.json**
3. **Add WhiteNoise configuration to settings.py**
4. **Update DATABASE_URL parsing in settings.py**
5. **Test locally with `ekolek_cenro` database**
6. **Push to GitHub**
7. **Connect Railway to GitHub**
8. **Add PostgreSQL and Redis plugins**
9. **Set environment variables**
10. **Deploy and monitor logs**

---

## 📚 Additional Resources

- Railway Docs: https://docs.railway.app
- Django Deployment Checklist: https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
- WhiteNoise: https://whitenoise.readthedocs.io/
- Gunicorn: https://docs.gunicorn.org/

---

**Ready to deploy! Follow the steps carefully and monitor Railway logs during deployment.** 🚀
