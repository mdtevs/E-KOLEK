# UPDATE YOUR RAILWAY VARIABLES TO MATCH LOCAL DEVELOPMENT

## Change these Railway variables back to standard Gmail SMTP:

```
EMAIL_BACKEND=accounts.email_backend.ResilientSMTPBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=ekolekcenro@gmail.com
EMAIL_HOST_PASSWORD=aeslhefyknzkuhet
DEFAULT_FROM_EMAIL=ekolekcenro@gmail.com
```

## What This Does:

The new **ResilientSMTPBackend** will automatically:

1. ✅ **Try port 587 with TLS** (your local dev config)
2. ✅ **Fall back to port 465 with SSL** (if 587 blocked)
3. ✅ **Try alternative ports** (2525, 8025, 25)
4. ✅ **Log which configuration works** for future reference
5. ✅ **Works exactly like local development** when ports aren't blocked

## Why This Is Better:

- **Same config locally and on Railway** (no environment-specific settings)
- **Automatic fallback** - tries all possible configurations
- **Detailed logging** - tells you exactly which port worked
- **No SendGrid needed** - uses your existing Gmail SMTP
- **Zero code changes** - just deploy and it works

## Testing:

After Railway deploys, check logs to see which port it connected with:

```bash
railway logs --service E-KOLEK | Select-String "WORKING SMTP"
```

You'll see output like:
```
🎉 WORKING SMTP CONFIGURATION FOUND!
   Host: smtp.gmail.com
   Port: 465
   SSL: True
   TLS: False
```

This tells you exactly which configuration Railway allows!
