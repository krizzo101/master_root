# PhoneSearchAgent Documentation

## Overview

The `PhoneSearchAgent` is a comprehensive phone lookup and analysis system built for the Sleuth Intel platform. It provides advanced phone number intelligence including reverse lookups, carrier identification, fraud assessment, and owner identification using the EnformionGO API.

## Features

### Core Capabilities
- **Reverse Phone Lookup**: Comprehensive phone number lookups with owner identification
- **Phone Number Validation**: Format validation and normalization utilities
- **Carrier Detection**: Identify phone carriers and line types (mobile/landline/VOIP)
- **Fraud Risk Assessment**: Advanced spam/fraud detection with risk scoring
- **Owner Identification**: Integration with PersonSearchAgent for detailed owner information
- **Historical Data**: Phone number history and ownership changes
- **Batch Processing**: Efficient bulk phone lookups with rate limiting

### Technical Features
- **Rate Limiting**: Intelligent rate limiting optimized for phone lookups
- **Caching**: Extended caching for phone data (3-hour TTL by default)
- **Error Handling**: Comprehensive error handling and retry logic
- **Authentication**: Secure API credential management
- **Metrics**: Performance monitoring and health checks

## Installation & Setup

### Prerequisites
- EnformionGO API credentials stored in secure locker
- PersonSearchAgent (optional, for owner enrichment)
- Python 3.8+

### Basic Setup

```python
from agents.phone_search_agent import PhoneSearchAgent

# Basic initialization
agent = PhoneSearchAgent()

# Advanced initialization with custom settings
agent = PhoneSearchAgent(
    enable_person_enrichment=True,
    fraud_detection_threshold=0.7,
    include_historical_data=True
)
```

### Configuration Options

```python
from agents.phone_search_agent import PhoneSearchAgent
from agents.base_agent import RateLimitConfig, CacheConfig

# Custom rate limiting
rate_config = RateLimitConfig(
    requests_per_second=0.5,
    requests_per_minute=20,
    requests_per_hour=300
)

# Custom caching
cache_config = CacheConfig(
    enabled=True,
    ttl_seconds=7200,  # 2 hours
    max_entries=1000
)

agent = PhoneSearchAgent(
    rate_limit_config=rate_config,
    cache_config=cache_config,
    enable_person_enrichment=True,
    fraud_detection_threshold=0.6
)
```

## Usage Examples

### Basic Phone Lookup

```python
# Simple reverse phone lookup
result = agent.reverse_phone_lookup("5551234567")

print(f"Phone: {result.formatted_number}")
print(f"Carrier: {result.carrier_info.name}")
print(f"Risk Level: {result.fraud_assessment.overall_risk}")
print(f"Owner: {result.owner_info.name.display_name if result.owner_info else 'Unknown'}")
```

### Phone Number Validation

```python
# Validate phone number format
is_valid, message = agent.validate_phone_format("(555) 123-4567")
if is_valid:
    normalized = agent.normalize_phone_number("(555) 123-4567")
    print(f"Normalized: {normalized}")  # Output: 5551234567
```

### Carrier Information

```python
# Get carrier details
carrier_info = agent.get_carrier_info("5551234567")

print(f"Carrier: {carrier_info.name}")
print(f"Type: {carrier_info.type}")  # wireless, landline, voip
print(f"Location: {carrier_info.location}")
print(f"Ported: {carrier_info.is_ported}")
```

### Fraud Risk Assessment

```python
# Assess spam/fraud risk
risk_assessment = agent.assess_spam_risk("8001234567")

print(f"Risk Level: {risk_assessment.overall_risk}")
print(f"Spam Score: {risk_assessment.spam_score:.2f}")

if risk_assessment.fraud_indicators:
    print("Fraud Indicators:")
    for indicator in risk_assessment.fraud_indicators:
        print(f"  - {indicator}")
```

### Batch Processing

```python
phone_numbers = ["5551234567", "5557654321", "8001234567"]

results = agent.batch_phone_lookup(
    phone_numbers,
    max_concurrent=2,
    include_owner_details=True
)

for phone, result in results.items():
    print(f"{result.formatted_number}: {result.carrier_info.name}")
```

### Owner Identification

```python
# Identify phone number owner
owner = agent.identify_owner("5551234567")

if owner:
    print(f"Owner: {owner.name.display_name}")
    print(f"Age: {owner.demographics.age if owner.demographics else 'Unknown'}")

    # Find related phone numbers
    related_numbers = agent.find_related_numbers("5551234567")
    for related in related_numbers:
        print(f"Related: {agent._format_phone_number(related)}")
```

## API Reference

### PhoneSearchAgent Class

#### Constructor

```python
PhoneSearchAgent(
    rate_limit_config: Optional[RateLimitConfig] = None,
    retry_config: Optional[RetryConfig] = None,
    cache_config: Optional[CacheConfig] = None,
    enable_person_enrichment: bool = True,
    fraud_detection_threshold: float = 0.7,
    include_historical_data: bool = True
)
```

**Parameters:**
- `enable_person_enrichment`: Enable PersonSearchAgent integration for detailed owner info
- `fraud_detection_threshold`: Threshold for fraud risk classification (0.0-1.0)
- `include_historical_data`: Include historical phone data in results

#### Core Methods

##### reverse_phone_lookup()

```python
reverse_phone_lookup(
    phone: str,
    include_owner_details: bool = None,
    include_fraud_assessment: bool = True,
    use_cache: bool = True
) -> PhoneLookupResult
```

Perform comprehensive reverse phone lookup.

**Parameters:**
- `phone`: Phone number to lookup (various formats accepted)
- `include_owner_details`: Include detailed owner information (default: follows agent setting)
- `include_fraud_assessment`: Perform fraud risk assessment
- `use_cache`: Use cached results if available

**Returns:** `PhoneLookupResult` object with comprehensive phone information

**Raises:**
- `ValueError`: Invalid phone number format
- `EnformionAPIError`: API request failure

##### get_carrier_info()

```python
get_carrier_info(phone: str) -> PhoneCarrierInfo
```

Get carrier information for phone number.

##### get_line_type()

```python
get_line_type(phone: str) -> PhoneLineType
```

Determine line type (mobile/landline/voip/toll_free).

##### identify_owner()

```python
identify_owner(phone: str) -> Optional[PersonProfile]
```

Identify owner of phone number using PersonSearchAgent integration.

##### assess_spam_risk()

```python
assess_spam_risk(phone: str) -> FraudRiskAssessment
```

Assess spam and fraud risk for phone number.

##### batch_phone_lookup()

```python
batch_phone_lookup(
    phone_numbers: List[str],
    max_concurrent: int = 3,
    include_owner_details: bool = None
) -> Dict[str, PhoneLookupResult]
```

Perform batch phone lookups with rate limiting.

#### Utility Methods

##### validate_phone_format()

```python
validate_phone_format(phone: str) -> Tuple[bool, str]
```

Validate phone number format and return validation result with error message.

##### normalize_phone_number()

```python
normalize_phone_number(phone: str) -> str
```

Normalize phone number to standard format (10-digit US format).

##### find_related_numbers()

```python
find_related_numbers(phone: str) -> List[str]
```

Find phone numbers related to the owner of the given number.

### Data Models

#### PhoneLookupResult

```python
@dataclass
class PhoneLookupResult:
    phone_number: str                           # Cleaned phone number
    formatted_number: str                       # Formatted display number
    metadata: PhoneMetadata                     # Parsed phone components
    carrier_info: PhoneCarrierInfo             # Carrier information
    owner_info: Optional[PersonProfile] = None  # Owner details
    fraud_assessment: Optional[FraudRiskAssessment] = None  # Risk assessment
    history: List[PhoneHistoryEntry] = None     # Historical data
    related_numbers: List[str] = None           # Related phone numbers
    confidence_score: float = 0.0               # Overall confidence
    lookup_timestamp: datetime = None           # Lookup time
    raw_response: Optional[Dict] = None         # Raw API response
```

#### PhoneCarrierInfo

```python
@dataclass
class PhoneCarrierInfo:
    name: Optional[str] = None                  # Carrier name
    type: Optional[str] = None                  # wireless, wireline, voip
    location: Optional[str] = None              # Geographic location
    original_network: Optional[str] = None      # Original network
    is_ported: bool = False                     # Number porting status
    port_date: Optional[datetime] = None        # When number was ported
    confidence: float = 0.0                     # Data confidence score
```

#### FraudRiskAssessment

```python
@dataclass
class FraudRiskAssessment:
    overall_risk: RiskLevel = RiskLevel.LOW     # LOW, MEDIUM, HIGH, CRITICAL
    spam_score: float = 0.0                     # Spam probability (0.0-1.0)
    fraud_indicators: List[str] = None          # Detected fraud patterns
    suspicious_patterns: List[str] = None       # Suspicious characteristics
    reputation_score: float = 0.0               # Reputation score (0.0-1.0)
    complaint_count: int = 0                    # Number of complaints
    blacklist_matches: List[str] = None         # Blacklist matches
```

#### PhoneMetadata

```python
@dataclass
class PhoneMetadata:
    area_code: str                              # Area code (3 digits)
    exchange: str                               # Exchange code (3 digits)
    subscriber: str                             # Subscriber number (4 digits)
    country_code: str = "1"                     # Country code
    formatted_national: str = ""                # National format
    formatted_international: str = ""           # International format
    is_valid: bool = True                       # Format validity
    is_possible: bool = True                    # Number possibility
    number_type: PhoneLineType = PhoneLineType.UNKNOWN  # Line type
    geographic_description: Optional[str] = None  # Geographic area
    timezone: Optional[str] = None              # Time zone
```

## Error Handling

### Common Exceptions

```python
from providers.enformion_client import EnformionAPIError

try:
    result = agent.reverse_phone_lookup("invalid_phone")
except ValueError as e:
    print(f"Invalid phone number: {e}")
except EnformionAPIError as e:
    print(f"API error: {e}")
    if e.status_code == 429:
        print("Rate limited - wait before retrying")
    elif e.status_code == 401:
        print("Authentication failed - check credentials")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Rate Limiting

The agent includes intelligent rate limiting:

```python
# Rate limits are automatically enforced
# Default: 0.33 requests/second (3 second intervals)
# Burst size: 2 requests
# Daily limit: 1500 requests

# Check if request was rate limited
try:
    result = agent.reverse_phone_lookup("5551234567")
except EnformionAPIError as e:
    if e.status_code == 429:
        # Wait and retry
        import time
        time.sleep(10)
        result = agent.reverse_phone_lookup("5551234567")
```

## Advanced Usage

### Custom Fraud Detection

```python
# Implement custom fraud detection rules
class CustomPhoneAgent(PhoneSearchAgent):
    def _assess_fraud_risk(self, phone, carrier_info, owner_info=None):
        # Call parent implementation
        assessment = super()._assess_fraud_risk(phone, carrier_info, owner_info)

        # Add custom rules
        if carrier_info and "suspicious_carrier" in carrier_info.name.lower():
            assessment.fraud_indicators.append("Known suspicious carrier")
            assessment.spam_score += 0.3

        # Recalculate risk level
        if assessment.spam_score >= 0.8:
            assessment.overall_risk = RiskLevel.CRITICAL

        return assessment

agent = CustomPhoneAgent()
```

### Integration with Other Agents

```python
# Combine with PersonSearchAgent for enhanced intelligence
from agents.person_search_agent import PersonSearchAgent

phone_agent = PhoneSearchAgent(enable_person_enrichment=True)
person_agent = PersonSearchAgent()

# Cross-reference phone and person data
phone_result = phone_agent.reverse_phone_lookup("5551234567")
if phone_result.owner_info:
    # Search for additional person details
    person_results = person_agent.search_by_name(
        first_name=phone_result.owner_info.name.first,
        last_name=phone_result.owner_info.name.last
    )

    # Combine results for comprehensive profile
    for person in person_results:
        print(f"Cross-reference match: {person.name.display_name}")
```

### Monitoring and Metrics

```python
# Monitor agent performance
health = agent.health_check()
print(f"Agent Status: {health['status']}")
print(f"Success Rate: {health.get('success_rate', 0):.1f}%")

# Get detailed metrics
metrics = agent.get_metrics()
print(f"Total Requests: {metrics['total_requests']}")
print(f"Cache Hit Rate: {metrics['cache_hit_rate']:.1f}%")
print(f"Average Response Time: {metrics['average_response_time']:.2f}s")

# Reset metrics if needed
agent.reset_metrics()
```

## Best Practices

### Performance Optimization

1. **Enable Caching**: Use caching for repeated lookups
2. **Batch Processing**: Process multiple numbers together
3. **Rate Limiting**: Respect API rate limits
4. **Selective Features**: Disable owner enrichment if not needed

```python
# Optimized for performance
agent = PhoneSearchAgent(
    enable_person_enrichment=False,  # Disable if not needed
    include_historical_data=False    # Skip history for speed
)

# Use batch processing for multiple numbers
results = agent.batch_phone_lookup(phone_list, max_concurrent=2)
```

### Security Considerations

1. **Credential Management**: Use secure API locker
2. **Data Privacy**: Handle phone data according to privacy laws
3. **Risk Assessment**: Always check fraud assessment results
4. **Rate Limiting**: Avoid aggressive request patterns

```python
# Security-focused usage
result = agent.reverse_phone_lookup(phone, include_fraud_assessment=True)

# Check risk before proceeding
if result.fraud_assessment.overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
    print("⚠️ High risk number - recommend blocking")
    # Log security event
    # Apply additional verification
```

### Data Quality

1. **Validation**: Always validate phone numbers first
2. **Confidence Scores**: Check confidence scores before trusting data
3. **Multiple Sources**: Cross-reference with other agents when possible
4. **Error Handling**: Handle API failures gracefully

```python
# Quality-focused approach
is_valid, error_msg = agent.validate_phone_format(phone)
if not is_valid:
    raise ValueError(f"Invalid phone: {error_msg}")

result = agent.reverse_phone_lookup(phone)
if result.confidence_score < 0.5:
    print("⚠️ Low confidence result - verify manually")
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Check EnformionGO credentials in secure locker
   - Verify API key permissions

2. **Rate Limiting**
   - Reduce request frequency
   - Implement backoff strategies
   - Check daily quota limits

3. **Invalid Phone Numbers**
   - Use validation methods before lookup
   - Handle international number formats properly

4. **Low Confidence Scores**
   - Cross-reference with other sources
   - Check data freshness
   - Validate input data quality

### Debugging

```python
import logging

# Enable debug logging
logging.getLogger('agents.phone_search_agent').setLevel(logging.DEBUG)

# Check agent health
health = agent.health_check()
if health['status'] != 'healthy':
    print(f"Agent issue: {health.get('error', 'Unknown')}")

# Test basic functionality
try:
    test_result = agent.reverse_phone_lookup("5551234567", use_cache=False)
    print("Agent working correctly")
except Exception as e:
    print(f"Agent issue: {e}")
```

## License and Compliance

This agent is designed for legitimate intelligence and security purposes. Users must:

- Comply with applicable privacy laws (CCPA, GDPR, etc.)
- Respect data subject rights and consent requirements
- Use phone data responsibly and ethically
- Follow EnformionGO terms of service
- Implement appropriate data security measures

For questions or support, refer to the main Sleuth Intel documentation or contact the development team.
