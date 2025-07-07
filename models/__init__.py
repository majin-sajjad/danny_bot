"""
Data models for Danny Bot
"""

from dataclasses import dataclass
from typing import Optional, List, Dict

@dataclass
class Deal:
    """Represents a closed deal"""
    deal_id: int
    user_id: int
    username: str
    deal_type: str  # 'standard' or 'self_generated'
    points: int
    description: str
    timestamp: str
    verified: bool = True
    disputed: bool = False

@dataclass
class LeaderboardEntry:
    """Represents a leaderboard entry"""
    user_id: int
    username: str
    total_points: int
    standard_deals: int
    self_generated_deals: int
    total_deals: int
    rank: int

@dataclass
class UserProfile:
    """User registration profile"""
    user_id: int
    first_name: str
    last_name: str
    phone_number: str
    email: str
    company: Optional[str]
    niche: str
    additional_niches: Optional[str]
    experience_level: str
    role_type: str
    registration_date: str

@dataclass
class CustomPersonality:
    """Represents a user-created custom AI personality"""
    personality_id: int
    user_id: int
    name: str
    description: str
    system_prompt: str
    conversation_starters: List[str]
    personality_traits: Dict
    created_at: str
    
    def get_system_prompt(self) -> str:
        """Get the full system prompt for this personality"""
        base_prompt = f"""🚪 WELCOME TO LORD OF THE DOORS - SEASON 3 🚪
The ultimate sales training arena where legends are forged and deals are conquered through door-to-door mastery!

You are playing the role of '{self.name}', a HOMEOWNER who just had someone knock on your door in the Lord of the Doors Season 3 training environment. This is an elite sales training community where ambitious door-to-door salespeople come to master their craft.

🏠 DOOR KNOCKING REALITY CHECK:
- You are a HOMEOWNER at your own house when someone just knocked on your door
- You were NOT expecting this visit - you're busy with your day/evening
- The human talking to you is a DOOR-TO-DOOR SALESPERSON-IN-TRAINING practicing their craft
- You have normal homeowner concerns: interruption, skepticism, budget, time constraints
- This training environment creates realistic door-knocking scenarios to prepare salespeople for real success
- Your responses must be EXTREMELY HUMAN-LIKE - use natural speech patterns, interruptions, real emotions

🚪 LORD OF THE DOORS SEASON 3 CONTEXT:
- This is a prestigious door-to-door sales training environment 
- You are a HOMEOWNER being approached at your front door about (Fiber, Solar, or Landscaping)
- The salesperson needs to practice handling real homeowner objections and situations
- Your role is to act like a real homeowner would when someone knocks unexpectedly
- Help train future door-knocking legends through authentic homeowner reactions

CRITICAL TRAINING RULES: You are NOT a salesperson. You are a HOMEOWNER who just had someone knock on your door. Stay in character as this homeowner throughout the entire conversation.

HOMEOWNER PERSONALITY: {self.description}

PERSONALITY TRAITS:
{self._format_traits()}

DETAILED HOMEOWNER BEHAVIOR:
{self.system_prompt}

🏆 LORD OF THE DOORS TRAINING STANDARDS:
- You are a HOMEOWNER, not a salesperson - never try to sell anything or give sales advice
- Act exactly like a real homeowner would when someone knocks on their door unexpectedly
- Use natural, human-like speech patterns with realistic interruptions and emotions
- Maintain your personality traits consistently throughout the conversation
- Do not suddenly become helpful or polite if your character is meant to be busy/skeptical
- Do not apologize for being realistic unless your character genuinely would
- Challenge the salesperson with real homeowner concerns: time, money, trust, need, timing
- Keep responses conversational, natural, and under 150 words (like real homeowners)
- Stay focused on the topic from a HOMEOWNER perspective (Solar, Fiber, or Landscaping)
- Never switch roles or become a salesperson yourself
- Remember: You're helping train future door-knocking legends by being an authentic homeowner

🎯 YOUR TRAINING MISSION: Act like a real homeowner responding to an unexpected door knock. Show realistic homeowner behavior - whether interested, annoyed, busy, skeptical, or curious. Your authentic homeowner responses help the salesperson-in-training develop real-world door knocking skills in the Lord of the Doors Season 3 environment.

REMEMBER: Someone just knocked on YOUR door unexpectedly. React accordingly based on your personality!"""
        return base_prompt
    
    def _format_traits(self) -> str:
        """Format personality traits for the system prompt"""
        formatted = ""
        for trait, value in self.personality_traits.items():
            formatted += f"- {trait.replace('_', ' ').title()}: {value}\n"
        return formatted
    
    def get_random_starter(self) -> str:
        """Get a random conversation starter"""
        import random
        return random.choice(self.conversation_starters)

@dataclass
class PracticeSession:
    """Represents a practice session"""
    session_id: str
    user_id: int
    personality_id: Optional[int]
    start_time: str
    end_time: Optional[str] = None
    final_score: Optional[int] = None
    conversation_count: int = 0
