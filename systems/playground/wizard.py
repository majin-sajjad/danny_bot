"""
Personality Creation Wizard
"""

import discord
import logging
import re
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

class PersonalityCreationWizard:
    """Interactive wizard for creating custom personalities"""
    
    def __init__(self, user_id: int, channel_id: int):
        self.user_id = user_id
        self.channel_id = channel_id
        self.step = 0
        self.data = {}
        self.active = True
        
    def get_current_step_info(self) -> Dict:
        """Get information about the current step"""
        steps = [
            {
                "title": "Step 1: Personality Name",
                "description": "What would you like to name your custom customer personality?",
                "prompt": "Enter a creative name for your customer (e.g., 'Tech-Savvy Homeowner', 'Budget-Conscious Family'):",
                "validation": self._validate_name
            },
            {
                "title": "Step 2: Personality Description", 
                "description": "Describe your customer's background and characteristics.",
                "prompt": "Write a brief description of this customer type (2-3 sentences):",
                "validation": self._validate_description
            },
            {
                "title": "Step 3: Customer Behavior",
                "description": "How does this customer typically behave in sales situations?",
                "prompt": "Describe their communication style, decision-making process, and key concerns:",
                "validation": self._validate_behavior
            },
            {
                "title": "Step 4: Conversation Starters",
                "description": "What would this customer say to start a conversation?",
                "prompt": "Provide 3 conversation starters this customer might use, separated by semicolons (;):",
                "validation": self._validate_starters
            },
            {
                "title": "Step 5: Review & Create",
                "description": "Review your custom personality and confirm creation.",
                "prompt": "Review the details below and type 'confirm' to create your personality:",
                "validation": self._validate_confirmation
            }
        ]
        
        if self.step < len(steps):
            return steps[self.step]
        return None
    
    def _validate_name(self, input_text: str) -> Tuple[bool, str]:
        """Validate personality name"""
        name = input_text.strip()
        if len(name) < 3:
            return False, "Name must be at least 3 characters long."
        if len(name) > 50:
            return False, "Name must be 50 characters or less."
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', name):
            return False, "Name can only contain letters, numbers, spaces, hyphens, and underscores."
        
        self.data['name'] = name
        return True, f"Great! Your personality will be named '{name}'."
    
    def _validate_description(self, input_text: str) -> Tuple[bool, str]:
        """Validate personality description"""
        description = input_text.strip()
        if len(description) < 20:
            return False, "Description must be at least 20 characters long."
        if len(description) > 300:
            return False, "Description must be 300 characters or less."
        
        self.data['description'] = description
        return True, "Perfect! Description saved."
    
    def _validate_behavior(self, input_text: str) -> Tuple[bool, str]:
        """Validate behavior description"""
        behavior = input_text.strip()
        if len(behavior) < 30:
            return False, "Behavior description must be at least 30 characters long."
        if len(behavior) > 500:
            return False, "Behavior description must be 500 characters or less."
        
        self.data['behavior'] = behavior
        return True, "Excellent! Behavior pattern saved."
    
    def _validate_starters(self, input_text: str) -> Tuple[bool, str]:
        """Validate conversation starters"""
        starters = [s.strip() for s in input_text.split(';') if s.strip()]
        
        if len(starters) < 2:
            return False, "Please provide at least 2 conversation starters separated by semicolons."
        if len(starters) > 5:
            return False, "Please provide no more than 5 conversation starters."
        
        for starter in starters:
            if len(starter) < 10:
                return False, f"Each starter must be at least 10 characters. '{starter}' is too short."
            if len(starter) > 150:
                return False, f"Each starter must be 150 characters or less. '{starter}' is too long."
        
        self.data['starters'] = starters
        return True, f"Great! {len(starters)} conversation starters saved."
    
    def _validate_confirmation(self, input_text: str) -> Tuple[bool, str]:
        """Validate confirmation"""
        if input_text.strip().lower() == 'confirm':
            return True, "Creating your custom personality..."
        return False, "Please type 'confirm' to create your personality, or share any changes you'd like to make."
    
    def advance_step(self) -> bool:
        """Advance to next step, return True if more steps remain"""
        self.step += 1
        return self.step < 5  # Total number of steps
    
    def get_review_embed(self) -> discord.Embed:
        """Create review embed for final step"""
        embed = discord.Embed(
            title="📋 Review Your Custom Personality",
            description="Please review the details below before creating your personality.",
            color=0x9b59b6
        )
        
        embed.add_field(
            name="👤 Name",
            value=self.data.get('name', 'Not set'),
            inline=False
        )
        
        embed.add_field(
            name="📝 Description",
            value=self.data.get('description', 'Not set'),
            inline=False
        )
        
        embed.add_field(
            name="🎭 Behavior",
            value=self.data.get('behavior', 'Not set')[:200] + "..." if len(self.data.get('behavior', '')) > 200 else self.data.get('behavior', 'Not set'),
            inline=False
        )
        
        starters = self.data.get('starters', [])
        if starters:
            starters_text = "\n".join([f"• {starter}" for starter in starters])
            embed.add_field(
                name="💬 Conversation Starters",
                value=starters_text,
                inline=False
            )
        
        embed.add_field(
            name="✅ Ready to Create?",
            value="Type **confirm** to create your personality, or describe any changes you'd like to make.",
            inline=False
        )
        
        return embed
    
    def create_step_embed(self, step_info: Dict) -> discord.Embed:
        """Create embed for current wizard step"""
        embed = discord.Embed(
            title=f"🧙‍♂️ {step_info['title']}",
            description=step_info['description'],
            color=0x9b59b6
        )
        
        embed.add_field(
            name="📝 Instructions",
            value=step_info['prompt'],
            inline=False
        )
        
        # Add progress indicator
        progress = f"Step {self.step + 1} of 5"
        progress_bar = "█" * (self.step + 1) + "░" * (4 - self.step)
        embed.add_field(
            name="📊 Progress",
            value=f"{progress}\n`{progress_bar}`",
            inline=False
        )
        
        # Add cancel option
        embed.set_footer(text="Type 'cancel' at any time to stop the creation process.")
        
        return embed 