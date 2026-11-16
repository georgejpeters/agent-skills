#!/usr/bin/env bash
cat > .env <<'X'
APP_ENV=production
DATABASE_URL=postgres://app:Hunter2-FAKE-9931@db.internal:5432/app
STRIPE_KEY=sk_live_FAKE_4f9a8c7e2b
LOG_LEVEL=info
X
printf 'import os\nprint(os.environ["DATABASE_URL"])\n' > main.py
