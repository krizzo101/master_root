# EmailSearchAgent Documentation

## Overview

The `EmailSearchAgent` is a comprehensive email intelligence and analysis tool that provides advanced email validation, reverse lookup capabilities, breach detection, and privacy-compliant data analysis. It integrates with the EnformionGO API to deliver professional-grade email intelligence services.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Privacy & Compliance](#privacy--compliance)
- [Performance & Rate Limiting](#performance--rate-limiting)
- [Error Handling](#error-handling)
- [Integration with Other Agents](#integration-with-other-agents)

## Features

### ✅ Email Validation
- **Format validation**: RFC-compliant email format checking
- **Deliverability validation**: MX record verification
- **Domain validation**: DNS and WHOIS lookup
- **Comprehensive error reporting**: Detailed validation issues

### 🔍 Email Intelligence
- **Reverse email lookup**: Find associated person/business information
- **Domain analysis**: Extract business affiliation and registration data
- **Email classification**: Professional vs personal vs disposable detection
- **Contact enrichment**: Phone numbers, addresses, and demographic data

### 🛡️ Security Features
- **Breach detection**: Check against known data breaches
- **Risk assessment**: Automated risk level calculation
- **Disposable email detection**: Identify temporary email services
- **Privacy-compliant processing**: Configurable data collection levels

### 🔗 Cross-Reference Capabilities
- **PersonSearchAgent integration**: Link email results with person profiles
- **Social media correlation**: Find associated social profiles (configurable)
- **Multi-source validation**: Cross-validate results across data sources

### ⚡ Performance Features
- **Intelligent caching**: Configurable response caching with TTL
- **Rate limiting**: API-safe request throttling
- **Batch processing**: Efficient multi-email processing
- **Health monitoring**: Real-time agent status and metrics

## Installation

### Prerequisites
```bash
pip install dnspython requests pydantic aiohttp python-whois
```

### Basic Setup
```python
from src.agents.email_search_agent import EmailSearchAgent

# Initialize with defaults
agent = EmailSearchAgent()
```

### Advanced Setup
```python
from src.agents.email_search_agent import EmailSearchAgent
from src.agents.base_agent import RateLimitConfig, CacheConfig

# Production configuration
rate_config = RateLimitConfig(
    requests_per_second=0.25,
    requests_per_minute=12,
    requests_per_hour=150
)

cache_config = CacheConfig(
    enabled=True,
    ttl_seconds=1800,
    max_entries=100
)

agent = EmailSearchAgent(
    rate_limit_config=rate_config,
    cache_config=cache_config,
    enable_breach_detection=True,
    enable_social_correlation=False,  # Privacy-safe default
    enable_mx_validation=True
)
```

## Quick Start

### Basic Email Validation
```python
# Validate email format
result = agent.validate_email_format("user@example.com")
if result['is_valid']:
    print(f"Valid email: {result['domain_part']}")
else:
    print(f"Invalid: {', '.join(result['issues'])}")

# Check deliverability
delivery = agent.validate_email_deliverability("user@example.com")
print(f"Deliverable: {delivery['deliverable']}")
```

### Email Intelligence Lookup
```python
# Reverse email lookup
intelligence = agent.reverse_email_lookup("contact@company.com")

if intelligence['found']:
    person = intelligence.get('person_info', {})
    business = intelligence.get('business_info', {})

    print(f"Person: {person.get('full_name', 'N/A')}")
    print(f"Business: {business.get('name', 'N/A')}")
    print(f"Confidence: {intelligence['confidence_score']:.2f}")
```

### Comprehensive Analysis
```python
# Complete email analysis
analysis = agent.comprehensive_email_analysis("analyst@company.com")

print(f"Overall Confidence: {analysis['overall_confidence']:.2f}")
print(f"Email Type: {analysis['classification']['type']}")
print(f"Processing Time: {analysis['processing_time']:.2f}s")
```

## Configuration

### Initialization Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `rate_limit_config` | `RateLimitConfig` | Default | API rate limiting configuration |
| `retry_config` | `RetryConfig` | Default | Request retry configuration |
| `cache_config` | `CacheConfig` | Default | Response caching configuration |
| `enable_breach_detection` | `bool` | `True` | Enable breach detection features |
| `enable_social_correlation` | `bool` | `False` | Enable social media correlation |
| `enable_mx_validation` | `bool` | `True` | Enable MX record validation |

### Rate Limiting Configuration
```python
rate_config = RateLimitConfig(
    requests_per_second=0.3,      # 3+ seconds between requests
    requests_per_minute=15,       # Max 15 requests per minute
    requests_per_hour=200,        # Max 200 requests per hour
    requests_per_day=1000,        # Max 1000 requests per day
    burst_size=2,                 # Allow 2 burst requests
    backoff_multiplier=2.0,       # Exponential backoff
    max_backoff=300.0             # Max 5 minutes backoff
)
```

### Cache Configuration
```python
cache_config = CacheConfig(
    enabled=True,                 # Enable caching
    ttl_seconds=3600,            # 1 hour cache TTL
    max_entries=200,             # Max 200 cached entries
    compress=True,               # Compress cached data
    cache_dir="./cache/email"    # Cache directory
)
```

## API Reference

### Core Methods

#### `validate_email_format(email: str) -> Dict[str, Any]`
Validates email address format and structure.

**Parameters:**
- `email` (str): Email address to validate

**Returns:**
```python
{
    'email': 'user@example.com',
    'is_valid': True,
    'format_valid': True,
    'local_part': 'user',
    'domain_part': 'example.com',
    'tld': 'com',
    'issues': []
}
```

#### `validate_email_deliverability(email: str) -> Dict[str, Any]`
Checks email deliverability through MX record validation.

**Parameters:**
- `email` (str): Email address to validate

**Returns:**
```python
{
    'email': 'user@example.com',
    'deliverable': True,
    'mx_valid': True,
    'mx_records': ['10 mail.example.com.'],
    'issues': []
}
```

#### `classify_email_type(email: str) -> Dict[str, Any]`
Classifies email as professional, personal, or disposable.

**Parameters:**
- `email` (str): Email address to classify

**Returns:**
```python
{
    'email': 'contact@company.com',
    'type': 'professional',
    'is_professional': True,
    'is_personal': False,
    'is_disposable': False,
    'is_business': True,
    'confidence': 0.9,
    'indicators': ['Business domain', 'Role-based email address']
}
```

#### `reverse_email_lookup(email: str, include_social: bool = None) -> Dict[str, Any]`
Performs reverse email lookup to find associated person/business information.

**Parameters:**
- `email` (str): Email address to lookup
- `include_social` (bool, optional): Include social media profiles

**Returns:**
```python
{
    'email': 'john.doe@company.com',
    'found': True,
    'person_info': {
        'first_name': 'John',
        'last_name': 'Doe',
        'full_name': 'John Doe',
        'age': 35,
        'phones': ['5551234567'],
        'addresses': [{'city': 'New York', 'state': 'NY'}]
    },
    'business_info': {
        'name': 'Acme Corp',
        'industry': 'Technology',
        'website': 'https://acme.com'
    },
    'confidence_score': 0.85,
    'timestamp': '2024-01-15T10:30:00'
}
```

#### `detect_email_breaches(email: str) -> Dict[str, Any]`
Checks if email appears in known data breaches.

**Parameters:**
- `email` (str): Email address to check

**Returns:**
```python
{
    'email': 'user@example.com',
    'found_in_breaches': True,
    'breach_count': 2,
    'breaches': [
        {
            'name': 'Example Breach',
            'date': '2020-01-01',
            'compromised_data': ['email', 'password']
        }
    ],
    'risk_level': 'medium',
    'timestamp': '2024-01-15T10:30:00'
}
```

#### `comprehensive_email_analysis(email: str, person_agent=None) -> Dict[str, Any]`
Performs complete comprehensive email analysis combining all methods.

**Parameters:**
- `email` (str): Email address to analyze
- `person_agent` (PersonSearchAgent, optional): For cross-referencing

**Returns:**
```python
{
    'email': 'analyst@company.com',
    'analysis_timestamp': '2024-01-15T10:30:00',
    'format_validation': {...},
    'deliverability': {...},
    'classification': {...},
    'domain_info': {...},
    'reverse_lookup': {...},
    'breach_detection': {...},
    'social_profiles': [...],
    'cross_reference': {...},
    'overall_confidence': 0.82,
    'processing_time': 2.45
}
```

### Utility Methods

#### `extract_domain_info(email: str) -> Dict[str, Any]`
Extracts domain registration and WHOIS information.

#### `find_social_profiles(email: str) -> List[Dict[str, Any]]`
Finds social media profiles associated with email (if enabled).

#### `cross_reference_with_person(email: str, person_agent=None) -> Dict[str, Any]`
Cross-references email results with PersonSearchAgent.

### BaseIntelligenceAgent Interface

#### `query(query_params: Dict[str, Any], **kwargs) -> Dict[str, Any]`
Executes email query using the base agent interface.

**Parameters:**
- `query_params` (Dict): Must contain 'email_address' or 'email' key
- `**kwargs`: Additional arguments (e.g., person_agent)

#### `health_check() -> Dict[str, Any]`
Performs comprehensive health check of the agent.

#### `get_metrics() -> Dict[str, Any]`
Returns performance metrics and statistics.

## Examples

### Basic Usage Examples

#### Email Validation Pipeline
```python
def validate_email_pipeline(email):
    agent = EmailSearchAgent()

    # Step 1: Format validation
    format_result = agent.validate_email_format(email)
    if not format_result['is_valid']:
        return {'valid': False, 'reason': 'Invalid format'}

    # Step 2: Deliverability check
    delivery_result = agent.validate_email_deliverability(email)
    if not delivery_result['deliverable']:
        return {'valid': False, 'reason': 'Not deliverable'}

    # Step 3: Classification
    classification = agent.classify_email_type(email)
    if classification['is_disposable']:
        return {'valid': False, 'reason': 'Disposable email'}

    return {'valid': True, 'type': classification['type']}
```

#### Batch Email Processing
```python
def process_email_list(email_list):
    agent = EmailSearchAgent()
    results = []

    for email in email_list:
        try:
            analysis = agent.comprehensive_email_analysis(email)

            results.append({
                'email': email,
                'valid': analysis['format_validation']['is_valid'],
                'type': analysis['classification']['type'],
                'confidence': analysis['overall_confidence'],
                'breach_risk': analysis['breach_detection'].get('risk_level', 'unknown')
            })

        except Exception as e:
            results.append({
                'email': email,
                'error': str(e)
            })

    return results
```

### Advanced Integration Examples

#### Cross-Reference with Person Search
```python
def find_person_by_email(email):
    email_agent = EmailSearchAgent()
    person_agent = PersonSearchAgent()

    # Get email intelligence
    email_result = email_agent.reverse_email_lookup(email)

    if email_result['found'] and email_result.get('person_info'):
        person_info = email_result['person_info']

        # Search for matching person profiles
        from src.models.query import PersonSearchQuery

        search_query = PersonSearchQuery(
            first_name=person_info.get('first_name'),
            last_name=person_info.get('last_name'),
            email=email,
            max_results=5
        )

        if search_query.has_sufficient_params():
            persons = person_agent.search(search_query)

            return {
                'email_data': email_result,
                'matching_persons': persons,
                'cross_reference_confidence': max(p.confidence_score for p in persons) if persons else 0.0
            }

    return {'email_data': email_result, 'matching_persons': []}
```

#### Security Risk Assessment
```python
def assess_email_security_risk(email):
    agent = EmailSearchAgent()

    # Comprehensive analysis
    analysis = agent.comprehensive_email_analysis(email)

    risk_score = 0.0
    risk_factors = []

    # Check breach history
    breach_info = analysis['breach_detection']
    if breach_info.get('found_in_breaches'):
        breach_count = breach_info['breach_count']
        if breach_count > 0:
            risk_score += min(breach_count * 0.2, 0.6)
            risk_factors.append(f"Found in {breach_count} breaches")

    # Check email type
    classification = analysis['classification']
    if classification['is_disposable']:
        risk_score += 0.4
        risk_factors.append("Disposable email service")

    # Check deliverability
    if not analysis['deliverability'].get('deliverable'):
        risk_score += 0.3
        risk_factors.append("Not deliverable")

    # Determine risk level
    if risk_score >= 0.7:
        risk_level = 'high'
    elif risk_score >= 0.4:
        risk_level = 'medium'
    else:
        risk_level = 'low'

    return {
        'email': email,
        'risk_score': min(risk_score, 1.0),
        'risk_level': risk_level,
        'risk_factors': risk_factors,
        'analysis': analysis
    }
```

## Privacy & Compliance

### Privacy-Safe Configuration
The EmailSearchAgent is designed with privacy compliance as a priority:

```python
# Privacy-compliant setup
agent = EmailSearchAgent(
    enable_breach_detection=True,      # Security-focused
    enable_social_correlation=False,   # Privacy-safe default
    enable_mx_validation=True          # Technical validation only
)
```

### Data Handling Principles

1. **Minimal Data Collection**: Only collect data necessary for the requested analysis
2. **Configurable Features**: All privacy-sensitive features can be disabled
3. **No Data Retention**: Results are not stored unless explicitly cached
4. **Masked Logging**: Sensitive information is masked in log outputs
5. **Secure Transmission**: All API communications use HTTPS

### Compliance Features

- **GDPR Compliance**: Configurable data processing levels
- **CCPA Compliance**: Minimal data collection by default
- **SOC 2 Compliance**: Secure credential management and audit logging
- **PCI Compliance**: No storage of sensitive personal data

### Best Practices

```python
# For privacy-sensitive applications
privacy_agent = EmailSearchAgent(
    enable_breach_detection=True,      # Security is important
    enable_social_correlation=False,   # Disable social lookup
    enable_mx_validation=True,         # Technical validation only
    cache_config=CacheConfig(         # Shorter cache times
        enabled=True,
        ttl_seconds=300,              # 5 minutes only
        max_entries=50
    )
)

# For security-focused applications
security_agent = EmailSearchAgent(
    enable_breach_detection=True,      # Enable all security features
    enable_social_correlation=True,    # For threat intelligence
    enable_mx_validation=True
)
```

## Performance & Rate Limiting

### Default Rate Limits
- **Requests per second**: 0.3 (3+ seconds between requests)
- **Requests per minute**: 15
- **Requests per hour**: 200
- **Requests per day**: 1000
- **Burst size**: 2

### Optimization Strategies

#### Caching Strategy
```python
# Optimize for performance
cache_config = CacheConfig(
    enabled=True,
    ttl_seconds=1800,     # 30 minutes for email data
    max_entries=500,      # Larger cache
    compress=True         # Save memory
)
```

#### Batch Processing
```python
# Process emails in batches with delays
def batch_process_emails(emails, batch_size=5, delay=2):
    agent = EmailSearchAgent()
    results = []

    for i in range(0, len(emails), batch_size):
        batch = emails[i:i+batch_size]

        for email in batch:
            result = agent.comprehensive_email_analysis(email)
            results.append(result)

        # Respect rate limits between batches
        if i + batch_size < len(emails):
            time.sleep(delay)

    return results
```

### Performance Monitoring
```python
# Monitor agent performance
def monitor_agent_performance(agent):
    metrics = agent.get_metrics()

    print(f"Success Rate: {metrics['success_rate']:.1f}%")
    print(f"Cache Hit Rate: {metrics['cache_hit_rate']:.1f}%")
    print(f"Average Response Time: {metrics['average_response_time']:.2f}s")
    print(f"Rate Limit Hits: {metrics['rate_limit_hits']}")

    if metrics['success_rate'] < 95:
        print("⚠️ Success rate is below 95%")

    if metrics['rate_limit_hits'] > 0:
        print("⚠️ Rate limits have been hit")
```

## Error Handling

### Common Error Types

#### API Errors
```python
from src.providers.enformion_client import EnformionAPIError

try:
    result = agent.reverse_email_lookup("test@example.com")
except EnformionAPIError as e:
    if e.status_code == 401:
        print("Authentication failed - check credentials")
    elif e.status_code == 429:
        print("Rate limit exceeded - wait before retrying")
    elif e.status_code == 402:
        print("Quota exhausted - upgrade plan or wait for reset")
    else:
        print(f"API error: {e}")
```

#### Validation Errors
```python
# Handle invalid email formats
result = agent.validate_email_format("invalid-email")
if not result['is_valid']:
    print(f"Validation errors: {', '.join(result['issues'])}")
```

#### Network Errors
```python
try:
    delivery_result = agent.validate_email_deliverability("test@example.com")
except Exception as e:
    if "DNS lookup" in str(e):
        print("DNS resolution failed - domain may not exist")
    elif "timeout" in str(e).lower():
        print("Network timeout - try again later")
    else:
        print(f"Network error: {e}")
```

### Error Recovery Strategies

#### Retry with Backoff
```python
import time
import random

def safe_email_lookup(agent, email, max_retries=3):
    for attempt in range(max_retries):
        try:
            return agent.reverse_email_lookup(email)
        except EnformionAPIError as e:
            if e.status_code == 429:  # Rate limited
                delay = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(delay)
                continue
            else:
                raise  # Re-raise non-retryable errors
        except Exception as e:
            if attempt == max_retries - 1:
                raise  # Last attempt, re-raise
            time.sleep(1)  # Brief delay before retry

    raise Exception(f"Failed after {max_retries} attempts")
```

#### Graceful Degradation
```python
def robust_email_analysis(agent, email):
    result = {
        'email': email,
        'format_valid': False,
        'deliverable': None,
        'classification': None,
        'intelligence': None,
        'errors': []
    }

    try:
        # Format validation (always works)
        format_result = agent.validate_email_format(email)
        result['format_valid'] = format_result['is_valid']

        if not result['format_valid']:
            result['errors'].extend(format_result['issues'])
            return result

        # Deliverability check (may fail due to DNS)
        try:
            delivery_result = agent.validate_email_deliverability(email)
            result['deliverable'] = delivery_result['deliverable']
        except Exception as e:
            result['errors'].append(f"Deliverability check failed: {str(e)}")

        # Classification (should always work for valid emails)
        try:
            classification = agent.classify_email_type(email)
            result['classification'] = classification
        except Exception as e:
            result['errors'].append(f"Classification failed: {str(e)}")

        # Intelligence lookup (may fail due to API issues)
        try:
            intelligence = agent.reverse_email_lookup(email)
            result['intelligence'] = intelligence
        except Exception as e:
            result['errors'].append(f"Intelligence lookup failed: {str(e)}")

    except Exception as e:
        result['errors'].append(f"Analysis failed: {str(e)}")

    return result
```

## Integration with Other Agents

### PersonSearchAgent Integration
```python
from src.agents.person_search_agent import PersonSearchAgent

# Initialize both agents
email_agent = EmailSearchAgent()
person_agent = PersonSearchAgent()

# Cross-reference email with person data
def find_complete_profile(email):
    # Get email intelligence
    email_data = email_agent.reverse_email_lookup(email)

    if email_data['found'] and email_data.get('person_info'):
        # Use email data to search for person profiles
        cross_ref = email_agent.cross_reference_with_person(email, person_agent)

        return {
            'email_intelligence': email_data,
            'person_matches': cross_ref.get('matching_persons', []),
            'overall_confidence': cross_ref.get('confidence_score', 0.0)
        }

    return {'email_intelligence': email_data}
```

### PhoneSearchAgent Integration
```python
from src.agents.phone_search_agent import PhoneSearchAgent

def correlate_email_and_phone(email, phone):
    email_agent = EmailSearchAgent()
    phone_agent = PhoneSearchAgent()

    # Get data from both sources
    email_data = email_agent.reverse_email_lookup(email)
    phone_data = phone_agent.reverse_phone_lookup(phone)

    # Find correlations
    correlations = []

    if (email_data.get('person_info') and phone_data.get('person_info')):
        email_person = email_data['person_info']
        phone_person = phone_data['person_info']

        # Check name similarity
        if (email_person.get('full_name') and phone_person.get('full_name')):
            if email_person['full_name'].lower() == phone_person['full_name'].lower():
                correlations.append('exact_name_match')

        # Check address overlap
        email_addresses = email_person.get('addresses', [])
        phone_addresses = phone_person.get('addresses', [])

        for email_addr in email_addresses:
            for phone_addr in phone_addresses:
                if (email_addr.get('city', '').lower() == phone_addr.get('city', '').lower() and
                    email_addr.get('state', '') == phone_addr.get('state', '')):
                    correlations.append('address_match')
                    break

    return {
        'email_data': email_data,
        'phone_data': phone_data,
        'correlations': correlations,
        'likely_same_person': len(correlations) > 0
    }
```

## Troubleshooting

### Common Issues

#### No Results from Lookup
```python
# Check if the issue is with the email or the API
result = agent.reverse_email_lookup("noresults@example.com")
if not result['found']:
    # Try a known good email to test API
    test_result = agent.reverse_email_lookup("test@gmail.com")
    if test_result.get('error'):
        print("API issue detected")
    else:
        print("Email not in database")
```

#### Rate Limiting Issues
```python
# Check rate limit status
metrics = agent.get_metrics()
if metrics['rate_limit_hits'] > 0:
    print("Rate limits have been exceeded")
    print("Consider:")
    print("- Reducing request frequency")
    print("- Implementing exponential backoff")
    print("- Upgrading API plan")
```

#### Cache Issues
```python
# Clear cache if results seem stale
agent.clear_cache()
print("Cache cleared - next requests will be fresh")
```

### Debug Mode
```python
import logging

# Enable debug logging
logging.getLogger('src.agents.email_search_agent').setLevel(logging.DEBUG)

# This will show detailed request/response information
result = agent.comprehensive_email_analysis("debug@example.com")
```

### Health Monitoring
```python
def continuous_health_check(agent, interval=300):
    """Monitor agent health every 5 minutes"""
    import time

    while True:
        health = agent.health_check()

        if health['status'] != 'healthy':
            print(f"⚠️ Agent unhealthy: {health.get('error', 'Unknown error')}")

            # Try to recover
            agent.clear_cache()
            time.sleep(60)  # Wait before retry

        time.sleep(interval)
```

## Advanced Topics

### Custom Email Classification
```python
# Extend email classification with custom rules
def custom_classify_email(agent, email):
    base_classification = agent.classify_email_type(email)

    # Add custom business logic
    domain = email.split('@')[1].lower()

    # Government emails
    if domain.endswith('.gov') or domain.endswith('.mil'):
        base_classification.update({
            'type': 'government',
            'is_government': True,
            'confidence': 0.95
        })

    # Education emails
    elif domain.endswith('.edu'):
        base_classification.update({
            'type': 'education',
            'is_education': True,
            'confidence': 0.90
        })

    # Non-profit organizations
    elif domain.endswith('.org'):
        base_classification.update({
            'is_nonprofit': True
        })

    return base_classification
```

### Advanced Breach Analysis
```python
def analyze_breach_timeline(agent, email):
    breach_data = agent.detect_email_breaches(email)

    if not breach_data.get('found_in_breaches'):
        return {'timeline': [], 'risk_trend': 'stable'}

    breaches = breach_data.get('breaches', [])

    # Sort breaches by date
    dated_breaches = []
    for breach in breaches:
        if breach.get('date'):
            try:
                breach_date = datetime.strptime(breach['date'], '%Y-%m-%d')
                dated_breaches.append((breach_date, breach))
            except ValueError:
                pass

    dated_breaches.sort()

    # Analyze timeline
    timeline = []
    risk_scores = []

    for date, breach in dated_breaches:
        # Calculate risk score based on compromised data types
        compromised_data = breach.get('compromised_data', [])
        risk_score = 0.0

        if 'password' in compromised_data:
            risk_score += 0.4
        if 'email' in compromised_data:
            risk_score += 0.2
        if 'financial' in compromised_data:
            risk_score += 0.6
        if 'personal' in compromised_data:
            risk_score += 0.3

        timeline.append({
            'date': date.isoformat(),
            'breach_name': breach.get('name'),
            'risk_score': min(risk_score, 1.0),
            'compromised_data': compromised_data
        })

        risk_scores.append(risk_score)

    # Determine risk trend
    if len(risk_scores) >= 2:
        if risk_scores[-1] > risk_scores[-2]:
            risk_trend = 'increasing'
        elif risk_scores[-1] < risk_scores[-2]:
            risk_trend = 'decreasing'
        else:
            risk_trend = 'stable'
    else:
        risk_trend = 'stable'

    return {
        'timeline': timeline,
        'risk_trend': risk_trend,
        'total_breaches': len(timeline),
        'highest_risk_score': max(risk_scores) if risk_scores else 0.0
    }
```

## Conclusion

The EmailSearchAgent provides comprehensive email intelligence capabilities while maintaining privacy compliance and security best practices. Its flexible configuration allows adaptation to various use cases, from basic email validation to advanced intelligence gathering.

For additional support or advanced use cases, consult the example files and integration documentation included with the agent.
