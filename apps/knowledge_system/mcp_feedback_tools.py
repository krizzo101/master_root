#!/usr/bin/env python3
"""
MCP Tools for Learning Feedback Loop

Provides simple tools for tracking knowledge usage and outcomes.
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Optional


class FeedbackSessionTool:
    """
    Start and manage feedback tracking sessions.
    """
    
    @staticmethod
    def start_session(task_description: str, session_id: Optional[str] = None) -> Dict:
        """
        Start a feedback tracking session.
        
        Args:
            task_description: What task is being performed
            session_id: Optional session ID (will generate if not provided)
            
        Returns:
            Cypher query to create session
        """
        if not session_id:
            session_id = hashlib.sha256(
                f"session_{task_description}_{datetime.now(timezone.utc).isoformat()}".encode()
            ).hexdigest()[:16]
        
        query = """
        CREATE (s:UsageSession {
            session_id: $session_id,
            task_description: $task_description,
            started_at: datetime(),
            status: 'active',
            knowledge_used: [],
            outcome: null
        })
        RETURN s.session_id as id
        """
        
        params = {
            "session_id": session_id,
            "task_description": task_description
        }
        
        return {
            "query": query,
            "params": params,
            "session_id": session_id,
            "instruction": "Execute via mcp__db__write_neo4j_cypher"
        }


class FeedbackUsageTool:
    """
    Track knowledge usage within a session.
    """
    
    @staticmethod
    def track_usage(session_id: str, knowledge_id: str, action: str = "applied") -> Dict:
        """
        Track that knowledge was used.
        
        Args:
            session_id: Active session ID
            knowledge_id: Knowledge that was used
            action: How it was used (applied, referenced, tested)
            
        Returns:
            Cypher query to track usage
        """
        query = """
        MATCH (s:UsageSession {session_id: $session_id})
        MATCH (k:Knowledge {knowledge_id: $knowledge_id})
        CREATE (s)-[u:USED_KNOWLEDGE {
            action: $action,
            timestamp: datetime()
        }]->(k)
        SET s.knowledge_used = CASE 
            WHEN $knowledge_id IN s.knowledge_used THEN s.knowledge_used
            ELSE s.knowledge_used + $knowledge_id
        END,
            k.usage_count = COALESCE(k.usage_count, 0) + 1,
            k.last_used = datetime()
        RETURN s.session_id as session_id, k.knowledge_id as knowledge_id
        """
        
        params = {
            "session_id": session_id,
            "knowledge_id": knowledge_id,
            "action": action
        }
        
        return {
            "query": query,
            "params": params,
            "instruction": "Execute via mcp__db__write_neo4j_cypher"
        }


class FeedbackOutcomeTool:
    """
    Record session outcomes and update confidence scores.
    """
    
    @staticmethod
    def record_outcome(session_id: str, success: bool, reason: Optional[str] = None) -> Dict:
        """
        Record the outcome of a session.
        
        Args:
            session_id: Session to complete
            success: Whether the task was successful
            reason: Optional reason for outcome
            
        Returns:
            Cypher queries to update session and knowledge
        """
        # First query: Update session
        session_query = """
        MATCH (s:UsageSession {session_id: $session_id})
        SET s.outcome = $success,
            s.outcome_reason = $reason,
            s.completed_at = datetime(),
            s.status = 'completed'
        RETURN s.session_id as id
        """
        
        # Second query: Update knowledge confidence based on outcome
        if success:
            # Increase confidence for successful usage
            knowledge_query = """
            MATCH (s:UsageSession {session_id: $session_id})-[:USED_KNOWLEDGE]->(k:Knowledge)
            SET k.success_count = COALESCE(k.success_count, 0) + 1,
                k.success_rate = CASE 
                    WHEN COALESCE(k.usage_count, 0) > 0 
                    THEN (COALESCE(k.success_count, 0) + 1.0) / k.usage_count
                    ELSE 1.0
                END,
                k.confidence_score = CASE
                    WHEN k.success_rate > 0.8 AND k.usage_count > 5
                    THEN CASE 
                        WHEN k.confidence_score + 0.02 > 1.0 THEN 1.0
                        ELSE k.confidence_score + 0.02
                    END
                    WHEN k.success_rate > 0.6
                    THEN CASE 
                        WHEN k.confidence_score + 0.01 > 1.0 THEN 1.0
                        ELSE k.confidence_score + 0.01
                    END
                    ELSE k.confidence_score
                END,
                k.last_success = datetime()
            RETURN count(k) as updated_count
            """
        else:
            # Decrease confidence for failed usage
            knowledge_query = """
            MATCH (s:UsageSession {session_id: $session_id})-[:USED_KNOWLEDGE]->(k:Knowledge)
            SET k.failure_count = COALESCE(k.failure_count, 0) + 1,
                k.success_rate = CASE 
                    WHEN COALESCE(k.usage_count, 0) > 0 
                    THEN COALESCE(k.success_count, 0) * 1.0 / k.usage_count
                    ELSE 0.0
                END,
                k.confidence_score = CASE
                    WHEN k.confidence_score - 0.05 < 0.1 THEN 0.1
                    ELSE k.confidence_score - 0.05
                END,
                k.last_failure = datetime(),
                k.last_failure_reason = $reason
            RETURN count(k) as updated_count
            """
        
        params = {
            "session_id": session_id,
            "success": success,
            "reason": reason
        }
        
        return {
            "session_query": session_query,
            "knowledge_query": knowledge_query,
            "params": params,
            "instruction": "Execute both queries via mcp__db__write_neo4j_cypher",
            "note": "Run session_query first, then knowledge_query"
        }


class FeedbackInsightsTool:
    """
    Get learning insights and patterns.
    """
    
    @staticmethod
    def get_insights(insight_type: str = "summary") -> Dict:
        """
        Get learning insights.
        
        Args:
            insight_type: Type of insights (summary, successful, problematic, recent)
            
        Returns:
            Cypher query for insights
        """
        if insight_type == "successful":
            # Most successful knowledge
            query = """
            MATCH (k:Knowledge)
            WHERE k.usage_count > 0 AND k.success_rate > 0.7
            RETURN k.knowledge_id as id,
                   k.knowledge_type as type,
                   k.content as content,
                   k.success_rate as success_rate,
                   k.usage_count as usage_count,
                   k.confidence_score as confidence
            ORDER BY k.success_rate DESC, k.usage_count DESC
            LIMIT 10
            """
            
        elif insight_type == "problematic":
            # Knowledge that often fails
            query = """
            MATCH (k:Knowledge)
            WHERE k.failure_count > 0 AND k.success_rate < 0.5
            RETURN k.knowledge_id as id,
                   k.knowledge_type as type,
                   k.content as content,
                   k.success_rate as success_rate,
                   k.failure_count as failures,
                   k.last_failure_reason as last_failure
            ORDER BY k.failure_count DESC
            LIMIT 10
            """
            
        elif insight_type == "recent":
            # Recently used knowledge
            query = """
            MATCH (k:Knowledge)
            WHERE k.last_used IS NOT NULL
            RETURN k.knowledge_id as id,
                   k.knowledge_type as type,
                   k.content as content,
                   k.usage_count as usage_count,
                   k.success_rate as success_rate,
                   k.last_used as last_used
            ORDER BY k.last_used DESC
            LIMIT 10
            """
            
        else:  # summary
            # Overall learning statistics
            query = """
            MATCH (k:Knowledge)
            WITH count(k) as total_knowledge,
                 sum(k.usage_count) as total_usage,
                 avg(k.confidence_score) as avg_confidence,
                 sum(CASE WHEN k.embedding IS NOT NULL THEN 1 ELSE 0 END) as with_embeddings
            MATCH (s:UsageSession)
            WHERE s.status = 'completed'
            WITH total_knowledge, total_usage, avg_confidence, with_embeddings,
                 count(s) as total_sessions,
                 sum(CASE WHEN s.outcome = true THEN 1 ELSE 0 END) as successful_sessions
            RETURN total_knowledge,
                   total_usage,
                   avg_confidence,
                   with_embeddings,
                   total_sessions,
                   successful_sessions,
                   CASE 
                       WHEN total_sessions > 0 
                       THEN successful_sessions * 1.0 / total_sessions
                       ELSE 0.0
                   END as overall_success_rate
            """
        
        return {
            "query": query,
            "params": {},
            "insight_type": insight_type,
            "instruction": "Execute via mcp__db__read_neo4j_cypher"
        }


if __name__ == "__main__":
    # Test the feedback tools
    print("Testing Feedback MCP Tools")
    print("-" * 50)
    
    # Test session creation
    print("\n1️⃣ Testing session creation...")
    result = FeedbackSessionTool.start_session("Test task for feedback loop")
    print(f"Session ID: {result['session_id']}")
    
    # Test usage tracking
    print("\n2️⃣ Testing usage tracking...")
    result = FeedbackUsageTool.track_usage(
        session_id=result['session_id'],
        knowledge_id="test_knowledge_001",
        action="applied"
    )
    print(f"Query keys: {list(result.keys())}")
    
    # Test outcome recording
    print("\n3️⃣ Testing outcome recording...")
    result = FeedbackOutcomeTool.record_outcome(
        session_id=result['session_id'],
        success=True,
        reason="Successfully completed test task"
    )
    print(f"Has session query: {'session_query' in result}")
    print(f"Has knowledge query: {'knowledge_query' in result}")
    
    # Test insights
    print("\n4️⃣ Testing insights...")
    result = FeedbackInsightsTool.get_insights("summary")
    print(f"Insight type: {result['insight_type']}")
    
    print("\n✅ Feedback tools ready!")