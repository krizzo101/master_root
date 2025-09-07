# Sleuth Intel Examples

This directory contains comprehensive examples demonstrating various use cases and integration patterns for the Sleuth Intel library.

## 📋 Prerequisites

Before running these examples, ensure you have:

1. **Installed sleuth-intel**:
   ```bash
   pip install sleuth-intel
   ```

2. **Set required environment variables**:
   ```bash
   export ENFORMION_API_USERNAME="your-username"
   export ENFORMION_API_PASSWORD="your-password"
   ```

3. **Installed optional dependencies** (for specific examples):
   ```bash
   # For webhook integration
   pip install aiohttp fastapi uvicorn

   # For database integration
   pip install sqlalchemy asyncpg psycopg2-binary

   # For reporting integration
   pip install jinja2 reportlab matplotlib
   ```

## 🚀 Basic Usage Examples

Simple, straightforward examples to get you started quickly.

### 1. [Simple Phone Lookup](simple_phone_lookup.py)
Basic phone number verification and owner lookup.
```bash
python simple_phone_lookup.py
```
- Single phone lookup
- Batch phone processing
- Rate limiting examples
- Result caching

### 2. [Person Investigation](person_investigation.py)
Comprehensive person search and data enrichment.
```bash
python person_investigation.py
```
- Multi-source person search
- Contact information gathering
- Relationship mapping
- Risk assessment

### 3. [Business Research](business_research.py)
Business entity verification and analysis.
```bash
python business_research.py
```
- Business entity search
- Officer verification
- Location validation
- Competitor analysis

### 4. [Address Analysis](address_analysis.py)
Property and neighborhood analysis.
```bash
python address_analysis.py
```
- Address standardization
- Property information
- Resident history
- Neighborhood demographics

### 5. [Email Validation](email_validation.py)
Email verification and social profile discovery.
```bash
python email_validation.py
```
- Email deliverability checks
- Disposable email detection
- Social profile mapping
- Campaign list cleaning

## 🔧 Advanced Workflow Examples

Complex, multi-step workflows for sophisticated use cases.

### 1. [Comprehensive Investigation](comprehensive_investigation.py)
Full-scale investigation workflow with evidence chain.
```bash
python comprehensive_investigation.py
```
- 10-phase investigation process
- Evidence chain management
- Risk scoring
- Automated report generation

### 2. [Bulk Processing](bulk_processing.py)
High-volume data processing with parallel execution.
```bash
python bulk_processing.py
```
- CSV batch processing
- Parallel worker pools
- Progress tracking
- Resume capability

### 3. [Real-Time Monitoring](real_time_monitoring.py)
Continuous monitoring with alerting.
```bash
python real_time_monitoring.py
```
- Real-time change detection
- Custom alert conditions
- Multiple monitor types
- Alert handler integration

### 4. [Fraud Detection Workflow](fraud_detection_workflow.py)
Advanced fraud detection and risk assessment.
```bash
python fraud_detection_workflow.py
```
- Identity fraud detection
- Transaction analysis
- Business fraud checks
- Risk scoring algorithms

## 🔌 Integration Examples

Examples showing how to integrate with external systems.

### 1. [Webhook Integration](webhook_integration.py)
Event-driven architecture with webhooks.
```bash
python webhook_integration.py
```
- Webhook sender client
- Webhook receiver server
- Event notifications
- Batch progress updates

### 2. [Database Integration](database_integration.py)
Persistent storage with SQLAlchemy.
```bash
python database_integration.py
```
- Database models
- Async operations
- Batch job management
- Query optimization

### 3. [Reporting Integration](reporting_integration.py)
Generate professional reports in multiple formats.
```bash
python reporting_integration.py
```
- PDF report generation
- HTML templates
- Excel exports
- Data visualization

### 4. [API Server Example](api_server_example.py)
RESTful API server for sleuth-intel.
```bash
python api_server_example.py
```
- FastAPI integration
- Authentication
- Rate limiting
- OpenAPI documentation

## 📚 Use Case Demonstrations

Industry-specific implementations and best practices.

### 1. [Skip Tracing Example](skip_tracing_example.py)
Locate individuals for debt collection or legal purposes.
```bash
python skip_tracing_example.py
```
- Multi-source searching
- Address verification
- Contact discovery
- Confidence scoring

### 2. [KYC Compliance Example](kyc_compliance_example.py)
Know Your Customer compliance workflows.
```bash
python kyc_compliance_example.py
```
- Identity verification
- Sanctions screening
- Risk assessment
- Audit trail

### 3. [Lead Enrichment Example](lead_enrichment_example.py)
Sales and marketing lead enrichment.
```bash
python lead_enrichment_example.py
```
- Contact enrichment
- Company research
- Social profile discovery
- Data quality scoring

### 4. [Due Diligence Example](due_diligence_example.py)
M&A and investment due diligence.
```bash
python due_diligence_example.py
```
- Executive background checks
- Business verification
- Financial analysis
- Risk reporting

## 📊 Expected Output

Each example includes sample output to help you understand what to expect:

### Person Search Output Example
```json
{
  "total_matches": 3,
  "top_match": {
    "name": "John Smith",
    "age": 35,
    "confidence": 95,
    "addresses": 2,
    "phones": 3,
    "emails": 1
  }
}
```

### Phone Verification Output Example
```json
{
  "phone": "555-123-4567",
  "valid": true,
  "type": "mobile",
  "carrier": "Verizon",
  "owner": "John Smith",
  "location": "Los Angeles, CA"
}
```

### Risk Assessment Output Example
```json
{
  "risk_score": 42,
  "risk_level": "MEDIUM",
  "risk_factors": [
    "Recent address changes",
    "Multiple phone numbers",
    "Unverified email"
  ],
  "recommendations": [
    "Request additional verification",
    "Monitor account activity"
  ]
}
```

## 🛠️ Configuration Options

Most examples support configuration through environment variables:

```bash
# API Configuration
export ENFORMION_API_USERNAME="your-username"
export ENFORMION_API_PASSWORD="your-password"
export ENFORMION_API_URL="https://api.enformion.com"  # Optional

# Rate Limiting
export RATE_LIMIT_PER_SECOND=10
export MAX_WORKERS=5

# Database (for database integration)
export DATABASE_URL="postgresql://user:pass@localhost/dbname"

# Webhooks (for webhook integration)
export WEBHOOK_URL="https://your-webhook-endpoint.com"
export WEBHOOK_SECRET="your-webhook-secret"

# Monitoring
export MONITORING_INTERVAL=3600  # seconds
export ALERT_EMAIL="admin@example.com"
```

## 📝 Best Practices

When using these examples in production:

1. **Error Handling**: Always implement proper error handling and retries
2. **Rate Limiting**: Respect API rate limits to avoid throttling
3. **Data Privacy**: Handle personal information according to regulations
4. **Caching**: Implement caching to reduce API calls and costs
5. **Logging**: Use structured logging for debugging and audit trails
6. **Security**: Never commit credentials to version control
7. **Testing**: Test with small datasets before processing large batches
8. **Monitoring**: Implement monitoring and alerting for critical workflows

## 🚨 Important Notes

1. **API Credentials**: These examples require valid Enformion API credentials
2. **Rate Limits**: Be aware of API rate limits and adjust accordingly
3. **Data Usage**: These examples may consume API credits
4. **Test Data**: Use test data when possible to avoid unnecessary costs
5. **Compliance**: Ensure usage complies with applicable laws and regulations

## 📚 Additional Resources

- [Sleuth Intel Documentation](../README.md)
- [API Reference](../docs/API.md)
- [Configuration Guide](../docs/CONFIGURATION.md)
- [Troubleshooting Guide](../docs/TROUBLESHOOTING.md)

## 💡 Contributing

Have an interesting use case or integration example? We welcome contributions!

1. Fork the repository
2. Create your example file
3. Add documentation to this README
4. Submit a pull request

## 📄 License

These examples are provided under the same license as the main sleuth-intel library. See [LICENSE](../LICENSE) for details.

## 🤝 Support

For questions or issues with these examples:
- Open an issue on GitHub
- Contact support@sleuth-intel.com
- Check the [FAQ](../docs/FAQ.md)

---

*Happy investigating! 🔍*
