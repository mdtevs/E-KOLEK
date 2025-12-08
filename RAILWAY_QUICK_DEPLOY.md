# 🚀 RAILWAY DEPLOYMENT - QUICK GUIDE

## 📍 STEP-BY-STEP CHECKLIST

### ✅ Step 1: Create Railway Project (IN BROWSER NOW)

1. **Sign in with GitHub** (if not already signed in)
2. Click **"Deploy from GitHub repo"**
3. Select **mdtevs/E-KOLEK**
4. Click **"Deploy Now"**

⏱️ Wait ~2-3 minutes for initial deployment

---

### ✅ Step 2: Add PostgreSQL Database

1. In Railway dashboard, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Done! (DATABASE_URL is auto-created)

---

### ✅ Step 3: Add Redis

1. Click **"+ New"** again
2. Select **"Database"** → **"Redis"**
3. Done! (REDIS_URL is auto-created)

---

### ✅ Step 4: Configure Environment Variables

Click on your **Django web service** → **Variables** tab → **Raw Editor**

Copy and paste ALL of this:

```
DJANGO_SECRET_KEY=6#h=&kzhrkystderfv557##4u0b@y&)w$0j574q92c(2q%t)8+
DJANGO_DEBUG=False
ALLOWED_HOSTS=.railway.app
SITE_URL=https://your-app.railway.app
CSRF_TRUSTED_ORIGINS=https://your-app.railway.app
CORS_ALLOWED_ORIGINS=https://your-app.railway.app
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=ekolekcenro@gmail.com
EMAIL_HOST_PASSWORD=aeslhefyknzkuhet
DEFAULT_FROM_EMAIL=ekolekcenro@gmail.com
SMS_ENABLED=True
SMS_API_URL=https://www.iprogsms.com/api/v1/sms_messages
SMS_API_TOKEN=561bedeeb04ee035c27dfc92edf670f9bb5a0e51
SMS_API_TIMEOUT=10
SMS_PROVIDER=2
OTP_EXPIRY_MINUTES=5
OTP_MAX_ATTEMPTS=3
OTP_RESEND_COOLDOWN_SECONDS=60
JWT_ACCESS_TOKEN_LIFETIME_HOURS=1
JWT_REFRESH_TOKEN_LIFETIME_DAYS=30
USE_GOOGLE_DRIVE=False
```

Click **"Save"** → Railway will auto-redeploy

---

### ✅ Step 5: Update Domain URLs (IMPORTANT!)

After deployment finishes:

1. Copy your Railway URL (e.g., `e-kolek-production-abc123.up.railway.app`)
2. Go back to **Variables** tab
3. Update these 4 variables with YOUR actual URL:
   ```
   ALLOWED_HOSTS=e-kolek-production-abc123.up.railway.app,.railway.app
   SITE_URL=https://e-kolek-production-abc123.up.railway.app
   CSRF_TRUSTED_ORIGINS=https://e-kolek-production-abc123.up.railway.app
   CORS_ALLOWED_ORIGINS=https://e-kolek-production-abc123.up.railway.app
   ```
4. Click **"Save"** → Railway redeploys again

---

### ✅ Step 6: Monitor Deployment Logs

Click **"Deployments"** → Latest deployment → **"View Logs"**

Look for:
```
✅ Collecting static files...
✅ Running migrations...
✅ Starting gunicorn...
```

---

### ✅ Step 7: Create Superuser

Once deployed successfully:

1. Click your **web service**
2. Click **"..."** (three dots) → **"Open Shell"**
3. Run: `python manage.py createsuperuser`
4. Or run: `python create_superadmin.py`

Follow prompts to create admin account.

---

### ✅ Step 8: Test Your Deployment

Visit these URLs (replace with your Railway URL):

1. **Homepage:** `https://your-app.railway.app/`
2. **Admin Login:** `https://your-app.railway.app/cenro/admin/login/`
3. **User Login:** `https://your-app.railway.app/login/`
4. **API:** `https://your-app.railway.app/api/`

---

## 🎉 SUCCESS CHECKLIST

- [ ] Railway project created
- [ ] PostgreSQL database added
- [ ] Redis database added
- [ ] Environment variables configured
- [ ] Domain URLs updated
- [ ] Deployment successful (no errors)
- [ ] Migrations completed
- [ ] Static files collected
- [ ] Superuser created
- [ ] Homepage loads with CSS
- [ ] Admin panel accessible
- [ ] Can login and register users

---

## 🔧 QUICK TROUBLESHOOTING

**Issue:** Build fails
- Check **Logs** for Python errors
- Verify all environment variables are set

**Issue:** Static files missing (no CSS)
- Logs should show "Collecting static files" succeeded
- WhiteNoise is already configured

**Issue:** Database error
- Verify PostgreSQL service is running
- DATABASE_URL should be auto-set

**Issue:** 403 CSRF errors
- Update ALLOWED_HOSTS with your Railway domain
- Update CSRF_TRUSTED_ORIGINS with https:// prefix

---

## 📱 OPTIONAL: Deploy Celery Workers

For email/SMS background tasks (after main app works):

**Celery Worker:**
1. **"+ New"** → **"Empty Service"**
2. Connect to mdtevs/E-KOLEK
3. **Custom Start Command:** `celery -A eko worker --loglevel=info --concurrency=2`
4. **Add Shared Variables** from main service

**Celery Beat:**
1. **"+ New"** → **"Empty Service"**
2. Connect to mdtevs/E-KOLEK
3. **Custom Start Command:** `celery -A eko beat --loglevel=info`
4. **Add Shared Variables**

---

## 💡 IMPORTANT NOTES

✅ **Do NOT add DATABASE_URL or REDIS_URL manually** - Railway provides these automatically

✅ **Python 3.12.0** is specified in runtime.txt

✅ **All migrations** run automatically on deploy

✅ **Static files** collected automatically via railway.json

✅ **Security** enabled (DEBUG=False, HTTPS, CSRF, CSP, etc.)

---

## 🎯 YOUR PRODUCTION SECRET KEY

```
6#h=&kzhrkystderfv557##4u0b@y&)w$0j574q92c(2q%t)8+
```

**Keep this safe!** Already included in the environment variables above.

---

## 📞 NEED HELP?

Check full guide: `RAILWAY_DEPLOY_NOW.md`

**Railway Docs:** https://docs.railway.app
**Django Deployment:** https://docs.djangoproject.com/en/5.2/howto/deployment/

---

**Estimated time:** 10-15 minutes
**You're ready to deploy!** 🚀
