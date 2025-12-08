# RAILWAY SMTP WORKAROUND - Use Railway's Internal SMTP Relay

Railway blocks external SMTP but may provide an internal relay. Let's try using Railway's potential internal services:

## Option 1: Railway Internal SMTP (Try First)

Some Railway projects have access to internal SMTP. Try these settings:

```
EMAIL_HOST = smtp.railway.app
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = ekolekcenro@gmail.com
EMAIL_HOST_PASSWORD = aeslhefyknzkuhet
```

If this doesn't work, Railway might need you to contact support.

## Option 2: Use Railway Environment Variable for Gmail Relay

Try setting up a Railway-specific Gmail relay:

```bash
railway variables set SMTP_RELAY_HOST=smtp-relay.gmail.com
railway variables set SMTP_RELAY_PORT=587
```

Then update settings to use:
```
EMAIL_HOST = smtp-relay.gmail.com
EMAIL_PORT = 587
```

## Option 3: SendGrid Free Tier (Guaranteed to Work)

If Railway truly blocks ALL SMTP:

1. Sign up: https://signup.sendgrid.com (free, no credit card)
2. Verify email
3. Create API key: Settings → API Keys → Create API Key
4. Update Railway variables:
   ```
   EMAIL_HOST = smtp.sendgrid.net
   EMAIL_PORT = 587
   EMAIL_USE_TLS = True
   EMAIL_HOST_USER = apikey
   EMAIL_HOST_PASSWORD = SG.xxxxx (your API key)
   DEFAULT_FROM_EMAIL = ekolekcenro@gmail.com
   ```
5. Verify sender: SendGrid → Sender Authentication → ekolekcenro@gmail.com

## Option 4: Contact Railway Support

Open a support ticket asking to whitelist Gmail SMTP for your project:
https://railway.app/help

Request: "Please enable outbound SMTP connections to smtp.gmail.com:587 for my project"

## Testing Which Option Works

I'll create a script to test Railway's internal SMTP options.
