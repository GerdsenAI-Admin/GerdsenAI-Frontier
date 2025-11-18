"""
Local AI Reasoning Engine

Runs entirely on the user's device. Maintains privacy while understanding
user context, analyzing problems, and generating capability profiles.

Key principles:
1. Privacy first - sensitive data never leaves the device
2. Transparent reasoning - users can see how conclusions are reached
3. Context-aware - understands user's full situation
4. Efficient - runs on consumer hardware
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import json
from datetime import datetime

from ...shared.models.core import (
    UserProfile,
    Capability,
    Need,
    CapabilityType,
    ProblemDomain,
    PrivacyLevel,
    ProvenanceGraph,
    ProvenanceStep
)


@dataclass
class ReasoningConfig:
    """Configuration for local reasoning"""
    model_name: str = "llama-3.1-70b"  # Or smaller for constrained devices
    max_tokens: int = 2048
    temperature: float = 0.7
    enable_provenance: bool = True


class LocalReasoningEngine:
    """
    LLM-powered reasoning that runs entirely on device

    Uses local LLM (Llama, Mistral, etc.) to:
    - Analyze user's problems and decompose them
    - Identify capability gaps
    - Generate shareable profiles
    - Maintain complete transparency
    """

    def __init__(self, config: Optional[ReasoningConfig] = None):
        self.config = config or ReasoningConfig()

        # In production: Load actual LLM (llama.cpp, transformers, etc.)
        # For now: Simulate with structured logic
        self.llm = None  # Would be: load_model(config.model_name)

        # Local knowledge graph (persisted to disk)
        self.knowledge_graph = {}

        # Reasoning history for transparency
        self.reasoning_history: List[ProvenanceGraph] = []

    def analyze_problem(
        self,
        problem_description: str,
        user_context: Dict[str, Any]
    ) -> Need:
        """
        Analyze a problem description and decompose it into structured needs

        Returns a Need object with full provenance of reasoning
        """

        provenance = ProvenanceGraph(decision_type="problem_analysis")

        # Step 1: Domain classification
        domain = self._classify_domain(problem_description, provenance)

        # Step 2: Extract key concepts
        concepts = self._extract_concepts(problem_description, provenance)

        # Step 3: Identify required capabilities
        required_caps = self._identify_required_capabilities(
            problem_description,
            concepts,
            provenance
        )

        # Step 4: Assess urgency and importance
        urgency, importance = self._assess_priority(
            problem_description,
            user_context,
            provenance
        )

        # Step 5: Extract constraints
        constraints = self._extract_constraints(
            problem_description,
            user_context,
            provenance
        )

        # Create structured Need
        need = Need(
            type=required_caps[0] if required_caps else CapabilityType.SKILL,
            name=self._generate_need_name(problem_description, concepts),
            description=problem_description,
            urgency=urgency,
            importance=importance,
            domain=domain,
            context=json.dumps(user_context),
            constraints=constraints,
            tags=set(concepts[:5])  # Top 5 concepts as tags
        )

        # Store reasoning history
        self.reasoning_history.append(provenance)

        return need

    def identify_user_capabilities(
        self,
        user_data: Dict[str, Any]
    ) -> List[Capability]:
        """
        Identify user's capabilities from their data

        Sources:
        - Explicit: Resume, skills list, projects
        - Implicit: Tool usage patterns, problem-solving history
        - Inferred: From projects and outcomes

        All analysis stays local.
        """

        capabilities = []
        provenance = ProvenanceGraph(decision_type="capability_identification")

        # Source 1: Explicit skills
        if "skills" in user_data:
            explicit_caps = self._extract_explicit_capabilities(
                user_data["skills"],
                provenance
            )
            capabilities.extend(explicit_caps)

        # Source 2: Projects and work history
        if "projects" in user_data:
            project_caps = self._infer_from_projects(
                user_data["projects"],
                provenance
            )
            capabilities.extend(project_caps)

        # Source 3: Tools and resources
        if "tools" in user_data:
            resource_caps = self._extract_resource_capabilities(
                user_data["tools"],
                provenance
            )
            capabilities.extend(resource_caps)

        # Source 4: Learning and expertise indicators
        if "learning" in user_data:
            learning_caps = self._assess_expertise_levels(
                user_data["learning"],
                provenance
            )
            capabilities.extend(learning_caps)

        # Deduplicate and merge similar capabilities
        capabilities = self._deduplicate_capabilities(capabilities, provenance)

        self.reasoning_history.append(provenance)

        return capabilities

    def generate_shareable_profile(
        self,
        user_profile: UserProfile,
        privacy_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate privacy-preserving profile for matching

        Respects user's privacy preferences while creating
        useful profile for coordination.
        """

        provenance = ProvenanceGraph(decision_type="profile_generation")

        # Start with base profile
        shareable = user_profile.to_shareable_profile()

        # Apply privacy filters
        shareable = self._apply_privacy_filters(
            shareable,
            privacy_preferences,
            provenance
        )

        # Anonymize sensitive information
        shareable = self._anonymize_profile(shareable, provenance)

        # Add confidence scores
        shareable["profile_confidence"] = self._assess_profile_confidence(
            user_profile,
            provenance
        )

        provenance.add_step(ProvenanceStep(
            operation="profile_generation_complete",
            outputs={
                "capabilities_shared": len(shareable.get("capabilities", [])),
                "privacy_level": "preserved"
            },
            reasoning="Generated shareable profile while preserving privacy",
            confidence=0.9
        ))

        self.reasoning_history.append(provenance)

        return {
            "profile": shareable,
            "provenance": provenance.to_dict()
        }

    def assess_match_quality(
        self,
        need: Need,
        proposed_match: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Help user assess if a proposed match is good

        Provides local analysis to complement cloud matching
        """

        provenance = ProvenanceGraph(decision_type="match_assessment")

        # Analyze alignment with need
        alignment_score = self._assess_alignment(
            need,
            proposed_match,
            provenance
        )

        # Check feasibility given user's constraints
        feasibility_score = self._assess_local_feasibility(
            proposed_match,
            user_context,
            provenance
        )

        # Identify potential concerns
        concerns = self._identify_concerns(
            need,
            proposed_match,
            user_context,
            provenance
        )

        # Generate recommendation
        recommendation = self._generate_recommendation(
            alignment_score,
            feasibility_score,
            concerns,
            provenance
        )

        return {
            "alignment_score": alignment_score,
            "feasibility_score": feasibility_score,
            "concerns": concerns,
            "recommendation": recommendation,
            "provenance": provenance.to_dict()
        }

    # Private helper methods

    def _classify_domain(
        self,
        problem_description: str,
        provenance: ProvenanceGraph
    ) -> ProblemDomain:
        """Classify problem into a domain"""

        # In production: Use LLM for classification
        # For now: Simple keyword matching

        description_lower = problem_description.lower()

        domain_keywords = {
            ProblemDomain.ROBOTICS: ["robot", "sensor", "motor", "actuator", "autonomous"],
            ProblemDomain.SOFTWARE: ["code", "software", "app", "api", "algorithm"],
            ProblemDomain.HARDWARE: ["circuit", "pcb", "electronic", "hardware"],
            ProblemDomain.RESEARCH: ["research", "study", "experiment", "hypothesis"],
            ProblemDomain.BIOLOGY: ["protein", "cell", "genetic", "organism"],
            ProblemDomain.CLIMATE: ["climate", "carbon", "renewable", "environment"],
        }

        best_domain = ProblemDomain.OTHER
        max_matches = 0

        for domain, keywords in domain_keywords.items():
            matches = sum(1 for kw in keywords if kw in description_lower)
            if matches > max_matches:
                max_matches = matches
                best_domain = domain

        provenance.add_step(ProvenanceStep(
            operation="domain_classification",
            inputs={"description": problem_description[:100]},
            outputs={"domain": best_domain.value},
            reasoning=f"Classified based on keyword matching ({max_matches} matches)",
            confidence=0.7 if max_matches > 0 else 0.3
        ))

        return best_domain

    def _extract_concepts(
        self,
        text: str,
        provenance: ProvenanceGraph
    ) -> List[str]:
        """Extract key concepts from text"""

        # In production: Use LLM or NLP for entity extraction
        # For now: Simple approach

        # Common words to filter out
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}

        words = text.lower().split()
        concepts = [w for w in words if len(w) > 4 and w not in stopwords]

        # Take unique concepts
        concepts = list(dict.fromkeys(concepts))[:10]

        provenance.add_step(ProvenanceStep(
            operation="concept_extraction",
            outputs={"concepts": concepts[:5]},
            reasoning="Extracted key concepts from problem description",
            confidence=0.6
        ))

        return concepts

    def _identify_required_capabilities(
        self,
        problem_description: str,
        concepts: List[str],
        provenance: ProvenanceGraph
    ) -> List[CapabilityType]:
        """Identify what types of capabilities are needed"""

        required = []

        # Heuristics for capability types (would use LLM in production)
        if any(word in problem_description.lower() for word in ["build", "create", "make"]):
            required.append(CapabilityType.SKILL)

        if any(word in problem_description.lower() for word in ["equipment", "lab", "tools"]):
            required.append(CapabilityType.RESOURCE)

        if any(word in problem_description.lower() for word in ["know", "understand", "expertise"]):
            required.append(CapabilityType.KNOWLEDGE)

        if any(word in problem_description.lower() for word in ["funding", "money", "budget"]):
            required.append(CapabilityType.FUNDING)

        if not required:
            required.append(CapabilityType.SKILL)  # Default

        provenance.add_step(ProvenanceStep(
            operation="capability_identification",
            outputs={"required_types": [c.value for c in required]},
            reasoning="Identified required capability types from problem description",
            confidence=0.65
        ))

        return required

    def _assess_priority(
        self,
        problem_description: str,
        user_context: Dict[str, Any],
        provenance: ProvenanceGraph
    ) -> tuple[float, float]:
        """Assess urgency and importance"""

        urgency = 0.5  # Default: moderate
        importance = 0.5

        # Urgency indicators
        urgent_words = ["urgent", "asap", "immediately", "critical", "deadline"]
        if any(word in problem_description.lower() for word in urgent_words):
            urgency = 0.9

        # Importance indicators
        important_words = ["critical", "essential", "key", "vital", "crucial"]
        if any(word in problem_description.lower() for word in important_words):
            importance = 0.9

        provenance.add_step(ProvenanceStep(
            operation="priority_assessment",
            outputs={"urgency": urgency, "importance": importance},
            reasoning="Assessed priority based on keywords and context",
            confidence=0.6
        ))

        return urgency, importance

    def _extract_constraints(
        self,
        problem_description: str,
        user_context: Dict[str, Any],
        provenance: ProvenanceGraph
    ) -> Dict[str, Any]:
        """Extract constraints from problem and context"""

        constraints = {}

        # Budget constraints
        if "budget" in user_context:
            constraints["budget"] = user_context["budget"]

        # Timeline constraints
        if "deadline" in user_context:
            constraints["deadline"] = user_context["deadline"]

        # Location constraints
        if "location_preference" in user_context:
            constraints["location"] = user_context["location_preference"]

        # Extract from description (simplified)
        if "remote" in problem_description.lower():
            constraints["location"] = "remote"

        provenance.add_step(ProvenanceStep(
            operation="constraint_extraction",
            outputs={"constraints": list(constraints.keys())},
            reasoning="Extracted constraints from context and description",
            confidence=0.7
        ))

        return constraints

    def _generate_need_name(self, description: str, concepts: List[str]) -> str:
        """Generate concise name for need"""
        # Take first few words or key concept
        words = description.split()[:5]
        return " ".join(words) + ("..." if len(description.split()) > 5 else "")

    def _extract_explicit_capabilities(
        self,
        skills: List[str],
        provenance: ProvenanceGraph
    ) -> List[Capability]:
        """Extract capabilities from explicit skill list"""

        capabilities = []

        for skill in skills:
            cap = Capability(
                type=CapabilityType.SKILL,
                name=skill,
                description=f"Explicit skill: {skill}",
                proficiency=0.7,  # Default for self-reported
                confidence=0.8,  # High confidence in explicit data
                privacy_level=PrivacyLevel.NETWORK,  # Shareable by default
                tags={skill.lower()}
            )
            capabilities.append(cap)

        provenance.add_step(ProvenanceStep(
            operation="explicit_capability_extraction",
            outputs={"count": len(capabilities)},
            reasoning="Extracted capabilities from user's skill list",
            confidence=0.9
        ))

        return capabilities

    def _infer_from_projects(
        self,
        projects: List[Dict[str, Any]],
        provenance: ProvenanceGraph
    ) -> List[Capability]:
        """Infer capabilities from past projects"""

        capabilities = []

        for project in projects:
            # Extract technologies used
            if "technologies" in project:
                for tech in project["technologies"]:
                    cap = Capability(
                        type=CapabilityType.SKILL,
                        name=tech,
                        description=f"Used in project: {project.get('name', 'Unknown')}",
                        proficiency=0.6,  # Inferred proficiency
                        confidence=0.7,  # Moderate confidence in inference
                        evidence=[f"Project: {project.get('name', 'Unknown')}"],
                        privacy_level=PrivacyLevel.NETWORK,
                        tags={tech.lower()}
                    )
                    capabilities.append(cap)

        provenance.add_step(ProvenanceStep(
            operation="project_inference",
            outputs={"count": len(capabilities)},
            reasoning="Inferred capabilities from project history",
            confidence=0.7
        ))

        return capabilities

    def _extract_resource_capabilities(
        self,
        tools: List[str],
        provenance: ProvenanceGraph
    ) -> List[Capability]:
        """Extract resource capabilities from tools/equipment"""

        capabilities = []

        for tool in tools:
            cap = Capability(
                type=CapabilityType.RESOURCE,
                name=tool,
                description=f"Available resource: {tool}",
                proficiency=1.0,  # You have it or you don't
                confidence=0.95,  # High confidence
                privacy_level=PrivacyLevel.NETWORK,
                tags={tool.lower()}
            )
            capabilities.append(cap)

        provenance.add_step(ProvenanceStep(
            operation="resource_extraction",
            outputs={"count": len(capabilities)},
            reasoning="Extracted resource capabilities from tools/equipment list",
            confidence=0.95
        ))

        return capabilities

    def _assess_expertise_levels(
        self,
        learning_data: Dict[str, Any],
        provenance: ProvenanceGraph
    ) -> List[Capability]:
        """Assess expertise levels from learning history"""

        # Would analyze courses, certifications, practice time, etc.
        # Simplified for now

        capabilities = []
        # Implementation would go here

        return capabilities

    def _deduplicate_capabilities(
        self,
        capabilities: List[Capability],
        provenance: ProvenanceGraph
    ) -> List[Capability]:
        """Merge duplicate or similar capabilities"""

        # Group by name (simplified - would use semantic similarity in production)
        grouped: Dict[str, List[Capability]] = {}

        for cap in capabilities:
            key = cap.name.lower()
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(cap)

        # Merge groups
        merged = []
        for caps in grouped.values():
            if len(caps) == 1:
                merged.append(caps[0])
            else:
                # Merge: take highest proficiency, combine evidence
                best = max(caps, key=lambda c: c.proficiency)
                best.evidence = []
                for cap in caps:
                    best.evidence.extend(cap.evidence)
                best.confidence = sum(c.confidence for c in caps) / len(caps)
                merged.append(best)

        provenance.add_step(ProvenanceStep(
            operation="deduplication",
            inputs={"original_count": len(capabilities)},
            outputs={"deduplicated_count": len(merged)},
            reasoning="Merged duplicate capabilities",
            confidence=0.85
        ))

        return merged

    def _apply_privacy_filters(
        self,
        profile: Dict[str, Any],
        preferences: Dict[str, Any],
        provenance: ProvenanceGraph
    ) -> Dict[str, Any]:
        """Apply user's privacy preferences"""

        filtered = profile.copy()

        # Remove private capabilities
        if "capabilities" in filtered:
            filtered["capabilities"] = [
                cap for cap in filtered["capabilities"]
                if cap.get("privacy_level") != PrivacyLevel.PRIVATE.value
            ]

        # Apply location privacy
        if preferences.get("hide_location"):
            filtered.pop("location_region", None)
            filtered.pop("timezone", None)

        provenance.add_step(ProvenanceStep(
            operation="privacy_filtering",
            reasoning="Applied privacy filters based on user preferences",
            confidence=1.0
        ))

        return filtered

    def _anonymize_profile(
        self,
        profile: Dict[str, Any],
        provenance: ProvenanceGraph
    ) -> Dict[str, Any]:
        """Remove personally identifiable information"""

        anonymized = profile.copy()

        # User ID is already anonymous UUID
        # Remove any other PII that might have leaked in

        provenance.add_step(ProvenanceStep(
            operation="anonymization",
            reasoning="Ensured no PII in shareable profile",
            confidence=0.95
        ))

        return anonymized

    def _assess_profile_confidence(
        self,
        profile: UserProfile,
        provenance: ProvenanceGraph
    ) -> float:
        """Assess how confident we are in this profile"""

        factors = []

        # More capabilities = higher confidence
        factors.append(min(1.0, len(profile.capabilities) / 10))

        # More complete fields = higher confidence
        completeness = sum([
            bool(profile.location_region),
            bool(profile.timezone),
            bool(profile.domains),
            bool(profile.capabilities)
        ]) / 4
        factors.append(completeness)

        confidence = sum(factors) / len(factors)

        provenance.add_step(ProvenanceStep(
            operation="confidence_assessment",
            outputs={"confidence": confidence},
            reasoning="Assessed profile confidence based on completeness",
            confidence=0.8
        ))

        return confidence

    def _assess_alignment(
        self,
        need: Need,
        match: Dict[str, Any],
        provenance: ProvenanceGraph
    ) -> float:
        """Assess how well match aligns with need"""

        # Would do semantic comparison
        # Simplified for now
        alignment = 0.7

        provenance.add_step(ProvenanceStep(
            operation="alignment_assessment",
            outputs={"score": alignment},
            reasoning="Assessed alignment between need and proposed match",
            confidence=0.7
        ))

        return alignment

    def _assess_local_feasibility(
        self,
        match: Dict[str, Any],
        user_context: Dict[str, Any],
        provenance: ProvenanceGraph
    ) -> float:
        """Assess feasibility from user's local context"""

        feasibility = 0.8  # Default

        # Check constraints
        # Implementation would go here

        provenance.add_step(ProvenanceStep(
            operation="feasibility_assessment",
            outputs={"score": feasibility},
            reasoning="Assessed feasibility given user's constraints",
            confidence=0.75
        ))

        return feasibility

    def _identify_concerns(
        self,
        need: Need,
        match: Dict[str, Any],
        user_context: Dict[str, Any],
        provenance: ProvenanceGraph
    ) -> List[str]:
        """Identify potential concerns with match"""

        concerns = []

        # Check for red flags
        # Implementation would go here

        return concerns

    def _generate_recommendation(
        self,
        alignment: float,
        feasibility: float,
        concerns: List[str],
        provenance: ProvenanceGraph
    ) -> str:
        """Generate recommendation for user"""

        overall = (alignment + feasibility) / 2

        if overall >= 0.8 and not concerns:
            recommendation = "Highly recommended - strong alignment and feasibility"
        elif overall >= 0.6:
            recommendation = "Recommended - good potential, review concerns"
        elif overall >= 0.4:
            recommendation = "Consider carefully - moderate match quality"
        else:
            recommendation = "Not recommended - low alignment or feasibility"

        provenance.add_step(ProvenanceStep(
            operation="recommendation_generation",
            outputs={"recommendation": recommendation},
            reasoning=f"Generated recommendation based on scores and concerns",
            confidence=0.8
        ))

        return recommendation
