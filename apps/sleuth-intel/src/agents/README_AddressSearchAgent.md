# AddressSearchAgent

Comprehensive address intelligence agent providing address validation, resident identification, property analysis, and neighborhood demographics using the EnformionGO `/address-search` endpoint.

## Features

### Core Address Intelligence
- **Address Validation & Standardization**: Parse, validate, and standardize address formats with quality scoring
- **Address Verification**: Verify deliverability and residential/commercial classification
- **Address Normalization**: Consistent formatting for comparison and deduplication
- **Geocoding**: Convert addresses to latitude/longitude coordinates

### Resident Intelligence
- **Current Resident Identification**: Identify people currently living at an address
- **Historical Resident Analysis**: Track previous residents with occupancy periods
- **Move Pattern Analysis**: Analyze individual movement patterns and stability scores
- **Relationship Classification**: Owner, renter, relative, etc.

### Property Intelligence
- **Ownership Analysis**: Current and historical property ownership records
- **Property Details**: Square footage, bedrooms, year built, lot size
- **Tax Assessment**: Assessed values, annual taxes, mortgage information
- **Ownership Type**: Individual, corporation, trust, LLC classification

### Neighborhood Intelligence
- **Demographic Profiling**: Population, income, education, age distribution within configurable radius
- **Housing Characteristics**: Home values, rent prices, homeownership rates
- **Economic Indicators**: Employment rates, major employers, economic growth
- **Crime Statistics**: Neighborhood safety and security metrics

### Real Estate Applications
- **Due Diligence Reports**: Comprehensive property analysis for buyers
- **Rental Property Screening**: Tenant history and property condition assessment
- **Market Analysis**: Comparative analysis across multiple addresses
- **Gentrification Analysis**: Neighborhood change indicators and displacement risks
- **Commercial Intelligence**: Business environment and investment potential

## Usage Examples

### Basic Address Validation
```python
from src.agents import AddressSearchAgent

agent = AddressSearchAgent()

# Validate and standardize address
validation = agent.validate_address("123 main st, anytown ny 12345")
print(f"Valid: {validation.is_valid}")
print(f"Standardized: {validation.standardized_address}")
print(f"Quality Score: {validation.quality_score}")
```

### Comprehensive Address Intelligence
```python
from src.models.query import AddressLookupQuery

# Create comprehensive query
query = AddressLookupQuery(
    full_address="123 Main Street, Anytown, NY 12345",
    include_residents=True,
    include_property_data=True,
    include_demographics=True
)

# Get full intelligence report
report = agent.search_comprehensive(query)
print(f"Current residents: {len(report.current_residents)}")
print(f"Property owner: {report.ownership_records[0].current_owner}")
print(f"Confidence: {report.confidence_score}")
```

### Real Estate Due Diligence
```python
from examples.address_search_real_estate_examples import RealEstateIntelligenceService

service = RealEstateIntelligenceService()

# Comprehensive property due diligence
due_diligence = service.property_due_diligence("123 Oak Lane, Suburbia, TX 75001")
print(f"Risk Level: {due_diligence['risk_assessment']['risk_level']}")
print(f"Red Flags: {due_diligence['risk_assessment']['red_flags']}")
```

### Integration with PersonSearchAgent
```python
from src.agents import PersonSearchAgent, AddressSearchAgent

person_agent = PersonSearchAgent()
address_agent = AddressSearchAgent(person_search_agent=person_agent)

# Movement pattern analysis uses PersonSearchAgent for address history
pattern = address_agent.analyze_movement_patterns("John Doe", "123 Main St")
print(f"Stability Score: {pattern.stability_score}")
print(f"Geographic Mobility: {pattern.geographic_mobility}")
```

## Configuration

### Rate Limiting (Address-Optimized)
```python
from src.agents.base_agent import RateLimitConfig

rate_config = RateLimitConfig(
    requests_per_second=0.8,  # Conservative for address searches
    requests_per_minute=40,
    requests_per_hour=800,
    requests_per_day=5000,
    burst_size=4
)

agent = AddressSearchAgent(rate_limit_config=rate_config)
```

### Extended Caching
```python
from src.agents.base_agent import CacheConfig

cache_config = CacheConfig(
    enabled=True,
    ttl_seconds=10800,  # 3 hours (addresses change less frequently)
    max_entries=1000,
    compress=True
)

agent = AddressSearchAgent(cache_config=cache_config)
```

## API Endpoints Used

The AddressSearchAgent uses several EnformionGO endpoints:

- `/address-search` - Core address lookup with resident information
- `/property-search` - Property ownership and characteristics
- `/demographics-search` - Neighborhood demographic data
- `/address-verification` - Address validation and deliverability
- `/geocode` - Latitude/longitude coordinates

## Response Models

### AddressValidationResult
- `is_valid: bool` - Address passes validation
- `standardized_address: str` - Cleaned, formatted address
- `quality_score: float` - Address completeness score (0-1)
- `validation_errors: List[str]` - Issues found
- `geocode: Dict` - Latitude/longitude if available

### ResidentProfile
- `name: str` - Resident full name
- `age: int` - Age if available
- `phone_numbers: List[str]` - Associated phone numbers
- `email_addresses: List[str]` - Associated email addresses
- `occupancy_period: Dict` - Start/end dates, current status
- `relationship_to_property: str` - Owner, renter, relative, etc.
- `confidence_score: float` - Data reliability (0-1)

### PropertyOwnershipRecord
- `current_owner: str` - Property owner name/entity
- `ownership_type: str` - Individual, corporation, trust, etc.
- `property_details: Dict` - Bedrooms, bathrooms, square footage, etc.
- `tax_assessment: Dict` - Assessed value, annual taxes
- `mortgage_info: Dict` - Loan details if available

### AddressIntelligenceReport
- `validation_result: AddressValidationResult` - Address validation
- `current_residents: List[ResidentProfile]` - Current occupants
- `historical_residents: List[ResidentProfile]` - Previous occupants
- `ownership_records: List[PropertyOwnershipRecord]` - Property ownership
- `demographic_profile: DemographicProfile` - Neighborhood demographics
- `movement_patterns: List[MovementPattern]` - Resident mobility analysis
- `verification_status: Dict` - Deliverability and classification
- `risk_indicators: List[Dict]` - Identified risks and concerns
- `confidence_score: float` - Overall report reliability

## Real Estate Use Cases

### 1. Property Due Diligence
Complete property analysis for home buyers including current occupancy, ownership history, neighborhood characteristics, and risk assessment.

### 2. Rental Property Screening
Landlord tool for property condition assessment, tenant history analysis, and rental market evaluation.

### 3. Market Analysis
Comparative analysis across multiple properties for real estate professionals and investors.

### 4. Gentrification Analysis
Neighborhood change detection including demographic shifts, displacement risks, and investment timing.

### 5. Commercial Real Estate Intelligence
Business environment analysis, market demand assessment, and commercial property evaluation.

## Error Handling

The AddressSearchAgent includes comprehensive error handling:

- **API Failures**: Graceful degradation with partial results
- **Invalid Addresses**: Clear validation feedback and suggestions
- **Rate Limiting**: Automatic retry with exponential backoff
- **Data Quality**: Confidence scoring and missing data handling
- **Timeout Protection**: Configurable timeouts for long-running requests

## Testing

Comprehensive test suite covers:
- Address parsing and validation
- API integration and error handling
- Real-world scenarios (single-family, apartments, commercial)
- Data quality and confidence scoring
- Integration with PersonSearchAgent

Run tests with:
```bash
pytest tests/agents/test_address_search_agent.py -v
```

## Security & Privacy

- **API Credentials**: Secure credential management via APILockerManager
- **Data Minimization**: Configurable data inclusion (residents, demographics)
- **Privacy Compliance**: Resident data limited and confidence-scored
- **Rate Limiting**: Prevents API abuse and quota exhaustion
- **Caching**: Reduces API calls while respecting data freshness

## Dependencies

- `BaseIntelligenceAgent` - Core agent framework
- `EnformionClient` - EnformionGO API integration
- `PersonSearchAgent` - Optional integration for movement analysis
- `AddressLookupQuery` - Query parameter model
- `Address`, `PersonProfile` - Response models

## Performance Characteristics

- **Rate Limits**: 0.8 RPS, 40 RPM, 800 RPH, 5000 RPD
- **Cache TTL**: 3 hours (addresses change infrequently)
- **Timeout**: 60 seconds (comprehensive searches take longer)
- **Batch Support**: Market analysis supports multiple addresses
- **Memory Usage**: Minimal with configurable cache limits

## Future Enhancements

- **School District Integration**: School ratings and district boundaries
- **Crime Data Enhancement**: Real-time crime statistics and trends
- **Zoning Information**: Current zoning and planned developments
- **Environmental Data**: Flood zones, soil conditions, environmental hazards
- **Transportation Access**: Transit routes, walkability scores
- **Historical Trends**: Property value and demographic change over time
