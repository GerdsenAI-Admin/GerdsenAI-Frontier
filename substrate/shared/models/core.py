"""
Core data models for Substrate

These models are shared across all layers (local, cloud, web) and define
the fundamental data structures for coordination and transparency.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Set
from uuid import uuid4


class PrivacyLevel(Enum):
    """Privacy levels for data sharing"""
    PUBLIC = "public"              # Anyone can see
    NETWORK = "network"            # Only matched collaborators
    PRIVATE = "private"            # Never leaves device
    CONFIDENTIAL = "confidential"  # Encrypted even locally


class CapabilityType(Enum):
    """Types of capabilities"""
    SKILL = "skill"                # Technical expertise
    RESOURCE = "resource"          # Physical resources (equipment, space)
    KNOWLEDGE = "knowledge"        # Domain knowledge
    NETWORK = "network"            # Connections and access
    TIME = "time"                  # Availability
    FUNDING = "funding"            # Financial resources


class ProblemDomain(Enum):
    """Problem domains for matching"""
    ROBOTICS = "robotics"
    RESEARCH = "research"
    SOFTWARE = "software"
    HARDWARE = "hardware"
    BIOLOGY = "biology"
    CLIMATE = "climate"
    HEALTH = "health"
    EDUCATION = "education"
    MANUFACTURING = "manufacturing"
    OTHER = "other"


@dataclass
class Capability:
    """A capability that someone possesses"""
    capability_id: str = field(default_factory=lambda: str(uuid4()))
    type: CapabilityType = CapabilityType.SKILL
    name: str = ""
    description: str = ""
    proficiency: float = 0.5  # 0.0 to 1.0
    confidence: float = 0.8   # How confident are we in this assessment?
    evidence: List[str] = field(default_factory=list)  # Supporting evidence
    privacy_level: PrivacyLevel = PrivacyLevel.NETWORK
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_shareable_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for sharing (respecting privacy)"""
        if self.privacy_level in [PrivacyLevel.PRIVATE, PrivacyLevel.CONFIDENTIAL]:
            return {}  # Don't share private data

        return {
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "proficiency": self.proficiency,
            "tags": list(self.tags)
        }


@dataclass
class Need:
    """A need that someone has"""
    need_id: str = field(default_factory=lambda: str(uuid4()))
    type: CapabilityType = CapabilityType.SKILL
    name: str = ""
    description: str = ""
    urgency: float = 0.5  # 0.0 (can wait) to 1.0 (urgent)
    importance: float = 0.5  # 0.0 (nice to have) to 1.0 (critical)
    domain: ProblemDomain = ProblemDomain.OTHER
    context: str = ""
    constraints: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "need_id": self.need_id,
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "urgency": self.urgency,
            "importance": self.importance,
            "domain": self.domain.value,
            "context": self.context,
            "constraints": self.constraints,
            "tags": list(self.tags)
        }


@dataclass
class UserProfile:
    """Anonymous user profile for matching"""
    user_id: str = field(default_factory=lambda: str(uuid4()))
    capabilities: List[Capability] = field(default_factory=list)
    needs: List[Need] = field(default_factory=list)
    domains: Set[ProblemDomain] = field(default_factory=set)
    location_region: Optional[str] = None  # Coarse location (country/region)
    timezone: Optional[str] = None
    availability: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_shareable_profile(self) -> Dict[str, Any]:
        """Generate privacy-preserving profile for matching"""
        return {
            "user_id": self.user_id,  # Anonymous ID
            "capabilities": [c.to_shareable_dict() for c in self.capabilities
                           if c.privacy_level != PrivacyLevel.PRIVATE],
            "needs": [n.to_dict() for n in self.needs],
            "domains": [d.value for d in self.domains],
            "location_region": self.location_region,
            "timezone": self.timezone,
        }


@dataclass
class ProvenanceStep:
    """A single step in the reasoning process"""
    step_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    operation: str = ""  # What operation was performed
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""  # Why was this done
    confidence: float = 1.0
    alternatives_considered: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "timestamp": self.timestamp.isoformat(),
            "operation": self.operation,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "alternatives_considered": self.alternatives_considered
        }


@dataclass
class ProvenanceGraph:
    """Complete provenance for a decision"""
    graph_id: str = field(default_factory=lambda: str(uuid4()))
    decision_type: str = ""  # e.g., "capability_match", "team_optimization"
    steps: List[ProvenanceStep] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_step(self, step: ProvenanceStep):
        """Add a reasoning step"""
        self.steps.append(step)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "decision_type": self.decision_type,
            "steps": [step.to_dict() for step in self.steps],
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }

    def get_summary(self) -> str:
        """Human-readable summary of the reasoning"""
        summary = f"Decision: {self.decision_type}\n"
        summary += f"Steps taken: {len(self.steps)}\n\n"
        for i, step in enumerate(self.steps, 1):
            summary += f"{i}. {step.operation}\n"
            summary += f"   Reasoning: {step.reasoning}\n"
            summary += f"   Confidence: {step.confidence:.2f}\n"
            if step.alternatives_considered:
                summary += f"   Alternatives considered: {len(step.alternatives_considered)}\n"
            summary += "\n"
        return summary


@dataclass
class Match:
    """A match between a need and a capability"""
    match_id: str = field(default_factory=lambda: str(uuid4()))
    need: Need = None
    need_user_id: str = ""
    capability: Capability = None
    capability_user_id: str = ""

    # Match quality metrics
    match_score: float = 0.0  # 0.0 to 1.0
    complementarity_score: float = 0.0
    feasibility_score: float = 0.0

    # Transparency
    provenance: ProvenanceGraph = field(default_factory=ProvenanceGraph)
    confidence: float = 0.0
    uncertainty_factors: List[str] = field(default_factory=list)

    # Evidence
    evidence: List[str] = field(default_factory=list)
    similar_past_matches: List[str] = field(default_factory=list)

    # Verification
    verification_methods: List[str] = field(default_factory=list)

    created_at: datetime = field(default_factory=datetime.now)

    def get_explanation(self) -> Dict[str, Any]:
        """Generate complete explanation for this match"""
        return {
            "match_id": self.match_id,
            "match_score": self.match_score,
            "confidence": self.confidence,
            "reasoning": self.provenance.get_summary(),
            "evidence": self.evidence,
            "uncertainty_factors": self.uncertainty_factors,
            "verification_methods": self.verification_methods,
            "complementarity": {
                "score": self.complementarity_score,
                "explanation": "How well the capabilities complement each other"
            },
            "feasibility": {
                "score": self.feasibility_score,
                "explanation": "How practical is this collaboration"
            },
            "similar_past_matches": self.similar_past_matches
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "match_id": self.match_id,
            "need": self.need.to_dict() if self.need else None,
            "capability": self.capability.to_shareable_dict() if self.capability else None,
            "match_score": self.match_score,
            "confidence": self.confidence,
            "explanation": self.get_explanation(),
            "created_at": self.created_at.isoformat()
        }


@dataclass
class Team:
    """A proposed team composition"""
    team_id: str = field(default_factory=lambda: str(uuid4()))
    problem_description: str = ""
    members: List[str] = field(default_factory=list)  # User IDs
    roles: Dict[str, str] = field(default_factory=dict)  # user_id -> role

    # Team metrics
    complementarity_score: float = 0.0
    diversity_score: float = 0.0
    feasibility_score: float = 0.0
    predicted_success_probability: float = 0.0

    # Transparency
    provenance: ProvenanceGraph = field(default_factory=ProvenanceGraph)
    confidence_interval: tuple = (0.0, 1.0)
    risk_factors: List[str] = field(default_factory=list)

    # Simulation results
    estimated_timeline: Optional[str] = None
    estimated_cost: Optional[float] = None
    required_resources: Dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=datetime.now)

    def get_explanation(self) -> Dict[str, Any]:
        """Generate complete explanation for this team composition"""
        return {
            "team_id": self.team_id,
            "predicted_success": {
                "probability": self.predicted_success_probability,
                "confidence_interval": self.confidence_interval,
                "explanation": self.provenance.get_summary()
            },
            "complementarity": {
                "score": self.complementarity_score,
                "explanation": "How well team members' skills complement each other"
            },
            "diversity": {
                "score": self.diversity_score,
                "explanation": "Diversity in perspectives and approaches"
            },
            "feasibility": {
                "score": self.feasibility_score,
                "explanation": "How practical is this team composition"
            },
            "risk_factors": self.risk_factors,
            "resources": {
                "timeline": self.estimated_timeline,
                "cost": self.estimated_cost,
                "required": self.required_resources
            }
        }


@dataclass
class CollaborationOutcome:
    """Track actual outcomes for learning"""
    outcome_id: str = field(default_factory=lambda: str(uuid4()))
    match_id: Optional[str] = None
    team_id: Optional[str] = None

    # What happened
    success: bool = False
    completion_date: Optional[datetime] = None
    actual_timeline: Optional[str] = None
    actual_cost: Optional[float] = None

    # Impact metrics
    problem_solved: bool = False
    knowledge_created: List[str] = field(default_factory=list)  # Papers, patents, etc.
    artifacts_produced: List[str] = field(default_factory=list)  # Products, code, etc.

    # Learning
    what_worked: List[str] = field(default_factory=list)
    what_didnt: List[str] = field(default_factory=list)
    lessons_learned: str = ""

    # Reputation impact
    participant_ratings: Dict[str, float] = field(default_factory=dict)

    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outcome_id": self.outcome_id,
            "match_id": self.match_id,
            "team_id": self.team_id,
            "success": self.success,
            "problem_solved": self.problem_solved,
            "impact": {
                "knowledge_created": self.knowledge_created,
                "artifacts_produced": self.artifacts_produced
            },
            "learning": {
                "what_worked": self.what_worked,
                "what_didnt": self.what_didnt,
                "lessons": self.lessons_learned
            },
            "timeline": {
                "predicted": None,  # Would link back to original prediction
                "actual": self.actual_timeline
            }
        }
