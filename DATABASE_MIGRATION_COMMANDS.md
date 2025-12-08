# Quick Command Reference - Database Migration to ekolek_cenro

## Option 1: Automated Script (Recommended)

```powershell
# Set PostgreSQL password
$env:PGPASSWORD = "renz123"

# Run migration script
.\migrate_to_ekolek_cenro.ps1

# Test the application
python manage.py runserver
```

---

## Option 2: Manual Commands

### Step 1: Create New Database
```powershell
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE ekolek_cenro;
GRANT ALL PRIVILEGES ON DATABASE ekolek_cenro TO postgres;
\q
```

### Step 2: Backup Old Database (Optional)
```powershell
# Backup cenro_db
pg_dump -U postgres cenro_db > backup_cenro_db.sql
```

### Step 3: Restore to New Database (If migrating data)
```powershell
# Restore to ekolek_cenro
psql -U postgres ekolek_cenro < backup_cenro_db.sql
```

### Step 4: Update .env File
```powershell
# Edit .env file and change:
# DB_NAME=cenro_db
# to:
DB_NAME=ekolek_cenro
```

### Step 5: Run Django Migrations
```powershell
# Run migrations
python manage.py migrate

# Create superuser (if fresh database)
python manage.py createsuperuser
```

### Step 6: Test Application
```powershell
python manage.py runserver
```

---

## Verification Commands

### Check Database Exists
```powershell
psql -U postgres -c "\l" | Select-String "ekolek_cenro"
```

### Check Tables Created
```powershell
psql -U postgres -d ekolek_cenro -c "\dt"
```

### Check Django Migrations
```powershell
python manage.py showmigrations
```

### Test Database Connection
```powershell
python manage.py check --database default
```

---

## Rollback (If Needed)

### Revert to Old Database
```powershell
# Edit .env file
# Change: DB_NAME=ekolek_cenro
# Back to: DB_NAME=cenro_db

# Test
python manage.py runserver
```

### Delete New Database (If needed)
```powershell
psql -U postgres -c "DROP DATABASE ekolek_cenro;"
```

---

## Common Issues

### Issue: "peer authentication failed"
**Solution**: Check `pg_hba.conf` and ensure password authentication is enabled

### Issue: "database does not exist"
**Solution**: Run CREATE DATABASE command again

### Issue: "permission denied"
**Solution**: Grant proper privileges:
```sql
GRANT ALL PRIVILEGES ON DATABASE ekolek_cenro TO postgres;
```

### Issue: Migration conflicts
**Solution**: 
```powershell
# Reset migrations (careful - deletes data!)
python manage.py migrate --fake-initial
```

---

## Production Database Setup (Railway)

Railway automatically creates PostgreSQL database. You don't need to run these commands.

Just configure environment variable:
```
DATABASE_URL=<provided by Railway>
```

And Railway will run migrations automatically if you have it in `railway.json`.

---

## Quick Checklist

- [ ] Database created: `ekolek_cenro`
- [ ] .env updated: `DB_NAME=ekolek_cenro`
- [ ] Migrations run: `python manage.py migrate`
- [ ] Superuser created (if needed)
- [ ] Application tested: `python manage.py runserver`
- [ ] Data accessible in admin panel
- [ ] All features working

---

**That's it! Your database is ready for local testing or Railway deployment.**
