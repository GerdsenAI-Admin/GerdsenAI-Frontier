"""
Transparency Engine - The Heart of Substrate

Every decision made by the system must be:
1. Explainable - Why was this decision made?
2. Verifiable - How can I check if this is true?
3. Transparent - What alternatives were considered?
4. Uncertain - What factors could affect confidence?
5. Traceable - Complete provenance from input to output

This solves the fundamental "black box AI" problem.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import json

from ...shared.models.core import (
    ProvenanceGraph,
    ProvenanceStep,
    Match,
    Team
)


class TransparencyEngine:
    """
    Generates explanations for every decision in the system

    Core principle: If we can't explain it, we don't do it.
    """

    def __init__(self):
        self.explanation_templates = self._load_templates()

    def create_provenance_graph(self, decision_type: str) -> ProvenanceGraph:
        """Start a new provenance graph for tracking a decision"""
        return ProvenanceGraph(decision_type=decision_type)

    def explain_match(
        self,
        match: Match,
        include_reasoning: bool = True,
        include_alternatives: bool = True,
        include_verification: bool = True
    ) -> Dict[str, Any]:
        """
        Generate complete explanation for a match

        Returns structured explanation that humans can verify
        """

        explanation = {
            "summary": self._generate_match_summary(match),
            "scores": {
                "overall_match": {
                    "value": match.match_score,
                    "interpretation": self._interpret_score(match.match_score),
                    "confidence": match.confidence
                },
                "complementarity": {
                    "value": match.complementarity_score,
                    "explanation": "How well the capabilities complement the need"
                },
                "feasibility": {
                    "value": match.feasibility_score,
                    "explanation": "How practical is this collaboration"
                }
            }
        }

        if include_reasoning:
            explanation["reasoning"] = {
                "step_by_step": self._format_provenance(match.provenance),
                "key_factors": self._extract_key_factors(match.provenance),
                "evidence": match.evidence
            }

        if include_alternatives:
            explanation["alternatives"] = {
                "total_considered": self._count_alternatives(match.provenance),
                "why_this_one": self._explain_choice(match.provenance),
                "other_options": self._get_alternative_summaries(match.provenance)
            }

        if include_verification:
            explanation["verification"] = {
                "methods": match.verification_methods,
                "how_to_check": self._generate_verification_steps(match),
                "external_sources": self._suggest_external_validation(match)
            }

        explanation["uncertainty"] = {
            "factors": match.uncertainty_factors,
            "confidence_interval": self._estimate_confidence_interval(match),
            "what_could_change": self._identify_sensitivity(match)
        }

        return explanation

    def explain_team_composition(
        self,
        team: Team,
        detailed: bool = True
    ) -> Dict[str, Any]:
        """
        Generate complete explanation for team composition

        Explains why this particular combination of people
        """

        explanation = {
            "summary": f"Team of {len(team.members)} members for: {team.problem_description}",
            "predicted_outcome": {
                "success_probability": team.predicted_success_probability,
                "confidence_interval": team.confidence_interval,
                "interpretation": self._interpret_probability(
                    team.predicted_success_probability
                )
            },
            "team_composition": {
                "roles": team.roles,
                "complementarity_score": team.complementarity_score,
                "diversity_score": team.diversity_score,
                "why_this_matters": "Diverse teams with complementary skills have higher success rates"
            }
        }

        if detailed:
            explanation["reasoning"] = {
                "optimization_process": self._format_provenance(team.provenance),
                "why_these_people": self._explain_team_selection(team),
                "synergies_identified": self._identify_synergies(team)
            }

            explanation["risk_assessment"] = {
                "identified_risks": team.risk_factors,
                "mitigation_strategies": self._suggest_mitigations(team),
                "what_to_monitor": self._suggest_monitoring(team)
            }

            explanation["resources"] = {
                "timeline": {
                    "estimate": team.estimated_timeline,
                    "confidence": "Based on similar past collaborations",
                    "factors_affecting": self._timeline_sensitivity(team)
                },
                "cost": {
                    "estimate": team.estimated_cost,
                    "breakdown": team.required_resources,
                    "confidence": "Rough estimate, adjust based on actual scope"
                }
            }

        return explanation

    def generate_verification_protocol(
        self,
        decision: Any,
        decision_type: str
    ) -> List[Dict[str, Any]]:
        """
        Generate step-by-step protocol for users to verify a decision

        This empowers users to check our work
        """

        protocol = []

        if decision_type == "match":
            protocol = [
                {
                    "step": 1,
                    "action": "Check capability alignment",
                    "how": "Compare the need description with the capability description",
                    "what_to_look_for": "Do they address the same problem domain?",
                    "red_flags": ["Mismatched domains", "Vague descriptions"]
                },
                {
                    "step": 2,
                    "action": "Verify evidence",
                    "how": "Check the cited sources and references",
                    "what_to_look_for": "Are the sources credible and relevant?",
                    "red_flags": ["Broken links", "Outdated info", "Weak sources"]
                },
                {
                    "step": 3,
                    "action": "Assess complementarity",
                    "how": "Consider if this collaboration makes sense",
                    "what_to_look_for": "Do the skills truly complement each other?",
                    "red_flags": ["Too much overlap", "Missing critical skills"]
                },
                {
                    "step": 4,
                    "action": "Check feasibility",
                    "how": "Consider practical constraints (location, time, resources)",
                    "what_to_look_for": "Can this actually work in practice?",
                    "red_flags": ["Incompatible timezones", "Resource conflicts"]
                },
                {
                    "step": 5,
                    "action": "Trust your judgment",
                    "how": "Does this feel right based on your expertise?",
                    "what_to_look_for": "Your domain knowledge is valuable",
                    "red_flags": ["Something feels off", "Too good to be true"]
                }
            ]

        elif decision_type == "team":
            protocol = [
                {
                    "step": 1,
                    "action": "Review team composition",
                    "how": "Look at each member's role and capabilities",
                    "what_to_look_for": "Are all necessary roles covered?",
                    "red_flags": ["Missing critical skills", "Unclear roles"]
                },
                {
                    "step": 2,
                    "action": "Assess synergies",
                    "how": "Consider how team members would work together",
                    "what_to_look_for": "Complementary skills, collaborative potential",
                    "red_flags": ["Conflicting approaches", "Communication barriers"]
                },
                {
                    "step": 3,
                    "action": "Evaluate feasibility",
                    "how": "Check timeline, cost, resource estimates",
                    "what_to_look_for": "Are estimates realistic?",
                    "red_flags": ["Too optimistic", "Missing dependencies"]
                },
                {
                    "step": 4,
                    "action": "Review risk factors",
                    "how": "Consider what could go wrong",
                    "what_to_look_for": "Are risks identified and addressable?",
                    "red_flags": ["Unmanaged risks", "No contingency plans"]
                }
            ]

        return protocol

    def explain_confidence(
        self,
        confidence: float,
        factors: List[str]
    ) -> Dict[str, Any]:
        """
        Explain what confidence means and what affects it
        """

        interpretation = ""
        if confidence >= 0.9:
            interpretation = "Very high confidence - strong evidence and clear reasoning"
        elif confidence >= 0.7:
            interpretation = "High confidence - good evidence, some uncertainty remains"
        elif confidence >= 0.5:
            interpretation = "Moderate confidence - reasonable evidence, notable uncertainty"
        elif confidence >= 0.3:
            interpretation = "Low confidence - limited evidence, significant uncertainty"
        else:
            interpretation = "Very low confidence - weak evidence, high uncertainty"

        return {
            "confidence_score": confidence,
            "interpretation": interpretation,
            "what_affects_confidence": factors,
            "how_to_increase": self._suggest_confidence_improvements(factors),
            "meaning": "Confidence represents how certain the system is about this decision. "
                      "Higher confidence means more evidence and clearer reasoning."
        }

    # Helper methods

    def _generate_match_summary(self, match: Match) -> str:
        """Generate human-readable summary"""
        return (
            f"Match score: {match.match_score:.2f} | "
            f"Confidence: {match.confidence:.2f} | "
            f"Complementarity: {match.complementarity_score:.2f}"
        )

    def _interpret_score(self, score: float) -> str:
        """Interpret what a score means"""
        if score >= 0.8:
            return "Excellent match"
        elif score >= 0.6:
            return "Good match"
        elif score >= 0.4:
            return "Moderate match"
        else:
            return "Weak match"

    def _format_provenance(self, provenance: ProvenanceGraph) -> List[Dict[str, Any]]:
        """Format provenance for human reading"""
        return [
            {
                "step": i + 1,
                "operation": step.operation,
                "reasoning": step.reasoning,
                "confidence": step.confidence
            }
            for i, step in enumerate(provenance.steps)
        ]

    def _extract_key_factors(self, provenance: ProvenanceGraph) -> List[str]:
        """Extract the most important factors from reasoning"""
        key_factors = []
        for step in provenance.steps:
            if step.confidence >= 0.8:  # High confidence steps are key
                key_factors.append(f"{step.operation}: {step.reasoning}")
        return key_factors

    def _count_alternatives(self, provenance: ProvenanceGraph) -> int:
        """Count total alternatives considered"""
        total = 0
        for step in provenance.steps:
            total += len(step.alternatives_considered)
        return total

    def _explain_choice(self, provenance: ProvenanceGraph) -> str:
        """Explain why this option was chosen over alternatives"""
        # Find the step with the most alternatives
        max_alts = max(
            provenance.steps,
            key=lambda s: len(s.alternatives_considered),
            default=None
        )
        if max_alts:
            return max_alts.reasoning
        return "This was the highest-scoring option"

    def _get_alternative_summaries(self, provenance: ProvenanceGraph) -> List[Dict[str, Any]]:
        """Get summaries of alternative options"""
        alternatives = []
        for step in provenance.steps:
            for alt in step.alternatives_considered[:3]:  # Top 3
                alternatives.append({
                    "option": alt.get("name", "Alternative option"),
                    "score": alt.get("score", 0),
                    "why_not": alt.get("reason_not_chosen", "Lower score")
                })
        return alternatives[:5]  # Return top 5 overall

    def _generate_verification_steps(self, match: Match) -> List[str]:
        """Generate specific steps to verify this match"""
        steps = []

        if match.evidence:
            steps.append(f"Check evidence: {match.evidence[0]}")

        if match.similar_past_matches:
            steps.append(f"Review similar past match: {match.similar_past_matches[0]}")

        steps.append("Compare need and capability descriptions manually")
        steps.append("Consider if this collaboration makes sense in your domain")

        return steps

    def _suggest_external_validation(self, match: Match) -> List[str]:
        """Suggest external sources for validation"""
        suggestions = [
            "Consult with domain experts",
            "Review relevant literature or case studies",
            "Check if similar collaborations have succeeded before"
        ]
        return suggestions

    def _estimate_confidence_interval(self, match: Match) -> tuple:
        """Estimate confidence interval for match score"""
        # Simple estimation based on confidence
        uncertainty = 1 - match.confidence
        margin = match.match_score * uncertainty * 0.3  # 30% of score as margin
        return (
            max(0, match.match_score - margin),
            min(1, match.match_score + margin)
        )

    def _identify_sensitivity(self, match: Match) -> List[str]:
        """Identify what could change the match score"""
        sensitivities = [
            "More detailed capability description could improve accuracy",
            "Additional context about constraints could affect feasibility",
            "Past collaboration outcomes would improve confidence"
        ]
        return sensitivities

    def _interpret_probability(self, prob: float) -> str:
        """Interpret success probability"""
        if prob >= 0.8:
            return "Highly likely to succeed"
        elif prob >= 0.6:
            return "Good chance of success"
        elif prob >= 0.4:
            return "Moderate chance of success"
        else:
            return "Success uncertain - consider risk mitigation"

    def _explain_team_selection(self, team: Team) -> str:
        """Explain why these specific people were selected"""
        return (
            f"This team was selected based on complementary skills, "
            f"feasibility of collaboration, and predicted synergies. "
            f"Complementarity score: {team.complementarity_score:.2f}"
        )

    def _identify_synergies(self, team: Team) -> List[str]:
        """Identify potential synergies between team members"""
        # Would be computed from actual member capabilities
        return [
            "Computational + Experimental expertise complement each other",
            "Geographic diversity enables 24/7 progress",
            "Different perspectives lead to creative solutions"
        ]

    def _suggest_mitigations(self, team: Team) -> Dict[str, str]:
        """Suggest mitigation strategies for risks"""
        mitigations = {}
        for risk in team.risk_factors:
            if "timezone" in risk.lower():
                mitigations[risk] = "Schedule regular overlapping meetings, use async communication"
            elif "communication" in risk.lower():
                mitigations[risk] = "Establish clear communication protocols early"
            elif "scope" in risk.lower():
                mitigations[risk] = "Define clear milestones and check-ins"
            else:
                mitigations[risk] = "Monitor closely and adapt as needed"
        return mitigations

    def _suggest_monitoring(self, team: Team) -> List[str]:
        """Suggest what to monitor during collaboration"""
        return [
            "Progress against milestones",
            "Communication frequency and quality",
            "Team morale and satisfaction",
            "Resource usage vs estimates",
            "Emerging risks or blockers"
        ]

    def _timeline_sensitivity(self, team: Team) -> List[str]:
        """What could affect the timeline"""
        return [
            "Scope changes or additions",
            "Resource availability",
            "External dependencies",
            "Team member capacity changes"
        ]

    def _suggest_confidence_improvements(self, factors: List[str]) -> List[str]:
        """Suggest how to increase confidence"""
        suggestions = []
        for factor in factors:
            if "data" in factor.lower():
                suggestions.append("Gather more relevant data")
            elif "evidence" in factor.lower():
                suggestions.append("Seek additional evidence or validation")
            elif "past" in factor.lower():
                suggestions.append("Look for similar past cases")
        return suggestions or ["Gather more information", "Seek expert validation"]

    def _load_templates(self) -> Dict[str, str]:
        """Load explanation templates"""
        return {
            "match": "Match between {need} and {capability}",
            "team": "Team composition for {problem}"
        }


class ExplanationFormatter:
    """
    Formats explanations for different audiences and mediums
    """

    @staticmethod
    def to_markdown(explanation: Dict[str, Any]) -> str:
        """Format explanation as Markdown"""
        md = "# Explanation\n\n"

        if "summary" in explanation:
            md += f"## Summary\n{explanation['summary']}\n\n"

        if "scores" in explanation:
            md += "## Scores\n"
            for metric, data in explanation["scores"].items():
                md += f"- **{metric}**: {data.get('value', 'N/A'):.2f}\n"
                if 'interpretation' in data:
                    md += f"  - {data['interpretation']}\n"
            md += "\n"

        if "reasoning" in explanation:
            md += "## Reasoning\n"
            if "step_by_step" in explanation["reasoning"]:
                for step in explanation["reasoning"]["step_by_step"]:
                    md += f"{step['step']}. {step['operation']}\n"
                    md += f"   - {step['reasoning']}\n"
            md += "\n"

        if "verification" in explanation:
            md += "## How to Verify\n"
            for i, method in enumerate(explanation["verification"].get("how_to_check", []), 1):
                md += f"{i}. {method}\n"
            md += "\n"

        return md

    @staticmethod
    def to_json(explanation: Dict[str, Any]) -> str:
        """Format explanation as JSON"""
        return json.dumps(explanation, indent=2)

    @staticmethod
    def to_simple_text(explanation: Dict[str, Any]) -> str:
        """Format explanation as simple text"""
        text = explanation.get("summary", "")
        if "scores" in explanation:
            text += "\n\nScores:\n"
            for metric, data in explanation["scores"].items():
                text += f"  {metric}: {data.get('value', 'N/A'):.2f}\n"
        return text
