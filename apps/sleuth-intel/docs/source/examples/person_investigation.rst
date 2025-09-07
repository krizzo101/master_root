====================
Person Investigation
====================

This guide demonstrates various person investigation scenarios using Sleuth Intel.

Basic Person Search
===================

Simple Name Search
------------------

.. code-block:: python

   from sleuth_intel.agents import PersonSearchAgent

   # Create agent
   agent = PersonSearchAgent()

   # Search by name
   results = agent.search({
       "first_name": "John",
       "last_name": "Doe"
   })

   # Process results
   for person in results:
       print(f"Name: {person['full_name']}")
       print(f"Age: {person.get('age', 'Unknown')}")
       print(f"Location: {person.get('current_address', 'Unknown')}")
       print("-" * 40)

Advanced Search Parameters
--------------------------

.. code-block:: python

   # Search with additional parameters
   detailed_results = agent.search({
       "first_name": "John",
       "middle_name": "Michael",
       "last_name": "Doe",
       "date_of_birth": "1980-01-15",
       "city": "New York",
       "state": "NY",
       "zip_code": "10001"
   })

   # More accurate results with additional parameters
   if detailed_results:
       person = detailed_results[0]
       print(f"Confidence Score: {person['confidence_score']}")

Comprehensive Background Check
===============================

Full Investigation Workflow
---------------------------

.. code-block:: python

   from sleuth_intel import InvestigationOrchestrator
   from sleuth_intel.agents import (
       PersonSearchAgent,
       PhoneSearchAgent,
       EmailSearchAgent,
       AddressSearchAgent,
       SocialMediaAgent,
       CourtRecordsAgent,
       FinancialAgent
   )

   def comprehensive_person_investigation(name, location=None):
       """Run comprehensive investigation on a person"""

       orchestrator = InvestigationOrchestrator()

       # Phase 1: Basic Information
       person_agent = PersonSearchAgent()
       person_data = person_agent.search({
           "name": name,
           "location": location
       })

       if not person_data:
           return {"error": "Person not found"}

       subject = person_data[0]
       investigation_results = {"person": subject}

       # Phase 2: Contact Information
       if phone_numbers := subject.get("phone_numbers"):
           phone_agent = PhoneSearchAgent()
           phone_results = []
           for phone in phone_numbers:
               phone_info = phone_agent.lookup(phone)
               phone_results.append(phone_info)
           investigation_results["phones"] = phone_results

       # Phase 3: Email Verification
       if emails := subject.get("email_addresses"):
           email_agent = EmailSearchAgent()
           email_results = []
           for email in emails:
               email_info = email_agent.verify(email)
               email_results.append(email_info)
           investigation_results["emails"] = email_results

       # Phase 4: Address History
       address_agent = AddressSearchAgent()
       addresses = address_agent.get_history(subject["id"])
       investigation_results["address_history"] = addresses

       # Phase 5: Social Media Presence
       social_agent = SocialMediaAgent()
       social_profiles = social_agent.find_profiles({
           "name": subject["full_name"],
           "email": emails[0] if emails else None
       })
       investigation_results["social_media"] = social_profiles

       # Phase 6: Court Records
       court_agent = CourtRecordsAgent()
       court_records = court_agent.search({
           "name": subject["full_name"],
           "date_of_birth": subject.get("date_of_birth")
       })
       investigation_results["court_records"] = court_records

       # Phase 7: Financial Information
       financial_agent = FinancialAgent()
       financial_data = financial_agent.search_public_records({
           "name": subject["full_name"],
           "ssn_last_four": subject.get("ssn_last_four")
       })
       investigation_results["financial"] = financial_data

       return investigation_results

   # Run investigation
   results = comprehensive_person_investigation(
       name="John Doe",
       location="New York, NY"
   )

Identity Verification
=====================

Multi-Source Verification
-------------------------

.. code-block:: python

   from sleuth_intel.verification import IdentityVerifier

   def verify_identity(claimed_identity, supporting_docs):
       """Verify person's identity using multiple sources"""

       verifier = IdentityVerifier()

       # Step 1: Document verification
       doc_verification = verifier.verify_documents(supporting_docs)

       # Step 2: Database cross-reference
       db_verification = verifier.cross_reference({
           "name": claimed_identity["name"],
           "dob": claimed_identity["date_of_birth"],
           "ssn": claimed_identity["ssn_last_four"]
       })

       # Step 3: Biometric verification (if available)
       biometric_verification = None
       if claimed_identity.get("photo"):
           biometric_verification = verifier.facial_recognition(
               claimed_identity["photo"]
           )

       # Calculate confidence score
       confidence_score = calculate_confidence(
           doc_verification,
           db_verification,
           biometric_verification
       )

       return {
           "verified": confidence_score > 0.85,
           "confidence_score": confidence_score,
           "verification_details": {
               "documents": doc_verification,
               "database": db_verification,
               "biometric": biometric_verification
           }
       }

   def calculate_confidence(*verifications):
       """Calculate overall confidence score"""
       scores = []
       weights = []

       for verification in verifications:
           if verification:
               scores.append(verification["score"])
               weights.append(verification["weight"])

       if not scores:
           return 0.0

       weighted_sum = sum(s * w for s, w in zip(scores, weights))
       total_weight = sum(weights)

       return weighted_sum / total_weight if total_weight > 0 else 0.0

Relationship Mapping
====================

Finding Connected Individuals
-----------------------------

.. code-block:: python

   from sleuth_intel.analysis import RelationshipMapper

   def map_relationships(person_id):
       """Map all relationships for a person"""

       mapper = RelationshipMapper()

       # Get direct relationships
       direct_relations = mapper.get_direct_relations(person_id)

       # Build relationship network
       network = {
           "person_id": person_id,
           "family": [],
           "associates": [],
           "business": [],
           "neighbors": []
       }

       for relation in direct_relations:
           relationship_type = relation["type"]

           if relationship_type in ["spouse", "child", "parent", "sibling"]:
               network["family"].append(relation)
           elif relationship_type in ["business_partner", "employer", "employee"]:
               network["business"].append(relation)
           elif relationship_type == "neighbor":
               network["neighbors"].append(relation)
           else:
               network["associates"].append(relation)

       # Get secondary relationships (2nd degree)
       for category in ["family", "associates"]:
           for person in network[category]:
               secondary = mapper.get_direct_relations(person["id"])
               person["connections"] = secondary[:5]  # Limit to 5

       return network

   # Example usage
   relationships = map_relationships("person_123456")

   # Visualize relationships
   print(f"Family Members: {len(relationships['family'])}")
   print(f"Business Associates: {len(relationships['business'])}")
   print(f"Known Associates: {len(relationships['associates'])}")

Risk Assessment
===============

Person Risk Scoring
-------------------

.. code-block:: python

   from sleuth_intel.risk import RiskAssessment

   def assess_person_risk(person_data):
       """Calculate risk score for a person"""

       risk_assessor = RiskAssessment()
       risk_factors = []

       # Check criminal history
       if person_data.get("court_records"):
           criminal_score = risk_assessor.evaluate_criminal_history(
               person_data["court_records"]
           )
           risk_factors.append({
               "category": "criminal",
               "score": criminal_score,
               "weight": 0.3
           })

       # Check financial issues
       if person_data.get("financial"):
           financial_score = risk_assessor.evaluate_financial_risk(
               person_data["financial"]
           )
           risk_factors.append({
               "category": "financial",
               "score": financial_score,
               "weight": 0.25
           })

       # Check identity consistency
       identity_score = risk_assessor.evaluate_identity_consistency(
           person_data
       )
       risk_factors.append({
           "category": "identity",
           "score": identity_score,
           "weight": 0.2
       })

       # Check social media behavior
       if person_data.get("social_media"):
           social_score = risk_assessor.evaluate_social_media(
               person_data["social_media"]
           )
           risk_factors.append({
               "category": "social",
               "score": social_score,
               "weight": 0.15
           })

       # Check address stability
       if person_data.get("address_history"):
           stability_score = risk_assessor.evaluate_stability(
               person_data["address_history"]
           )
           risk_factors.append({
               "category": "stability",
               "score": stability_score,
               "weight": 0.1
           })

       # Calculate overall risk score
       total_score = sum(
           factor["score"] * factor["weight"]
           for factor in risk_factors
       )

       return {
           "overall_risk_score": total_score,
           "risk_level": get_risk_level(total_score),
           "risk_factors": risk_factors,
           "recommendations": generate_recommendations(risk_factors)
       }

   def get_risk_level(score):
       """Convert score to risk level"""
       if score < 3:
           return "LOW"
       elif score < 6:
           return "MEDIUM"
       elif score < 8:
           return "HIGH"
       else:
           return "CRITICAL"

   def generate_recommendations(risk_factors):
       """Generate recommendations based on risk factors"""
       recommendations = []

       for factor in risk_factors:
           if factor["score"] > 7:
               if factor["category"] == "criminal":
                   recommendations.append("Conduct detailed criminal background check")
               elif factor["category"] == "financial":
                   recommendations.append("Verify financial statements")
               elif factor["category"] == "identity":
                   recommendations.append("Request additional identity verification")

       return recommendations

Historical Analysis
===================

Timeline Reconstruction
-----------------------

.. code-block:: python

   from sleuth_intel.analysis import TimelineBuilder
   from datetime import datetime

   def build_person_timeline(person_id):
       """Reconstruct person's historical timeline"""

       builder = TimelineBuilder()
       timeline = []

       # Get all data sources
       person_data = get_person_data(person_id)

       # Add birth event
       if dob := person_data.get("date_of_birth"):
           timeline.append({
               "date": dob,
               "event": "Birth",
               "type": "personal",
               "location": person_data.get("birth_place")
           })

       # Add address changes
       for address in person_data.get("address_history", []):
           timeline.append({
               "date": address["move_in_date"],
               "event": f"Moved to {address['address']}",
               "type": "residence",
               "location": address["address"]
           })

       # Add employment history
       for job in person_data.get("employment_history", []):
           timeline.append({
               "date": job["start_date"],
               "event": f"Started working at {job['company']}",
               "type": "employment",
               "location": job.get("location")
           })

           if job.get("end_date"):
               timeline.append({
                   "date": job["end_date"],
                   "event": f"Left {job['company']}",
                   "type": "employment",
                   "location": job.get("location")
               })

       # Add court events
       for case in person_data.get("court_records", []):
           timeline.append({
               "date": case["file_date"],
               "event": f"Court case: {case['case_type']}",
               "type": "legal",
               "details": case["case_number"]
           })

       # Add marriage/divorce
       for event in person_data.get("marriage_records", []):
           timeline.append({
               "date": event["date"],
               "event": event["type"],
               "type": "personal",
               "details": event.get("spouse_name")
           })

       # Sort timeline by date
       timeline.sort(key=lambda x: x["date"])

       return timeline

   # Generate timeline
   timeline = build_person_timeline("person_123456")

   # Display timeline
   for event in timeline:
       print(f"{event['date']}: {event['event']}")
       if event.get('details'):
           print(f"  Details: {event['details']}")

Monitoring and Alerts
=====================

Continuous Monitoring
---------------------

.. code-block:: python

   from sleuth_intel.monitoring import PersonMonitor
   import asyncio

   class PersonMonitoringService:
       def __init__(self):
           self.monitor = PersonMonitor()
           self.alerts = []

       async def monitor_person(self, person_id, criteria):
           """Monitor person for changes"""

           # Set up monitoring
           await self.monitor.add_subject(person_id, criteria)

           # Define alert handlers
           @self.monitor.on("address_change")
           async def handle_address_change(event):
               self.alerts.append({
                   "type": "address_change",
                   "person_id": person_id,
                   "old_address": event["old_address"],
                   "new_address": event["new_address"],
                   "timestamp": event["timestamp"]
               })

           @self.monitor.on("new_court_record")
           async def handle_court_record(event):
               self.alerts.append({
                   "type": "court_record",
                   "person_id": person_id,
                   "case_type": event["case_type"],
                   "case_number": event["case_number"],
                   "timestamp": event["timestamp"]
               })

           @self.monitor.on("employment_change")
           async def handle_employment(event):
               self.alerts.append({
                   "type": "employment_change",
                   "person_id": person_id,
                   "change": event["change_type"],
                   "details": event["details"],
                   "timestamp": event["timestamp"]
               })

           # Start monitoring
           await self.monitor.start()

       async def get_alerts(self):
           """Get all alerts"""
           return self.alerts

       async def stop_monitoring(self):
           """Stop monitoring"""
           await self.monitor.stop()

   # Example usage
   async def main():
       service = PersonMonitoringService()

       # Start monitoring
       await service.monitor_person(
           person_id="person_123456",
           criteria={
               "check_interval": 3600,  # Check every hour
               "alert_on": ["address", "court", "employment"],
               "notification_webhook": "https://example.com/webhook"
           }
       )

       # Run for 24 hours
       await asyncio.sleep(86400)

       # Get alerts
       alerts = await service.get_alerts()
       print(f"Generated {len(alerts)} alerts")

       # Stop monitoring
       await service.stop_monitoring()

   # Run monitoring
   asyncio.run(main())
