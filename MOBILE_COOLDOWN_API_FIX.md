# 🔧 Mobile App Cooldown API Fix

## Issue Description
Mobile app game cooldown feature stopped working after admin interface fixes were deployed.

## Root Cause
When fixing the admin cooldown interface, `DEFAULT_PERMISSION_CLASSES` in DRF settings was commented out to bypass DRF authentication for admin endpoints. This inadvertently broke mobile API authentication which requires JWT tokens.

## Architecture Overview

### Admin Interface (Session-based)
- **Path:** `/game/*` and `/cenro/*`
- **Authentication:** Custom admin session (admin_user_id)
- **Middleware:** AdminAccessControlMiddleware validates session
- **URL Structure:** Moved OUT of `/api/` to avoid DRF interception

### Mobile API (JWT-based)
- **Path:** `/api/*` (uses DRF)
- **Authentication:** JWT tokens via `rest_framework_simplejwt`
- **Decorators:** `@api_view`, `@authentication_classes([JWTAuthentication])`, `@permission_classes([IsAuthenticated])`
- **URL Structure:** Stays in `/api/` namespace

## The Fix Applied

### Changed: `eko/settings.py` (Lines 364-376)

**BEFORE:**
```python
'DEFAULT_PERMISSION_CLASSES': [
    # CHANGED: Allow unauthenticated by default
    # 'rest_framework.permissions.IsAuthenticated',  # DISABLED
],
```

**AFTER:**
```python
'DEFAULT_PERMISSION_CLASSES': [
    # Mobile API endpoints under /api/ require JWT authentication
    # Admin endpoints under /game/ and /cenro/ use custom session auth (bypass DRF)
    'rest_framework.permissions.IsAuthenticated',
],
```

## Mobile Cooldown API Endpoints

### 1. Get All Configurations
```
GET /api/game/configurations/
Headers: Authorization: Bearer <JWT_TOKEN>
```

**Response:**
```json
{
  "success": true,
  "configurations": {
    "quiz": {
      "cooldown_hours": 72,
      "cooldown_minutes": 0,
      "total_milliseconds": 259200000,
      "total_seconds": 259200,
      "formatted_duration": "72 hours",
      "is_active": true
    },
    "drag_drop": {
      "cooldown_hours": 72,
      "cooldown_minutes": 0,
      "total_milliseconds": 259200000,
      "total_seconds": 259200,
      "formatted_duration": "72 hours",
      "is_active": true
    },
    "default": {
      "cooldown_hours": 72,
      "cooldown_minutes": 0,
      "total_milliseconds": 259200000,
      "total_seconds": 259200,
      "formatted_duration": "72 hours",
      "is_active": true
    }
  }
}
```

### 2. Get Specific Game Cooldown
```
GET /api/game/cooldown/<game_type>/
Headers: Authorization: Bearer <JWT_TOKEN>

game_type: 'quiz' | 'drag_drop' | 'all'
```

**Response:**
```json
{
  "success": true,
  "game_type": "quiz",
  "cooldown_hours": 72,
  "cooldown_minutes": 0,
  "total_milliseconds": 259200000,
  "total_seconds": 259200,
  "formatted_duration": "72 hours",
  "is_active": true
}
```

### 3. Quiz Cooldown Convenience Endpoint
```
GET /api/game/cooldown/quiz/
Headers: Authorization: Bearer <JWT_TOKEN>
```

### 4. Drag & Drop Cooldown Convenience Endpoint
```
GET /api/game/cooldown/dragdrop/
Headers: Authorization: Bearer <JWT_TOKEN>
```

## Testing Checklist

### ✅ Before Deployment (LOCAL)
- [ ] Verify admin cooldown update still works at `/game/cooldown/update/`
- [ ] Confirm admin interface doesn't get 401 errors
- [ ] Test preset buttons (1 day, 3 days, 7 days, etc.)
- [ ] Test custom days input
- [ ] Verify changes save to database

### ✅ After Deployment (RAILWAY)

#### Admin Interface Tests:
1. **Login to Admin:** `https://your-app.railway.app/cenro/admin/login/`
2. **Navigate to Games:** Click "Games" tab → "Cooldown Settings"
3. **Test Quiz Cooldown:**
   - Click "3 Days" preset → Click "Update Cooldown"
   - Verify success message appears
4. **Test Drag & Drop Cooldown:**
   - Enter "5" in "Custom Days" → Click "Set Custom" → "Update Cooldown"
5. **Test All Games Default:**
   - Click "7 Days" preset → "Update Cooldown"

#### Mobile API Tests (Use Postman/Thunder Client):

**Step 1: Get JWT Token**
```bash
POST https://your-app.railway.app/api/login/
Content-Type: application/json

{
  "username_or_email": "test_user",
  "password": "test_password"
}

# Then verify OTP:
POST https://your-app.railway.app/api/login/verify-otp/
Content-Type: application/json

{
  "phone_number": "+639123456789",
  "otp_code": "123456"
}

# Response will include:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Step 2: Test Cooldown APIs**
```bash
# Test 1: Get all configurations
GET https://your-app.railway.app/api/game/configurations/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...

Expected: 200 OK with configurations object

# Test 2: Get quiz cooldown
GET https://your-app.railway.app/api/game/cooldown/quiz/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...

Expected: 200 OK with quiz cooldown data

# Test 3: Get drag_drop cooldown
GET https://your-app.railway.app/api/game/cooldown/drag_drop/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...

Expected: 200 OK with drag_drop cooldown data

# Test 4: Test without JWT token (should fail)
GET https://your-app.railway.app/api/game/configurations/

Expected: 401 Unauthorized
{
  "detail": "Authentication credentials were not provided."
}
```

## Database Verification

### Check GameConfiguration Records

**Via Railway CLI:**
```bash
railway run python manage.py shell

# Then in shell:
from game.models import GameConfiguration

# List all configurations
for config in GameConfiguration.objects.all():
    print(f"{config.game_type}: {config.cooldown_hours}h {config.cooldown_minutes}m - Active: {config.is_active}")

# Check specific game
quiz_config = GameConfiguration.get_cooldown_for_game('quiz')
print(f"Quiz cooldown: {quiz_config.total_cooldown_milliseconds}ms")
```

**Via Railway PostgreSQL:**
```sql
-- Connect to Railway PostgreSQL
SELECT game_type, cooldown_hours, cooldown_minutes, is_active, updated_at
FROM game_gameconfiguration
ORDER BY game_type;
```

### Expected Records:
```
game_type    | cooldown_hours | cooldown_minutes | is_active
-------------|----------------|------------------|----------
all          | 72             | 0                | true
drag_drop    | 72             | 0                | true
quiz         | 72             | 0                | true
```

## Troubleshooting

### Issue: Mobile API returns 401 Unauthorized

**Possible Causes:**
1. JWT token expired → Get new token via `/api/login/` + OTP verification
2. JWT token malformed → Check Authorization header format: `Bearer <token>`
3. User not authenticated → Verify user exists and login was successful

**Solution:**
```bash
# Get fresh token
POST /api/login/ → POST /api/login/verify-otp/
# Use access token in Authorization header
```

### Issue: Mobile API returns 500 Internal Server Error

**Possible Causes:**
1. GameConfiguration records don't exist in database
2. Database connection issue

**Solution:**
```bash
# Create default configurations via Railway shell
railway run python manage.py shell

from game.models import GameConfiguration

# Create default configurations if they don't exist
for game_type in ['quiz', 'drag_drop', 'all']:
    config, created = GameConfiguration.objects.get_or_create(
        game_type=game_type,
        defaults={
            'cooldown_hours': 72,
            'cooldown_minutes': 0,
            'is_active': True,
            'updated_by': 'system'
        }
    )
    print(f"{'Created' if created else 'Exists'}: {game_type}")
```

### Issue: Admin interface returns 401 after deployment

**This should NOT happen** - admin endpoints are outside `/api/` path.

**If it does happen:**
1. Check you're logged in to admin at `/cenro/admin/login/`
2. Verify session cookie `ekolek_session` is present
3. Check Railway logs for middleware errors

**Emergency Fix:**
```python
# In eko/security_middleware.py
# Verify API_ADMIN_PATHS excludes /api/ paths:
API_ADMIN_PATHS = ['/game/']  # NOT /api/game/
```

### Issue: Cooldown values not updating in mobile app

**Possible Causes:**
1. Mobile app caching old values
2. Database not updating

**Solution:**
1. **Check Railway Database:**
   ```sql
   SELECT * FROM game_gameconfiguration 
   WHERE game_type = 'quiz' 
   ORDER BY updated_at DESC LIMIT 1;
   ```
2. **Clear mobile app cache** and re-fetch
3. **Force refresh** by restarting the app
4. **Verify API response** matches database values

## Files Modified

### 1. `eko/settings.py`
- **Line 369-371:** Re-enabled `DEFAULT_PERMISSION_CLASSES` for mobile JWT auth
- **Comment:** Documented that admin uses `/game/` (bypasses DRF) while mobile uses `/api/` (requires JWT)

## Architecture Decision Record

### Why Two Authentication Systems?

**Admin Interface:**
- Uses Django's session-based authentication
- Custom middleware validates `admin_user_id` in session
- URLs moved to `/game/*` to avoid DRF interception
- Reason: Admin interface needs CSRF protection and session management

**Mobile API:**
- Uses JWT token authentication via DRF
- Stateless authentication for mobile apps
- URLs stay in `/api/*` to leverage DRF features
- Reason: Mobile apps need token-based auth without cookies/sessions

### Why DRF Authentication Works Now

1. **URL Separation:**
   - Admin: `/game/*`, `/cenro/*` → Never processed by DRF
   - Mobile: `/api/*` → Processed by DRF with JWT auth

2. **Middleware Order:**
   - `AdminAccessControlMiddleware` checks `/game/` paths BEFORE DRF
   - For `/api/` paths, custom middleware doesn't interfere
   - DRF handles `/api/` authentication natively

3. **Settings Configuration:**
   - `DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]` → Applies to `/api/*` only
   - Admin endpoints never reach DRF, so not affected

## Deployment Instructions

```bash
# 1. Commit the fix
git add eko/settings.py MOBILE_COOLDOWN_API_FIX.md
git commit -m "FIX: Restore DRF authentication for mobile cooldown API

ISSUE: Mobile app cooldown feature stopped working
ROOT CAUSE: DEFAULT_PERMISSION_CLASSES was disabled during admin fixes

SOLUTION: 
- Re-enabled DRF IsAuthenticated for mobile API (/api/*)
- Admin endpoints (/game/*) remain outside DRF scope
- Both authentication systems now work independently

TESTING REQUIRED:
- Mobile API authentication with JWT tokens
- Admin cooldown update functionality
- All preset buttons and custom days input

Files Modified:
- eko/settings.py - Re-enabled DEFAULT_PERMISSION_CLASSES
- MOBILE_COOLDOWN_API_FIX.md - Complete documentation"

# 2. Push to Railway
git push origin master

# 3. Wait for Railway deployment (check logs)
# 4. Test admin interface first
# 5. Test mobile API with Postman
# 6. Verify with Flutter app
```

## Success Criteria

✅ **Admin Interface:**
- Can update cooldowns without 401 errors
- Preset buttons work correctly
- Custom days input works
- Changes persist to database

✅ **Mobile API:**
- Returns 200 OK with valid JWT token
- Returns 401 without token or with expired token
- Cooldown values match admin settings
- Response format compatible with Flutter Duration

✅ **Database:**
- GameConfiguration records exist for all game types
- Values update correctly via admin interface
- Mobile API reads correct values

## Contact & Support

If issues persist after deployment:
1. Check Railway deployment logs
2. Verify database migrations applied
3. Test API endpoints with Postman
4. Review middleware logs for authentication issues

---

**Fix Applied:** December 22, 2025
**Status:** ✅ Ready for Testing
**Priority:** HIGH - Mobile feature broken
