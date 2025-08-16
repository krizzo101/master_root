#!/usr/bin/env python3
"""
Learning Feedback Loop for Knowledge System

Tracks knowledge usage and outcomes to improve confidence scores and identify
the most valuable knowledge over time.
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from neo4j import GraphDatabase

# Neo4j connection settings
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"


class KnowledgeUsageTracker:
    """
    Tracks when knowledge is retrieved and used.
    Creates a usage session to link knowledge to outcomes.
    """
    
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        
    def start_usage_session(self, session_id: Optional[str] = None) -> str:
        """
        Start a new usage session to track knowledge usage and outcomes.
        
        Args:
            session_id: Optional session ID (will generate if not provided)
            
        Returns:
            Session ID for tracking
        """
        if not session_id:
            session_id = hashlib.sha256(
                f"session_{datetime.now(timezone.utc).isoformat()}".encode()
            ).hexdigest()[:16]
        
        with self.driver.session() as session:
            session.run("""
                CREATE (s:UsageSession {
                    session_id: $session_id,
                    started_at: datetime(),
                    status: 'active',
                    knowledge_used: [],
                    outcome: null
                })
            """, session_id=session_id)
        
        return session_id
    
    def track_knowledge_usage(self, session_id: str, knowledge_id: str, action: str = "retrieved"):
        """
        Track that a piece of knowledge was used in a session.
        
        Args:
            session_id: The active session ID
            knowledge_id: The knowledge entry that was used
            action: How the knowledge was used (retrieved, applied, referenced)
        """
        with self.driver.session() as session:
            # Create relationship between session and knowledge
            session.run("""
                MATCH (s:UsageSession {session_id: $session_id})
                MATCH (k:Knowledge {knowledge_id: $knowledge_id})
                CREATE (s)-[u:USED_KNOWLEDGE {
                    action: $action,
                    timestamp: datetime()
                }]->(k)
                SET s.knowledge_used = s.knowledge_used + $knowledge_id
                SET k.usage_count = k.usage_count + 1
                SET k.last_used = datetime()
            """, session_id=session_id, knowledge_id=knowledge_id, action=action)
    
    def record_outcome(self, session_id: str, success: bool, details: Optional[Dict] = None):
        """
        Record the outcome of a usage session.
        
        Args:
            session_id: The session to record outcome for
            success: Whether the session was successful
            details: Optional details about the outcome
        """
        details_json = json.dumps(details) if details else "{}"
        
        with self.driver.session() as session:
            # Update session with outcome
            session.run("""
                MATCH (s:UsageSession {session_id: $session_id})
                SET s.outcome = $success,
                    s.outcome_details = $details,
                    s.completed_at = datetime(),
                    s.status = 'completed'
            """, session_id=session_id, success=success, details=details_json)
            
            # Update confidence scores for all knowledge used in session
            if success:
                # Increase confidence for knowledge that led to success
                session.run("""
                    MATCH (s:UsageSession {session_id: $session_id})-[:USED_KNOWLEDGE]->(k:Knowledge)
                    SET k.success_count = COALESCE(k.success_count, 0) + 1,
                        k.success_rate = CASE 
                            WHEN k.usage_count > 0 
                            THEN COALESCE(k.success_count, 0) + 1.0 / k.usage_count
                            ELSE 0.0
                        END,
                        k.confidence_score = CASE
                            WHEN k.success_rate > 0.8 AND k.usage_count > 5
                            THEN CASE 
                                WHEN k.confidence_score + 0.02 > 1.0 THEN 1.0
                                ELSE k.confidence_score + 0.02
                            END
                            ELSE k.confidence_score
                        END
                """, session_id=session_id)
            else:
                # Decrease confidence for knowledge that led to failure
                session.run("""
                    MATCH (s:UsageSession {session_id: $session_id})-[:USED_KNOWLEDGE]->(k:Knowledge)
                    SET k.failure_count = COALESCE(k.failure_count, 0) + 1,
                        k.success_rate = CASE 
                            WHEN k.usage_count > 0 
                            THEN COALESCE(k.success_count, 0) * 1.0 / k.usage_count
                            ELSE 0.0
                        END,
                        k.confidence_score = CASE
                            WHEN k.confidence_score - 0.05 < 0.1 THEN 0.1
                            ELSE k.confidence_score - 0.05
                        END
                """, session_id=session_id)
    
    def get_learning_insights(self) -> Dict:
        """
        Get insights about knowledge effectiveness and learning patterns.
        
        Returns:
            Dictionary with learning insights
        """
        insights = {}
        
        with self.driver.session() as session:
            # Most successful knowledge
            result = session.run("""
                MATCH (k:Knowledge)
                WHERE k.usage_count > 0
                RETURN k.knowledge_id as id,
                       k.knowledge_type as type,
                       k.content as content,
                       k.success_rate as success_rate,
                       k.usage_count as usage_count,
                       k.confidence_score as confidence
                ORDER BY k.success_rate DESC, k.usage_count DESC
                LIMIT 5
            """)
            insights['most_successful'] = list(result)
            
            # Most used knowledge
            result = session.run("""
                MATCH (k:Knowledge)
                WHERE k.usage_count > 0
                RETURN k.knowledge_id as id,
                       k.knowledge_type as type,
                       k.content as content,
                       k.usage_count as usage_count,
                       k.success_rate as success_rate
                ORDER BY k.usage_count DESC
                LIMIT 5
            """)
            insights['most_used'] = list(result)
            
            # Knowledge needing improvement
            result = session.run("""
                MATCH (k:Knowledge)
                WHERE k.success_rate < 0.5 AND k.usage_count > 2
                RETURN k.knowledge_id as id,
                       k.knowledge_type as type,
                       k.content as content,
                       k.success_rate as success_rate,
                       k.failure_count as failures
                ORDER BY k.failure_count DESC
                LIMIT 5
            """)
            insights['needs_improvement'] = list(result)
            
            # Learning velocity (new knowledge vs outcomes)
            result = session.run("""
                MATCH (k:Knowledge)
                WHERE k.created_at > datetime() - duration('P7D')
                RETURN count(k) as new_knowledge_week
            """)
            weekly_new = list(result)[0]['new_knowledge_week']
            
            result = session.run("""
                MATCH (s:UsageSession)
                WHERE s.completed_at > datetime() - duration('P7D')
                RETURN count(s) as sessions_week,
                       sum(CASE WHEN s.outcome = true THEN 1 ELSE 0 END) as successful_sessions
            """)
            session_stats = list(result)[0]
            
            insights['learning_velocity'] = {
                'new_knowledge_per_week': weekly_new,
                'sessions_per_week': session_stats['sessions_week'],
                'success_rate': session_stats['successful_sessions'] / max(1, session_stats['sessions_week'])
            }
            
        return insights
    
    def close(self):
        """Close the database connection."""
        self.driver.close()


class FeedbackLoopManager:
    """
    Manages the complete feedback loop lifecycle.
    """
    
    def __init__(self):
        self.tracker = KnowledgeUsageTracker()
        self.active_session = None
    
    def start_task(self, task_description: str) -> str:
        """
        Start tracking a new task.
        
        Args:
            task_description: Description of the task being performed
            
        Returns:
            Session ID for the task
        """
        # Generate session ID from task
        session_id = hashlib.sha256(
            f"task_{task_description}_{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()[:16]
        
        self.active_session = self.tracker.start_usage_session(session_id)
        return self.active_session
    
    def used_knowledge(self, knowledge_id: str, how: str = "applied"):
        """
        Record that knowledge was used in the current task.
        
        Args:
            knowledge_id: The knowledge that was used
            how: How it was used (applied, referenced, etc.)
        """
        if self.active_session:
            self.tracker.track_knowledge_usage(self.active_session, knowledge_id, how)
    
    def task_complete(self, success: bool, reason: Optional[str] = None):
        """
        Mark the current task as complete with outcome.
        
        Args:
            success: Whether the task was successful
            reason: Optional reason for success/failure
        """
        if self.active_session:
            details = {"reason": reason} if reason else None
            self.tracker.record_outcome(self.active_session, success, details)
            self.active_session = None
    
    def get_insights(self) -> Dict:
        """Get current learning insights."""
        return self.tracker.get_learning_insights()
    
    def close(self):
        """Clean up resources."""
        self.tracker.close()


if __name__ == "__main__":
    # Test the feedback loop
    print("Testing Learning Feedback Loop")
    print("-" * 50)
    
    manager = FeedbackLoopManager()
    
    # Simulate a task
    print("\n1️⃣ Starting task tracking...")
    session_id = manager.start_task("Fix Python import error")
    print(f"Session ID: {session_id}")
    
    # Simulate using knowledge
    print("\n2️⃣ Recording knowledge usage...")
    manager.used_knowledge("error_001", "applied")
    manager.used_knowledge("pattern_001", "referenced")
    
    # Record success
    print("\n3️⃣ Recording successful outcome...")
    manager.task_complete(success=True, reason="Import error resolved")
    
    # Get insights
    print("\n4️⃣ Learning insights:")
    insights = manager.get_insights()
    print(f"Learning velocity: {insights.get('learning_velocity', {})}")
    
    manager.close()
    print("\n✅ Feedback loop test complete!")