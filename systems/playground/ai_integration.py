"""
AI Integration for Playground System - Enhanced for Realistic Homeowner Personalities
"""

import logging
import os
import random
from typing import Dict, List
from openai import OpenAI
from models import CustomPersonality

logger = logging.getLogger(__name__)

class PlaygroundAI:
    """Enhanced AI integration for creating realistic homeowner personalities with objections and pushback"""
    
    def __init__(self):
        self.client = None
        
        # Niche-specific objection patterns
        self.niche_objections = {
            'fiber': [
                "We already have internet that works fine",
                "I'm locked into a contract with my current provider",
                "How do I know your service won't go down all the time?",
                "The installation seems too disruptive to my home",
                "I've heard fiber is overpriced for what you get",
                "We barely use the internet anyway",
                "I don't trust door-to-door sales"
            ],
            'solar': [
                "Solar panels are too expensive upfront",
                "I don't think my roof gets enough sun",
                "I've heard they damage your roof during installation",
                "What happens when it's cloudy or winter?",
                "I'm planning to move in a few years",
                "My electric bill isn't that high anyway",
                "I don't want to deal with maintenance issues"
            ],
            'landscaping': [
                "We like doing our own yard work",
                "I don't have the budget for landscaping right now",
                "I'm not sure what I even want done",
                "How do I know you won't damage my plants?",
                "I need to check with my spouse first",
                "The timing isn't right with the season",
                "I've had bad experiences with contractors before"
            ]
        }
        
        # Personality archetypes for homeowners
        self.personality_archetypes = {
            'skeptical_budget_conscious': {
                'traits': 'Very careful with money, questions everything, wants proof of value',
                'behavior': 'Asks lots of questions about cost, compares to competitors, negotiates'
            },
            'busy_professional': {
                'traits': 'Time-pressed, values efficiency, decisive when convinced',
                'behavior': 'Checks watch frequently, wants quick answers, appreciates expertise'
            },
            'friendly_neighbor': {
                'traits': 'Polite but cautious, wants to help but protective of family',
                'behavior': 'Listens but asks about guarantees, references, and safety'
            },
            'tech_savvy_researcher': {
                'traits': 'Knowledgeable, does homework, asks technical questions',
                'behavior': 'Tests your knowledge, brings up competitor features, wants specs'
            },
            'family_focused': {
                'traits': 'Prioritizes family needs and safety, makes joint decisions',
                'behavior': 'Asks about impact on kids, wants spouse input, values stability'
            },
            'early_retiree': {
                'traits': 'Fixed income mindset, cautious about changes, values reliability',
                'behavior': 'Concerned about long-term costs, wants proven track record'
            }
        }
    
    def _get_client(self):
        """Lazy initialization of OpenAI client"""
        if self.client is None:
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            self.client = OpenAI(api_key=api_key)
        return self.client
    
    async def generate_enhanced_homeowner_personality(self, wizard_data: Dict) -> str:
        """Generate a comprehensive homeowner personality with realistic objections and persuasion patterns"""
        try:
            # Extract niche from wizard data
            niche = wizard_data.get('niche', '').lower()
            if niche not in self.niche_objections:
                niche = 'solar'  # default
            
            # Select random personality archetype
            archetype_name = random.choice(list(self.personality_archetypes.keys()))
            archetype = self.personality_archetypes[archetype_name]
            
            # Get niche-specific objections
            objections = random.sample(self.niche_objections[niche], 3)
            
            prompt = f"""Create an ADVANCED SYSTEM PROMPT for an AI playing a realistic HOMEOWNER in "Lord of the Doors Season 3" door-to-door sales training. This homeowner should provide CHALLENGING but FAIR training for {niche} salespeople.

🏠 HOMEOWNER PROFILE:
Name: {wizard_data['name']}
Basic Description: {wizard_data['description']}
Personality Archetype: {archetype_name.replace('_', ' ').title()}
Core Traits: {archetype['traits']}
Behavioral Pattern: {archetype['behavior']}

🎯 NICHE: {niche.upper()} SALES TRAINING

🚪 ADVANCED TRAINING REQUIREMENTS:

**OBJECTION PATTERNS:** This homeowner will initially present these realistic objections:
1. {objections[0]}
2. {objections[1]}
3. {objections[2]}

**PERSUASION FRAMEWORK:** The homeowner CAN be persuaded if the salesperson:
- Demonstrates genuine expertise in {niche}
- Addresses concerns with specific solutions
- Builds trust through professional approach
- Shows clear value proposition
- Handles objections without being pushy

**HOMEOWNER PSYCHOLOGY:**
- Initially skeptical but not impossible to convince
- Has real concerns that need addressing
- Values honesty and transparency
- Can become interested if approached correctly
- Makes decisions based on logic + emotion

**CONVERSATION FLOW:**
1. INITIAL RESISTANCE (60% of interaction) - Present objections, show skepticism
2. OBJECTION HANDLING (25% of interaction) - Test salesperson's responses
3. POTENTIAL INTEREST (15% of interaction) - Show openness if well-handled

**REALISTIC BEHAVIORS:**
- Use natural speech patterns with interruptions
- Show time pressure and distractions
- Ask follow-up questions when interested
- Reference past experiences (good/bad)
- Mention spouse/family considerations
- Display authentic emotional responses

**SUCCESS TRIGGERS:** Show increased interest when salesperson:
- Provides specific benefits for your situation
- Offers credible proof/references
- Addresses your main concerns directly
- Respects your time and intelligence
- Demonstrates {niche} expertise

Create a detailed system prompt that makes this homeowner CHALLENGING but FAIR - they should give realistic pushback but be persuadable by skilled salespeople. The goal is to train world-class door-to-door sales professionals.

Return ONLY the complete system prompt text."""

            response = self._get_client().chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1200,
                temperature=0.8
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating enhanced homeowner personality: {e}")
            return self._create_enhanced_fallback_prompt(wizard_data)
    
    def _create_enhanced_fallback_prompt(self, wizard_data: Dict) -> str:
        """Create enhanced fallback system prompt with objections and persuasion patterns"""
        niche = wizard_data.get('niche', 'solar').lower()
        objections = self.niche_objections.get(niche, self.niche_objections['solar'])[:3]
        
        return f"""🚪 LORD OF THE DOORS SEASON 3 - ADVANCED HOMEOWNER TRAINING 🚪

You are {wizard_data['name']}, a HOMEOWNER who just had someone knock on your door unexpectedly. You're being approached about {niche} services.

🏠 YOUR HOMEOWNER MINDSET:
- You were NOT expecting this visit - you're busy with your day
- You're naturally skeptical of door-to-door salespeople
- You have legitimate concerns about {niche} services
- BUT you CAN be persuaded if approached professionally

🎯 YOUR OBJECTION PATTERN:
You will initially present these concerns:
1. "{objections[0]}"
2. "{objections[1]}"  
3. "{objections[2]}"

🧠 PERSUASION PSYCHOLOGY:
You CAN become interested if the salesperson:
✅ Shows genuine {niche} expertise
✅ Addresses your specific concerns
✅ Provides credible proof/references
✅ Respects your time and intelligence
✅ Offers clear value for your situation

❌ You will remain resistant if they:
❌ Are pushy or ignore your concerns
❌ Can't answer technical questions
❌ Seem scripted or inexperienced
❌ Don't understand your specific needs

🎭 PERSONALITY: {wizard_data['description']}

🗣️ CONVERSATION STYLE:
- Start with polite but clear skepticism
- Present realistic homeowner objections
- Ask follow-up questions to test their knowledge
- Show slight interest if they handle objections well
- Make them EARN your trust through competence
- Use natural speech with realistic interruptions

🏆 TRAINING GOAL: Challenge the salesperson with real objections while being fair enough that skilled professionals can persuade you. Help them become better by being a realistic homeowner!

Remember: You're helping train future {niche} sales legends by being an authentic, challenging but fair homeowner."""

    async def generate_system_prompt(self, wizard_data: Dict) -> str:
        """Generate enhanced system prompt (backward compatibility)"""
        return await self.generate_enhanced_homeowner_personality(wizard_data)
    
    async def generate_conversation_starter(self, homeowner_data: Dict, niche: str) -> str:
        """Generate a realistic conversation starter for the homeowner"""
        try:
            prompt = f"""Generate a realistic FIRST RESPONSE for this homeowner when someone knocks on their door selling {niche} services:

HOMEOWNER: {homeowner_data['name']}
PERSONALITY: {homeowner_data.get('personality_description', 'Typical homeowner')}
NICHE: {niche}

The homeowner just heard someone knock on their door. Create their FIRST realistic response - this could be:
- Opening the door and asking who's there
- Speaking through the door first
- Opening with slight annoyance at being interrupted
- Being polite but cautious

Keep it under 30 words and make it sound natural. Examples:
- "Yes? Can I help you with something?"
- "Hi there... I wasn't expecting anyone. What's this about?"
- "Sorry, but if you're selling something, I'm really not interested."

Return ONLY the homeowner's first response."""

            response = self._get_client().chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.9
            )
            
            return response.choices[0].message.content.strip().replace('"', '')
            
        except Exception as e:
            logger.error(f"Error generating conversation starter: {e}")
            return "Hi there... I wasn't expecting anyone. What's this about?"
    
    async def generate_optimization_suggestions(self, personality: CustomPersonality) -> Dict:
        """Generate optimization suggestions for a personality"""
        try:
            prompt = f"""Analyze this custom homeowner personality for the "Lord of the Doors Season 3" sales training environment and provide optimization suggestions:

CURRENT PERSONALITY:
Name: {personality.name}
Description: {personality.description}
System Prompt: {personality.system_prompt[:500]}...

OPTIMIZATION AREAS TO ANALYZE:
1. Realism - Does this homeowner act like a real person would?
2. Training Value - Does this personality provide good sales training?
3. Engagement - Is this personality interesting to practice with?
4. Authenticity - Are the reactions and objections realistic?
5. Challenge Level - Does this provide appropriate difficulty for salespeople?

Provide specific suggestions in these categories:
- PERSONALITY_IMPROVEMENTS: Ways to make the homeowner more realistic
- CONVERSATION_STARTERS: Better opening lines this homeowner might use
- OBJECTIONS: More realistic objections this homeowner type would have
- ENGAGEMENT: Ways to make interactions more interesting
- TRAINING_VALUE: How to better challenge salespeople-in-training

Format your response with clear sections marked by the categories above."""

            response = self._get_client().chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )
            
            return self._parse_optimization_response(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error generating optimization suggestions: {e}")
            return {
                'personality_improvements': "No suggestions available at this time.",
                'conversation_starters': [],
                'objections': "No suggestions available.",
                'engagement': "No suggestions available.",
                'training_value': "No suggestions available."
            }
    
    def _parse_optimization_response(self, response_text: str) -> Dict:
        """Parse the optimization response into structured data"""
        sections = {
            'personality_improvements': self._extract_section(response_text, "PERSONALITY_IMPROVEMENTS", "CONVERSATION_STARTERS"),
            'conversation_starters': self._extract_conversation_starters(response_text),
            'objections': self._extract_section(response_text, "OBJECTIONS", "ENGAGEMENT"),
            'engagement': self._extract_section(response_text, "ENGAGEMENT", "TRAINING_VALUE"),
            'training_value': self._extract_section(response_text, "TRAINING_VALUE", None)
        }
        
        return sections
    
    def _extract_section(self, text: str, start_marker: str, end_marker: str) -> str:
        """Extract a section from AI response text"""
        try:
            start_idx = text.find(start_marker)
            if start_idx == -1:
                return "No suggestions available."
            
            start_idx = text.find(":", start_idx) + 1
            
            if end_marker:
                end_idx = text.find(end_marker, start_idx)
                if end_idx == -1:
                    section = text[start_idx:].strip()
                else:
                    section = text[start_idx:end_idx].strip()
            else:
                section = text[start_idx:].strip()
            
            return section.strip()
        except:
            return "No suggestions available."
    
    def _extract_conversation_starters(self, text: str) -> List[str]:
        """Extract conversation starters from AI response"""
        try:
            section = self._extract_section(text, "CONVERSATION_STARTERS", "OBJECTIONS")
            
            # Look for bullet points, numbered lists, or quoted strings
            import re
            starters = []
            
            # Match lines that start with -, *, numbers, or quotes
            matches = re.findall(r'[•\-\*]\s*"([^"]+)"', section)
            if matches:
                starters.extend(matches)
            else:
                # Fallback: split by newlines and clean up
                lines = section.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and len(line) > 10 and not line.lower().startswith('no suggestions'):
                        # Clean up formatting
                        line = re.sub(r'^[•\-\*\d\.\s]+', '', line)
                        line = line.strip('"\'')
                        if line:
                            starters.append(line)
            
            return starters[:5]  # Limit to 5 starters
            
        except:
            return [] 