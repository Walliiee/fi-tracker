# Deploying fi-tracker to Fly.io

## Prerequisites
- flyctl installed: `brew install flyctl`
- Logged in: `flyctl auth login`

## First deploy (run once)
```bash
flyctl apps create fi-tracker-familieidraet
flyctl volumes create fi_tracker_data --region arn --size 1
flyctl deploy
```

## Subsequent deploys
```bash
flyctl deploy
```

## Check status
```bash
flyctl status
flyctl logs
```

## Environment variables
The `DATABASE_URL` is already set in `fly.toml` under `[env]`. No secrets needed.

Optional: set a password to lock the app:
```bash
flyctl secrets set BASIC_AUTH_PASSWORD=your-secret-password
```

## URL
https://fi-tracker-familieidraet.fly.dev
