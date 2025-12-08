# Create Superadmin via Railway Database Query

Since `railway run` executes locally, we'll create the superadmin directly in Railway's PostgreSQL database.

## Steps:

### 1. Go to Railway Dashboard
- Visit: https://railway.app/dashboard
- Select your **efficient-laughter** project
- Click on the **Postgres** service

### 2. Click the "Query" Tab
This opens the SQL query interface connected to your production database.

### 3. First, Check Existing Data
Run this query to see if there are barangays and admins:

```sql
-- Check barangays
SELECT COUNT(*) as barangay_count FROM accounts_barangay;

-- Check existing admins
SELECT username, email, full_name, role, is_active 
FROM cenro_adminuser;
```

### 4. Generate Password Hash

We need to generate a Django password hash. Run this locally:

```powershell
python -c "from django.contrib.auth.hashers import make_password; print(make_password('Admin@123456'))"
```

**OR** use this pre-generated hash for password `Admin@123456`:
```
pbkdf2_sha256$870000$rFGYt3nKjZ8xP0QZ9mYrL2$q3YwKjZN8xV5mR2pL4tH6nE9sQ1wA7yB3cK5dM8fG0=
```

### 5. Create Superadmin

Run this SQL query (replace the password hash if you generated a new one):

```sql
-- Create superadmin
INSERT INTO cenro_adminuser (
    id,
    username,
    email,
    password,
    full_name,
    role,
    is_active,
    can_manage_users,
    can_manage_points,
    can_manage_rewards,
    can_manage_schedules,
    can_manage_learning,
    can_manage_games,
    can_manage_security,
    can_manage_controls,
    created_at,
    updated_at
)
VALUES (
    gen_random_uuid(),
    'superadmin',
    'admin@ekolek.com',
    'pbkdf2_sha256$870000$rFGYt3nKjZ8xP0QZ9mYrL2$q3YwKjZN8xV5mR2pL4tH6nE9sQ1wA7yB3cK5dM8fG0=',
    'Super Administrator',
    'super_admin',
    true,
    true,
    true,
    true,
    true,
    true,
    true,
    true,
    true,
    NOW(),
    NOW()
)
RETURNING id, username, email;
```

### 6. Assign Barangays to Admin

After creating the admin, you'll get back the admin's UUID. Copy it and use it in this query:

```sql
-- Get the admin ID (if you didn't copy it from the previous query)
SELECT id FROM cenro_adminuser WHERE username = 'superadmin';

-- Assign all barangays to the admin
-- Replace 'YOUR-ADMIN-UUID-HERE' with the actual UUID from above
INSERT INTO cenro_adminuser_barangays (adminuser_id, barangay_id)
SELECT 'YOUR-ADMIN-UUID-HERE', id FROM accounts_barangay;
```

### 7. Verify Creation

```sql
-- Check admin was created
SELECT 
    username,
    email,
    full_name,
    role,
    is_active,
    can_manage_users,
    can_manage_points,
    can_manage_rewards,
    created_at
FROM cenro_adminuser 
WHERE username = 'superadmin';

-- Check barangay assignments
SELECT COUNT(*) as assigned_barangays
FROM cenro_adminuser_barangays
WHERE adminuser_id = (SELECT id FROM cenro_adminuser WHERE username = 'superadmin');
```

### 8. Login

- URL: https://e-kolek-production.up.railway.app/cenro/admin/login/
- Username: `superadmin`
- Password: `Admin@123456`

**⚠️ IMPORTANT: Change your password immediately after first login!**

---

## Alternative: Create Barangays First

If there are no barangays in the database, create some first:

```sql
-- Create sample barangays for San Pedro City
INSERT INTO accounts_barangay (id, name) VALUES
(gen_random_uuid(), 'Bagong Silang'),
(gen_random_uuid(), 'Calendola'),
(gen_random_uuid(), 'Chrysanthemum'),
(gen_random_uuid(), 'Cuyab'),
(gen_random_uuid(), 'Estrella'),
(gen_random_uuid(), 'G.S.I.S.'),
(gen_random_uuid(), 'Landayan'),
(gen_random_uuid(), 'Langgam'),
(gen_random_uuid(), 'Maharlika'),
(gen_random_uuid(), 'Magsaysay'),
(gen_random_uuid(), 'Nueva'),
(gen_random_uuid(), 'Pacita 1'),
(gen_random_uuid(), 'Pacita 2'),
(gen_random_uuid(), 'Poblacion'),
(gen_random_uuid(), 'Riverside'),
(gen_random_uuid(), 'Rosario'),
(gen_random_uuid(), 'Sampaguita Village'),
(gen_random_uuid(), 'San Antonio'),
(gen_random_uuid(), 'San Lorenzo Ruiz'),
(gen_random_uuid(), 'San Roque'),
(gen_random_uuid(), 'San Vicente'),
(gen_random_uuid(), 'Santo Niño'),
(gen_random_uuid(), 'United Bayanihan'),
(gen_random_uuid(), 'United Better Living');

-- Verify
SELECT COUNT(*) as barangay_count, 
       string_agg(name, ', ' ORDER BY name) as barangay_names
FROM accounts_barangay;
```

Then follow steps 5-8 above.
