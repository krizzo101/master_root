# Gemini API Key Issue - Free Tier Limits

## Problem
The current API key (`AIzaSyDcABMDq_BnwtwYDW-xDYwpblaPaHxQFsY`) is being treated as a **FREE TIER** key despite having an Ultra plan subscription.

## Evidence
API responses show free tier quota errors:
- `generate_content_free_tier_input_token_count`
- `GenerateRequestsPerMinutePerProjectPerModel-FreeTier`
- Limit: 5 requests/minute for gemini-2.5-pro

## Root Cause
The API key is not properly associated with the Ultra plan billing account.

## Solutions

### 1. Generate New API Key (Recommended)
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Ensure you're logged in with the Ultra plan account
3. Generate a new API key
4. Update the key in:
   - `/home/opsvi/master_root/.env`
   - `/home/opsvi/master_root/.mcp.json`
   - `/home/opsvi/master_root/.cursor/mcp.json`

### 2. Use Google Cloud Project (Alternative)
If you have a Google Cloud project with billing:

```bash
# Set up Application Default Credentials
gcloud auth application-default login

# Or use a service account key
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

Then modify the Gemini server to use Google Cloud auth instead of API key.

### 3. Verify Billing Association
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Check project billing status
3. Ensure the project is linked to your Ultra plan subscription

## Current Workaround
Using `gemini-1.5-pro` model which has slightly better free tier limits than `gemini-2.5-pro`.

## Testing After Fix
Once you have a properly associated API key:

```bash
# Test the new key
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key=YOUR_NEW_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents": [{"parts": [{"text": "Test"}]}]}'
```

If successful, you should NOT see "free_tier" in any error messages.

## Files to Update with New Key
1. `/home/opsvi/master_root/.env` - Line with `GEMINI_API_KEY=`
2. `/home/opsvi/master_root/.mcp.json` - Under `gemini-agent.env.GEMINI_API_KEY`
3. `/home/opsvi/master_root/.cursor/mcp.json` - Under `gemini-agent.env.GEMINI_API_KEY`

## Benefits of Ultra Plan (Once Fixed)
- **2M requests/day** (vs 50/day free)
- **4M TPM** (tokens per minute) for gemini-2.5-pro
- **10 RPM** (requests per minute) for gemini-2.5-pro
- Access to all premium models
- Priority processing