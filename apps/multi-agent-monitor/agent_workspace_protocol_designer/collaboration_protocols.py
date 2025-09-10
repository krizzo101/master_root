"""
Collaboration Protocols
Structured patterns for agent cooperation
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from interfaces import ICollaborationProtocol, Message, MessageType


class CollaborationStatus(Enum):
    """Status of collaboration activities"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Review:
    """Peer review data structure"""

    review_id: str
    artifact: Dict[str, Any]
    author: str
    reviewers: List[str]
    reviews: Dict[str, Dict] = field(default_factory=dict)
    status: CollaborationStatus = CollaborationStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TaskHandoff:
    """Task handoff data structure"""

    handoff_id: str
    task: Dict[str, Any]
    from_agent: str
    to_agent: str
    reason: str
    status: CollaborationStatus = CollaborationStatus.PENDING
    handoff_time: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Proposal:
    """Decision proposal structure"""

    proposal_id: str
    proposer: str
    title: str
    description: str
    options: List[str]
    votes: Dict[str, str] = field(default_factory=dict)
    status: CollaborationStatus = CollaborationStatus.PENDING
    deadline: Optional[datetime] = None


class CollaborationProtocols(ICollaborationProtocol):
    """Implementation of agent collaboration patterns"""

    def __init__(self, message_bus):
        self.message_bus = message_bus
        self.active_reviews: Dict[str, Review] = {}
        self.active_handoffs: Dict[str, TaskHandoff] = {}
        self.active_proposals: Dict[str, Proposal] = {}

    async def request_review(self, artifact: Dict, reviewers: List[str]) -> str:
        """Initiate peer review process"""
        review_id = str(uuid.uuid4())

        review = Review(
            review_id=review_id,
            artifact=artifact,
            author=artifact.get("author", "unknown"),
            reviewers=reviewers,
        )

        self.active_reviews[review_id] = review

        # Send review requests
        for reviewer in reviewers:
            message = Message(
                id=str(uuid.uuid4()),
                type=MessageType.REQUEST,
                sender="system",
                recipient=reviewer,
                topic="peer_review",
                content={
                    "review_id": review_id,
                    "artifact": artifact,
                    "action": "review_requested",
                },
                timestamp=datetime.utcnow(),
                correlation_id=review_id,
                priority=7,
            )

            await self.message_bus.send_message(message)

        review.status = CollaborationStatus.IN_PROGRESS
        return review_id

    async def submit_review(self, review_id: str, reviewer: str, feedback: Dict):
        """Submit review feedback"""
        if review_id not in self.active_reviews:
            return False

        review = self.active_reviews[review_id]
        review.reviews[reviewer] = {
            "feedback": feedback,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Check if all reviews are complete
        if len(review.reviews) >= len(review.reviewers):
            review.status = CollaborationStatus.COMPLETED

            # Notify author
            message = Message(
                id=str(uuid.uuid4()),
                type=MessageType.NOTIFICATION,
                sender="system",
                recipient=review.author,
                topic="peer_review",
                content={
                    "review_id": review_id,
                    "status": "completed",
                    "reviews": review.reviews,
                },
                timestamp=datetime.utcnow(),
                correlation_id=review_id,
            )

            await self.message_bus.send_message(message)

        return True

    async def handoff_task(self, task: Dict, from_agent: str, to_agent: str) -> bool:
        """Transfer task ownership between agents"""
        handoff_id = str(uuid.uuid4())

        handoff = TaskHandoff(
            handoff_id=handoff_id,
            task=task,
            from_agent=from_agent,
            to_agent=to_agent,
            reason=task.get("handoff_reason", "Task transfer"),
        )

        self.active_handoffs[handoff_id] = handoff

        # Notify receiving agent
        message = Message(
            id=str(uuid.uuid4()),
            type=MessageType.REQUEST,
            sender=from_agent,
            recipient=to_agent,
            topic="task_handoff",
            content={
                "handoff_id": handoff_id,
                "task": task,
                "from_agent": from_agent,
                "reason": handoff.reason,
            },
            timestamp=datetime.utcnow(),
            correlation_id=handoff_id,
            priority=8,
        )

        await self.message_bus.send_message(message)

        handoff.status = CollaborationStatus.IN_PROGRESS
        return True

    async def accept_handoff(self, handoff_id: str) -> bool:
        """Accept a task handoff"""
        if handoff_id not in self.active_handoffs:
            return False

        handoff = self.active_handoffs[handoff_id]
        handoff.status = CollaborationStatus.COMPLETED

        # Notify original agent
        message = Message(
            id=str(uuid.uuid4()),
            type=MessageType.RESPONSE,
            sender=handoff.to_agent,
            recipient=handoff.from_agent,
            topic="task_handoff",
            content={"handoff_id": handoff_id, "status": "accepted"},
            timestamp=datetime.utcnow(),
            correlation_id=handoff_id,
        )

        await self.message_bus.send_message(message)
        return True

    async def create_proposal(
        self,
        proposer: str,
        title: str,
        description: str,
        options: List[str],
        voters: List[str],
        deadline: Optional[datetime] = None,
    ) -> str:
        """Create a proposal for voting"""
        proposal_id = str(uuid.uuid4())

        proposal = Proposal(
            proposal_id=proposal_id,
            proposer=proposer,
            title=title,
            description=description,
            options=options,
            deadline=deadline,
        )

        self.active_proposals[proposal_id] = proposal

        # Notify voters
        for voter in voters:
            message = Message(
                id=str(uuid.uuid4()),
                type=MessageType.REQUEST,
                sender=proposer,
                recipient=voter,
                topic="proposal_vote",
                content={
                    "proposal_id": proposal_id,
                    "title": title,
                    "description": description,
                    "options": options,
                    "deadline": deadline.isoformat() if deadline else None,
                },
                timestamp=datetime.utcnow(),
                correlation_id=proposal_id,
                priority=6,
            )

            await self.message_bus.send_message(message)

        proposal.status = CollaborationStatus.IN_PROGRESS
        return proposal_id

    async def vote_on_proposal(self, proposal_id: str, vote: bool) -> bool:
        """Vote on a proposal"""
        if proposal_id not in self.active_proposals:
            return False

        proposal = self.active_proposals[proposal_id]

        # Record vote (simplified - in reality would track voter ID)
        voter_id = f"voter_{len(proposal.votes)}"
        proposal.votes[voter_id] = "approve" if vote else "reject"

        # Check if voting is complete (simplified logic)
        if len(proposal.votes) >= 3:  # Assuming 3 voters minimum
            approvals = sum(1 for v in proposal.votes.values() if v == "approve")
            proposal.status = (
                CollaborationStatus.COMPLETED
                if approvals > len(proposal.votes) / 2
                else CollaborationStatus.FAILED
            )

            # Notify proposer
            message = Message(
                id=str(uuid.uuid4()),
                type=MessageType.RESPONSE,
                sender="system",
                recipient=proposal.proposer,
                topic="proposal_result",
                content={
                    "proposal_id": proposal_id,
                    "result": proposal.status.value,
                    "votes": proposal.votes,
                },
                timestamp=datetime.utcnow(),
                correlation_id=proposal_id,
            )

            await self.message_bus.send_message(message)

        return True
