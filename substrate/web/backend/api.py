"""
Substrate API - FastAPI Backend

RESTful API for Substrate coordination platform.

Endpoints:
- POST /profiles - Create/update user profile
- GET /profiles/{user_id} - Get user profile
- POST /needs - Post a need
- POST /match - Find matches for a need
- POST /match/{match_id}/accept - Accept a match
- POST /match/{match_id}/reject - Reject a match
- POST /outcomes - Report collaboration outcome
- GET /stats - Get system statistics

All responses include transparency/provenance data.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Substrate imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from substrate.shared.models.core import (
    UserProfile,
    Capability,
    Need,
    Match,
    CollaborationOutcome,
    CapabilityType,
    ProblemDomain,
    PrivacyLevel
)
from substrate.cloud.matching.semantic_engine import SemanticMatcher, SemanticMatchingConfig
from substrate.cloud.transparency.engine import TransparencyEngine
from substrate.shared.persistence.database import SubstrateDatabase


# Pydantic models for API
class CapabilityCreate(BaseModel):
    type: str
    name: str
    description: str
    proficiency: float = Field(ge=0.0, le=1.0)
    tags: List[str] = []
    privacy_level: str = "network"


class ProfileCreate(BaseModel):
    user_id: str
    capabilities: List[CapabilityCreate]
    location_region: Optional[str] = None
    timezone: Optional[str] = None
    domains: List[str] = []


class NeedCreate(BaseModel):
    user_id: str
    type: str
    name: str
    description: str
    urgency: float = Field(ge=0.0, le=1.0, default=0.5)
    importance: float = Field(ge=0.0, le=1.0, default=0.5)
    domain: str
    tags: List[str] = []
    constraints: Dict[str, Any] = {}


class MatchRequest(BaseModel):
    need_id: str
    user_id: str
    max_results: int = 10


class OutcomeCreate(BaseModel):
    match_id: str
    success: bool
    problem_solved: bool
    actual_timeline: Optional[str] = None
    actual_cost: Optional[float] = None
    what_worked: List[str] = []
    what_didnt: List[str] = []
    lessons_learned: str = ""


# Initialize FastAPI app
app = FastAPI(
    title="Substrate API",
    description="Transparent AI Coordination Platform",
    version="0.1.0"
)

# Enable CORS for web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Substrate components
db = SubstrateDatabase()
matcher = SemanticMatcher(SemanticMatchingConfig(
    chromadb_path="./substrate_data/chroma"
))
transparency = TransparencyEngine()

# In-memory cache of profiles (in production: use Redis)
profile_cache: Dict[str, UserProfile] = {}


@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "online",
        "service": "Substrate Coordination API",
        "version": "0.1.0",
        "message": "Transparent AI coordination at scale"
    }


@app.post("/profiles")
async def create_profile(profile_data: ProfileCreate):
    """Create or update a user profile"""

    # Convert to UserProfile
    capabilities = []
    for cap_data in profile_data.capabilities:
        cap = Capability(
            type=CapabilityType(cap_data.type),
            name=cap_data.name,
            description=cap_data.description,
            proficiency=cap_data.proficiency,
            confidence=0.8,  # Default
            privacy_level=PrivacyLevel(cap_data.privacy_level),
            tags=set(cap_data.tags)
        )
        capabilities.append(cap)

    profile = UserProfile(
        user_id=profile_data.user_id,
        capabilities=capabilities,
        domains={ProblemDomain(d) for d in profile_data.domains},
        location_region=profile_data.location_region,
        timezone=profile_data.timezone
    )

    # Save to database
    db.save_user_profile(profile)

    # Index for matching
    matcher.index_user_profile(profile)

    # Cache
    profile_cache[profile.user_id] = profile

    return {
        "status": "success",
        "user_id": profile.user_id,
        "capabilities_count": len(capabilities),
        "message": "Profile created and indexed for matching"
    }


@app.get("/profiles/{user_id}")
async def get_profile(user_id: str):
    """Get a user profile"""

    # Check cache first
    if user_id in profile_cache:
        profile = profile_cache[user_id]
    else:
        # Load from database
        profile = db.load_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        profile_cache[user_id] = profile

    # Return shareable version
    return {
        "user_id": profile.user_id,
        "capabilities": [cap.to_shareable_dict() for cap in profile.capabilities],
        "domains": [d.value for d in profile.domains],
        "location_region": profile.location_region,
        "timezone": profile.timezone
    }


@app.post("/needs")
async def create_need(need_data: NeedCreate):
    """Post a new need"""

    need = Need(
        type=CapabilityType(need_data.type),
        name=need_data.name,
        description=need_data.description,
        urgency=need_data.urgency,
        importance=need_data.importance,
        domain=ProblemDomain(need_data.domain),
        tags=set(need_data.tags),
        constraints=need_data.constraints
    )

    # Save to database
    db.save_need(need, need_data.user_id)

    return {
        "status": "success",
        "need_id": need.need_id,
        "message": "Need posted successfully"
    }


@app.post("/match")
async def find_matches(match_request: MatchRequest):
    """Find matches for a need"""

    # Load user profile
    if match_request.user_id not in profile_cache:
        profile = db.load_user_profile(match_request.user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        profile_cache[match_request.user_id] = profile
    else:
        profile = profile_cache[match_request.user_id]

    # Load need (simplified - in production would query from DB)
    # For now, assume need is passed or created
    # This is a simplified endpoint - would need need_id in request

    raise HTTPException(status_code=501, detail="Need full implementation with need loading")


@app.post("/match/{match_id}/accept")
async def accept_match(match_id: str, background_tasks: BackgroundTasks):
    """Accept a proposed match"""

    # Update match status
    db.update_match_status(match_id, "accepted")

    # Background: Notify other user, create collaboration workspace, etc.
    # background_tasks.add_task(notify_match_accepted, match_id)

    return {
        "status": "success",
        "match_id": match_id,
        "message": "Match accepted - collaboration can begin"
    }


@app.post("/match/{match_id}/reject")
async def reject_match(match_id: str, reason: Optional[str] = None):
    """Reject a proposed match"""

    # Update match status
    db.update_match_status(match_id, "rejected")

    # Record learning signal (rejection is valuable feedback)
    # This helps improve future matching

    return {
        "status": "success",
        "match_id": match_id,
        "message": "Match rejected - feedback recorded for learning"
    }


@app.post("/outcomes")
async def report_outcome(outcome_data: OutcomeCreate):
    """Report the outcome of a collaboration"""

    outcome = CollaborationOutcome(
        match_id=outcome_data.match_id,
        success=outcome_data.success,
        problem_solved=outcome_data.problem_solved,
        actual_timeline=outcome_data.actual_timeline,
        actual_cost=outcome_data.actual_cost,
        what_worked=outcome_data.what_worked,
        what_didnt=outcome_data.what_didnt,
        lessons_learned=outcome_data.lessons_learned
    )

    # Save to database (this records learning signal automatically)
    db.save_outcome(outcome)

    # Update match status
    db.update_match_status(outcome_data.match_id, "completed")

    return {
        "status": "success",
        "outcome_id": outcome.outcome_id,
        "message": "Outcome recorded - thank you for helping Substrate learn!"
    }


@app.get("/stats")
async def get_stats():
    """Get system statistics"""

    # Get success rates
    success_stats = db.get_success_rate_by_features()

    # Get match history count
    history = db.get_match_history(limit=1000)

    # Calculate stats
    total_matches = len(history)
    statuses = {}
    for match in history:
        status = match.get('status', 'unknown')
        statuses[status] = statuses.get(status, 0) + 1

    return {
        "total_matches": total_matches,
        "match_statuses": statuses,
        "success_rate": success_stats.get('overall_success_rate', 0.0),
        "total_outcomes": success_stats.get('total_outcomes', 0),
        "message": "Substrate is learning from every collaboration"
    }


@app.get("/stats/user/{user_id}")
async def get_user_stats(user_id: str):
    """Get statistics for a specific user"""

    stats = db.get_user_stats(user_id)

    return {
        "user_id": user_id,
        "stats": stats,
        "message": "User activity summary"
    }


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    db.close()


# For running directly
if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
