# Sleuth Intel - People & Business Discovery Tool

A secure, API-driven platform for people, phone, and business intelligence using multiple data providers with encrypted credential management.

## Features

- 🔒 **Secure API Key Management** - TokenPool-inspired encrypted credential storage
- 📞 **Reverse Phone Lookup** - Find owners, carrier info, and validation
- 👤 **People Search** - Identity verification and contact enrichment
- 🏢 **Business Intelligence** - Company data and corporate records
- 🔄 **Multi-Provider Support** - EnformionGO, IPQualityScore, Trestle, NumVerify
- ⚡ **High Performance** - Async operations and credential rotation

## Supported Providers

### EnformionGO (Primary)
- **Coverage**: 300M+ US people profiles, 120B+ records
- **Features**: Reverse phone, identity verification, contact enrichment
- **Pricing**: Free tier (100 searches), $0.10/match starter, $0.01/match pro
- **Documentation**: https://enformiongo.readme.io/reference/overview

### IPQualityScore
- **Coverage**: Phone validation, fraud scoring, carrier lookup
- **Features**: Free tier (1,000 lookups/month), spam detection
- **Pricing**: Free tier available, paid from $14.99/month

### Trestle
- **Coverage**: Identity verification, phone metadata
- **Features**: $0.07/query, high accuracy (90%+)
- **Pricing**: Pay-per-use, enterprise custom

### NumVerify
- **Coverage**: 232 countries, phone validation
- **Features**: Carrier detection, line type identification
- **Pricing**: Free (100 requests), paid from $9.99/month

## Quick Start

### 1. Setup API Keys

```bash
cd /home/opsvi/master_root/apps/sleuth-intel

# Run setup script to store your EnformionGO credentials securely
python3 setup_api_keys.py
```

Your credentials will be encrypted and stored in `~/.sleuth-intel/api_keys.enc`

### 2. Basic Usage

```python
from src.providers.enformion_client import lookup_phone, lookup_person

# Reverse phone lookup
result = lookup_phone("(910) 392-5349")
print(f"Owner: {result}")

# Person search
person = lookup_person("John", "Smith", city="Los Angeles", state="CA")
print(f"Contact info: {person}")
```

### 3. Advanced Usage

```python
from src.providers.enformion_client import EnformionClient

client = EnformionClient()

# Identity verification
identity = client.identity_verification(
    first_name="John",
    last_name="Smith",
    address="123 Main St",
    phone="5551234567"
)

# Contact enrichment
enriched = client.contact_enrichment(
    email="john@example.com",
    phone="5551234567"
)

# Business search
business = client.business_search(
    business_name="Tech Company Inc",
    city="San Francisco",
    state="CA"
)
```

## Security Features

### Encrypted Storage
- All API keys encrypted using XOR + Base64 (upgrade to AES for production)
- File permissions set to 0o600 (owner read/write only)
- Separate encryption key via `SLEUTH_INTEL_ENCRYPTION_KEY` environment variable

### Credential Rotation
- Round-robin rotation across multiple API keys per provider
- Usage statistics and tracking
- Thread-safe operations with locks

### Safe Logging
- API keys never logged in plaintext
- SHA256 hashes used for tracking
- Safe identifiers for monitoring

## API Reference

### EnformionClient Methods

| Method | Description | Parameters |
|--------|-------------|------------|
| `reverse_phone_search(phone)` | Find owner of phone number | phone: str |
| `caller_id_lookup(phone)` | Get caller ID info | phone: str |
| `person_search(**kwargs)` | Search by name/address | first_name, last_name, address, city, state, zip |
| `business_search(**kwargs)` | Search businesses | business_name, address, city, state |
| `identity_verification(**kwargs)` | Verify and enrich identity | first_name, last_name, address, phone, email |
| `contact_enrichment(**kwargs)` | Enrich contact data | Any combination of name, phone, email, address |

### Response Format

```json
{
  "person": {
    "name": {
      "firstName": "John",
      "lastName": "Smith"
    },
    "addresses": [{
      "street": "123 Main St",
      "city": "Los Angeles",
      "state": "CA",
      "zip": "90210"
    }],
    "phones": [{
      "number": "(310) 555-1234",
      "type": "mobile",
      "isConnected": true
    }],
    "emails": ["john@example.com"]
  }
}
```

## Configuration

### Environment Variables

```bash
# Required for encryption (use strong key in production)
export SLEUTH_INTEL_ENCRYPTION_KEY="your-secure-encryption-key"

# Optional: Additional provider keys
export IPQS_KEY="your-ipqs-api-key"
export TRESTLE_KEY="your-trestle-api-key"
export NUMVERIFY_KEY="your-numverify-access-key"
```

### Config File Format

Create `~/.sleuth-intel/credentials.json`:

```json
{
  "enformion": {
    "key_name": "profile_access_key",
    "key_value": "your-api-key",
    "password": "your-api-password",
    "base_url": "https://api.enformion.com/v1",
    "rate_limit": 1000
  },
  "ipqualityscore": {
    "key_value": "your-ipqs-key",
    "base_url": "https://ipqualityscore.com/api/json"
  }
}
```

## Testing

```bash
# Test the system without making API calls
python3 test_system.py

# Test with actual API calls (will use credits)
python3 -c "from src.providers.enformion_client import lookup_phone; print(lookup_phone('9103925349'))"
```

## Error Handling

```python
from src.providers.enformion_client import EnformionClient, EnformionAPIError

try:
    client = EnformionClient()
    result = client.reverse_phone_search("5551234567")
except EnformionAPIError as e:
    print(f"API Error: {e}")
    print(f"Status Code: {e.status_code}")
    print(f"Response: {e.response_data}")
```

## Rate Limits

- **EnformionGO**: 1000 requests/month (starter), unlimited (pro)
- **IPQualityScore**: 1000 requests/month (free), 5K-250K (paid)
- **Trestle**: 10 QPS standard, custom for enterprise
- **NumVerify**: 100 requests/month (free), 2K-250K (paid)

## Project Structure

```
sleuth-intel/
├── README.md
├── setup_api_keys.py          # Secure credential setup
├── test_system.py             # System tests
├── src/
│   ├── core/
│   │   └── secure_api_locker.py  # Encrypted credential management
│   └── providers/
│       └── enformion_client.py   # EnformionGO API client
└── ~/.sleuth-intel/
    └── api_keys.enc           # Encrypted credentials
```

## Production Deployment

### Security Hardening
1. Replace XOR encryption with AES-256-GCM
2. Use dedicated encryption key management service
3. Implement API key rotation policies
4. Add audit logging and monitoring
5. Set up rate limiting and retry logic

### Scaling
1. Add Redis for credential caching
2. Implement connection pooling
3. Add async/await support for concurrent requests
4. Set up load balancing across providers

## License

Internal tool for Sleuth Intelligence operations.
