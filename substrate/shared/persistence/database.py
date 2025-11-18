"""
Substrate Persistence Layer

Makes Substrate remember everything:
- User profiles and capabilities
- Matches and their outcomes
- Learning from what works
- Complete history for analysis

This enables the system to actually get better over time.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import sqlite3
import json
from pathlib import Path

from ...shared.models.core import (
    UserProfile,
    Capability,
    Need,
    Match,
    Team,
    CollaborationOutcome,
    CapabilityType,
    ProblemDomain,
    PrivacyLevel
)


class SubstrateDatabase:
    """
    SQLite persistence for Substrate

    Stores:
    - User profiles (with privacy controls)
    - Capabilities and needs
    - Matches and outcomes
    - Learning signals for improvement
    """

    def __init__(self, db_path: str = "./substrate_data/substrate.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        self._create_tables()

    def _create_tables(self):
        """Create database schema"""

        cursor = self.conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                location_region TEXT,
                timezone TEXT,
                domains TEXT,  -- JSON array
                preferences TEXT,  -- JSON object
                created_at TEXT,
                updated_at TEXT
            )
        """)

        # Capabilities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS capabilities (
                capability_id TEXT PRIMARY KEY,
                user_id TEXT,
                type TEXT,
                name TEXT,
                description TEXT,
                proficiency REAL,
                confidence REAL,
                evidence TEXT,  -- JSON array
                privacy_level TEXT,
                tags TEXT,  -- JSON array
                metadata TEXT,  -- JSON object
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Create index on capabilities
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_capabilities_user
            ON capabilities(user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_capabilities_type
            ON capabilities(type)
        """)

        # Needs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS needs (
                need_id TEXT PRIMARY KEY,
                user_id TEXT,
                type TEXT,
                name TEXT,
                description TEXT,
                urgency REAL,
                importance REAL,
                domain TEXT,
                context TEXT,
                constraints TEXT,  -- JSON object
                tags TEXT,  -- JSON array
                created_at TEXT,
                resolved BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Matches table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                match_id TEXT PRIMARY KEY,
                need_id TEXT,
                need_user_id TEXT,
                capability_id TEXT,
                capability_user_id TEXT,
                match_score REAL,
                complementarity_score REAL,
                feasibility_score REAL,
                confidence REAL,
                provenance TEXT,  -- JSON object
                evidence TEXT,  -- JSON array
                uncertainty_factors TEXT,  -- JSON array
                created_at TEXT,
                status TEXT DEFAULT 'proposed',  -- proposed, accepted, rejected, completed
                FOREIGN KEY (need_id) REFERENCES needs(need_id),
                FOREIGN KEY (capability_id) REFERENCES capabilities(capability_id)
            )
        """)

        # Create index on matches
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_matches_need
            ON matches(need_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_matches_users
            ON matches(need_user_id, capability_user_id)
        """)

        # Collaboration outcomes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS outcomes (
                outcome_id TEXT PRIMARY KEY,
                match_id TEXT,
                success BOOLEAN,
                completion_date TEXT,
                actual_timeline TEXT,
                actual_cost REAL,
                problem_solved BOOLEAN,
                knowledge_created TEXT,  -- JSON array
                artifacts_produced TEXT,  -- JSON array
                what_worked TEXT,  -- JSON array
                what_didnt TEXT,  -- JSON array
                lessons_learned TEXT,
                participant_ratings TEXT,  -- JSON object
                created_at TEXT,
                FOREIGN KEY (match_id) REFERENCES matches(match_id)
            )
        """)

        # Learning signals table (for improving matching over time)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_signals (
                signal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id TEXT,
                signal_type TEXT,  -- acceptance, rejection, outcome
                signal_value REAL,  -- 0-1 score
                features TEXT,  -- JSON object with match features
                created_at TEXT,
                FOREIGN KEY (match_id) REFERENCES matches(match_id)
            )
        """)

        self.conn.commit()

    def save_user_profile(self, profile: UserProfile):
        """Save or update a user profile"""

        cursor = self.conn.cursor()

        # Save user
        cursor.execute("""
            INSERT OR REPLACE INTO users
            (user_id, location_region, timezone, domains, preferences, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            profile.user_id,
            profile.location_region,
            profile.timezone,
            json.dumps([d.value for d in profile.domains]),
            json.dumps(profile.preferences),
            profile.created_at.isoformat(),
            profile.updated_at.isoformat()
        ))

        # Save capabilities
        for cap in profile.capabilities:
            cursor.execute("""
                INSERT OR REPLACE INTO capabilities
                (capability_id, user_id, type, name, description, proficiency,
                 confidence, evidence, privacy_level, tags, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cap.capability_id,
                profile.user_id,
                cap.type.value,
                cap.name,
                cap.description,
                cap.proficiency,
                cap.confidence,
                json.dumps(cap.evidence),
                cap.privacy_level.value,
                json.dumps(list(cap.tags)),
                json.dumps(cap.metadata),
                datetime.now().isoformat()
            ))

        self.conn.commit()

    def load_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Load a user profile"""

        cursor = self.conn.cursor()

        # Load user
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user_row = cursor.fetchone()

        if not user_row:
            return None

        # Load capabilities
        cursor.execute("SELECT * FROM capabilities WHERE user_id = ?", (user_id,))
        cap_rows = cursor.fetchall()

        capabilities = []
        for row in cap_rows:
            cap = Capability(
                capability_id=row['capability_id'],
                type=CapabilityType(row['type']),
                name=row['name'],
                description=row['description'],
                proficiency=row['proficiency'],
                confidence=row['confidence'],
                evidence=json.loads(row['evidence']),
                privacy_level=PrivacyLevel(row['privacy_level']),
                tags=set(json.loads(row['tags'])),
                metadata=json.loads(row['metadata'])
            )
            capabilities.append(cap)

        # Create profile
        profile = UserProfile(
            user_id=user_row['user_id'],
            capabilities=capabilities,
            domains={ProblemDomain(d) for d in json.loads(user_row['domains'])},
            location_region=user_row['location_region'],
            timezone=user_row['timezone'],
            preferences=json.loads(user_row['preferences']),
            created_at=datetime.fromisoformat(user_row['created_at']),
            updated_at=datetime.fromisoformat(user_row['updated_at'])
        )

        return profile

    def save_need(self, need: Need, user_id: str):
        """Save a need"""

        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO needs
            (need_id, user_id, type, name, description, urgency, importance,
             domain, context, constraints, tags, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            need.need_id,
            user_id,
            need.type.value,
            need.name,
            need.description,
            need.urgency,
            need.importance,
            need.domain.value,
            need.context,
            json.dumps(need.constraints),
            json.dumps(list(need.tags)),
            datetime.now().isoformat()
        ))

        self.conn.commit()

    def save_match(self, match: Match):
        """Save a match"""

        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO matches
            (match_id, need_id, need_user_id, capability_id, capability_user_id,
             match_score, complementarity_score, feasibility_score, confidence,
             provenance, evidence, uncertainty_factors, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            match.match_id,
            match.need.need_id if match.need else None,
            match.need_user_id,
            match.capability.capability_id if match.capability else None,
            match.capability_user_id,
            match.match_score,
            match.complementarity_score,
            match.feasibility_score,
            match.confidence,
            json.dumps(match.provenance.to_dict()),
            json.dumps(match.evidence),
            json.dumps(match.uncertainty_factors),
            match.created_at.isoformat()
        ))

        self.conn.commit()

    def update_match_status(self, match_id: str, status: str):
        """Update match status (proposed → accepted → completed)"""

        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE matches SET status = ? WHERE match_id = ?
        """, (status, match_id))
        self.conn.commit()

    def save_outcome(self, outcome: CollaborationOutcome):
        """Save collaboration outcome"""

        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO outcomes
            (outcome_id, match_id, success, completion_date, actual_timeline,
             actual_cost, problem_solved, knowledge_created, artifacts_produced,
             what_worked, what_didnt, lessons_learned, participant_ratings, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            outcome.outcome_id,
            outcome.match_id,
            outcome.success,
            outcome.completion_date.isoformat() if outcome.completion_date else None,
            outcome.actual_timeline,
            outcome.actual_cost,
            outcome.problem_solved,
            json.dumps(outcome.knowledge_created),
            json.dumps(outcome.artifacts_produced),
            json.dumps(outcome.what_worked),
            json.dumps(outcome.what_didnt),
            outcome.lessons_learned,
            json.dumps(outcome.participant_ratings),
            outcome.created_at.isoformat()
        ))

        self.conn.commit()

        # Record learning signal
        self._record_learning_signal(outcome)

    def _record_learning_signal(self, outcome: CollaborationOutcome):
        """Record a learning signal for improving matching"""

        if not outcome.match_id:
            return

        # Load the match to get features
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM matches WHERE match_id = ?", (outcome.match_id,))
        match_row = cursor.fetchone()

        if not match_row:
            return

        # Extract features that led to this outcome
        features = {
            'match_score': match_row['match_score'],
            'complementarity_score': match_row['complementarity_score'],
            'feasibility_score': match_row['feasibility_score'],
            'confidence': match_row['confidence']
        }

        # Signal value: 1.0 for success, 0.0 for failure
        signal_value = 1.0 if outcome.success else 0.0

        cursor.execute("""
            INSERT INTO learning_signals
            (match_id, signal_type, signal_value, features, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            outcome.match_id,
            'outcome',
            signal_value,
            json.dumps(features),
            datetime.now().isoformat()
        ))

        self.conn.commit()

    def get_match_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent match history"""

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM matches
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_learning_signals(self, signal_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get learning signals for model improvement"""

        cursor = self.conn.cursor()

        if signal_type:
            cursor.execute("""
                SELECT * FROM learning_signals
                WHERE signal_type = ?
                ORDER BY created_at DESC
            """, (signal_type,))
        else:
            cursor.execute("""
                SELECT * FROM learning_signals
                ORDER BY created_at DESC
            """)

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_success_rate_by_features(self) -> Dict[str, float]:
        """Analyze which match features correlate with success"""

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT features, signal_value
            FROM learning_signals
            WHERE signal_type = 'outcome'
        """)

        rows = cursor.fetchall()

        if not rows:
            return {}

        # Simple analysis: average success rate
        total = len(rows)
        successes = sum(1 for row in rows if row['signal_value'] > 0.5)

        return {
            'overall_success_rate': successes / total if total > 0 else 0.0,
            'total_outcomes': total,
            'total_successes': successes
        }

    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics for a user"""

        cursor = self.conn.cursor()

        # Matches as need requester
        cursor.execute("""
            SELECT COUNT(*) as count, AVG(match_score) as avg_score
            FROM matches WHERE need_user_id = ?
        """, (user_id,))
        need_stats = dict(cursor.fetchone())

        # Matches as capability provider
        cursor.execute("""
            SELECT COUNT(*) as count, AVG(match_score) as avg_score
            FROM matches WHERE capability_user_id = ?
        """, (user_id,))
        cap_stats = dict(cursor.fetchone())

        return {
            'as_requester': need_stats,
            'as_provider': cap_stats
        }

    def close(self):
        """Close database connection"""
        self.conn.close()
