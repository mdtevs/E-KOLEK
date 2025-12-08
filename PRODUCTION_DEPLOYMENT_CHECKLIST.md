# Production Deployment Checklist - E-KOLEK

This comprehensive checklist ensures your E-KOLEK application is properly configured for production deployment.

## ✅ Pre-Deployment Verification

### 1. Environment Configuration (.env file)

- [ ] **Generate NEW SECRET_KEY** - Never reuse development secret key in production
  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
  
- [ ] **Set DEBUG mode to False**
  ```
  DJANGO_DEBUG=False
  ```

- [ ] **Configure ALLOWED_HOSTS** - Remove localhost and development IPs
  ```
  ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com
  ```

- [ ] **Update SITE_URL** - Use production domain with HTTPS
  ```
  SITE_URL=https://yourdomain.com
  ```

- [ ] **Configure CSRF_TRUSTED_ORIGINS** - Required when DEBUG=False
  ```
  CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
  ```

- [ ] **Configure CORS_ALLOWED_ORIGINS** - Only if using mobile app
  ```
  CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
  ```

### 2. Database Security

- [ ] **Use strong database password** - Replace weak password like "renz123"
- [ ] **Ensure database is NOT publicly accessible**
- [ ] **Configure database connection limits** (already set to CONN_MAX_AGE=600)
- [ ] **Set up automated database backups**
- [ ] **Test database connection from production server**

### 3. Email Configuration

- [ ] **Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD** - Use production email
- [ ] **Test email sending** (password reset, OTP, notifications)
- [ ] **Configure SPF and DKIM records** for your domain (reduces spam)
- [ ] **Monitor email delivery rates**

### 4. SMS & OTP Configuration

- [ ] **Verify SMS_API_TOKEN is valid** for production environment
- [ ] **Test OTP delivery** to real phone numbers
- [ ] **Verify SMS provider account has sufficient credits**
- [ ] **Monitor OTP delivery success rates**

### 5. Google Drive Storage (if using)

- [ ] **Update Google Drive file paths** to production server absolute paths
- [ ] **Verify google-drive-oauth-credentials.json is present** on production server
- [ ] **Ensure google-drive-token.pickle file permissions** are secure (600)
- [ ] **Test file upload/download** functionality
- [ ] **Configure backup for Google Drive credentials**

### 6. Security Settings

- [ ] **Enable HTTPS** - Install valid SSL certificate
  - Configure web server (Nginx/Apache) to force HTTPS
  - Test with SSL Labs (https://www.ssllabs.com/ssltest/)
  
- [ ] **Verify HSTS is enabled** (automatically enabled when DEBUG=False)
  - SECURE_HSTS_SECONDS = 31536000 (1 year)
  - SECURE_HSTS_INCLUDE_SUBDOMAINS = True
  - SECURE_HSTS_PRELOAD = True

- [ ] **Verify CSP (Content Security Policy)** settings
  - Test that external CDNs are whitelisted
  - Verify no inline scripts break functionality

- [ ] **Test CSRF protection** on all forms
- [ ] **Verify X-Frame-Options is set** (already set to DENY)
- [ ] **Check security headers** using securityheaders.com

### 7. Static & Media Files

- [ ] **Run collectstatic command**
  ```bash
  python manage.py collectstatic --noinput
  ```

- [ ] **Configure web server** to serve static files directly (Nginx/Apache)
- [ ] **Verify STATIC_ROOT and MEDIA_ROOT** permissions
- [ ] **Test static file access** (CSS, JS, images)
- [ ] **Set up CDN** for static files (optional, for better performance)

### 8. Celery & Redis Configuration

- [ ] **Verify Redis server is running** on production
  ```bash
  redis-cli ping
  ```

- [ ] **Configure Redis password** (recommended for production)
- [ ] **Start Celery worker** as a system service
  ```bash
  celery -A eko worker --loglevel=info
  ```

- [ ] **Start Celery beat** (for scheduled tasks)
  ```bash
  celery -A eko beat --loglevel=info
  ```

- [ ] **Monitor Celery task queue** for failures
- [ ] **Set up Celery monitoring** (Flower recommended)

### 9. Logging & Monitoring

- [ ] **Verify logs directory exists** (automatically created by settings.py)
- [ ] **Configure log rotation** (logrotate on Linux)
- [ ] **Set up monitoring alerts** (disk space, memory, CPU)
- [ ] **Monitor error logs** regularly
  - `logs/django.log` - General application logs
  - `logs/security.log` - Security-related events

- [ ] **Configure external logging service** (optional: Sentry, LogDNA)

### 10. Database Migrations

- [ ] **Run migrations on production database**
  ```bash
  python manage.py migrate
  ```

- [ ] **Verify all migrations applied successfully**
  ```bash
  python manage.py showmigrations
  ```

- [ ] **Create database backup BEFORE running migrations**

### 11. Superadmin Account

- [ ] **Create production superadmin account**
  ```bash
  python create_superadmin.py
  ```

- [ ] **Use STRONG password** for superadmin
- [ ] **Document superadmin credentials** in secure location (password manager)
- [ ] **Enable 2FA** for admin accounts (if implemented)

### 12. Testing in Staging Environment

- [ ] **Deploy to staging environment first** (identical to production)
- [ ] **Test all user flows**:
  - Registration with OTP
  - Login (web and mobile)
  - Password reset
  - Profile updates
  - File uploads
  - Points/rewards system
  - Learning module
  - Game module
  - EkoScan functionality
  - Admin dashboard

- [ ] **Test mobile app** against staging API
- [ ] **Load testing** (simulate concurrent users)
- [ ] **Security testing** (penetration testing)

### 13. Performance Optimization

- [ ] **Enable database query optimization** (already configured)
- [ ] **Configure caching** (Redis recommended)
  ```
  CACHE_BACKEND=django_redis.cache.RedisCache
  CACHE_LOCATION=redis://localhost:6379/1
  ```

- [ ] **Enable gzip compression** in web server
- [ ] **Minify CSS and JavaScript** files
- [ ] **Optimize images** in media folder
- [ ] **Configure CDN** for static assets (optional)

### 14. Backup Strategy

- [ ] **Set up automated database backups** (daily recommended)
- [ ] **Test database restore procedure**
- [ ] **Backup environment variables** (.env file) - store securely
- [ ] **Backup Google Drive credentials**
- [ ] **Backup uploaded media files** (if not using Google Drive)
- [ ] **Document backup locations and procedures**

### 15. Web Server Configuration

- [ ] **Install and configure web server** (Nginx or Apache)
- [ ] **Configure WSGI server** (Gunicorn or uWSGI)
  ```bash
  pip install gunicorn
  gunicorn eko.wsgi:application --bind 0.0.0.0:8000 --workers 4
  ```

- [ ] **Set up systemd service** for Django application
- [ ] **Configure web server to serve static files**
- [ ] **Set up reverse proxy** for Django application
- [ ] **Configure SSL certificates** (Let's Encrypt recommended)

### 16. Firewall Configuration

- [ ] **Open required ports**:
  - 80 (HTTP - redirect to HTTPS)
  - 443 (HTTPS)
  - 5432 (PostgreSQL - only from localhost, NOT public)
  - 6379 (Redis - only from localhost, NOT public)

- [ ] **Close unnecessary ports**
- [ ] **Configure fail2ban** to prevent brute-force attacks
- [ ] **Enable UFW firewall** (Ubuntu) or equivalent

### 17. Final Verification

- [ ] **Test complete user registration flow**
- [ ] **Test OTP delivery and verification**
- [ ] **Test mobile app login**
- [ ] **Test file uploads**
- [ ] **Test all admin functions**
- [ ] **Verify email notifications work**
- [ ] **Verify SMS notifications work**
- [ ] **Check all external integrations**
- [ ] **Monitor logs for errors** (30 minutes after deployment)
- [ ] **Test from different devices and networks**

### 18. Documentation

- [ ] **Document deployment procedure**
- [ ] **Document rollback procedure**
- [ ] **Document environment variables** (in password manager)
- [ ] **Update API documentation** with production URLs
- [ ] **Create incident response plan**

### 19. Post-Deployment Monitoring

- [ ] **Monitor server resources** (CPU, RAM, disk usage)
- [ ] **Monitor application logs** for errors
- [ ] **Monitor database performance**
- [ ] **Monitor API response times**
- [ ] **Set up uptime monitoring** (UptimeRobot, Pingdom)
- [ ] **Set up error tracking** (Sentry)

### 20. Important Files Checklist

Ensure these files are properly configured and secured:

#### Files that MUST be present on production server:
- [x] `eko/settings.py` - Main settings file
- [x] `.env` - Environment variables (properly secured)
- [ ] `google-drive-oauth-credentials.json` - Google Drive credentials
- [ ] `google-drive-token.pickle` - Google Drive auth token
- [ ] `manage.py` - Django management script

#### Files that should NOT be on production server:
- [x] `.env.example` - Template only (keep for reference)
- [x] `settings_backup.py` - Development backup
- [x] All `.bat` files - Windows scripts
- [x] All `.ps1` files - PowerShell scripts
- [x] `docs/*.md` - Documentation files

#### Files that must be in `.gitignore`:
- [x] `.env` - Sensitive environment variables
- [x] `google-drive-*.json` - Google credentials
- [x] `google-drive-token.pickle` - OAuth tokens
- [x] `*.log` - Log files
- [x] `media/` - User uploads
- [x] `staticfiles/` - Collected static files
- [x] `cache/` - Cache files
- [x] `*.rdb` - Redis dumps

---

## 🚨 Critical Security Reminders

1. **NEVER commit `.env` to version control**
2. **NEVER use development SECRET_KEY in production**
3. **NEVER set DEBUG=True in production**
4. **NEVER expose database ports publicly**
5. **NEVER use weak passwords** (database, admin accounts)
6. **ALWAYS use HTTPS in production**
7. **ALWAYS test in staging before production**
8. **ALWAYS have backup and rollback plan**

---

## 📞 Emergency Contacts

Document these BEFORE deployment:

- [ ] Database administrator contact
- [ ] Server/hosting provider support
- [ ] DNS provider support
- [ ] SSL certificate provider support
- [ ] SMS API provider support
- [ ] Email provider support

---

## 🔄 Rollback Plan

If deployment fails:

1. **Stop the application** immediately
2. **Restore database backup** (if migrations were run)
3. **Revert code to previous version**
4. **Restart services** with previous version
5. **Verify application is working** with old version
6. **Investigate and fix issues** before re-deploying

---

**DEPLOYMENT STATUS**: [ ] NOT READY  [ ] READY FOR STAGING  [ ] READY FOR PRODUCTION

**Deployed by**: ________________  **Date**: ________________

**Verified by**: ________________  **Date**: ________________
