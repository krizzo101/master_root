"""
Analysis Workflow Examples for Sleuth Intel AnalysisAgent
Demonstrates various analysis scenarios and use cases
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from src.agents.analysis_agent import AnalysisAgent
from src.models.business import BusinessLocation, BusinessProfile, Principal
from src.models.intelligence import ConfidenceLevel
from src.models.person import (
    Address,
    Demographics,
    Email,
    PersonName,
    PersonProfile,
    Phone,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalysisWorkflowExamples:
    """
    Example workflows demonstrating AnalysisAgent capabilities
    """

    def __init__(self):
        self.analysis_agent = AnalysisAgent()

    async def comprehensive_person_analysis_workflow(self) -> None:
        """
        Comprehensive person analysis workflow example
        Demonstrates full intelligence analysis for a person of interest
        """
        print("\n" + "=" * 60)
        print("COMPREHENSIVE PERSON ANALYSIS WORKFLOW")
        print("=" * 60)

        # Sample person data (normally from multiple intelligence sources)
        person_data = [
            # Person profile data
            {
                "type": "person_profile",
                "name": {"first": "John", "last": "Smith", "middle": "A"},
                "demographics": {"age": 45, "gender": "M"},
                "phones": [
                    {
                        "number": "+1-555-123-4567",
                        "type": "mobile",
                        "first_seen": "2023-01-15",
                    },
                    {
                        "number": "+1-555-987-6543",
                        "type": "landline",
                        "first_seen": "2020-03-20",
                    },
                ],
                "emails": [
                    {
                        "address": "john.smith@email.com",
                        "type": "personal",
                        "first_seen": "2021-06-10",
                    },
                    {
                        "address": "j.smith@company.com",
                        "type": "business",
                        "first_seen": "2022-01-01",
                    },
                ],
                "addresses": [
                    {
                        "street": "123 Main St",
                        "city": "New York",
                        "state": "NY",
                        "postal_code": "10001",
                        "type": "residential",
                        "first_seen": "2020-01-01",
                        "last_seen": "2024-01-01",
                    }
                ],
                "source": "data_enrichment_agent",
                "confidence": 0.9,
            },
            # Financial activity data
            {
                "type": "financial_activity",
                "entity_id": "john_smith_001",
                "activities": [
                    {
                        "date": "2024-01-15",
                        "type": "large_cash_deposit",
                        "amount": 15000,
                        "location": "Bank of NY, Times Square",
                        "flags": ["unusual_amount", "cash_transaction"],
                    },
                    {
                        "date": "2024-01-20",
                        "type": "wire_transfer",
                        "amount": 50000,
                        "destination": "Cayman Islands",
                        "flags": ["high_risk_jurisdiction", "large_amount"],
                    },
                ],
                "source": "financial_intelligence",
                "confidence": 0.85,
            },
            # Travel data
            {
                "type": "travel_records",
                "entity_id": "john_smith_001",
                "travels": [
                    {
                        "date": "2024-01-10",
                        "origin": "JFK, NY",
                        "destination": "Grand Cayman, KY",
                        "purpose": "business",
                        "duration_days": 3,
                    },
                    {
                        "date": "2024-02-15",
                        "origin": "JFK, NY",
                        "destination": "Zurich, CH",
                        "purpose": "business",
                        "duration_days": 2,
                    },
                ],
                "source": "travel_records",
                "confidence": 0.95,
            },
            # Communication data
            {
                "type": "communication_patterns",
                "entity_id": "john_smith_001",
                "patterns": [
                    {
                        "contact": "+1-555-999-8888",
                        "contact_type": "unknown",
                        "frequency": 45,
                        "last_contact": "2024-01-25",
                        "duration_avg_minutes": 15,
                        "times_of_day": ["22:00-02:00", "05:00-07:00"],  # Unusual hours
                        "flags": ["high_frequency", "unusual_hours", "unknown_contact"],
                    }
                ],
                "source": "communication_intelligence",
                "confidence": 0.8,
            },
            # Business associations
            {
                "type": "business_associations",
                "entity_id": "john_smith_001",
                "associations": [
                    {
                        "business_name": "Smith Consulting LLC",
                        "role": "owner",
                        "ownership_percentage": 100,
                        "incorporation_date": "2023-01-01",
                        "jurisdiction": "Delaware",
                        "business_type": "consulting",
                        "annual_revenue": 2000000,
                    },
                    {
                        "business_name": "Offshore Holdings Inc",
                        "role": "beneficial_owner",
                        "ownership_percentage": 80,
                        "incorporation_date": "2023-06-15",
                        "jurisdiction": "Cayman Islands",
                        "business_type": "investment_holding",
                        "flags": ["offshore", "high_risk_jurisdiction"],
                    },
                ],
                "source": "corporate_records",
                "confidence": 0.88,
            },
        ]

        # Execute comprehensive analysis
        analysis_params = {
            "analysis_type": "comprehensive_person",
            "data": person_data,
            "focus_areas": ["risk", "patterns", "network", "timeline", "behavior"],
            "risk_threshold": 0.6,
            "include_predictions": True,
        }

        print("Executing comprehensive analysis...")
        report = self.analysis_agent.query(analysis_params)

        # Display results
        print(f"\nAnalysis Report ID: {report.report_id}")
        print(f"Analysis Type: {report.analysis_type}")
        print(f"Timestamp: {report.timestamp}")

        print(f"\nExecutive Summary:")
        print(report.executive_summary)

        print(f"\nKey Findings ({len(report.key_findings)}):")
        for i, finding in enumerate(report.key_findings, 1):
            print(f"  {i}. {finding}")

        print(f"\nRisk Recommendations ({len(report.risk_recommendations)}):")
        for i, rec in enumerate(report.risk_recommendations, 1):
            print(f"  {i}. {rec}")

        print(
            f"\nOverall Confidence: {report.confidence_assessment.overall_score:.2f} ({report.confidence_assessment.level})"
        )

        # Display detailed analysis results
        if report.risk_assessment and not report.risk_assessment.get("error"):
            print(f"\nRisk Assessment:")
            print(
                f"  Overall Risk Score: {report.risk_assessment.get('overall_risk_score', 0):.2f}"
            )
            print(
                f"  Risk Level: {report.risk_assessment.get('risk_level', 'UNKNOWN')}"
            )
            print(
                f"  Risk Factors: {len(report.risk_assessment.get('risk_factors', []))}"
            )

        if report.pattern_analysis and not report.pattern_analysis.get("error"):
            print(f"\nPattern Analysis:")
            pattern_summary = report.pattern_analysis.get("pattern_summary", {})
            print(f"  Patterns Detected: {pattern_summary.get('total_patterns', 0)}")
            print(f"  Anomalies Found: {pattern_summary.get('anomalies_detected', 0)}")

        if report.network_analysis and not report.network_analysis.get("error"):
            print(f"\nNetwork Analysis:")
            network_metrics = report.network_analysis.get("network_metrics", {})
            print(f"  Entities: {network_metrics.get('node_count', 0)}")
            print(f"  Relationships: {network_metrics.get('edge_count', 0)}")
            print(f"  Network Density: {network_metrics.get('density', 0):.3f}")

        print(f"\nProcessing Metrics:")
        metrics = report.processing_metrics
        print(f"  Processing Time: {metrics.get('processing_time_seconds', 0):.2f}s")
        print(f"  Data Points Analyzed: {metrics.get('data_points_analyzed', 0)}")
        print(f"  Analysis Components: {metrics.get('analysis_components', 0)}")

    async def fraud_detection_workflow(self) -> None:
        """
        Fraud detection workflow example
        Focuses on identifying potential fraudulent activity patterns
        """
        print("\n" + "=" * 60)
        print("FRAUD DETECTION ANALYSIS WORKFLOW")
        print("=" * 60)

        # Sample fraud-related data
        fraud_data = [
            {
                "type": "transaction_data",
                "entity_id": "suspect_001",
                "transactions": [
                    {
                        "date": "2024-01-01",
                        "amount": 9900,  # Just under reporting threshold
                        "type": "cash_deposit",
                        "location": "Bank A, Location 1",
                        "time": "14:30",
                    },
                    {
                        "date": "2024-01-01",
                        "amount": 9800,  # Just under reporting threshold
                        "type": "cash_deposit",
                        "location": "Bank B, Location 2",
                        "time": "16:45",
                    },
                    {
                        "date": "2024-01-02",
                        "amount": 9950,  # Just under reporting threshold
                        "type": "cash_deposit",
                        "location": "Bank C, Location 3",
                        "time": "10:15",
                    },
                ],
                "flags": [
                    "structuring_pattern",
                    "multiple_locations",
                    "consecutive_days",
                ],
                "source": "transaction_monitoring",
                "confidence": 0.92,
            },
            {
                "type": "identity_verification",
                "entity_id": "suspect_001",
                "verification_attempts": [
                    {
                        "date": "2023-12-15",
                        "result": "failed",
                        "reason": "document_mismatch",
                        "document_type": "drivers_license",
                    },
                    {
                        "date": "2023-12-20",
                        "result": "failed",
                        "reason": "photo_mismatch",
                        "document_type": "passport",
                    },
                    {
                        "date": "2024-01-05",
                        "result": "passed",
                        "reason": "manual_override",
                        "document_type": "state_id",
                        "notes": "Document appeared altered",
                    },
                ],
                "flags": ["multiple_failures", "manual_override", "document_concerns"],
                "source": "kyc_system",
                "confidence": 0.95,
            },
            {
                "type": "device_fingerprinting",
                "entity_id": "suspect_001",
                "devices": [
                    {
                        "device_id": "dev_001",
                        "first_seen": "2024-01-01",
                        "ip_addresses": ["192.168.1.1", "10.0.0.1", "172.16.0.1"],
                        "locations": ["New York, NY", "Miami, FL", "Los Angeles, CA"],
                        "user_agents": ["Chrome/Win", "Safari/iOS", "Firefox/Linux"],
                        "flags": ["multiple_ips", "impossible_travel", "os_spoofing"],
                    }
                ],
                "source": "device_intelligence",
                "confidence": 0.87,
            },
        ]

        # Execute fraud-focused analysis
        analysis_params = {
            "analysis_type": "fraud_detection",
            "data": fraud_data,
            "focus_areas": ["risk", "patterns", "timeline"],
            "risk_threshold": 0.5,  # Lower threshold for fraud detection
            "pattern_types": ["structuring", "identity_fraud", "device_fraud"],
            "include_ml_scoring": True,
        }

        print("Executing fraud detection analysis...")
        report = self.analysis_agent.query(analysis_params)

        # Display fraud-specific results
        print(f"\nFraud Analysis Results:")
        print(f"Report ID: {report.report_id}")
        print(f"Executive Summary: {report.executive_summary}")

        if report.risk_assessment and not report.risk_assessment.get("error"):
            risk_score = report.risk_assessment.get("overall_risk_score", 0)
            risk_level = report.risk_assessment.get("risk_level", "UNKNOWN")
            print(f"\nFraud Risk Score: {risk_score:.2f} ({risk_level})")

            # Show specific fraud risk factors
            risk_factors = report.risk_assessment.get("risk_factors", [])
            fraud_factors = [
                rf
                for rf in risk_factors
                if "fraud" in rf.get("factor_type", "").lower()
            ]

            print(f"Fraud-Specific Risk Factors ({len(fraud_factors)}):")
            for factor in fraud_factors:
                print(
                    f"  - {factor.get('description', 'N/A')} (Risk: {factor.get('risk_level', 0):.2f})"
                )

        print(f"\nRecommended Actions:")
        for rec in report.risk_recommendations:
            print(f"  • {rec}")

    async def network_analysis_workflow(self) -> None:
        """
        Network analysis workflow example
        Demonstrates relationship mapping and social network analysis
        """
        print("\n" + "=" * 60)
        print("NETWORK ANALYSIS WORKFLOW")
        print("=" * 60)

        # Sample network data representing connections between entities
        network_data = [
            {
                "type": "entity_relationships",
                "relationships": [
                    {
                        "source": "person_001",
                        "source_type": "person",
                        "source_name": "John Smith",
                        "target": "business_001",
                        "target_type": "business",
                        "target_name": "ABC Corp",
                        "relationship_type": "director",
                        "strength": 0.9,
                        "first_observed": "2020-01-01",
                        "last_observed": "2024-01-01",
                        "evidence": ["corporate_filing", "sec_records"],
                        "frequency": 1,
                    },
                    {
                        "source": "person_001",
                        "target": "person_002",
                        "target_name": "Jane Doe",
                        "relationship_type": "business_partner",
                        "strength": 0.8,
                        "first_observed": "2021-06-15",
                        "last_observed": "2024-01-15",
                        "evidence": ["joint_ventures", "shared_addresses"],
                        "frequency": 12,
                    },
                    {
                        "source": "person_002",
                        "target": "business_002",
                        "target_name": "XYZ Holdings",
                        "relationship_type": "beneficial_owner",
                        "strength": 0.95,
                        "first_observed": "2022-01-01",
                        "last_observed": "2024-02-01",
                        "evidence": ["ownership_records", "banking_records"],
                        "frequency": 1,
                    },
                    {
                        "source": "business_002",
                        "target": "business_003",
                        "target_name": "Offshore LLC",
                        "relationship_type": "subsidiary",
                        "strength": 1.0,
                        "first_observed": "2022-03-15",
                        "last_observed": "2024-02-01",
                        "evidence": ["corporate_structure", "financial_records"],
                        "frequency": 1,
                        "flags": ["offshore", "complex_structure"],
                    },
                    {
                        "source": "person_001",
                        "target": "location_001",
                        "target_type": "location",
                        "target_name": "123 Suspicious St, Miami FL",
                        "relationship_type": "frequent_visitor",
                        "strength": 0.7,
                        "first_observed": "2023-01-01",
                        "last_observed": "2024-01-30",
                        "evidence": ["location_intelligence", "surveillance"],
                        "frequency": 25,
                        "flags": ["high_frequency", "known_risk_location"],
                    },
                ],
                "source": "relationship_intelligence",
                "confidence": 0.88,
            },
            {
                "type": "communication_network",
                "entity_id": "person_001",
                "communications": [
                    {
                        "contact": "person_002",
                        "contact_name": "Jane Doe",
                        "method": "phone",
                        "frequency": 150,
                        "duration_total_minutes": 2250,
                        "last_contact": "2024-01-25",
                        "pattern": "regular_business_hours",
                    },
                    {
                        "contact": "person_003",
                        "contact_name": "Unknown Contact",
                        "method": "encrypted_messaging",
                        "frequency": 85,
                        "last_contact": "2024-01-30",
                        "pattern": "unusual_hours",
                        "flags": ["encrypted", "unknown_identity", "suspicious_timing"],
                    },
                ],
                "source": "communication_analysis",
                "confidence": 0.82,
            },
        ]

        # Execute network analysis
        analysis_params = {
            "analysis_type": "network_analysis",
            "data": network_data,
            "focus_areas": ["network"],
            "network_algorithms": [
                "centrality",
                "community_detection",
                "path_analysis",
            ],
            "include_visualizations": True,
            "suspicious_connection_threshold": 0.6,
        }

        print("Executing network analysis...")
        report = self.analysis_agent.query(analysis_params)

        # Display network analysis results
        if report.network_analysis and not report.network_analysis.get("error"):
            print(f"\nNetwork Analysis Results:")

            network_metrics = report.network_analysis.get("network_metrics", {})
            print(
                f"Network Size: {network_metrics.get('node_count', 0)} entities, {network_metrics.get('edge_count', 0)} relationships"
            )
            print(f"Network Density: {network_metrics.get('density', 0):.3f}")
            print(
                f"Connected Components: {network_metrics.get('connected_components', 0)}"
            )

            # Show influential entities
            influential_entities = report.network_analysis.get(
                "influential_entities", []
            )
            if influential_entities:
                print(f"\nMost Influential Entities:")
                for entity in influential_entities[:5]:  # Top 5
                    print(
                        f"  - {entity.get('entity_name', 'Unknown')} (Influence Score: {entity.get('influence_score', 0):.3f})"
                    )

            # Show suspicious connections
            suspicious_connections = report.network_analysis.get(
                "suspicious_connections", []
            )
            if suspicious_connections:
                print(f"\nSuspicious Connections ({len(suspicious_connections)}):")
                for connection in suspicious_connections[:3]:  # Top 3
                    print(
                        f"  - {connection.get('description', 'Unknown connection')} (Risk: {connection.get('risk_score', 0):.2f})"
                    )

            # Show detected communities
            communities = report.network_analysis.get("community_detection", [])
            if communities:
                print(f"\nDetected Communities: {len(communities)}")
                for i, community in enumerate(communities, 1):
                    print(
                        f"  Community {i}: {community.get('size', 0)} members, Cohesion: {community.get('cohesion', 0):.3f}"
                    )

        print(f"\nNetwork Analysis Insights:")
        for finding in report.key_findings:
            if (
                "network" in finding.lower()
                or "relationship" in finding.lower()
                or "connection" in finding.lower()
            ):
                print(f"  • {finding}")

    async def behavioral_analysis_workflow(self) -> None:
        """
        Behavioral analysis workflow example
        Demonstrates behavioral pattern detection and prediction
        """
        print("\n" + "=" * 60)
        print("BEHAVIORAL ANALYSIS WORKFLOW")
        print("=" * 60)

        # Sample behavioral data
        behavioral_data = [
            {
                "type": "activity_patterns",
                "entity_id": "subject_001",
                "activities": [
                    {
                        "activity_type": "login",
                        "timestamp": "2024-01-01T09:15:00Z",
                        "location": "New York, NY",
                        "device": "laptop_001",
                        "duration_minutes": 45,
                    },
                    {
                        "activity_type": "transaction",
                        "timestamp": "2024-01-01T14:30:00Z",
                        "location": "New York, NY",
                        "amount": 5000,
                        "transaction_type": "wire_transfer",
                    },
                    {
                        "activity_type": "login",
                        "timestamp": "2024-01-02T09:18:00Z",
                        "location": "New York, NY",
                        "device": "laptop_001",
                        "duration_minutes": 42,
                    },
                    {
                        "activity_type": "login",
                        "timestamp": "2024-01-03T03:45:00Z",  # Unusual time
                        "location": "Miami, FL",  # Different location
                        "device": "mobile_001",
                        "duration_minutes": 5,  # Very short session
                        "flags": ["unusual_time", "location_change", "short_session"],
                    },
                    {
                        "activity_type": "transaction",
                        "timestamp": "2024-01-03T04:00:00Z",
                        "location": "Miami, FL",
                        "amount": 25000,  # Much larger amount
                        "transaction_type": "cash_withdrawal",
                        "flags": ["unusual_time", "large_amount", "location_change"],
                    },
                ],
                "source": "activity_monitoring",
                "confidence": 0.91,
            },
            {
                "type": "communication_behavior",
                "entity_id": "subject_001",
                "communication_patterns": [
                    {
                        "time_period": "weekdays_9_to_5",
                        "frequency": 25,
                        "contact_types": ["business", "known"],
                        "duration_avg": 12,
                        "sentiment": "professional",
                    },
                    {
                        "time_period": "late_night_weekend",
                        "frequency": 8,  # Unusual for this person
                        "contact_types": ["unknown", "encrypted"],
                        "duration_avg": 3,  # Very short
                        "sentiment": "cautious",
                        "flags": [
                            "unusual_timing",
                            "unknown_contacts",
                            "short_duration",
                        ],
                    },
                ],
                "source": "communication_intelligence",
                "confidence": 0.85,
            },
        ]

        # Execute behavioral analysis
        analysis_params = {
            "analysis_type": "behavioral_analysis",
            "data": behavioral_data,
            "focus_areas": ["behavior", "patterns", "timeline"],
            "behavioral_models": [
                "activity_clustering",
                "anomaly_detection",
                "trend_prediction",
            ],
            "lookback_days": 90,
            "prediction_horizon_days": 30,
        }

        print("Executing behavioral analysis...")
        report = self.analysis_agent.query(analysis_params)

        # Display behavioral analysis results
        if report.behavioral_analysis and not report.behavioral_analysis.get("error"):
            print(f"\nBehavioral Analysis Results:")

            behavioral_summary = report.behavioral_analysis.get(
                "behavioral_summary", {}
            )
            print(f"Patterns Identified: {behavioral_summary.get('total_patterns', 0)}")
            print(
                f"Anomalies Detected: {behavioral_summary.get('anomalies_detected', 0)}"
            )
            print(
                f"High-Risk Behaviors: {behavioral_summary.get('high_risk_behaviors', 0)}"
            )
            print(
                f"Behavior Stability: {behavioral_summary.get('behavior_stability', 0):.2f}"
            )
            print(
                f"Prediction Confidence: {behavioral_summary.get('prediction_confidence', 0):.2f}"
            )

            # Show behavioral patterns
            patterns = report.behavioral_analysis.get("patterns", [])
            if patterns:
                print(f"\nKey Behavioral Patterns:")
                for pattern in patterns[:3]:  # Top 3
                    print(
                        f"  - {pattern.get('pattern_name', 'Unknown')}: {pattern.get('description', 'N/A')}"
                    )
                    print(f"    Strength: {pattern.get('pattern_strength', 0):.2f}")

            # Show risk behaviors
            risk_behaviors = report.behavioral_analysis.get("risk_behaviors", [])
            if risk_behaviors:
                print(f"\nRisk Behaviors ({len(risk_behaviors)}):")
                for behavior in risk_behaviors:
                    print(
                        f"  - {behavior.get('behavior_type', 'Unknown')} (Risk Level: {behavior.get('risk_level', 0):.2f})"
                    )

            # Show predictions
            predictions = report.behavioral_analysis.get("trend_predictions", [])
            if predictions:
                print(f"\nBehavioral Predictions:")
                for prediction in predictions[:3]:  # Top 3
                    print(
                        f"  - {prediction.get('prediction', 'Unknown')} (Confidence: {prediction.get('confidence', 0):.2f})"
                    )

    async def run_all_workflows(self) -> None:
        """Run all workflow examples"""
        print("SLEUTH INTEL ANALYSIS AGENT - WORKFLOW EXAMPLES")
        print("=" * 60)

        workflows = [
            (
                "Comprehensive Person Analysis",
                self.comprehensive_person_analysis_workflow,
            ),
            ("Fraud Detection Analysis", self.fraud_detection_workflow),
            ("Network Relationship Analysis", self.network_analysis_workflow),
            ("Behavioral Pattern Analysis", self.behavioral_analysis_workflow),
        ]

        for workflow_name, workflow_func in workflows:
            try:
                await workflow_func()
                print(f"\n✓ {workflow_name} completed successfully")
            except Exception as e:
                print(f"\n✗ {workflow_name} failed: {str(e)}")
                logger.exception(f"Workflow {workflow_name} failed")

        print("\n" + "=" * 60)
        print("ALL ANALYSIS WORKFLOWS COMPLETED")
        print("=" * 60)


# Standalone functions for specific analysis scenarios


def quick_risk_assessment(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Quick risk assessment for a single entity

    Args:
        data: Entity data for risk assessment

    Returns:
        Risk assessment results
    """
    analysis_agent = AnalysisAgent()

    analysis_params = {
        "analysis_type": "quick_risk",
        "data": data,
        "focus_areas": ["risk"],
        "risk_threshold": 0.5,
    }

    report = analysis_agent.query(analysis_params)

    return {
        "overall_risk_score": report.risk_assessment.get("overall_risk_score", 0),
        "risk_level": report.risk_assessment.get("risk_level", "UNKNOWN"),
        "key_findings": report.key_findings,
        "recommendations": report.risk_recommendations,
        "confidence": report.confidence_assessment.overall_score,
    }


def detect_entity_patterns(
    data: List[Dict[str, Any]], pattern_types: List[str] = None
) -> Dict[str, Any]:
    """
    Detect specific patterns in entity data

    Args:
        data: Entity data for pattern detection
        pattern_types: Specific pattern types to look for

    Returns:
        Pattern detection results
    """
    analysis_agent = AnalysisAgent()

    analysis_params = {
        "analysis_type": "pattern_detection",
        "data": data,
        "focus_areas": ["patterns"],
        "pattern_types": pattern_types or ["temporal", "geographic", "communication"],
    }

    report = analysis_agent.query(analysis_params)

    return {
        "patterns_detected": len(report.pattern_analysis.get("patterns", [])),
        "anomalies_found": len(report.pattern_analysis.get("anomalies", [])),
        "patterns": report.pattern_analysis.get("patterns", []),
        "pattern_summary": report.pattern_analysis.get("pattern_summary", {}),
        "confidence": report.confidence_assessment.overall_score,
    }


def analyze_entity_network(
    data: List[Dict[str, Any]], focus_entity: str = None
) -> Dict[str, Any]:
    """
    Analyze network relationships for entities

    Args:
        data: Network relationship data
        focus_entity: Specific entity to focus analysis on

    Returns:
        Network analysis results
    """
    analysis_agent = AnalysisAgent()

    analysis_params = {
        "analysis_type": "network_analysis",
        "data": data,
        "focus_areas": ["network"],
        "focus_entity": focus_entity,
        "network_algorithms": ["centrality", "community_detection"],
    }

    report = analysis_agent.query(analysis_params)

    return {
        "network_size": {
            "entities": report.network_analysis.get("network_metrics", {}).get(
                "node_count", 0
            ),
            "relationships": report.network_analysis.get("network_metrics", {}).get(
                "edge_count", 0
            ),
        },
        "influential_entities": report.network_analysis.get("influential_entities", []),
        "suspicious_connections": report.network_analysis.get(
            "suspicious_connections", []
        ),
        "communities": report.network_analysis.get("community_detection", []),
        "confidence": report.confidence_assessment.overall_score,
    }


if __name__ == "__main__":
    """
    Run workflow examples when script is executed directly
    """
    examples = AnalysisWorkflowExamples()
    asyncio.run(examples.run_all_workflows())
