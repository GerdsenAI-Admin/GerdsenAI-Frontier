"""
Capability Matching Engine

Finds complementary capabilities across the network to enable coordination.

Core principle: Match needs with capabilities in a way that creates value
for both parties, with complete transparency about why matches were made.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import math
from collections import defaultdict

from ...shared.models.core import (
    UserProfile,
    Need,
    Capability,
    Match,
    ProvenanceGraph,
    ProvenanceStep,
    CapabilityType
)
from ..transparency.engine import TransparencyEngine


@dataclass
class MatchingConfig:
    """Configuration for matching algorithm"""
    min_match_score: float = 0.4  # Don't return matches below this
    max_matches_per_need: int = 10
    include_provenance: bool = True
    weight_complementarity: float = 0.4
    weight_proficiency: float = 0.3
    weight_feasibility: float = 0.3


class CapabilityMatcher:
    """
    Finds complementary capabilities across the network

    Uses semantic similarity, complementarity analysis, and feasibility
    assessment to match needs with capabilities.
    """

    def __init__(self, config: Optional[MatchingConfig] = None):
        self.config = config or MatchingConfig()
        self.transparency = TransparencyEngine()

        # In production, this would be a real vector DB (e.g., ChromaDB)
        self.capability_index: Dict[str, List[Tuple[UserProfile, Capability]]] = defaultdict(list)

        # Learning from past matches
        self.match_history: List[Match] = []
        self.success_patterns: Dict[str, float] = {}

    def index_user_profile(self, profile: UserProfile):
        """
        Index a user's capabilities for matching

        In production: Store in vector database for semantic search
        """
        for capability in profile.capabilities:
            # Index by type
            key = f"type:{capability.type.value}"
            self.capability_index[key].append((profile, capability))

            # Index by tags
            for tag in capability.tags:
                key = f"tag:{tag}"
                self.capability_index[key].append((profile, capability))

            # Index by name tokens (simplified)
            for token in capability.name.lower().split():
                if len(token) > 3:  # Skip short words
                    key = f"token:{token}"
                    self.capability_index[key].append((profile, capability))

    def find_matches(
        self,
        need: Need,
        need_user_profile: UserProfile,
        max_results: Optional[int] = None
    ) -> List[Match]:
        """
        Find capabilities that match a need

        Returns ranked list of matches with full transparency
        """

        # Create provenance graph for this matching operation
        provenance = self.transparency.create_provenance_graph("capability_match")

        # Step 1: Candidate retrieval
        candidates = self._retrieve_candidates(need, need_user_profile, provenance)

        # Step 2: Score each candidate
        scored_matches = []
        for profile, capability in candidates:
            match = self._score_match(
                need,
                need_user_profile,
                capability,
                profile,
                provenance
            )
            if match.match_score >= self.config.min_match_score:
                scored_matches.append(match)

        # Step 3: Rank and return top matches
        scored_matches.sort(key=lambda m: m.match_score, reverse=True)

        max_results = max_results or self.config.max_matches_per_need
        top_matches = scored_matches[:max_results]

        # Step 4: Add final reasoning
        self._add_ranking_reasoning(top_matches, provenance)

        return top_matches

    def _retrieve_candidates(
        self,
        need: Need,
        need_user_profile: UserProfile,
        provenance: ProvenanceGraph
    ) -> List[Tuple[UserProfile, Capability]]:
        """
        Retrieve candidate capabilities that might match the need

        Uses multiple retrieval strategies and combines results
        """

        candidates = []

        # Strategy 1: Match by type
        type_key = f"type:{need.type.value}"
        type_matches = self.capability_index.get(type_key, [])
        candidates.extend(type_matches)

        # Strategy 2: Match by tags
        for tag in need.tags:
            tag_key = f"tag:{tag}"
            tag_matches = self.capability_index.get(tag_key, [])
            candidates.extend(tag_matches)

        # Strategy 3: Match by name tokens
        for token in need.name.lower().split():
            if len(token) > 3:
                token_key = f"token:{token}"
                token_matches = self.capability_index.get(token_key, [])
                candidates.extend(token_matches)

        # Deduplicate based on user_id and capability_id
        seen = set()
        unique_candidates = []
        for profile, cap in candidates:
            key = (profile.user_id, cap.capability_id)
            if key not in seen:
                seen.add(key)
                unique_candidates.append((profile, cap))

        # Filter out self-matches
        candidates = [
            (profile, cap) for profile, cap in unique_candidates
            if profile.user_id != need_user_profile.user_id
        ]

        # Record retrieval step
        provenance.add_step(ProvenanceStep(
            operation="candidate_retrieval",
            inputs={
                "need_type": need.type.value,
                "need_tags": list(need.tags)
            },
            outputs={
                "candidates_found": len(candidates)
            },
            reasoning=f"Retrieved {len(candidates)} candidates using type, tag, and semantic matching",
            confidence=0.9
        ))

        return list(candidates)

    def _score_match(
        self,
        need: Need,
        need_user_profile: UserProfile,
        capability: Capability,
        capability_user_profile: UserProfile,
        provenance: ProvenanceGraph
    ) -> Match:
        """
        Score how well a capability matches a need

        Returns Match object with score and complete explanation
        """

        # Initialize match object
        match = Match(
            need=need,
            need_user_id=need_user_profile.user_id,
            capability=capability,
            capability_user_id=capability_user_profile.user_id,
            provenance=self.transparency.create_provenance_graph("match_scoring")
        )

        # Component 1: Semantic similarity
        semantic_score = self._compute_semantic_similarity(need, capability)
        match.provenance.add_step(ProvenanceStep(
            operation="semantic_similarity",
            inputs={
                "need_name": need.name,
                "capability_name": capability.name
            },
            outputs={"score": semantic_score},
            reasoning=f"Computed semantic similarity between need and capability",
            confidence=0.8
        ))

        # Component 2: Complementarity
        complementarity_score = self._compute_complementarity(
            need_user_profile,
            capability_user_profile
        )
        match.complementarity_score = complementarity_score
        match.provenance.add_step(ProvenanceStep(
            operation="complementarity_analysis",
            outputs={"score": complementarity_score},
            reasoning="Analyzed how well the users' capabilities complement each other",
            confidence=0.7
        ))

        # Component 3: Feasibility
        feasibility_score = self._compute_feasibility(
            need_user_profile,
            capability_user_profile,
            need
        )
        match.feasibility_score = feasibility_score
        match.provenance.add_step(ProvenanceStep(
            operation="feasibility_assessment",
            outputs={"score": feasibility_score},
            reasoning="Assessed practical feasibility (location, time, resources)",
            confidence=0.75
        ))

        # Component 4: Historical success patterns
        historical_boost = self._apply_historical_learning(need, capability)
        match.provenance.add_step(ProvenanceStep(
            operation="historical_learning",
            outputs={"boost": historical_boost},
            reasoning=f"Applied learning from {len(self.match_history)} past matches",
            confidence=0.6 if self.match_history else 0.3
        ))

        # Combine scores
        match.match_score = (
            semantic_score * 0.3 +
            complementarity_score * self.config.weight_complementarity +
            capability.proficiency * self.config.weight_proficiency +
            feasibility_score * self.config.weight_feasibility +
            historical_boost * 0.1
        )

        # Compute overall confidence
        match.confidence = self._compute_confidence(match)

        # Add evidence
        match.evidence = self._gather_evidence(need, capability)

        # Add verification methods
        match.verification_methods = [
            f"Check {capability_user_profile.user_id}'s past work in this domain",
            "Verify the capability description aligns with the need",
            "Consider if practical constraints are manageable"
        ]

        # Identify uncertainty factors
        match.uncertainty_factors = self._identify_uncertainties(
            need_user_profile,
            capability_user_profile
        )

        return match

    def _compute_semantic_similarity(self, need: Need, capability: Capability) -> float:
        """
        Compute semantic similarity between need and capability

        In production: Use embedding-based similarity (e.g., sentence transformers)
        For now: Simple token-based similarity
        """

        need_tokens = set(need.name.lower().split() + need.description.lower().split())
        cap_tokens = set(capability.name.lower().split() + capability.description.lower().split())

        # Add tags
        need_tokens.update(need.tags)
        cap_tokens.update(capability.tags)

        # Jaccard similarity
        if not need_tokens or not cap_tokens:
            return 0.0

        intersection = len(need_tokens & cap_tokens)
        union = len(need_tokens | cap_tokens)

        return intersection / union if union > 0 else 0.0

    def _compute_complementarity(
        self,
        need_user_profile: UserProfile,
        capability_user_profile: UserProfile
    ) -> float:
        """
        Compute how well the users' capabilities complement each other

        High complementarity = they have different skills that work well together
        """

        # Get all capabilities
        user1_caps = {(c.type.value, c.name) for c in need_user_profile.capabilities}
        user2_caps = {(c.type.value, c.name) for c in capability_user_profile.capabilities}

        # Calculate overlap (lower is more complementary)
        overlap = len(user1_caps & user2_caps)
        total = len(user1_caps | user2_caps)

        if total == 0:
            return 0.5  # Neutral if no data

        # Complementarity is inverse of overlap
        # Some overlap is good (common ground), too much is redundant
        overlap_ratio = overlap / total
        optimal_overlap = 0.2  # Sweet spot: 20% overlap

        # Distance from optimal
        distance = abs(overlap_ratio - optimal_overlap)
        complementarity = 1.0 - (distance * 2)  # Scale to 0-1

        return max(0.0, min(1.0, complementarity))

    def _compute_feasibility(
        self,
        need_user_profile: UserProfile,
        capability_user_profile: UserProfile,
        need: Need
    ) -> float:
        """
        Compute practical feasibility of collaboration

        Considers: location, timezone, availability, constraints
        """

        feasibility = 1.0

        # Factor 1: Geographic/timezone compatibility
        if (need_user_profile.timezone and
            capability_user_profile.timezone and
            need_user_profile.timezone != capability_user_profile.timezone):
            # Penalize extreme timezone differences
            # (in production: calculate actual timezone offset)
            feasibility *= 0.8

        # Factor 2: Availability alignment
        # (simplified - in production would check actual schedules)
        if (need_user_profile.availability and
            capability_user_profile.availability):
            # Check if there's overlap (simplified)
            feasibility *= 0.9

        # Factor 3: Constraint satisfaction
        if need.constraints:
            # Check if capability satisfies constraints
            # (simplified - in production would do real constraint checking)
            budget_constraint = need.constraints.get("budget")
            if budget_constraint:
                # Would check if collaboration fits budget
                feasibility *= 0.95

        # Factor 4: Urgency alignment
        if need.urgency > 0.8:
            # High urgency needs quick response
            # Would check capability_user's responsiveness
            feasibility *= 0.9

        return max(0.0, min(1.0, feasibility))

    def _apply_historical_learning(self, need: Need, capability: Capability) -> float:
        """
        Apply learning from past successful matches

        Returns boost factor based on similar past successes
        """

        if not self.match_history:
            return 0.0  # No history yet

        # Find similar past matches
        similar_matches = [
            m for m in self.match_history
            if m.need.type == need.type and m.capability.type == capability.type
        ]

        if not similar_matches:
            return 0.0

        # Average success rate for similar matches
        # (would track actual outcomes in production)
        avg_score = sum(m.match_score for m in similar_matches) / len(similar_matches)

        # Small boost if similar matches were successful
        return (avg_score - 0.5) * 0.2  # ±0.1 boost

    def _compute_confidence(self, match: Match) -> float:
        """
        Compute overall confidence in this match

        Based on quality of evidence, completeness of profiles, etc.
        """

        confidence_factors = []

        # Factor 1: Match score (higher score = higher confidence)
        confidence_factors.append(match.match_score)

        # Factor 2: Evidence quality
        if match.evidence:
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.5)

        # Factor 3: Profile completeness
        # (in production: check how complete the profiles are)
        confidence_factors.append(0.8)

        # Factor 4: Historical data availability
        if self.match_history:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.5)

        # Average confidence
        return sum(confidence_factors) / len(confidence_factors)

    def _gather_evidence(self, need: Need, capability: Capability) -> List[str]:
        """
        Gather evidence supporting this match
        """

        evidence = []

        # Evidence from descriptions
        if need.description and capability.description:
            evidence.append(f"Need and capability descriptions are aligned")

        # Evidence from tags
        common_tags = need.tags & capability.tags
        if common_tags:
            evidence.append(f"Shared domain tags: {', '.join(common_tags)}")

        # Evidence from proficiency
        if capability.proficiency >= 0.7:
            evidence.append(f"High proficiency level: {capability.proficiency:.2f}")

        # Would add more in production: citations, past work, etc.

        return evidence

    def _identify_uncertainties(
        self,
        need_user_profile: UserProfile,
        capability_user_profile: UserProfile
    ) -> List[str]:
        """
        Identify factors that create uncertainty in this match
        """

        uncertainties = []

        # Limited profile data
        if len(need_user_profile.capabilities) < 3:
            uncertainties.append("Limited capability data for need user")

        if len(capability_user_profile.capabilities) < 3:
            uncertainties.append("Limited capability data for capability user")

        # No historical data
        if not self.match_history:
            uncertainties.append("No historical match data for calibration")

        # Missing important fields
        if not need_user_profile.timezone:
            uncertainties.append("Unknown timezone for need user")

        if not capability_user_profile.timezone:
            uncertainties.append("Unknown timezone for capability user")

        return uncertainties

    def _add_ranking_reasoning(
        self,
        matches: List[Match],
        provenance: ProvenanceGraph
    ):
        """
        Add reasoning about why matches were ranked this way
        """

        if not matches:
            return

        provenance.add_step(ProvenanceStep(
            operation="ranking",
            inputs={"total_matches": len(matches)},
            outputs={
                "top_match_score": matches[0].match_score,
                "score_range": f"{matches[-1].match_score:.2f} - {matches[0].match_score:.2f}"
            },
            reasoning=f"Ranked {len(matches)} matches by combined score of semantic similarity, "
                     f"complementarity, proficiency, and feasibility",
            confidence=0.85
        ))

    def learn_from_outcome(self, match: Match, success: bool):
        """
        Learn from actual collaboration outcomes

        This enables the system to improve over time
        """

        # Store match in history
        self.match_history.append(match)

        # Update success patterns
        pattern_key = f"{match.need.type.value}:{match.capability.type.value}"

        if pattern_key not in self.success_patterns:
            self.success_patterns[pattern_key] = match.match_score if success else 0.0
        else:
            # Exponential moving average
            alpha = 0.3
            current = self.success_patterns[pattern_key]
            new_value = match.match_score if success else 0.0
            self.success_patterns[pattern_key] = alpha * new_value + (1 - alpha) * current

        # In production: Retrain models, update embeddings, etc.


class BatchMatcher:
    """
    Efficient matching for multiple needs/capabilities at once

    Uses graph algorithms for global optimization
    """

    def __init__(self, matcher: CapabilityMatcher):
        self.matcher = matcher

    def find_optimal_matching(
        self,
        needs: List[Tuple[UserProfile, Need]],
        capabilities: List[Tuple[UserProfile, Capability]]
    ) -> Dict[str, List[Match]]:
        """
        Find globally optimal matching across multiple needs

        Uses maximum weighted bipartite matching
        (simplified implementation - production would use proper graph algorithms)
        """

        all_matches = defaultdict(list)

        # For each need, find all possible matches
        for need_profile, need in needs:
            matches = []
            for cap_profile, cap in capabilities:
                if need_profile.user_id != cap_profile.user_id:
                    # Create temporary capability index
                    self.matcher.index_user_profile(cap_profile)

                    # Score this specific match
                    match = self.matcher._score_match(
                        need,
                        need_profile,
                        cap,
                        cap_profile,
                        self.matcher.transparency.create_provenance_graph("batch_match")
                    )
                    matches.append(match)

            # Store top matches for this need
            matches.sort(key=lambda m: m.match_score, reverse=True)
            all_matches[need.need_id] = matches[:10]

        return all_matches
