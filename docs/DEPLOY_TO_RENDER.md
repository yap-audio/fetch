# Render Deployment Guide

## Overview

Deploy two services to Render:
1. **negotiator-buyer** - Buyer agent service
2. **negotiator-seller** - Seller agent service

## Service 1: Buyer Agent

### Settings
- **Name**: `negotiator-buyer`
- **Environment**: `Web Service`
- **Region**: Your preferred region
- **Branch**: `main` (or your branch)
- **Root Directory**: Leave blank (will use commands to navigate)

### Build & Deploy
- **Build Command**: 
  ```
  cd negotiator && uv sync
  ```

- **Start Command**:
  ```
  cd negotiator && uv run python main.py --port $PORT
  ```

### Environment Variables
```
ANTHROPIC_API_KEY=sk-ant-...
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
SELLER_AGENT_URL=https://negotiator-seller.onrender.com
```

⚠️ **Note**: Set `SELLER_AGENT_URL` after deploying seller service

---

## Service 2: Seller Agent

### Settings
- **Name**: `negotiator-seller`
- **Environment**: `Web Service`
- **Region**: Same as buyer for lower latency
- **Branch**: `main` (or your branch)
- **Root Directory**: Leave blank

### Build & Deploy
- **Build Command**:
  ```
  cd negotiator && uv sync
  ```

- **Start Command**:
  ```
  cd negotiator && uv run python main.py --port $PORT
  ```

### Environment Variables
```
ANTHROPIC_API_KEY=sk-ant-...
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
BUYER_AGENT_URL=https://negotiator-buyer.onrender.com
```

⚠️ **Note**: Set `BUYER_AGENT_URL` after deploying buyer service

---

## Deployment Steps

1. **Deploy Buyer Service First**
   - Create web service in Render
   - Use settings above (without SELLER_AGENT_URL for now)
   - Wait for deployment to complete
   - Copy the Render URL (e.g., `https://negotiator-buyer.onrender.com`)

2. **Deploy Seller Service**
   - Create second web service
   - Use settings above
   - Set `BUYER_AGENT_URL` to the buyer service URL from step 1
   - Wait for deployment

3. **Update Buyer Service**
   - Go back to buyer service
   - Add environment variable: `SELLER_AGENT_URL=https://negotiator-seller.onrender.com`
   - Redeploy (or it will pick up automatically)

4. **Verify Deployment**
   ```bash
   # Check buyer health
   curl https://negotiator-buyer.onrender.com/
   
   # Check seller health  
   curl https://negotiator-seller.onrender.com/
   
   # Both should return: {"status":"ok","service":"negotiation-agent"}
   ```

## Testing Deployed Services

### Test Buyer Agent
```bash
curl -X POST https://negotiator-buyer.onrender.com/negotiate \
  -H "Content-Type: application/json" \
  -d '{
    "intent_id": "32ec0fba-931e-49b2-b4c2-02a1d6929a9c",
    "seller_message": "I can sell this for $14,000",
    "agent_type": "buyer"
  }'
```

### Test Seller Initiation
```bash
curl -X POST https://negotiator-seller.onrender.com/initiate \
  -H "Content-Type: application/json" \
  -d '{
    "intent_id": "32ec0fba-931e-49b2-b4c2-02a1d6929a9c",
    "agent_type": "seller"
  }'
```

Should return seller's pitch + buyer's response!

## Frontend Integration

Your app can call either service:

```typescript
// Seller initiates negotiation
const response = await fetch('https://negotiator-seller.onrender.com/initiate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    intent_id: intentId,
    agent_type: 'seller'
  })
});

const { seller_pitch, buyer_response, buyer_decision } = await response.json();

// Continue negotiation via /negotiate endpoint
```

## Monitoring

### Check Logs
- Render dashboard → Service → Logs
- Look for "Starting negotiation service on port"
- Check for any errors

### Health Checks
Both services expose `GET /` for health checks.

## Troubleshooting

### "BUYER_AGENT_URL not configured"
- Make sure environment variable is set
- Check spelling (case-sensitive)
- Redeploy after adding env var

### Connection timeout
- Check both services are deployed and running
- Verify URLs in environment variables
- Check Render logs for errors

### Claude API errors
- Verify ANTHROPIC_API_KEY is correct
- Check API quota/limits

## Cost Optimization

- **Instance Type**: Use smallest instance for hackathon
- **Auto-deploy**: Enable for easier updates
- **Sleep Settings**: Render free tier sleeps after inactivity (keep in mind for demos)

## Success Checklist

✅ Both services deployed
✅ Environment variables set correctly
✅ Health checks return 200
✅ /negotiate endpoint works
✅ /initiate endpoint connects services
✅ Claude API responding
✅ Supabase connection working

Ready for your hackathon demo! 🚀

