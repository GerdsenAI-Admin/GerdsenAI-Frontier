"""
Semantic Matching Engine - Powered by Embeddings

This upgrades Substrate from keyword matching to true semantic understanding.

Key improvements:
1. Embeddings capture meaning, not just keywords
2. "sensor fusion" matches "multi-modal perception" (same concept, different words)
3. Deep semantic similarity using state-of-the-art models
4. ChromaDB for persistent vector storage
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("⚠️  sentence-transformers not available, falling back to keyword matching")

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("⚠️  ChromaDB not available, using in-memory storage")

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
class SemanticMatchingConfig:
    """Configuration for semantic matching"""
    embedding_model: str = "all-MiniLM-L6-v2"  # Fast, good quality
    min_match_score: float = 0.4
    max_matches_per_need: int = 10
    similarity_threshold: float = 0.3  # Cosine similarity threshold
    weight_semantic: float = 0.4
    weight_complementarity: float = 0.3
    weight_proficiency: float = 0.2
    weight_feasibility: float = 0.1
    chromadb_path: str = "./substrate_data/chroma"


class SemanticMatcher:
    """
    Semantic capability matching using embeddings

    This is the "smart" version of Substrate that actually understands meaning.
    """

    def __init__(self, config: Optional[SemanticMatchingConfig] = None):
        self.config = config or SemanticMatchingConfig()
        self.transparency = TransparencyEngine()

        # Initialize embedding model
        if EMBEDDINGS_AVAILABLE:
            print(f"🧠 Loading embedding model: {self.config.embedding_model}")
            self.embedding_model = SentenceTransformer(self.config.embedding_model)
            print("✓ Embeddings ready")
        else:
            self.embedding_model = None
            print("⚠️  Running without embeddings (keyword fallback)")

        # Initialize ChromaDB for vector storage
        if CHROMADB_AVAILABLE:
            print(f"💾 Initializing ChromaDB at: {self.config.chromadb_path}")
            self.chroma_client = chromadb.PersistentClient(
                path=self.config.chromadb_path
            )

            # Create collections
            self.capabilities_collection = self.chroma_client.get_or_create_collection(
                name="capabilities",
                metadata={"description": "User capabilities for matching"}
            )
            print("✓ ChromaDB ready")
        else:
            self.chroma_client = None
            self.capabilities_collection = None
            print("⚠️  Running without ChromaDB (in-memory only)")

        # Fallback: in-memory storage
        self.memory_capabilities: List[Tuple[UserProfile, Capability, np.ndarray]] = []

        # Learning from outcomes
        self.match_history: List[Match] = []

    def index_user_profile(self, profile: UserProfile):
        """
        Index a user's capabilities with semantic embeddings

        This makes their capabilities searchable by meaning, not just keywords
        """

        for capability in profile.capabilities:
            # Generate embedding from capability description
            embedding = self._embed_capability(capability)

            # Create metadata for filtering
            metadata = {
                "user_id": profile.user_id,
                "capability_id": capability.capability_id,
                "type": capability.type.value,
                "name": capability.name,
                "proficiency": capability.proficiency,
                "privacy_level": capability.privacy_level.value,
            }

            # Add tags to metadata
            for i, tag in enumerate(list(capability.tags)[:10]):  # Max 10 tags
                metadata[f"tag_{i}"] = tag

            # Store in ChromaDB if available
            if self.capabilities_collection is not None and embedding is not None:
                self.capabilities_collection.add(
                    embeddings=[embedding.tolist()],
                    documents=[self._capability_to_text(capability)],
                    metadatas=[metadata],
                    ids=[capability.capability_id]
                )

            # Also store in memory for fallback
            if embedding is not None:
                self.memory_capabilities.append((profile, capability, embedding))

    def find_matches(
        self,
        need: Need,
        need_user_profile: UserProfile,
        max_results: Optional[int] = None
    ) -> List[Match]:
        """
        Find capabilities that semantically match a need

        Uses embedding similarity to understand meaning, not just keywords
        """

        # Create provenance graph
        provenance = self.transparency.create_provenance_graph("semantic_capability_match")

        # Generate embedding for the need
        need_embedding = self._embed_need(need)

        provenance.add_step(ProvenanceStep(
            operation="need_embedding_generation",
            inputs={"need_description": need.description[:100]},
            outputs={"embedding_generated": need_embedding is not None},
            reasoning="Generated semantic embedding to capture meaning of the need",
            confidence=0.95 if need_embedding is not None else 0.3
        ))

        # Find semantically similar capabilities
        if need_embedding is not None and self.capabilities_collection is not None:
            candidates = self._query_chromadb(need, need_embedding, need_user_profile, provenance)
        else:
            # Fallback to memory search
            candidates = self._query_memory(need, need_embedding, need_user_profile, provenance)

        # Score each candidate
        scored_matches = []
        for profile, capability in candidates:
            match = self._score_match(
                need,
                need_user_profile,
                capability,
                profile,
                need_embedding,
                provenance
            )
            if match.match_score >= self.config.min_match_score:
                scored_matches.append(match)

        # Rank matches
        scored_matches.sort(key=lambda m: m.match_score, reverse=True)

        max_results = max_results or self.config.max_matches_per_need
        top_matches = scored_matches[:max_results]

        # Add ranking reasoning
        if top_matches:
            provenance.add_step(ProvenanceStep(
                operation="ranking",
                inputs={"total_matches": len(scored_matches)},
                outputs={
                    "top_match_score": top_matches[0].match_score,
                    "returned_matches": len(top_matches)
                },
                reasoning=f"Ranked by semantic similarity + complementarity + proficiency + feasibility",
                confidence=0.9
            ))

        return top_matches

    def _embed_capability(self, capability: Capability) -> Optional[np.ndarray]:
        """Generate embedding for a capability"""
        if self.embedding_model is None:
            return None

        text = self._capability_to_text(capability)
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding

    def _embed_need(self, need: Need) -> Optional[np.ndarray]:
        """Generate embedding for a need"""
        if self.embedding_model is None:
            return None

        text = self._need_to_text(need)
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding

    def _capability_to_text(self, capability: Capability) -> str:
        """Convert capability to text for embedding"""
        parts = [
            f"Capability: {capability.name}",
            f"Description: {capability.description}",
            f"Type: {capability.type.value}",
        ]
        if capability.tags:
            parts.append(f"Tags: {', '.join(capability.tags)}")
        return " | ".join(parts)

    def _need_to_text(self, need: Need) -> str:
        """Convert need to text for embedding"""
        parts = [
            f"Need: {need.name}",
            f"Description: {need.description}",
            f"Type: {need.type.value}",
            f"Domain: {need.domain.value}",
        ]
        if need.tags:
            parts.append(f"Tags: {', '.join(need.tags)}")
        if need.context:
            parts.append(f"Context: {need.context[:200]}")
        return " | ".join(parts)

    def _query_chromadb(
        self,
        need: Need,
        need_embedding: np.ndarray,
        need_user_profile: UserProfile,
        provenance: ProvenanceGraph
    ) -> List[Tuple[UserProfile, Capability]]:
        """Query ChromaDB for similar capabilities"""

        # Query by semantic similarity
        results = self.capabilities_collection.query(
            query_embeddings=[need_embedding.tolist()],
            n_results=50,  # Get top 50 candidates
            where={
                # Could add filters here, e.g., by type
            }
        )

        candidates = []
        if results and results['ids'] and results['ids'][0]:
            # Extract results
            for i, cap_id in enumerate(results['ids'][0]):
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i] if results['distances'] else 0

                # Convert distance to similarity (1 - distance for cosine)
                similarity = 1 - distance

                # Skip if below threshold
                if similarity < self.config.similarity_threshold:
                    continue

                # Skip self-matches
                if metadata['user_id'] == need_user_profile.user_id:
                    continue

                # Find the actual profile and capability from memory
                for profile, cap, _ in self.memory_capabilities:
                    if cap.capability_id == cap_id:
                        candidates.append((profile, cap))
                        break

        provenance.add_step(ProvenanceStep(
            operation="chromadb_query",
            inputs={"query_type": "semantic_similarity"},
            outputs={"candidates_found": len(candidates)},
            reasoning=f"Found {len(candidates)} semantically similar capabilities using embedding search",
            confidence=0.9
        ))

        return candidates

    def _query_memory(
        self,
        need: Need,
        need_embedding: Optional[np.ndarray],
        need_user_profile: UserProfile,
        provenance: ProvenanceGraph
    ) -> List[Tuple[UserProfile, Capability]]:
        """Fallback: query in-memory storage"""

        candidates = []

        if need_embedding is not None:
            # Semantic search in memory
            for profile, cap, cap_embedding in self.memory_capabilities:
                # Skip self-matches
                if profile.user_id == need_user_profile.user_id:
                    continue

                # Compute cosine similarity
                similarity = self._cosine_similarity(need_embedding, cap_embedding)

                if similarity >= self.config.similarity_threshold:
                    candidates.append((profile, cap))

        else:
            # Keyword fallback (from original engine)
            for profile, cap, _ in self.memory_capabilities:
                if profile.user_id == need_user_profile.user_id:
                    continue

                # Simple keyword matching
                if (cap.type == need.type or
                    any(tag in cap.tags for tag in need.tags)):
                    candidates.append((profile, cap))

        provenance.add_step(ProvenanceStep(
            operation="memory_query",
            outputs={"candidates_found": len(candidates)},
            reasoning=f"Searched in-memory storage, found {len(candidates)} candidates",
            confidence=0.7
        ))

        return candidates

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def _score_match(
        self,
        need: Need,
        need_user_profile: UserProfile,
        capability: Capability,
        capability_user_profile: UserProfile,
        need_embedding: Optional[np.ndarray],
        provenance: ProvenanceGraph
    ) -> Match:
        """Score a match using semantic similarity and other factors"""

        match = Match(
            need=need,
            need_user_id=need_user_profile.user_id,
            capability=capability,
            capability_user_id=capability_user_profile.user_id,
            provenance=self.transparency.create_provenance_graph("semantic_match_scoring")
        )

        # 1. Semantic similarity
        if need_embedding is not None:
            cap_embedding = self._embed_capability(capability)
            if cap_embedding is not None:
                semantic_sim = self._cosine_similarity(need_embedding, cap_embedding)
            else:
                semantic_sim = 0.5
        else:
            # Fallback to keyword similarity
            semantic_sim = self._keyword_similarity(need, capability)

        match.provenance.add_step(ProvenanceStep(
            operation="semantic_similarity",
            outputs={"similarity": semantic_sim},
            reasoning=f"Computed deep semantic similarity using embeddings (not just keywords)",
            confidence=0.9 if need_embedding is not None else 0.6
        ))

        # 2. Complementarity
        complementarity = self._compute_complementarity(
            need_user_profile,
            capability_user_profile
        )
        match.complementarity_score = complementarity

        # 3. Feasibility
        feasibility = self._compute_feasibility(
            need_user_profile,
            capability_user_profile,
            need
        )
        match.feasibility_score = feasibility

        # 4. Combined score
        match.match_score = (
            semantic_sim * self.config.weight_semantic +
            complementarity * self.config.weight_complementarity +
            capability.proficiency * self.config.weight_proficiency +
            feasibility * self.config.weight_feasibility
        )

        # 5. Confidence
        match.confidence = self._compute_confidence(match, need_embedding is not None)

        # 6. Evidence
        match.evidence = [
            f"Semantic similarity: {semantic_sim:.2f}",
            f"Complementarity: {complementarity:.2f}",
            f"Proficiency: {capability.proficiency:.2f}",
            f"Feasibility: {feasibility:.2f}"
        ]

        # 7. Verification methods
        match.verification_methods = [
            "Review the capability description for alignment",
            "Check if semantic similarity score makes sense",
            "Verify proficiency level is adequate"
        ]

        # 8. Uncertainty factors
        match.uncertainty_factors = []
        if not need_embedding:
            match.uncertainty_factors.append("No embeddings available (keyword fallback)")
        if len(self.match_history) < 10:
            match.uncertainty_factors.append("Limited historical data for calibration")

        return match

    def _keyword_similarity(self, need: Need, capability: Capability) -> float:
        """Fallback keyword similarity"""
        need_words = set(need.name.lower().split() + need.description.lower().split())
        cap_words = set(capability.name.lower().split() + capability.description.lower().split())

        need_words.update(need.tags)
        cap_words.update(capability.tags)

        if not need_words or not cap_words:
            return 0.0

        intersection = len(need_words & cap_words)
        union = len(need_words | cap_words)

        return intersection / union if union > 0 else 0.0

    def _compute_complementarity(
        self,
        profile1: UserProfile,
        profile2: UserProfile
    ) -> float:
        """Compute capability complementarity between users"""
        caps1 = {(c.type.value, c.name) for c in profile1.capabilities}
        caps2 = {(c.type.value, c.name) for c in profile2.capabilities}

        overlap = len(caps1 & caps2)
        total = len(caps1 | caps2)

        if total == 0:
            return 0.5

        overlap_ratio = overlap / total
        optimal = 0.2  # 20% overlap is ideal
        distance = abs(overlap_ratio - optimal)

        return max(0.0, min(1.0, 1.0 - (distance * 2)))

    def _compute_feasibility(
        self,
        profile1: UserProfile,
        profile2: UserProfile,
        need: Need
    ) -> float:
        """Compute practical feasibility"""
        feasibility = 1.0

        # Timezone penalty for very different timezones
        if profile1.timezone and profile2.timezone:
            if profile1.timezone != profile2.timezone:
                feasibility *= 0.9

        # Urgency considerations
        if need.urgency > 0.8:
            feasibility *= 0.9

        return feasibility

    def _compute_confidence(self, match: Match, has_embeddings: bool) -> float:
        """Compute confidence in match quality"""
        factors = []

        # Higher confidence with embeddings
        if has_embeddings:
            factors.append(0.9)
        else:
            factors.append(0.6)

        # Match score affects confidence
        factors.append(match.match_score)

        # Evidence quality
        if match.evidence:
            factors.append(0.8)
        else:
            factors.append(0.5)

        # Historical data
        if len(self.match_history) > 10:
            factors.append(0.8)
        else:
            factors.append(0.5)

        return sum(factors) / len(factors)

    def learn_from_outcome(self, match: Match, success: bool):
        """Learn from collaboration outcomes"""
        self.match_history.append(match)
        # Future: Retrain, update weights, improve matching
