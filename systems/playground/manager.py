"""
Enhanced Playground Management System with AI Conversation Practice
"""

import discord
from discord.ext import commands
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from core.database_manager import DatabaseManager
from .database import PlaygroundDatabase
from .ai_integration import PlaygroundAI
import asyncio

logger = logging.getLogger(__name__)

class PlaygroundManager(commands.Cog):
    """Enhanced playground system with AI-driven door-to-door sales practice"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = PlaygroundDatabase()
        self.database_manager = DatabaseManager()
        self.ai = PlaygroundAI()
        self.active_practice_sessions = {}  # user_id -> session_data
        
    async def cog_load(self):
        """Initialize playground database"""
        await self.db.setup_database()
        # 🔧 NEW: Restore active practice sessions from database
        await self._restore_active_sessions()
        logger.info("Playground system loaded successfully")
    
    async def _restore_active_sessions(self):
        """Restore active practice sessions from database on startup"""
        try:
            # Get all active practice sessions from database
            sessions = await self.db.get_active_sessions()
            
            for session_data in sessions:
                user_id = session_data['user_id']
                
                # Restore session to active sessions
                self.active_practice_sessions[user_id] = {
                    'session_id': session_data['session_id'],
                    'personality_id': session_data['personality_id'],
                    'homeowner_data': session_data.get('homeowner_data', {}),
                    'conversation_history': session_data.get('conversation_history', []),
                    'status': 'active',
                    'start_time': session_data.get('start_time')
                }
                
                logger.info(f"Restored playground session for user {user_id}")
                
            logger.info(f"Successfully restored {len(self.active_practice_sessions)} active playground sessions")
            
        except Exception as e:
            logger.error(f"Error restoring active sessions: {e}")
            # Don't raise here, just log - system can continue without restored sessions
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle AI conversation practice in training zone channels"""
        # Skip bot messages
        if message.author.bot:
            return
            
        # Check if this is a training zone channel with active practice
        if not self._is_training_zone_channel(message.channel):
            return
            
        user_id = message.author.id
        
        # Check if user has an active practice session
        if user_id not in self.active_practice_sessions:
            return
            
        session_data = self.active_practice_sessions[user_id]
        
        # Check if the session is active and in the right channel
        if session_data.get('status') != 'active':
            return
            
        # Process the conversation with the AI homeowner
        await self._handle_practice_conversation(message, session_data)
    
    def _is_training_zone_channel(self, channel) -> bool:
        """Check if this is a channel where practice conversations can happen"""
        # Training zones have specific naming patterns
        training_keywords = ['training', 'practice', 'playground', 'door-knocking', 'sales-practice', 'library']
        channel_name = channel.name.lower()
        
        # Also check for specific playground library channels
        playground_keywords = ['playground-library', 'homeowner-library', 'ai-practice']
        
        return (any(keyword in channel_name for keyword in training_keywords) or 
                any(keyword in channel_name for keyword in playground_keywords) or
                'playground' in channel.category.name.lower() if channel.category else False)
    
    async def _handle_practice_conversation(self, message: discord.Message, session_data: Dict):
        """Handle AI conversation between user and homeowner personality"""
        try:
            # Get homeowner data
            homeowner_data = session_data['homeowner_data']
            
            # Check if this is the first message (door knock)
            if 'conversation_history' not in session_data:
                session_data['conversation_history'] = []
                
                # Generate the homeowner's first response to the door knock
                first_response = await self.ai.generate_conversation_starter(
                    homeowner_data, 
                    homeowner_data['niche']
                )
                
                # Show typing indicator
                async with message.channel.typing():
                    await asyncio.sleep(2)  # Realistic typing delay
                
                # Send homeowner's first response
                embed = discord.Embed(
                    title=f"🚪 {homeowner_data['name']} (Homeowner)",
                    description=first_response,
                    color=0xe67e22
                )
                
                embed.set_footer(text=f"{homeowner_data['niche'].title()} Practice Session • Type your response naturally")
                
                await message.channel.send(embed=embed)
                
                # Add to conversation history
                session_data['conversation_history'].append({
                    'role': 'user', 
                    'content': message.content,
                    'timestamp': datetime.now().isoformat()
                })
                session_data['conversation_history'].append({
                    'role': 'homeowner', 
                    'content': first_response,
                    'timestamp': datetime.now().isoformat()
                })
                
                return
            
            # Add user message to history
            session_data['conversation_history'].append({
                'role': 'user',
                'content': message.content,
                'timestamp': datetime.now().isoformat()
            })
            
            # Generate AI response using the enhanced personality system
            ai_response = await self._generate_homeowner_response(
                message.content,
                homeowner_data,
                session_data['conversation_history']
            )
            
            # Show typing indicator for realism
            async with message.channel.typing():
                await asyncio.sleep(1.5)
            
            # Send homeowner response
            embed = discord.Embed(
                title=f"🏠 {homeowner_data['name']} (Homeowner)",
                description=ai_response,
                color=0xe67e22
            )
            
            # Add contextual footer based on conversation progress
            conversation_count = len([msg for msg in session_data['conversation_history'] if msg['role'] == 'user'])
            if conversation_count <= 3:
                footer_text = f"{homeowner_data['niche'].title()} Practice • Building rapport..."
            elif conversation_count <= 6:
                footer_text = f"{homeowner_data['niche'].title()} Practice • Handling objections..."
            else:
                footer_text = f"{homeowner_data['niche'].title()} Practice • Closing opportunity..."
                
            embed.set_footer(text=footer_text)
            
            await message.channel.send(embed=embed)
            
            # Add AI response to history
            session_data['conversation_history'].append({
                'role': 'homeowner',
                'content': ai_response,
                'timestamp': datetime.now().isoformat()
            })
            
            # Check if session should end (natural conclusion or length)
            if self._should_end_session(session_data):
                await self._end_practice_session(message.channel, session_data)
                
        except Exception as e:
            logger.error(f"Error handling practice conversation: {e}")
            await message.channel.send("❌ **Practice Session Error** - Please try starting a new practice session.")
    
    async def _generate_homeowner_response(self, user_message: str, homeowner_data: Dict, conversation_history: List) -> str:
        """Generate realistic homeowner response using enhanced AI system"""
        try:
            # Build conversation context
            conversation_context = "\n".join([
                f"{'Salesperson' if msg['role'] == 'user' else 'Homeowner'}: {msg['content']}"
                for msg in conversation_history[-6:]  # Last 6 messages for context
            ])
            
            prompt = f"""You are {homeowner_data['name']}, a homeowner in a door-to-door sales training scenario.

ENHANCED PERSONALITY PROMPT:
{homeowner_data.get('ai_enhanced_description', homeowner_data['personality_description'])}

CURRENT CONVERSATION:
{conversation_context}

LATEST SALESPERSON MESSAGE: "{user_message}"

Respond as this homeowner would naturally respond. Remember:
- You're helping train a {homeowner_data['niche']} salesperson
- Give realistic objections but can be persuaded if they do well
- Keep responses under 100 words and conversational
- Use natural speech patterns with realistic interruptions
- Show your personality consistently

Your response as {homeowner_data['name']}:"""

            response = self.ai._get_client().chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.8
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating homeowner response: {e}")
            return f"*{homeowner_data['name']} seems distracted* Sorry, could you repeat that?"
    
    def _should_end_session(self, session_data: Dict) -> bool:
        """Determine if practice session should naturally end"""
        conversation_count = len([msg for msg in session_data['conversation_history'] if msg['role'] == 'user'])
        
        # End after 10-15 exchanges or if homeowner indicates session should end
        if conversation_count >= 12:
            return True
            
        # Check last homeowner response for ending indicators
        last_homeowner_msg = None
        for msg in reversed(session_data['conversation_history']):
            if msg['role'] == 'homeowner':
                last_homeowner_msg = msg['content'].lower()
                break
                
        if last_homeowner_msg:
            ending_phrases = [
                'need to go', 'have to run', 'not interested', 'no thanks',
                'think about it', 'call you back', 'maybe later', 'husband/wife'
            ]
            if any(phrase in last_homeowner_msg for phrase in ending_phrases):
                return True
                
        return False
    
    async def _end_practice_session(self, channel: discord.TextChannel, session_data: Dict):
        """End the practice session and provide feedback"""
        try:
            user_id = session_data['user_id']
            homeowner_data = session_data['homeowner_data']
            conversation_history = session_data['conversation_history']
            
            # Generate session summary
            user_messages = [msg for msg in conversation_history if msg['role'] == 'user']
            session_duration = len(user_messages)
            
            # Remove from active sessions
            if user_id in self.active_practice_sessions:
                del self.active_practice_sessions[user_id]
            
            # Create session summary embed
            embed = discord.Embed(
                title="🎯 Practice Session Complete!",
                description=f"Your door-knocking practice with **{homeowner_data['name']}** has ended.",
                color=0x00ff88
            )
            
            embed.add_field(
                name="📊 Session Stats",
                value=f"**Duration:** {session_duration} exchanges\n**Niche:** {homeowner_data['niche'].title()}\n**Homeowner:** {homeowner_data['name']}",
                inline=False
            )
            
            embed.add_field(
                name="🎓 What's Next",
                value="• Practice with different homeowner personalities\n• Try the same homeowner again with a different approach\n• Create your own custom homeowner personalities",
                inline=False
            )
            
            embed.set_footer(text="Great job practicing! Every conversation makes you better at door-to-door sales.")
            
            await channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error ending practice session: {e}")
    
    async def start_practice_session(self, user_id: int, homeowner_data: Dict, channel: discord.TextChannel):
        """Start a new AI practice session"""
        try:
            session_data = {
                'user_id': user_id,
                'homeowner_data': homeowner_data,
                'channel_id': channel.id,
                'started_at': datetime.now().isoformat(),
                'status': 'active'
            }
            
            # Store active session
            self.active_practice_sessions[user_id] = session_data
            
            # Send initial practice instructions
            embed = discord.Embed(
                title="🚪 Door Knocking Practice Started!",
                description=f"You're now at the door of **{homeowner_data['name']}**",
                color=0x3498db
            )
            
            embed.add_field(
                name="🎯 Your Mission",
                value=f"Practice your {homeowner_data['niche']} sales approach with this homeowner. They will respond realistically based on their personality and may have objections.",
                inline=False
            )
            
            embed.add_field(
                name="🚀 Getting Started",
                value="**Knock on their door!** Type your opening approach in this channel. They'll respond just like a real homeowner would.",
                inline=False
            )
            
            embed.add_field(
                name="💡 Pro Tips",
                value="• Be natural and conversational\n• Handle objections professionally\n• Build rapport and trust\n• Listen for buying signals",
                inline=False
            )
            
            embed.set_footer(text=f"{homeowner_data['niche'].title()} Practice Session • Type your door knock!")
            
            await channel.send(embed=embed)
            
            logger.info(f"Started practice session for user {user_id} with homeowner {homeowner_data['name']}")
            
        except Exception as e:
            logger.error(f"Error starting practice session: {e}")

async def setup(bot):
    """Setup function for the playground manager"""
    await bot.add_cog(PlaygroundManager(bot)) 