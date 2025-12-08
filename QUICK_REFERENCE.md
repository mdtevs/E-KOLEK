# Quick Reference - Production Deployment

## 🚀 Quick Start Commands

### Development Mode
```bash
# Activate virtual environment
env\Scripts\activate

# Run development server
python manage.py runserver
```

### Production Mode - Quick Test (Staging)

1. **Update .env file**:
```env
DJANGO_DEBUG=False
ALLOWED_HOSTS=your-staging-domain.com
CSRF_TRUSTED_ORIGINS=https://your-staging-domain.com
```

2. **Run production checks**:
```bash
python manage.py check --deploy
python manage.py collectstatic --noinput
```

3. **Start with Gunicorn**:
```bash
pip install gunicorn
gunicorn eko.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

---

## 🔐 Critical Environment Variables for Production

**Must Change Before Deployment**:
```env
DJANGO_SECRET_KEY=<generate-new-key>
DJANGO_DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SITE_URL=https://yourdomain.com
DB_PASSWORD=<strong-password>
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
```

**Generate New Secret Key**:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## ✅ Pre-Flight Checklist (Must Do Before Production)

- [ ] Generate NEW SECRET_KEY
- [ ] Set DEBUG=False
- [ ] Update ALLOWED_HOSTS
- [ ] Configure HTTPS/SSL
- [ ] Set CSRF_TRUSTED_ORIGINS
- [ ] Use strong DB password
- [ ] Test all functionality in staging
- [ ] Set up database backups
- [ ] Configure monitoring

---

## 📁 Important Files

| File | Purpose | Committed? |
|------|---------|-----------|
| `eko/settings.py` | Main configuration | ✅ Yes |
| `.env` | Secrets & environment vars | ❌ **NEVER** |
| `.env.example` | Template for .env | ✅ Yes |
| `.gitignore` | Ignore sensitive files | ✅ Yes |
| `google-drive-*.json` | Google Drive credentials | ❌ **NEVER** |
| `logs/` | Application logs | ❌ No |

---

## 🔧 Common Tasks

### Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### Run Migrations
```bash
python manage.py migrate
```

### Create Superadmin
```bash
python create_superadmin.py
```

### Start Celery Worker
```bash
celery -A eko worker --loglevel=info
```

### Start Celery Beat (Scheduled Tasks)
```bash
celery -A eko beat --loglevel=info
```

---

## 🐛 Troubleshooting

### "ALLOWED_HOSTS" Error
**Problem**: `DisallowedHost at /`  
**Solution**: Add your domain to `ALLOWED_HOSTS` in `.env`

### CSRF Verification Failed
**Problem**: `403 Forbidden - CSRF verification failed`  
**Solution**: Add your domain with `https://` to `CSRF_TRUSTED_ORIGINS` in `.env`

### Static Files Not Loading
**Problem**: CSS/JS not loading in production  
**Solution**: 
1. Run `python manage.py collectstatic`
2. Configure web server to serve `/static/` from `staticfiles/` directory

### Database Connection Error
**Problem**: `could not connect to server`  
**Solution**: Check `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` in `.env`

---

## 📊 Monitoring Commands

### Check System Status
```bash
python manage.py check --deploy
```

### View Recent Logs
```bash
# Windows PowerShell
Get-Content logs\django.log -Tail 50
Get-Content logs\security.log -Tail 50

# Linux/Mac
tail -f logs/django.log
tail -f logs/security.log
```

### Check Database Migrations
```bash
python manage.py showmigrations
```

### Check Celery Status
```bash
celery -A eko inspect active
celery -A eko inspect stats
```

---

## 🔒 Security Checklist

- [x] All secrets in `.env` file
- [x] `.env` in `.gitignore`
- [x] DEBUG=False in production
- [x] HTTPS enabled
- [x] HSTS enabled
- [x] CSRF protection enabled
- [x] XSS protection enabled
- [x] CSP configured
- [x] Secure cookies enabled
- [x] SQL injection protection (middleware)
- [x] Brute force protection (middleware)

---

## 📖 Full Documentation

- **Complete Deployment Guide**: `PRODUCTION_DEPLOYMENT_CHECKLIST.md`
- **Changes Summary**: `PRODUCTION_PREPARATION_SUMMARY.md`
- **Setup Instructions**: `docs/SETUP_INSTRUCTIONS_UPDATED.md`
- **System Architecture**: `docs/SYSTEM_ARCHITECTURE_OVERVIEW.md`

---

## 🆘 Emergency Rollback

If deployment fails:

1. **Stop the application**
```bash
# Stop Gunicorn/uWSGI service
sudo systemctl stop gunicorn
```

2. **Restore database backup**
```bash
psql -U postgres -d cenro_db < backup_file.sql
```

3. **Revert code to previous version**
```bash
git checkout <previous-commit-hash>
```

4. **Restart with old version**
```bash
sudo systemctl start gunicorn
```

5. **Verify application is working**

---

**Status**: ✅ Production Ready

**Last Updated**: 2024

**Django Version**: 5.2.6
