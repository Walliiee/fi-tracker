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

## Environment variables (set if needed)
```bash
flyctl secrets set DATABASE_URL=/data/fi_tracker.db
```

## URL
https://fi-tracker-familieidraet.fly.dev
