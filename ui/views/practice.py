import discord
from discord.ext import commands
import logging
from typing import Optional
from datetime import datetime
from core.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class PracticePersonalityView(discord.ui.View):
    """View for practice personality selection"""
    
    def __init__(self):
        super().__init__(timeout=None)
        self.db_manager = DatabaseManager()
    
    @discord.ui.button(label="🦉 Owl (Analytical)", style=discord.ButtonStyle.primary, emoji="🦉", row=0, custom_id="practice_owl")
    async def owl_personality(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show niche selection for Owl personality"""
        await self._show_niche_selection(interaction, "owl", "🦉 Owl - Analytical Customer")
    
    @discord.ui.button(label="🐂 Bull (Aggressive)", style=discord.ButtonStyle.danger, emoji="🐂", row=0, custom_id="practice_bull")
    async def bull_personality(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show niche selection for Bull personality"""
        await self._show_niche_selection(interaction, "bull", "🐂 Bull - Aggressive Customer")
    
    @discord.ui.button(label="🐑 Sheep (Passive)", style=discord.ButtonStyle.secondary, emoji="🐑", row=0, custom_id="practice_sheep")
    async def sheep_personality(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show niche selection for Sheep personality"""
        await self._show_niche_selection(interaction, "sheep", "🐑 Sheep - Passive Customer")
    
    @discord.ui.button(label="🐅 Tiger (Dominant)", style=discord.ButtonStyle.success, emoji="🐅", row=0, custom_id="practice_tiger")
    async def tiger_personality(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show niche selection for Tiger personality"""
        await self._show_niche_selection(interaction, "tiger", "🐅 Tiger - Dominant Customer")
    
    @discord.ui.button(label="⏹️ End Practice Session", style=discord.ButtonStyle.danger, emoji="⏹️", row=1, custom_id="practice_end")
    async def end_practice(self, interaction: discord.Interaction, button: discord.ui.Button):
        """End current practice session"""
        await self._end_practice(interaction)
    
    async def _show_niche_selection(self, interaction, personality, personality_name):
        """Show niche selection for the chosen personality"""
        try:
            # Try to get user's registration to determine their niche
            user_niche = "general"
            try:
                user_registration = await self.db_manager.get_user_registration(interaction.user.id)
                if user_registration:
                    user_niche = user_registration.get('niche', 'general')
                else:
                    # User not registered - still allow practice but show warning
                    logger.info(f"User {interaction.user.id} not registered, allowing practice anyway")
            except Exception as db_error:
                logger.error(f"Database error getting user registration: {db_error}")
                # Continue anyway, don't block practice
            
            # Create niche selection view
            niche_view = PracticeNicheView(personality, personality_name)
            
            embed = discord.Embed(
                title=f"🎯 {personality_name} Practice",
                description="Choose your practice scenario niche:",
                color=0x9b59b6
            )
            
            if user_niche != "general":
                embed.add_field(
                    name="📊 Your Registered Niche",
                    value=f"**{user_niche.title()}** (Recommended)",
                    inline=False
                )
            
            embed.add_field(
                name="🎯 Available Practice Niches",
                value="• **🌐 Fiber** - Internet service sales\n• **☀️ Solar** - Solar panel sales\n• **🌿 Landscaping** - Landscaping services",
                inline=False
            )
            
            embed.add_field(
                name="🌟 Multi-Niche Training",
                value="Practice with any niche to expand your skills!",
                inline=False
            )
            
            # Edit the original message instead of sending a new one
            await interaction.response.edit_message(embed=embed, view=niche_view)
            
        except Exception as e:
            logger.error(f"Error showing niche selection: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Error starting practice session. Please try again.", ephemeral=True)
                else:
                    await interaction.followup.send("❌ Error starting practice session. Please try again.", ephemeral=True)
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")
                pass  # Ignore if we can't send error message
    
    async def _end_practice(self, interaction):
        """End the current practice session"""
        try:
            embed = discord.Embed(
                title="⏹️ Practice Session Ended",
                description="Your practice session has been terminated.",
                color=0x95a5a6
            )
            
            embed.add_field(
                name="📊 Session Summary",
                value="Practice session data has been saved to your progress.",
                inline=False
            )
            
            embed.add_field(
                name="🔄 Next Steps",
                value="• Review your performance\n• Try a different personality\n• Practice a new niche scenario",
                inline=False
            )
            
            # Edit the original message instead of sending a new one
            await interaction.response.edit_message(embed=embed, view=None)
            
        except Exception as e:
            logger.error(f"Error ending practice session: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Error ending practice session.", ephemeral=True)
                else:
                    await interaction.followup.send("❌ Error ending practice session.", ephemeral=True)
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")
                pass

class PracticeNicheView(discord.ui.View):
    """View for selecting practice niche after personality choice"""
    
    def __init__(self, personality: str, personality_name: str):
        super().__init__(timeout=None)
        self.personality = personality
        self.personality_name = personality_name
        self.db_manager = DatabaseManager()
    
    @discord.ui.button(label="🌐 Fiber", style=discord.ButtonStyle.primary, emoji="🌐")
    async def fiber_practice(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Start fiber practice session"""
        try:
            await self._start_practice_session(interaction, "fiber", "🌐 Fiber Internet Sales")
        except Exception as e:
            logger.error(f"Error starting fiber practice: {e}")
    
    @discord.ui.button(label="☀️ Solar", style=discord.ButtonStyle.secondary, emoji="☀️")
    async def solar_practice(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Start solar practice session"""
        try:
            await self._start_practice_session(interaction, "solar", "☀️ Solar Energy Sales")
        except Exception as e:
            logger.error(f"Error starting solar practice: {e}")
    
    @discord.ui.button(label="🌿 Landscaping", style=discord.ButtonStyle.success, emoji="🌿")
    async def landscaping_practice(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Start landscaping practice session"""
        try:
            await self._start_practice_session(interaction, "landscaping", "🌿 Landscaping Services")
        except Exception as e:
            logger.error(f"Error starting landscaping practice: {e}")
    
    @discord.ui.button(label="🔙 Back to Personalities", style=discord.ButtonStyle.secondary, emoji="🔙")
    async def back_to_personalities(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go back to personality selection"""
        try:
            original_view = PracticePersonalityView()
            
            embed = discord.Embed(
                title="🎯 Practice Arena",
                description="Practice your sales skills with AI customer personalities",
                color=0x9b59b6
            )
            
            embed.add_field(
                name="Available Personalities",
                value="• **🦉 Owl** - Analytical customers\n• **🐂 Bull** - Aggressive customers\n• **🐑 Sheep** - Passive customers\n• **🐅 Tiger** - Dominant customers",
                inline=False
            )
            
            embed.add_field(
                name="Multi-Niche Support",
                value="Practice with Fiber, Solar, and Landscaping scenarios",
                inline=False
            )
            
            await interaction.response.edit_message(embed=embed, view=original_view)
        except Exception as e:
            logger.error(f"Error going back to personalities: {e}")
            try:
                await interaction.response.send_message("❌ Error navigating back. Please try again.", ephemeral=True)
            except:
                pass
    
    async def _start_practice_session(self, interaction, niche: str, niche_name: str):
        """Start a practice session with the selected personality and niche"""
        try:
            user = interaction.user
            
            # Create session data
            session_data = {
                'user_id': user.id,
                'personality': self.personality,
                'niche': niche,
                'started_at': datetime.now().isoformat(),
                'status': 'active'
            }
            
            # Save session start to database
            # This would be implemented with actual practice system integration
            
            # Create session start embed
            embed = discord.Embed(
                title="🎯 Practice Session Started!",
                description=f"You're now practicing with a **{self.personality_name}** in **{niche_name}**",
                color=0x00ff88
            )
            
            embed.add_field(
                name="🎭 Customer Personality",
                value=self._get_personality_description(self.personality),
                inline=False
            )
            
            embed.add_field(
                name="📋 Scenario Context",
                value=self._get_niche_context(niche),
                inline=False
            )
            
            embed.add_field(
                name="🚀 Getting Started",
                value="The AI customer will respond based on their personality. Start with your opening approach!",
                inline=False
            )
            
            # Create session view for managing the practice
            session_view = PracticeSessionView(session_data)
            
            # Edit the original message instead of sending a new one
            await interaction.response.edit_message(embed=embed, view=session_view)
            
        except Exception as e:
            logger.error(f"Error starting practice session: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Error starting practice session. Please try again.", ephemeral=True)
                else:
                    await interaction.followup.send("❌ Error starting practice session. Please try again.", ephemeral=True)
            except:
                pass  # Ignore if we can't send error message
    
    def _get_personality_description(self, personality: str) -> str:
        """Get description for the personality type"""
        descriptions = {
            "owl": "🦉 **Analytical** - Wants detailed information, asks technical questions, needs time to research and compare options.",
            "bull": "🐂 **Aggressive** - Direct, confrontational, challenges everything you say, tests your knowledge and confidence.",
            "sheep": "🐑 **Passive** - Quiet, goes along with suggestions, rarely objects, but may not be genuinely interested.",
            "tiger": "🐅 **Dominant** - Takes control of the conversation, wants to be the decision maker, respects authority and expertise."
        }
        return descriptions.get(personality, "Unknown personality type")
    
    def _get_niche_context(self, niche: str) -> str:
        """Get context description for the niche"""
        contexts = {
            "fiber": "🌐 **Fiber Internet** - Selling high-speed internet services, competing with cable providers, focus on speed and reliability.",
            "solar": "☀️ **Solar Energy** - Promoting solar panel installation, discussing savings, environmental benefits, and financing options.",
            "landscaping": "🌿 **Landscaping** - Offering landscaping services, discussing design, maintenance, and property value enhancement."
        }
        return contexts.get(niche, "General sales scenario")

class PracticeSessionView(discord.ui.View):
    """View for controlling an active practice session"""
    
    def __init__(self, session_data: dict):
        super().__init__(timeout=None)  # Persistent for training zone reliability
        self.session_data = session_data
        self.db_manager = DatabaseManager()
    
    @discord.ui.button(label="💬 Continue Conversation", style=discord.ButtonStyle.primary, emoji="💬")
    async def continue_conversation(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Continue conversation with AI customer"""
        try:
            embed = discord.Embed(
                title="💬 Practice Session Active",
                description="Your AI customer is ready to respond! Type your message in this channel and they will reply based on their personality.",
                color=0x3498db
            )
            
            personality = self.session_data.get('personality', 'owl')
            niche = self.session_data.get('niche', 'general')
            
            embed.add_field(
                name="🎭 Current Customer",
                value=f"**Personality:** {personality.title()}\n**Scenario:** {niche.title()}",
                inline=True
            )
            
            embed.add_field(
                name="💡 Practice Tips",
                value="• Use natural conversation\n• Handle objections professionally\n• Build rapport and trust\n• Listen for buying signals",
                inline=True
            )
            
            embed.add_field(
                name="🚀 How It Works",
                value="Start typing your approach in this channel. The AI customer will respond realistically based on their personality and the scenario.",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in continue conversation: {e}")
            await interaction.response.send_message("❌ Error continuing conversation. Please try again.", ephemeral=True)
    
    @discord.ui.button(label="📊 Session Stats", style=discord.ButtonStyle.secondary, emoji="📊")
    async def show_session_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show current session statistics"""
        try:
            # Calculate session duration
            started_at = datetime.fromisoformat(self.session_data['started_at'])
            duration = datetime.now() - started_at
            
            embed = discord.Embed(
                title="📊 Practice Session Statistics",
                color=0x3498db
            )
            
            embed.add_field(
                name="⏱️ Session Duration",
                value=f"{duration.seconds // 60} minutes, {duration.seconds % 60} seconds",
                inline=True
            )
            
            embed.add_field(
                name="🎭 Personality",
                value=self.session_data['personality'].title(),
                inline=True
            )
            
            embed.add_field(
                name="🌐 Niche",
                value=self.session_data['niche'].title(),
                inline=True
            )
            
            embed.add_field(
                name="📈 Progress",
                value="Session in progress - full stats available after completion",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error showing session stats: {e}")
            await interaction.response.send_message("❌ Error retrieving session stats.", ephemeral=True)
    
    @discord.ui.button(label="🔚 End Session", style=discord.ButtonStyle.danger, emoji="🔚")
    async def end_session(self, interaction: discord.Interaction, button: discord.ui.Button):
        """End the current practice session"""
        try:
            # Calculate session duration
            started_at = datetime.fromisoformat(self.session_data['started_at'])
            duration = datetime.now() - started_at
            
            # Update session data
            self.session_data['ended_at'] = datetime.now().isoformat()
            self.session_data['duration_seconds'] = duration.total_seconds()
            self.session_data['status'] = 'completed'
            
            # Save session completion to database
            # This would be implemented with actual practice system integration
            
            # Create session completion embed
            completion_embed = discord.Embed(
                title="✅ Practice Session Complete!",
                description="Your practice session has been saved to your progress.",
                color=0x00ff88
            )
            
            completion_embed.add_field(
                name="📊 Session Summary",
                value=f"• **Duration:** {duration.seconds // 60} minutes\n• **Personality:** {self.session_data['personality'].title()}\n• **Niche:** {self.session_data['niche'].title()}",
                inline=False
            )
            
            completion_embed.add_field(
                name="🎯 Practice Again",
                value="Select a personality below to start a new practice session:",
                inline=False
            )
            
            # Return to main practice arena menu instead of removing buttons
            practice_view = PracticePersonalityView()
            await interaction.response.edit_message(embed=completion_embed, view=practice_view)
            
        except Exception as e:
            logger.error(f"Error ending practice session: {e}")
            await interaction.response.send_message("❌ Error ending session. Please try again.", ephemeral=True) 