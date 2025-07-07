"""
Solar Sales Training Scoring System
===================================

Evaluates salesperson performance based on personality-specific criteria
"""

import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ScoreBreakdown:
    """Individual score component"""
    category: str
    score: int
    max_score: int
    feedback: str
    weight: float

@dataclass
class SessionScore:
    """Complete session scoring"""
    overall_score: int
    percentage: float
    grade: str
    breakdown: List[ScoreBreakdown]
    strengths: List[str]
    improvements: List[str]
    solar_specific_feedback: str
    conversation_count: int

class SolarSalesScorer:
    """Evaluates solar sales conversations based on personality types"""
    
    def __init__(self):
        self.personality_weights = {
            "owl": {
                "technical_knowledge": 0.30,
                "patience_shown": 0.20,
                "data_provided": 0.25,
                "professionalism": 0.15,
                "solar_expertise": 0.10
            },
            "bull": {
                "confidence": 0.25,
                "directness": 0.20,
                "value_focus": 0.30,
                "assertiveness": 0.15,
                "solar_expertise": 0.10
            },
            "sheep": {
                "guidance_provided": 0.30,
                "trust_building": 0.25,
                "recommendations": 0.20,
                "reassurance": 0.15,
                "solar_expertise": 0.10
            },
            "tiger": {
                "expertise_demonstrated": 0.30,
                "premium_positioning": 0.25,
                "professionalism": 0.20,
                "confidence": 0.15,
                "solar_expertise": 0.10
            }
        }
    
    def evaluate_conversation(self, personality_type: str, conversation_history: List[Dict], user_id: str) -> SessionScore:
        """Evaluate a complete conversation and return detailed scoring"""
        
        user_messages = [msg for msg in conversation_history if msg['message_type'] == 'user']
        ai_messages = [msg for msg in conversation_history if msg['message_type'] == 'ai']
        
        if len(user_messages) < 2:
            return self._create_minimal_score(personality_type, len(user_messages))
        
        if personality_type == "owl":
            return self._evaluate_owl_performance(user_messages, ai_messages)
        elif personality_type == "bull":
            return self._evaluate_bull_performance(user_messages, ai_messages)
        elif personality_type == "sheep":
            return self._evaluate_sheep_performance(user_messages, ai_messages)
        elif personality_type == "tiger":
            return self._evaluate_tiger_performance(user_messages, ai_messages)
        else:
            return self._create_minimal_score(personality_type, len(user_messages))
    
    def _evaluate_owl_performance(self, user_messages: List[Dict], ai_messages: List[Dict]) -> SessionScore:
        """Evaluate performance with analytical (Owl) customer"""
        breakdown = []
        
        tech_score = self._evaluate_technical_knowledge(user_messages)
        breakdown.append(ScoreBreakdown("Technical Knowledge", tech_score, 100, self._get_tech_feedback(tech_score), 0.30))
        
        patience_score = self._evaluate_patience(user_messages, ai_messages)
        breakdown.append(ScoreBreakdown("Patience & Thoroughness", patience_score, 100, self._get_patience_feedback(patience_score), 0.20))
        
        data_score = self._evaluate_data_provision(user_messages)
        breakdown.append(ScoreBreakdown("Data & Evidence", data_score, 100, self._get_data_feedback(data_score), 0.25))
        
        prof_score = self._evaluate_professionalism(user_messages)
        breakdown.append(ScoreBreakdown("Professionalism", prof_score, 100, self._get_professionalism_feedback(prof_score), 0.15))
        
        solar_score = self._evaluate_solar_expertise(user_messages)
        breakdown.append(ScoreBreakdown("Solar Expertise", solar_score, 100, self._get_solar_feedback(solar_score), 0.10))
        
        return self._compile_final_score(breakdown, "owl", len(user_messages))
    
    def _evaluate_bull_performance(self, user_messages: List[Dict], ai_messages: List[Dict]) -> SessionScore:
        """Evaluate performance with aggressive (Bull) customer"""
        breakdown = []
        
        confidence_score = self._evaluate_confidence(user_messages)
        breakdown.append(ScoreBreakdown("Confidence Under Pressure", confidence_score, 100, self._get_confidence_feedback(confidence_score), 0.25))
        
        directness_score = self._evaluate_directness(user_messages)
        breakdown.append(ScoreBreakdown("Direct Communication", directness_score, 100, self._get_directness_feedback(directness_score), 0.20))
        
        value_score = self._evaluate_value_focus(user_messages)
        breakdown.append(ScoreBreakdown("Value & ROI Focus", value_score, 100, self._get_value_feedback(value_score), 0.30))
        
        assert_score = self._evaluate_assertiveness(user_messages)
        breakdown.append(ScoreBreakdown("Assertiveness", assert_score, 100, self._get_assertiveness_feedback(assert_score), 0.15))
        
        solar_score = self._evaluate_solar_expertise(user_messages)
        breakdown.append(ScoreBreakdown("Solar Expertise", solar_score, 100, self._get_solar_feedback(solar_score), 0.10))
        
        return self._compile_final_score(breakdown, "bull", len(user_messages))
    
    def _evaluate_sheep_performance(self, user_messages: List[Dict], ai_messages: List[Dict]) -> SessionScore:
        """Evaluate performance with passive (Sheep) customer"""
        breakdown = []
        
        guidance_score = self._evaluate_guidance(user_messages)
        breakdown.append(ScoreBreakdown("Guidance & Leadership", guidance_score, 100, self._get_guidance_feedback(guidance_score), 0.30))
        
        trust_score = self._evaluate_trust_building(user_messages)
        breakdown.append(ScoreBreakdown("Trust Building", trust_score, 100, self._get_trust_feedback(trust_score), 0.25))
        
        rec_score = self._evaluate_recommendations(user_messages)
        breakdown.append(ScoreBreakdown("Clear Recommendations", rec_score, 100, self._get_recommendations_feedback(rec_score), 0.20))
        
        reassurance_score = self._evaluate_reassurance(user_messages)
        breakdown.append(ScoreBreakdown("Reassurance & Support", reassurance_score, 100, self._get_reassurance_feedback(reassurance_score), 0.15))
        
        solar_score = self._evaluate_solar_expertise(user_messages)
        breakdown.append(ScoreBreakdown("Solar Expertise", solar_score, 100, self._get_solar_feedback(solar_score), 0.10))
        
        return self._compile_final_score(breakdown, "sheep", len(user_messages))
    
    def _evaluate_tiger_performance(self, user_messages: List[Dict], ai_messages: List[Dict]) -> SessionScore:
        """Evaluate performance with dominant (Tiger) customer"""
        breakdown = []
        
        expertise_score = self._evaluate_expertise_demonstration(user_messages)
        breakdown.append(ScoreBreakdown("Expertise Demonstrated", expertise_score, 100, self._get_expertise_feedback(expertise_score), 0.30))
        
        premium_score = self._evaluate_premium_positioning(user_messages)
        breakdown.append(ScoreBreakdown("Premium Positioning", premium_score, 100, self._get_premium_feedback(premium_score), 0.25))
        
        prof_score = self._evaluate_professionalism(user_messages)
        breakdown.append(ScoreBreakdown("Professional Authority", prof_score, 100, self._get_professionalism_feedback(prof_score), 0.20))
        
        confidence_score = self._evaluate_confidence(user_messages)
        breakdown.append(ScoreBreakdown("Executive Confidence", confidence_score, 100, self._get_confidence_feedback(confidence_score), 0.15))
        
        solar_score = self._evaluate_solar_expertise(user_messages)
        breakdown.append(ScoreBreakdown("Solar Expertise", solar_score, 100, self._get_solar_feedback(solar_score), 0.10))
        
        return self._compile_final_score(breakdown, "tiger", len(user_messages))
    
    def _evaluate_technical_knowledge(self, messages: List[Dict]) -> int:
        """Evaluate technical knowledge demonstrated"""
        score = 60
        technical_terms = ['efficiency', 'kwh', 'inverter', 'warranty', 'degradation', 'installation', 'permits', 'grid', 'net metering', 'panels']
        all_text = ' '.join([msg['content'].lower() for msg in messages])
        
        for term in technical_terms:
            if term in all_text:
                score += 4
        
        if any(len(msg['content']) > 200 for msg in messages):
            score += 10
        
        return min(score, 100)
    
    def _evaluate_patience(self, user_messages: List[Dict], ai_messages: List[Dict]) -> int:
        """Evaluate patience shown with analytical customer"""
        score = 70
        avg_length = sum(len(msg['content']) for msg in user_messages) / len(user_messages)
        if avg_length > 150:
            score += 15
        elif avg_length > 100:
            score += 10
        
        rushed_indicators = ['quick', 'fast', 'hurry', 'simple']
        for msg in user_messages:
            if any(word in msg['content'].lower() for word in rushed_indicators):
                score -= 5
        
        return max(min(score, 100), 0)
    
    def _evaluate_data_provision(self, messages: List[Dict]) -> int:
        """Evaluate data and evidence provided"""
        score = 50
        data_indicators = ['data', 'study', 'research', 'statistics', 'numbers', 'percentage', 'average', 'typical', 'example', 'case']
        all_text = ' '.join([msg['content'].lower() for msg in messages])
        
        for indicator in data_indicators:
            if indicator in all_text:
                score += 5
        
        import re
        if re.search(r'\d+%|\$\d+|\d+\s*kwh', all_text):
            score += 15
        
        return min(score, 100)
    
    def _evaluate_confidence(self, messages: List[Dict]) -> int:
        """Evaluate confidence demonstrated"""
        score = 70
        confident_words = ['absolutely', 'definitely', 'guaranteed', 'proven', 'confident', 'certain', 'sure', 'experience']
        weak_words = ['maybe', 'might', 'possibly', 'not sure', 'think', 'guess']
        all_text = ' '.join([msg['content'].lower() for msg in messages])
        
        for word in confident_words:
            if word in all_text:
                score += 3
        
        for word in weak_words:
            if word in all_text:
                score -= 5
        
        return max(min(score, 100), 0)
    
    def _evaluate_directness(self, messages: List[Dict]) -> int:
        """Evaluate direct communication"""
        score = 60
        avg_length = sum(len(msg['content']) for msg in messages) / len(messages)
        if avg_length < 100:
            score += 20
        elif avg_length < 150:
            score += 10
        
        direct_indicators = ['bottom line', 'simply', 'directly', 'exactly', 'specifically']
        all_text = ' '.join([msg['content'].lower() for msg in messages])
        
        for indicator in direct_indicators:
            if indicator in all_text:
                score += 8
        
        return min(score, 100)
    
    def _evaluate_value_focus(self, messages: List[Dict]) -> int:
        """Evaluate focus on value and ROI"""
        score = 50
        value_terms = ['save', 'savings', 'roi', 'return', 'investment', 'money', 'cost', 'value', 'benefit', 'profit', 'reduce']
        all_text = ' '.join([msg['content'].lower() for msg in messages])
        
        for term in value_terms:
            if term in all_text:
                score += 5
        
        import re
        if re.search(r'\$\d+|save.*\d+|reduce.*\d+', all_text):
            score += 20
        
        return min(score, 100)
    
    def _evaluate_solar_expertise(self, messages: List[Dict]) -> int:
        """Evaluate solar-specific expertise"""
        score = 50
        solar_terms = ['solar', 'panels', 'photovoltaic', 'pv', 'renewable', 'energy', 'installation', 'system', 'grid', 'metering']
        all_text = ' '.join([msg['content'].lower() for msg in messages])
        
        for term in solar_terms:
            if term in all_text:
                score += 5
        
        return min(score, 100)
    
    def _evaluate_professionalism(self, messages: List[Dict]) -> int:
        """Evaluate professional communication"""
        score = 75
        for msg in messages:
            if len(msg['content']) > 20:
                if msg['content'][0].isupper():
                    score += 2
                if '.' in msg['content'] or '?' in msg['content']:
                    score += 2
        
        return min(score, 100)
    
    def _evaluate_assertiveness(self, messages: List[Dict]) -> int:
        """Evaluate assertiveness in communication"""
        score = 65
        assertive_indicators = ['recommend', 'suggest', 'should', 'will', 'can', 'best']
        all_text = ' '.join([msg['content'].lower() for msg in messages])
        
        for indicator in assertive_indicators:
            if indicator in all_text:
                score += 5
        
        return min(score, 100)
    
    def _evaluate_guidance(self, messages: List[Dict]) -> int:
        """Evaluate guidance provided to passive customer"""
        score = 60
        guidance_words = ['recommend', 'suggest', 'help', 'guide', 'best', 'should', 'typically']
        all_text = ' '.join([msg['content'].lower() for msg in messages])
        
        for word in guidance_words:
            if word in all_text:
                score += 5
        
        return min(score, 100)
    
    def _evaluate_trust_building(self, messages: List[Dict]) -> int:
        """Evaluate trust building efforts"""
        score = 65
        trust_indicators = ['understand', 'help', 'experience', 'customers', 'guarantee', 'promise']
        all_text = ' '.join([msg['content'].lower() for msg in messages])
        
        for indicator in trust_indicators:
            if indicator in all_text:
                score += 5
        
        return min(score, 100)
    
    def _evaluate_recommendations(self, messages: List[Dict]) -> int:
        """Evaluate clear recommendations given"""
        score = 60
        rec_words = ['recommend', 'suggest', 'best choice', 'ideal', 'perfect', 'right for you']
        all_text = ' '.join([msg['content'].lower() for msg in messages])
        
        for word in rec_words:
            if word in all_text:
                score += 8
        
        return min(score, 100)
    
    def _evaluate_reassurance(self, messages: List[Dict]) -> int:
        """Evaluate reassurance provided"""
        score = 70
        reassuring_words = ['safe', 'secure', 'guarantee', 'support', 'help', 'easy']
        all_text = ' '.join([msg['content'].lower() for msg in messages])
        
        for word in reassuring_words:
            if word in all_text:
                score += 4
        
        return min(score, 100)
    
    def _evaluate_expertise_demonstration(self, messages: List[Dict]) -> int:
        """Evaluate expertise demonstration for Tiger customer"""
        score = 60
        expertise_indicators = ['experience', 'expertise', 'professional', 'certified', 'qualified', 'specialist', 'expert']
        all_text = ' '.join([msg['content'].lower() for msg in messages])
        
        for indicator in expertise_indicators:
            if indicator in all_text:
                score += 6
        
        return min(score, 100)
    
    def _evaluate_premium_positioning(self, messages: List[Dict]) -> int:
        """Evaluate premium positioning"""
        score = 55
        premium_words = ['premium', 'best', 'top', 'quality', 'superior', 'excellence', 'luxury']
        all_text = ' '.join([msg['content'].lower() for msg in messages])
        
        for word in premium_words:
            if word in all_text:
                score += 6
        
        return min(score, 100)
    
    def _compile_final_score(self, breakdown: List[ScoreBreakdown], personality: str, msg_count: int) -> SessionScore:
        """Compile final session score"""
        total_score = sum(score.score * score.weight for score in breakdown)
        percentage = total_score
        
        if percentage >= 90:
            grade = "A+"
        elif percentage >= 85:
            grade = "A"
        elif percentage >= 80:
            grade = "B+"
        elif percentage >= 75:
            grade = "B"
        elif percentage >= 70:
            grade = "C+"
        elif percentage >= 65:
            grade = "C"
        elif percentage >= 60:
            grade = "D"
        else:
            grade = "F"
        
        strengths = []
        improvements = []
        
        for score in breakdown:
            if score.score >= 80:
                strengths.append(f"Strong {score.category.lower()}")
            elif score.score < 65:
                improvements.append(f"Improve {score.category.lower()}")
        
        solar_feedback = self._get_solar_specific_feedback(personality, percentage)
        
        return SessionScore(
            overall_score=int(total_score),
            percentage=percentage,
            grade=grade,
            breakdown=breakdown,
            strengths=strengths,
            improvements=improvements,
            solar_specific_feedback=solar_feedback,
            conversation_count=msg_count
        )
    
    def _create_minimal_score(self, personality: str, msg_count: int) -> SessionScore:
        """Create minimal score for short conversations"""
        return SessionScore(
            overall_score=50,
            percentage=50.0,
            grade="C",
            breakdown=[],
            strengths=[],
            improvements=["Have longer conversations", "Provide more detailed responses"],
            solar_specific_feedback="Practice longer conversations to improve your solar sales skills.",
            conversation_count=msg_count
        )
    
    # Feedback methods
    def _get_tech_feedback(self, score: int) -> str:
        if score >= 80:
            return "Excellent technical knowledge demonstrated"
        elif score >= 65:
            return "Good technical understanding, could be more detailed"
        else:
            return "Need more solar technical knowledge"
    
    def _get_patience_feedback(self, score: int) -> str:
        if score >= 80:
            return "Great patience with analytical customer"
        elif score >= 65:
            return "Good patience, avoid rushing responses"
        else:
            return "Show more patience with detailed questions"
    
    def _get_data_feedback(self, score: int) -> str:
        if score >= 80:
            return "Excellent use of data and evidence"
        elif score >= 65:
            return "Good data provision, add more specifics"
        else:
            return "Provide more concrete data and examples"
    
    def _get_confidence_feedback(self, score: int) -> str:
        if score >= 80:
            return "Strong confident communication"
        elif score >= 65:
            return "Good confidence, avoid uncertain language"
        else:
            return "Be more confident and assertive"
    
    def _get_directness_feedback(self, score: int) -> str:
        if score >= 80:
            return "Excellent direct communication"
        elif score >= 65:
            return "Good directness, be more concise"
        else:
            return "Be more direct and to the point"
    
    def _get_value_feedback(self, score: int) -> str:
        if score >= 80:
            return "Strong focus on value and ROI"
        elif score >= 65:
            return "Good value focus, add more specifics"
        else:
            return "Focus more on financial benefits"
    
    def _get_professionalism_feedback(self, score: int) -> str:
        if score >= 80:
            return "Highly professional communication"
        elif score >= 65:
            return "Professional, improve structure"
        else:
            return "Improve professional communication"
    
    def _get_solar_feedback(self, score: int) -> str:
        if score >= 80:
            return "Strong solar expertise shown"
        elif score >= 65:
            return "Good solar knowledge, be more specific"
        else:
            return "Study solar technology more"
    
    def _get_assertiveness_feedback(self, score: int) -> str:
        if score >= 80:
            return "Appropriately assertive approach"
        elif score >= 65:
            return "Good assertiveness, be more decisive"
        else:
            return "Be more assertive in recommendations"
    
    def _get_guidance_feedback(self, score: int) -> str:
        if score >= 80:
            return "Excellent guidance provided"
        elif score >= 65:
            return "Good guidance, be more directive"
        else:
            return "Provide clearer guidance and direction"
    
    def _get_trust_feedback(self, score: int) -> str:
        if score >= 80:
            return "Strong trust building demonstrated"
        elif score >= 65:
            return "Good trust building, add more reassurance"
        else:
            return "Focus more on building customer trust"
    
    def _get_recommendations_feedback(self, score: int) -> str:
        if score >= 80:
            return "Clear, specific recommendations given"
        elif score >= 65:
            return "Good recommendations, be more specific"
        else:
            return "Provide clearer, more specific recommendations"
    
    def _get_reassurance_feedback(self, score: int) -> str:
        if score >= 80:
            return "Excellent reassurance provided"
        elif score >= 65:
            return "Good reassurance, address more concerns"
        else:
            return "Provide more reassurance and support"
    
    def _get_expertise_feedback(self, score: int) -> str:
        if score >= 80:
            return "Strong expertise demonstration"
        elif score >= 65:
            return "Good expertise, showcase more credentials"
        else:
            return "Better demonstrate your solar expertise"
    
    def _get_premium_feedback(self, score: int) -> str:
        if score >= 80:
            return "Excellent premium positioning"
        elif score >= 65:
            return "Good premium approach, emphasize quality more"
        else:
            return "Better position yourself as premium provider"
    
    def _get_solar_specific_feedback(self, personality: str, score: float) -> str:
        """Get personality-specific solar feedback"""
        if personality == "owl":
            if score >= 80:
                return "Excellent handling of analytical solar customer! You provided detailed technical information and showed patience."
            else:
                return "With analytical solar customers, focus on providing specific data, efficiency ratings, and performance studies."
        elif personality == "bull":
            if score >= 80:
                return "Great job with aggressive solar customer! You stayed confident and focused on ROI."
            else:
                return "With aggressive solar customers, be more direct about savings and avoid lengthy technical explanations."
        elif personality == "sheep":
            if score >= 80:
                return "Excellent guidance for passive solar customer! You provided clear recommendations and reassurance."
            else:
                return "With passive solar customers, take charge by providing specific recommendations and building confidence."
        elif personality == "tiger":
            if score >= 80:
                return "Outstanding premium solar positioning! You demonstrated expertise and matched their high standards."
            else:
                return "With dominant solar customers, emphasize your premium credentials and showcase top-tier solar solutions."
        else:
            return "Continue practicing to improve your solar sales skills across different customer types." 