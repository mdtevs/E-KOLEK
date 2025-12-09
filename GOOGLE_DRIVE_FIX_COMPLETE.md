# GOOGLE DRIVE FIX - COMPLETE SOLUTION

## Problem Summary

**Error:** `Invalid JWT Signature` when uploading files to Google Drive  
**Root Cause:** Service account credentials in `google-drive-credentials.json` are invalid/revoked  
**Impact:** Files fall back to local storage → disappear after Railway restart

## Solution Implemented

**Switched from Service Account to OAuth 2.0 Authentication**

OAuth is more reliable because:
- ✅ No private key formatting issues
- ✅ Tokens refresh automatically
- ✅ Easier to manage and debug
- ✅ Works perfectly (tested locally)

## Changes Made

### 1. Updated Storage Backend (`eko/google_drive_storage.py`)

Added OAuth support with automatic refresh:
```python
# Now tries OAuth FIRST, then falls back to service account
if self.oauth_refresh_token and self.oauth_client_id and self.oauth_client_secret:
    credentials = OAuthCredentials(
        None,
        refresh_token=self.oauth_refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=self.oauth_client_id,
        client_secret=self.oauth_client_secret,
        scopes=['https://www.googleapis.com/auth/drive.file']
    )
    credentials.refresh(Request())  # Auto-refresh access token
```

### 2. Updated Settings (`eko/settings.py`)

Added OAuth configuration variables:
```python
# OAuth credentials (PREFERRED)
GOOGLE_DRIVE_OAUTH_REFRESH_TOKEN = config('GOOGLE_DRIVE_OAUTH_REFRESH_TOKEN', default=None)
GOOGLE_DRIVE_OAUTH_CLIENT_ID = config('GOOGLE_DRIVE_OAUTH_CLIENT_ID', default=None)
GOOGLE_DRIVE_OAUTH_CLIENT_SECRET = config('GOOGLE_DRIVE_OAUTH_CLIENT_SECRET', default=None)

# Service account credentials (fallback)
GOOGLE_DRIVE_CREDENTIALS_JSON = config('GOOGLE_DRIVE_CREDENTIALS_JSON', default=None)
```

### 3. Set Railway Environment Variables

```bash
GOOGLE_DRIVE_OAUTH_REFRESH_TOKEN = "<refresh-token-from-oauth-flow>"
GOOGLE_DRIVE_OAUTH_CLIENT_ID = "<client-id-from-google-cloud-console>"
GOOGLE_DRIVE_OAUTH_CLIENT_SECRET = "<client-secret-from-google-cloud-console>"
```

✅ **Already set in Railway** (see Railway dashboard for actual values)

## Testing Results

### Local OAuth Test (test_oauth_drive.py)
```
✅ OAuth credentials obtained
✅ Drive service built
✅ API call successful! Found 10 files
✅ ALL TESTS PASSED!
```

Files found in folder:
- tagalog.docx
- terms.docx
- centurytuna.jpg
- tagalog_ZoB85GO.docx
- tagalog.docx

### Service Account Test (test_google_drive.py)
```
❌ Error: invalid_grant: Invalid JWT Signature
```
This confirms the service account credentials are revoked/invalid.

## Deployment Status

**Railway Variables Set:** ✅
```
GOOGLE_DRIVE_FOLDER_ID           = 1_uPLF-A7C3R0UR_vtUknkvCrk14FH2nl
GOOGLE_DRIVE_OAUTH_CLIENT_ID     = <set in Railway>
GOOGLE_DRIVE_OAUTH_CLIENT_SECRET = <set in Railway>
GOOGLE_DRIVE_OAUTH_REFRESH_TOKEN = <set in Railway>
USE_GOOGLE_DRIVE                 = True
```

**Code Changes:** ✅
- eko/google_drive_storage.py - Updated
- eko/settings.py - Updated

**Waiting For:** Railway to auto-deploy with new code

## How OAuth Works

1. **Initial Setup** (Done locally):
   - User logs in via browser
   - Grants Drive access
   - Gets refresh token (never expires unless revoked)

2. **In Production** (Automatic):
   - App uses refresh token to get short-lived access token
   - Access token expires after 1 hour
   - App automatically refreshes using refresh token
   - No user interaction needed

## Verification Steps

### After Railway Deploys:

1. **Check logs for OAuth success:**
   ```powershell
   railway logs --tail 100 | Select-String "OAuth|Google Drive"
   ```
   
   Look for:
   ```
   🔐 Using OAuth credentials
   🔄 Refreshing OAuth access token...
   ✅ OAuth credentials refreshed successfully
   ✅ Google Drive service initialized successfully
   ```

2. **Upload a test image:**
   - Go to Admin Rewards page
   - Create or edit a reward
   - Upload an image
   - Check logs for success message
   
3. **Verify file in Google Drive:**
   - Go to: https://drive.google.com/drive/folders/1_uPLF-A7C3R0UR_vtUknkvCrk14FH2nl
   - New file should appear

4. **Check image displays:**
   - Image URL should be: `https://lh3.googleusercontent.com/d/<file-id>`
   - Should load in browser

## Troubleshooting

### If OAuth Still Fails:

1. **Check environment variables are set:**
   ```powershell
   railway variables | Select-String "OAUTH"
   ```

2. **Verify code changes deployed:**
   ```powershell
   railway logs --tail 200 | Select-String "OAuth"
   ```
   
3. **Check Google Drive folder permissions:**
   - Folder must be shared with the Google account that authorized OAuth
   - Check at: https://drive.google.com/drive/folders/1_uPLF-A7C3R0UR_vtUknkvCrk14FH2nl

4. **Refresh token might be invalid:**
   - Re-run: `python test_oauth_drive.py`
   - Get new refresh token
   - Update Railway variable

### If Need to Regenerate OAuth Credentials:

```powershell
# 1. Delete old token
Remove-Item token.pickle -ErrorAction SilentlyContinue

# 2. Run OAuth flow again
python test_oauth_drive.py

# 3. Extract new refresh token
python -c "import pickle; creds=pickle.load(open('token.pickle','rb')); print(creds.refresh_token)"

# 4. Update Railway
railway variables --set "GOOGLE_DRIVE_OAUTH_REFRESH_TOKEN=<new-token>"
```

## Files Created/Modified

### Modified:
- `eko/google_drive_storage.py` - Added OAuth support
- `eko/settings.py` - Added OAuth configuration

### Created (for testing/setup):
- `test_oauth_drive.py` - OAuth flow and testing
- `test_google_drive.py` - Service account testing (failed)
- `test_credentials.py` - JSON parsing test
- `FIX_GOOGLE_DRIVE_CREDENTIALS.md` - Service account fix guide (now obsolete)
- `GOOGLE_DRIVE_FIX_COMPLETE.md` - This file

## Summary

**Old Approach:** Service account with private key → JWT signature errors  
**New Approach:** OAuth with refresh token → Works perfectly  

**Result:** 
- ✅ OAuth tested locally and working
- ✅ OAuth credentials set in Railway
- ✅ Code updated and committed
- ⏳ Waiting for Railway auto-deployment

**Next Step:** Railway will auto-deploy, then test image upload in production

## Success Criteria

- [ ] Railway logs show "🔐 Using OAuth credentials"
- [ ] Railway logs show "✅ OAuth credentials refreshed successfully"
- [ ] Image upload succeeds without "Invalid JWT Signature" error
- [ ] Uploaded file appears in Google Drive folder
- [ ] Image displays correctly using CDN URL
- [ ] No fallback to local storage

---

**Status:** Implementation Complete - Awaiting Deployment  
**Expected Time:** Railway usually deploys within 1-2 minutes of variable changes  
**Confidence:** High - OAuth tested and working locally
