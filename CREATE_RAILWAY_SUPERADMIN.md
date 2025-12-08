# Create Superadmin on Railway Production

## Option 1: Railway CLI (RECOMMENDED - Most Flexible)

### Step 1: Install Railway CLI
```powershell
npm i -g @railway/cli
```

### Step 2: Login to Railway
```powershell
railway login
```
This opens your browser to authenticate.

### Step 3: Link Your Project
```powershell
cd "C:\Users\Lorenz\Documents\kolek - With OTP\kolek"
railway link
```
Select your **E-KOLEK** project from the list.

### Step 4: Create Superadmin
Choose ONE of these methods:

**Method A: Use the Custom Script (Interactive)**
```powershell
railway run python create_superadmin.py
```
This runs your interactive script that creates a CENRO AdminUser with all permissions.

**Method B: Use Django's Built-in Command (Simple)**
```powershell
railway run python manage.py createsuperuser
```
This creates a regular Django superuser (accounts.Users model).

**Method C: Open a Shell (Most Control)**
```powershell
railway run python manage.py shell
```
Then paste this code:
```python
from cenro.models import AdminUser
from accounts.models import Barangay
from django.contrib.auth.hashers import make_password

# Create superadmin
admin = AdminUser.objects.create(
    username='superadmin',
    email='admin@ekolek.com',
    password=make_password('YourSecurePassword123!'),
    full_name='Super Administrator',
    role='super_admin',
    is_active=True,
    # All permissions enabled
    can_manage_users=True,
    can_manage_points=True,
    can_manage_rewards=True,
    can_manage_schedules=True,
    can_manage_learning=True,
    can_manage_games=True,
    can_manage_security=True,
    can_manage_controls=True,
)

# Assign all barangays
all_barangays = Barangay.objects.all()
admin.barangays.set(all_barangays)

print(f"✅ Superadmin created: {admin.username}")
print(f"   Email: {admin.email}")
print(f"   Barangays: {admin.barangays.count()}")
```

---

## Option 2: Railway Dashboard SQL Query

1. Go to Railway Dashboard: https://railway.app
2. Click your **E-KOLEK** project
3. Click **PostgreSQL** database
4. Click **Query** tab
5. Run this SQL:

```sql
-- First, check if barangays exist
SELECT * FROM accounts_barangay LIMIT 5;

-- Create superadmin (replace values with your data)
INSERT INTO cenro_adminuser (
    id, username, email, password, full_name, role,
    is_active, can_manage_users, can_manage_points,
    can_manage_rewards, can_manage_schedules,
    can_manage_learning, can_manage_games,
    can_manage_security, can_manage_controls,
    created_at, updated_at
)
VALUES (
    gen_random_uuid(),
    'superadmin',
    'admin@ekolek.com',
    'pbkdf2_sha256$870000$yourhashhere',  -- You need to generate this hash
    'Super Administrator',
    'super_admin',
    true, true, true, true, true, true, true, true, true,
    NOW(), NOW()
);

-- Get the admin ID
SELECT id FROM cenro_adminuser WHERE username = 'superadmin';

-- Assign all barangays (replace UUID with admin ID from above)
INSERT INTO cenro_adminuser_barangays (adminuser_id, barangay_id)
SELECT 'YOUR-ADMIN-UUID-HERE', id FROM accounts_barangay;
```

**Problem with this method:** You need to generate the password hash separately.

---

## Option 3: Create Admin Through Database Migration

Create a data migration that runs on Railway:

```powershell
# In your local terminal (after fixing dependencies)
python manage.py makemigrations cenro --empty --name create_superadmin
```

Then edit the migration file to create the admin. **This is complex and not recommended.**

---

## 🎯 **QUICKEST SOLUTION - USE OPTION 1, METHOD A:**

```powershell
npm i -g @railway/cli
railway login
cd "C:\Users\Lorenz\Documents\kolek - With OTP\kolek"
railway link
railway run python create_superadmin.py
```

Then login at: https://e-kolek-production.up.railway.app/cenro/admin/login/

---

## Troubleshooting

### If Railway CLI doesn't work:
- Make sure Node.js is installed: `node --version`
- Update npm: `npm install -g npm@latest`
- Try using `npx @railway/cli run python create_superadmin.py` instead

### If you need the password hash manually:
```python
from django.contrib.auth.hashers import make_password
print(make_password('YourPassword123!'))
```

### Check if migrations ran:
```powershell
railway run python manage.py showmigrations
```

### Check if database has data:
```powershell
railway run python manage.py shell
```
Then:
```python
from accounts.models import Barangay
print(f"Barangays: {Barangay.objects.count()}")
from cenro.models import AdminUser
print(f"Admins: {AdminUser.objects.count()}")
```
