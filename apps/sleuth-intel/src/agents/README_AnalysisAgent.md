# AnalysisAgent

The AnalysisAgent provides advanced intelligence analysis capabilities for the Sleuth Intel system, offering comprehensive pattern recognition, risk assessment, relationship network analysis, and behavioral analysis.

## Features

### Core Analysis Capabilities
- **Multi-dimensional Pattern Recognition**: Detect temporal, geographic, communication, identity, and business patterns
- **Risk Assessment & Scoring**: Comprehensive risk evaluation with confidence-weighted scoring
- **Network Relationship Analysis**: Social and business network mapping with centrality analysis
- **Timeline Reconstruction**: Event sequencing and temporal pattern analysis
- **Behavioral Pattern Analysis**: Activity pattern detection and behavioral anomaly identification

### Specialized Analysis Functions
- **Identity Verification Confidence**: Assess identity verification reliability
- **Fraud Risk Assessment**: Detect potential fraudulent activity patterns
- **Social Network Analysis**: Map and analyze entity relationships
- **Geographic Pattern Analysis**: Location-based pattern recognition
- **Communication Pattern Analysis**: Communication behavior analysis

### Advanced Analytics
- **Statistical Analysis**: Correlation analysis and significance testing
- **Anomaly Detection**: Statistical outlier identification
- **Predictive Scoring Models**: Risk prediction and trend forecasting
- **Data Correlation**: Cross-source data correlation and validation

## Usage

### Basic Analysis
```python
from src.agents import AnalysisAgent

# Initialize agent
agent = AnalysisAgent()

# Basic risk assessment
analysis_params = {
    'analysis_type': 'risk_assessment',
    'data': [your_data],
    'focus_areas': ['risk']
}

report = agent.query(analysis_params)
print(f"Risk Score: {report.risk_assessment['overall_risk_score']}")
```

### Comprehensive Analysis
```python
# Full intelligence analysis
analysis_params = {
    'analysis_type': 'comprehensive',
    'data': intelligence_data,
    'focus_areas': ['risk', 'patterns', 'network', 'timeline', 'behavior'],
    'risk_threshold': 0.7
}

report = agent.query(analysis_params)

# Access results
print("Executive Summary:", report.executive_summary)
print("Key Findings:", report.key_findings)
print("Risk Recommendations:", report.risk_recommendations)
```

### Fraud Detection
```python
# Fraud-focused analysis
fraud_params = {
    'analysis_type': 'fraud_detection',
    'data': transaction_data,
    'focus_areas': ['risk', 'patterns', 'timeline'],
    'pattern_types': ['structuring', 'identity_fraud', 'device_fraud']
}

fraud_report = agent.query(fraud_params)
```

### Network Analysis
```python
# Relationship network analysis
network_params = {
    'analysis_type': 'network_analysis',
    'data': relationship_data,
    'focus_areas': ['network'],
    'network_algorithms': ['centrality', 'community_detection']
}

network_report = agent.query(network_params)
```

## Analysis Report Structure

The AnalysisAgent returns comprehensive AnalysisReport objects containing:

### Core Analysis Results
- `risk_assessment`: Risk factors, scores, and classifications
- `pattern_analysis`: Detected patterns, anomalies, and correlations
- `network_analysis`: Network metrics, influential nodes, communities
- `timeline_analysis`: Event reconstruction, temporal patterns, gaps
- `behavioral_analysis`: Behavioral patterns, anomalies, predictions

### Summary & Insights
- `executive_summary`: High-level analysis summary
- `key_findings`: Critical findings requiring attention
- `risk_recommendations`: Risk mitigation recommendations
- `confidence_assessment`: Overall analysis confidence scoring

### Supporting Data
- `data_sources`: Attribution and quality metadata
- `processing_metrics`: Performance and coverage metrics
- `visualizations`: Generated charts and graphs (when enabled)

## Configuration Options

### Analysis Focus Areas
- `risk`: Risk assessment and scoring
- `patterns`: Pattern recognition and correlation
- `network`: Relationship network analysis
- `timeline`: Temporal reconstruction and analysis
- `behavior`: Behavioral pattern analysis

### Risk Assessment Parameters
- `risk_threshold`: Minimum risk score threshold (default: 0.7)
- `confidence_threshold`: Analysis confidence threshold
- `risk_categories`: Specific risk categories to evaluate

### Pattern Analysis Parameters
- `pattern_significance_threshold`: Statistical significance threshold
- `pattern_types`: Specific pattern types to detect
- `anomaly_threshold`: Statistical deviation threshold for anomalies

### Network Analysis Parameters
- `network_edge_threshold`: Minimum relationship strength
- `network_algorithms`: Specific algorithms to apply
- `suspicious_connection_threshold`: Threshold for flagging connections

## Data Input Formats

The AnalysisAgent accepts various data formats:

### Person Profile Data
```python
{
    "type": "person_profile",
    "name": {"first": "John", "last": "Smith"},
    "demographics": {"age": 35, "gender": "M"},
    "phones": [{"number": "+1-555-123-4567", "type": "mobile"}],
    "emails": [{"address": "john@example.com", "type": "personal"}],
    "addresses": [{"street": "123 Main St", "city": "New York"}],
    "source": "data_source",
    "confidence": 0.9
}
```

### Financial Activity Data
```python
{
    "type": "financial_activity",
    "entity_id": "person_001",
    "activities": [
        {
            "date": "2024-01-15",
            "type": "large_cash_deposit",
            "amount": 15000,
            "location": "Bank Branch",
            "flags": ["unusual_amount", "cash_transaction"]
        }
    ],
    "source": "financial_intelligence",
    "confidence": 0.85
}
```

### Network Relationship Data
```python
{
    "type": "entity_relationships",
    "relationships": [
        {
            "source": "person_001",
            "target": "business_001",
            "relationship_type": "director",
            "strength": 0.9,
            "evidence": ["corporate_filing"],
            "first_observed": "2020-01-01"
        }
    ],
    "source": "relationship_intelligence",
    "confidence": 0.88
}
```

## Performance Considerations

- **Large Datasets**: Optimized for datasets up to 10,000 entities
- **Concurrent Analysis**: Thread-safe for multiple simultaneous analyses
- **Memory Usage**: Efficient caching and data structures
- **Processing Time**: Typical analysis completes within 5-30 seconds

## Error Handling

The AnalysisAgent provides robust error handling:
- Individual analysis components can fail without affecting others
- Errors are captured in component results with descriptive messages
- Analysis continues with available data when components fail
- Confidence scores reflect analysis completeness

## Examples

See `examples/analysis_workflows.py` for comprehensive workflow examples including:
- Comprehensive person analysis
- Fraud detection workflows
- Network relationship analysis
- Behavioral pattern analysis

## Testing

Run the test suite:
```bash
python -m pytest tests/test_analysis_agent.py -v
```

Test categories:
- **Unit Tests**: Core functionality testing
- **Integration Tests**: Realistic scenario testing
- **Performance Tests**: Large dataset and concurrent analysis testing

## Dependencies

Required packages:
- `numpy`: Numerical computing
- `scipy`: Statistical analysis
- `networkx`: Network analysis
- `scikit-learn`: Machine learning algorithms
- `matplotlib`: Visualization generation
- `seaborn`: Statistical visualization

## Inheritance

The AnalysisAgent inherits from `BaseIntelligenceAgent`, providing:
- Secure credential management
- Rate limiting and retry logic
- Response caching
- Performance metrics
- Health monitoring

## Future Enhancements

Planned improvements:
- Machine learning model integration
- Real-time streaming analysis
- Advanced visualization options
- Custom analysis plugins
- API integration capabilities
