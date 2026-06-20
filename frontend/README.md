# Deploy frontend to Vercel from GitHub (recommended)

When importing on https://vercel.com/new:

1. **Root Directory**: `frontend`
2. **Framework**: Next.js (auto-detected)
3. **Environment variable**:
   - `NEXT_PUBLIC_API_URL` = your public API URL (or leave unset — dashboard shows graceful offline state)

## CLI deploy (from frontend/)

```powershell
cd frontend
vercel login
vercel link
vercel env add NEXT_PUBLIC_API_URL production   # optional
vercel --prod
```

## GitHub repo

https://github.com/romaxnova/lux-arbitrage
