# 🚀 E-KOLEK Railway Deployment Guide
## Complete Step-by-Step Instructions

---

## ✅ PRE-DEPLOYMENT CHECKLIST

### What's Already Done ✓
- [x] WhiteNoise configured for static files
- [x] Gunicorn installed and configured
- [x] Procfile created with web, worker, and beat processes
- [x] runtime.txt set to Python 3.12.0
- [x] railway.json configured with auto-migration
- [x] .gitignore properly configured
- [x] Database supports both DATABASE_URL and individual settings
- [x] Redis/Celery supports REDIS_URL from Railway
- [x] All requirements in requirements.txt
- [x] django-ratelimit added
- [x] Security middleware configured

### Critical Configuration Updates Made ✓
1. **Database Configuration** - Now supports Railway's DATABASE_URL
2. **Redis/Celery Configuration** - Auto-detects Railway's REDIS_URL
3. **Static Files** - WhiteNoise properly configured
4. **Runtime** - Updated to Python 3.12.0

---

## 🎯 RAILWAY DEPLOYMENT STEPS

### Step 1: Push to GitHub

```powershell
cd "c:\Users\Lorenz\Documents\kolek - With OTP\kolek"

# Check git status
git status

# Add all files
git add .

# Commit changes
git commit -m "Prepare for Railway deployment - production ready"

# Push to GitHub
git push origin main
```

**Verify**: Check https://github.com/mdtevs/E-KOLEK.git to confirm all files are uploaded

---

### Step 2: Create Railway Project

1. Go to https://railway.app
2. Sign in with GitHub
3. Click **"New Project"**
4. Select **"Deploy from GitHub repo"**
5. Choose **mdtevs/E-KOLEK** repository
6. Click **"Deploy Now"**

---

### Step 3: Add PostgreSQL Database

1. In your Railway project dashboard
2. Click **"+ New"**
3. Select **"Database"** → **"PostgreSQL"**
4. Railway will automatically:
   - Create a PostgreSQL database
   - Generate `DATABASE_URL` environment variable
   - Make it available to your app

**Note**: `DATABASE_URL` format: `postgresql://user:password@host:port/database`

---

### Step 4: Add Redis (For Celery)

1. In your Railway project dashboard
2. Click **"+ New"**  
3. Select **"Database"** → **"Redis"**
4. Railway will automatically:
   - Create a Redis instance
   - Generate `REDIS_URL` environment variable
   - Make it available to your app

---

### Step 5: Configure Environment Variables

1. Click on your **Django web service**
2. Go to **"Variables"** tab
3. Click **"+ New Variable"**
4. Add each variable below:

```env
# === CORE DJANGO ===
DJANGO_SECRET_KEY=<GENERATE_NEW_SECRET_KEY>
DJANGO_DEBUG=False
ALLOWED_HOSTS=.railway.app
SITE_URL=https://<your-app>.railway.app

# === DATABASE (AUTO-PROVIDED BY RAILWAY) ===
# DATABASE_URL is automatically set - don't add manually

# === REDIS (AUTO-PROVIDED BY RAILWAY) ===
# REDIS_URL is automatically set - don't add manually

# === SECURITY ===
CSRF_TRUSTED_ORIGINS=https://<your-app>.railway.app
CORS_ALLOWED_ORIGINS=https://<your-app>.railway.app

# === EMAIL ===
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=ekolekcenro@gmail.com
EMAIL_HOST_PASSWORD=aeslhefyknzkuhet
DEFAULT_FROM_EMAIL=ekolekcenro@gmail.com

# === SMS & OTP ===
SMS_ENABLED=True
SMS_API_URL=https://www.iprogsms.com/api/v1/sms_messages
SMS_API_TOKEN=561bedeeb04ee035c27dfc92edf670f9bb5a0e51
SMS_API_TIMEOUT=10
SMS_PROVIDER=2
OTP_EXPIRY_MINUTES=5
OTP_MAX_ATTEMPTS=3
OTP_RESEND_COOLDOWN_SECONDS=60

# === JWT ===
JWT_ACCESS_TOKEN_LIFETIME_HOURS=1
JWT_REFRESH_TOKEN_LIFETIME_DAYS=30

# === GOOGLE DRIVE (DISABLED FOR RAILWAY) ===
USE_GOOGLE_DRIVE=False

# === CORS (ADD YOUR MOBILE APP DOMAINS IF NEEDED) ===
# CORS_ALLOWED_ORIGINS=https://your-mobile-app.com,https://<your-app>.railway.app
```

#### 🔑 Generate New SECRET_KEY

**CRITICAL**: Never use your development secret key in production!

Run locally:
```powershell
cd "c:\Users\Lorenz\Documents\kolek - With OTP\kolek"
& .\newenv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and use it as `DJANGO_SECRET_KEY` in Railway.

---

### Step 6: Update App-Specific URLs

After Railway deploys, you'll get a URL like: `https://your-app-name-production.up.railway.app`

Update these variables in Railway:
```env
ALLOWED_HOSTS=your-app-name-production.up.railway.app,.railway.app
SITE_URL=https://your-app-name-production.up.railway.app
CSRF_TRUSTED_ORIGINS=https://your-app-name-production.up.railway.app
CORS_ALLOWED_ORIGINS=https://your-app-name-production.up.railway.app
```

---

### Step 7: Monitor Deployment

1. Go to **"Deployments"** tab
2. Click on the latest deployment
3. Watch the **build logs** for any errors
4. Look for:
   ```
   ✓ Collecting static files...
   ✓ Running migrations...
   ✓ Starting gunicorn...
   ```

**Expected build time**: 3-5 minutes

---

### Step 8: Run Post-Deployment Commands

Once deployed successfully, create superadmin:

1. In Railway project, go to your **web service**
2. Click **"..."** (three dots) → **"Open Shell"**
3. Run:
```bash
python manage.py createsuperuser
```

Follow prompts to create admin account.

Or use the create_superadmin script:
```bash
python create_superadmin.py
```

---

### Step 9: Verify Deployment

1. **Check Homepage**: Visit `https://<your-app>.railway.app`
2. **Check Admin Panel**: Visit `https://<your-app>.railway.app/cenro/admin/login/`
3. **Test API**: Visit `https://<your-app>.railway.app/api/`
4. **Check Static Files**: Verify CSS/JS loads correctly

---

### Step 10: (Optional) Deploy Celery Workers

For background tasks (email OTP, SMS), you can deploy separate Celery services:

#### Celery Worker Service
1. Click **"+ New"** in Railway
2. Select **"Empty Service"**
3. Connect to same GitHub repo
4. Go to **"Settings"** → **"Deploy"**
5. Set **Custom Start Command**:
   ```bash
   celery -A eko worker --loglevel=info --concurrency=2
   ```
6. Go to **"Variables"** and **"Add Shared Variables"** from your main service

#### Celery Beat Service
1. Click **"+ New"** in Railway
2. Select **"Empty Service"**
3. Connect to same GitHub repo
4. Set **Custom Start Command**:
   ```bash
   celery -A eko beat --loglevel=info
   ```
5. Add same shared variables

---

## 🔍 TROUBLESHOOTING

### Issue: Static Files Not Loading
**Symptoms**: Website appears but no CSS/styling
**Solution**: 
1. Check build logs for collectstatic errors
2. Verify WhiteNoise is in MIDDLEWARE
3. Check STATICFILES_STORAGE setting

### Issue: Database Connection Error
**Symptoms**: 500 error or "database connection failed"
**Solution**:
1. Verify PostgreSQL service is running in Railway
2. Check DATABASE_URL is automatically set
3. Verify dj-database-url is in requirements.txt
4. Check migration logs

### Issue: Application Crashed / Not Starting
**Symptoms**: "Application failed to respond"
**Solution**:
1. Check deployment logs for Python errors
2. Verify gunicorn command in Procfile
3. Check PORT binding (should use $PORT)
4. Review Django system check errors

### Issue: Celery Tasks Not Running  
**Symptoms**: OTP emails not sending
**Solution**:
1. Check if Redis service is running
2. Verify REDIS_URL is set
3. Deploy separate Celery worker service
4. Check worker logs

### Issue: CSRF/CORS Errors
**Symptoms**: 403 Forbidden or CORS errors
**Solution**:
1. Update ALLOWED_HOSTS with Railway domain
2. Set CSRF_TRUSTED_ORIGINS correctly
3. Update CORS_ALLOWED_ORIGINS
4. Ensure https:// prefix in origins

---

## 📊 RAILWAY COSTS ESTIMATION

### Free Tier (Hobby Plan)
- **$5/month credit** (enough for small projects)
- PostgreSQL: ~$3-5/month
- Redis: ~$2-3/month
- Web service: Included in credit
- **Total**: ~$5-8/month (may exceed free tier)

### Pro Plan (Recommended for Production)
- **$20/month**
- Includes more resources
- Better performance
- Priority support

---

## 🔒 SECURITY CHECKLIST

- [x] DEBUG=False in production
- [x] Strong SECRET_KEY (never reuse development key)
- [x] ALLOWED_HOSTS configured with Railway domain
- [x] CSRF_TRUSTED_ORIGINS set
- [x] HTTPS enabled (Railway provides this)
- [x] Sensitive data in environment variables
- [x] .env file in .gitignore
- [x] Security middleware enabled
- [x] Session cookies secure (when not DEBUG)
- [x] CSRF cookies secure (when not DEBUG)

---

## 📈 POST-DEPLOYMENT TASKS

### Immediate
1. ✅ Test user registration
2. ✅ Test OTP functionality  
3. ✅ Test admin login
4. ✅ Verify email sending
5. ✅ Check SMS OTP

### Within 24 Hours
1. Create initial barangays
2. Create initial waste types
3. Configure game settings
4. Upload learning videos
5. Test mobile app connection

### Ongoing
1. Monitor Railway logs
2. Check database size
3. Review Celery task results
4. Monitor email/SMS usage
5. Backup database regularly

---

## 🎓 USEFUL RAILWAY COMMANDS

### View Logs
```bash
# In Railway shell or CLI
railway logs
```

### Run Django Commands
```bash
# Create superuser
python manage.py createsuperuser

# Run migrations
python manage.py migrate

# Check deployment
python manage.py check --deploy

# Collect static files
python manage.py collectstatic --noinput
```

### Database Access
```bash
# Access database shell
python manage.py dbshell

# Or use Railway PostgreSQL connection
railway connect postgres
```

---

## 📚 ADDITIONAL RESOURCES

- **Railway Docs**: https://docs.railway.app
- **Django Deployment**: https://docs.djangoproject.com/en/5.2/howto/deployment/
- **WhiteNoise**: https://whitenoise.readthedocs.io/
- **Gunicorn**: https://docs.gunicorn.org/
- **Celery**: https://docs.celeryq.dev/

---

## 🎉 SUCCESS INDICATORS

Your deployment is successful when:
- ✅ Homepage loads with styling
- ✅ Admin panel accessible and functional
- ✅ User registration works
- ✅ OTP emails/SMS send successfully
- ✅ Static files (CSS/JS/images) load
- ✅ No errors in Railway logs
- ✅ Database queries working
- ✅ Celery tasks processing

---

## 💡 TIPS FOR SMOOTH DEPLOYMENT

1. **Test Locally First**: Always test with `DEBUG=False` locally
2. **Monitor Logs**: Keep Railway logs open during first deployment
3. **One Step at a Time**: Don't rush through configuration
4. **Save Variables**: Keep a backup of your environment variables
5. **Document Changes**: Note any custom configurations
6. **Regular Backups**: Export database regularly
7. **Update Dependencies**: Keep packages updated for security

---

## 🆘 NEED HELP?

If you encounter issues:

1. **Check Railway Status**: https://status.railway.app
2. **Review Logs**: Railway dashboard → Deployments → Logs
3. **Django Debug**: Temporarily enable DEBUG=True to see errors (remember to disable!)
4. **Community**: Railway Discord or Django forums
5. **Documentation**: Re-read relevant sections of this guide

---

## 📞 FINAL CHECKLIST

Before considering deployment complete:

- [ ] Website accessible via Railway URL
- [ ] Admin panel working
- [ ] User registration functional
- [ ] OTP system working (email/SMS)
- [ ] Static files loading correctly
- [ ] Database persistent across deployments
- [ ] No errors in logs
- [ ] Celery workers running (if deployed)
- [ ] Mobile API endpoints responding
- [ ] All environment variables set correctly
- [ ] HTTPS working (Railway provides this)
- [ ] Monitoring/alerts configured (optional)

---

## 🚀 YOU'RE READY TO DEPLOY!

Your E-KOLEK application is now **fully configured** and **production-ready** for Railway deployment.

**Key improvements made:**
- Database configuration supports Railway's DATABASE_URL
- Redis/Celery auto-detects Railway's REDIS_URL
- All security settings properly configured
- Static files handled by WhiteNoise
- Comprehensive error handling
- Production-grade logging

**Follow the steps above carefully, and your deployment will be smooth and successful!**

Good luck! 🎉
