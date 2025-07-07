import discord
from discord.ext import commands
import logging
import aiosqlite
import asyncio

logger = logging.getLogger(__name__)

class TrainingZoneManager(commands.Cog):
    """Manages user training zones creation and setup"""
    
    def __init__(self, bot):
        self.bot = bot
        from core.database_manager import DatabaseManager
        self.db_manager = DatabaseManager()
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle messages in training zones for AI responses"""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Check if this is a training zone channel
        if not message.channel.category or "Training Zone" not in message.channel.category.name:
            return
        
        # Check if this is a Danny Clone Mentor channel
        if "danny-clone-mentor" in message.channel.name.lower():
            try:
                # Get user's registered name and niche
                user_registration = await self.db_manager.get_user_registration(message.author.id)
                user_name = "Champion"
                user_niche = "sales"
                
                if user_registration:
                    user_name = user_registration.get('first_name', 'Champion')
                    user_niche = user_registration.get('niche', 'sales')
                
                # Generate AI response as Danny Clone
                ai_response = await self._generate_danny_response(message.content, user_name, user_niche)
                
                if ai_response:
                    # Simple send - let's see if the issue was just the token limit
                    await message.channel.send(ai_response)
                
            except Exception as e:
                logger.error(f"Error generating Danny AI response: {e}")
        
        # Check if this is a practice arena session
        elif "practice-arena" in message.channel.name.lower() or "practice" in message.channel.name.lower():
            try:
                # Check if there's an active practice session
                await self._handle_practice_session_message(message)
                
            except Exception as e:
                logger.error(f"Error handling practice session message: {e}")
    
    async def _handle_practice_session_message(self, message):
        """Handle messages during practice sessions with AI customer responses"""
        try:
            # For now, create a simple practice response system
            # This would be enhanced with actual session tracking
            
            # Generate AI customer response based on message content
            customer_response = await self._generate_practice_customer_response(
                message.content, 
                "owl",  # Default personality, would be from session data
                "general"  # Default niche, would be from session data
            )
            
            if customer_response:
                # Send response with slight delay to feel more natural
                await asyncio.sleep(2)
                await message.channel.send(f"**🎭 AI Customer:** {customer_response}")
                
        except Exception as e:
            logger.error(f"Error generating practice customer response: {e}")
    
    async def _generate_practice_customer_response(self, user_message: str, personality: str, niche: str) -> str:
        """Generate AI customer response for practice sessions"""
        try:
            # Import AI engine
            from ai_response_engine import AIResponseEngine
            ai_engine = AIResponseEngine()
            
            # Create personality context
            personality_prompts = {
                "owl": "You are an analytical customer who asks detailed questions and wants to see data and proof before making decisions.",
                "bull": "You are an aggressive, impatient customer who is skeptical and challenges everything the salesperson says.",
                "sheep": "You are a passive, indecisive customer who is easily influenced but needs reassurance and guidance.",
                "tiger": "You are a dominant, confident customer who takes charge of conversations and has strong opinions."
            }
            
            niche_contexts = {
                "fiber": "This is about fiber internet services and installation.",
                "solar": "This is about solar panel installation and renewable energy.",
                "landscaping": "This is about landscaping services and outdoor improvements.",
                "general": "This is a general sales scenario."
            }
            
            personality_context = personality_prompts.get(personality, personality_prompts["owl"])
            niche_context = niche_contexts.get(niche, niche_contexts["general"])
            
            system_prompt = f"""You are playing a customer personality in a sales training scenario. {personality_context} {niche_context}

IMPORTANT: Keep responses under 100 words and act like a real customer would when being approached by a salesperson. You can be interested, skeptical, busy, or curious - whatever fits your personality. Do not be overly helpful or break character.

Respond naturally to: "{user_message}" """
            
            response = await ai_engine.generate_response(system_prompt, user_message)
            return response
            
        except Exception as e:
            logger.error(f"Error generating practice response: {e}")
            return None
    
    async def _generate_danny_response(self, user_message: str, user_name: str, user_niche: str) -> str:
        """Generate Danny Clone Mentor response"""
        try:
            # Import AI engine
            from ai_response_engine import AIResponseEngine
            ai_engine = AIResponseEngine()
            
            # Create Danny Pessy system prompt
            system_prompt = f"""You are Danny Pessy, a high-energy, motivational door-to-door sales coach and mentor. You're talking to {user_name}, who works in {user_niche}. 

🔥 YOUR PERSONALITY:
- HIGH ENERGY and motivational (use caps, exclamation points, fire emojis)
- Direct, practical advice mixed with emotional pump-ups
- Comedian's charisma + relentless hustle + emotional resilience
- You help people become UNSTOPPABLE door-to-door sales machines

💪 YOUR COACHING STYLE:
- Start responses with high-energy greetings ("YO {user_name}!" or "WHAT'S UP CHAMPION!")
- Mix practical tactics with mindset coaching
- Always end with motivational call-to-action
- Use sales terminology and door-knocking language
- Reference overcoming rejection, building confidence, crushing objections

🎯 RESPONSE FORMAT:
- Keep responses UNDER 250 words (Discord limit is 2000 characters)
- Include practical tactics AND motivation
- Use emojis (🔥💪🚀⚡💥) 
- Always pump them up for action
- Be concise but impactful

Remember: You're here to make {user_name} an absolute LEGEND at {user_niche} door-to-door sales!"""
            
            response = await ai_engine.generate_response(system_prompt, user_message)
            return response
            
        except Exception as e:
            logger.error(f"Error generating Danny response: {e}")
            # Fallback response
            return f"🔥 YO {user_name}! I'm having some technical difficulties right now, but I'm still here to help you CRUSH those doors! 💪 Try asking me again in a moment!"

    async def _send_long_message(self, channel, message: str):
        """Send a message that might exceed Discord's 2000 character limit"""
        if len(message) <= 2000:
            # Message is within limit, send normally
            await channel.send(message)
        else:
            # Message is too long, split it intelligently
            parts = []
            current_part = ""
            
            # Split by sentences first (look for periods, exclamation marks, question marks)
            import re
            sentences = re.split(r'([.!?])', message)
            
            for i in range(0, len(sentences) - 1, 2):
                sentence = sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else "")
                
                if len(current_part + sentence) <= 1950:  # Leave some buffer
                    current_part += sentence
                else:
                    if current_part:
                        parts.append(current_part.strip())
                        current_part = sentence
                    else:
                        # Single sentence too long, truncate
                        parts.append(sentence[:1950] + "...")
                        break
            
            if current_part:
                parts.append(current_part.strip())
            
            # Send all parts
            for part in parts:
                if part.strip():
                    await channel.send(part)

    async def create_user_training_zone(self, guild, user):
        """Create a complete training zone for a user"""
        try:
            # Check if user already has a training zone
            existing_category = discord.utils.get(guild.categories, name=f"🔒 {user.display_name}'s Training Zone")
            
            if existing_category:
                logger.info(f"Training zone already exists for {user.display_name}")
                return existing_category
            
            # Create the category
            category = await guild.create_category(
                f"🔒 {user.display_name}'s Training Zone",
                reason=f"Personal training zone for {user.display_name}"
            )
            
            # Set permissions - only user and bot can see
            await category.set_permissions(guild.default_role, read_messages=False)
            await category.set_permissions(user, read_messages=True, send_messages=True)
            await category.set_permissions(guild.me, read_messages=True, send_messages=True, manage_channels=True)
            
            # Create initial registration channel
            registration_channel = await category.create_text_channel(
                "📝registration",
                topic="Complete your registration to unlock all training features"
            )
            
            # Send registration setup message
            await self.send_registration_setup_message(registration_channel, user, category)
            
            logger.info(f"Created training zone for {user.display_name}: {category.name}")
            return category
            
        except Exception as e:
            logger.error(f"Error creating training zone for {user.display_name}: {e}")
            return None
    
    async def send_registration_setup_message(self, channel, user, category):
        """Send registration setup message to the registration channel"""
        try:
            embed = discord.Embed(
                title="🎯 Welcome to Your Personal Training Zone!",
                description=f"**{user.display_name}**, this is your exclusive training space! Let's get you set up.",
                color=0x3498db
            )
            
            embed.add_field(
                name="📝 Step 1: Complete Registration",
                value="Click the registration button below to:\n• Provide your contact information\n• Choose your sales niche (Solar, Fiber, Landscaping)\n• Unlock your full training zone",
                inline=False
            )
            
            embed.add_field(
                name="🚀 What You'll Get After Registration",
                value="• **🔥 Danny Clone Mentor** - Personal AI sales coach\n• **💪 Practice Arena** - Train with AI customers\n• **🛠️ Playground & Library** - Create custom AI personalities\n• **💰 Deal Submission** - Track your wins and earn points\n• **📊 My Progress** - View stats and leaderboards",
                inline=False
            )
            
            embed.add_field(
                name="💡 Why Registration Matters",
                value="• **Personalized Experience** - AI uses your real name\n• **Niche-Specific Training** - Tailored to your industry\n• **Point System** - Different scoring for each niche\n• **Leaderboard Tracking** - Compete with others in your field",
                inline=False
            )
            
            embed.set_footer(text="Ready to unlock your full potential? Let's register! 🏆")
            
            # Create temporary registration view
            from ui.views.registration import RegistrationView
            view = RegistrationView()
            
            await channel.send(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error sending registration setup message: {e}")
    
    async def complete_training_zone_after_registration(self, guild, user, category, user_data):
        """Complete training zone setup after user registration"""
        try:
            # Remove the registration channel
            registration_channel = discord.utils.get(category.channels, name="📝registration")
            if registration_channel:
                await registration_channel.delete(reason="Registration completed")
            
            # Create the full training zone channels in the new order
            channels = {}
            
            # Danny Clone Mentor (First)
            channels['assistant'] = await category.create_text_channel(
                "🔥danny-clone-mentor",
                topic="Your high-energy Danny Pessy AI sales coach for mindset, tactics, and motivation"
            )
            
            # Practice Arena (Second)
            channels['practice'] = await category.create_text_channel(
                "💪practice-arena",
                topic="Practice sales skills with AI personalities (Owl, Bull, Sheep, Tiger)"
            )
            
            # Combined Playground & Library (Third)
            channels['playground'] = await category.create_text_channel(
                "🛠️playground-library",
                topic="Create custom AI personalities, manage your library, and test playground features"
            )
            
            # Deal Submission (Fourth)
            channels['deals'] = await category.create_text_channel(
                "💰deal-submission",
                topic="Submit your closed deals for leaderboard tracking"
            )
            
            # Progress Tracking (Last)
            channels['progress'] = await category.create_text_channel(
                "📊my-progress",
                topic="View your profile, stats, leaderboards, and track your training progress"
            )
            
            # Setup welcome messages for each channel
            await self.send_channel_welcome_messages(user, channels, user_data)
            
            # Send completion message to the Danny Clone Mentor (first channel)
            completion_embed = discord.Embed(
                title="🎉 Training Zone Complete!",
                description=f"**{user_data.get('first_name', user.display_name)}**, your training zone is now fully set up!",
                color=0x00ff88
            )
            
            niche_list = user_data.get('niche', 'solar')
            completion_embed.add_field(
                name="🎯 Your Niche",
                value=f"**Selected:** {niche_list}",
                inline=False
            )
            
            completion_embed.add_field(
                name="🚀 Getting Started",
                value="• **Danny Clone Mentor** - Get high-energy sales coaching\n• **Practice Arena** - Start with AI customers\n• **Playground Library** - Create custom AI personalities\n• **Deal Submission** - Log your closed deals\n• **My Progress** - Track stats and leaderboards",
                inline=False
            )
            
            completion_embed.set_footer(text="Welcome to Danny Bot! Happy training! 🚀")
            
            # Send to the Danny Clone Mentor (first channel)
            await channels['assistant'].send(embed=completion_embed)
            
            return category
            
        except Exception as e:
            logger.error(f"Error completing training zone for {user.display_name}: {e}")
            # Try to notify the user in any available channel
            for channel in category.channels:
                if isinstance(channel, discord.TextChannel):
                    try:
                        await channel.send(f"❌ Error completing your training zone setup: {str(e)}\nPlease contact an administrator for assistance.")
                        break
                    except:
                        continue
    
    async def send_channel_welcome_messages(self, user, channels, user_data):
        """Send welcome messages to all training zone channels"""
        try:
            # Send welcome message to each channel
            await self.send_personal_assistant_welcome(channels['assistant'], user)
            await self.send_quick_start_guide(channels['practice'], user)
            await self.send_playground_library_welcome(channels['playground'], user)
            await self.send_deal_submission_welcome(channels['deals'], user, user_data)
            await self.send_progress_welcome(channels['progress'], user)
            
        except Exception as e:
            logger.error(f"Error sending channel welcome messages: {e}")
    
    async def send_personal_assistant_welcome(self, channel, user):
        """Send welcome message to Danny Clone Mentor channel"""
        try:
            embed = discord.Embed(
                title="🔥 Welcome to Danny Clone Mentor!",
                description=f"**YO {user.display_name.upper()}!** Your high-energy Danny Pessy AI sales coach is ready!",
                color=0xff4444
            )
            
            embed.add_field(
                name="💪 What I Do",
                value="• **High-Energy Motivation** - Pump you up for success!\n• **Sales Mindset Coaching** - Mental game strategies\n• **Tactical Advice** - Proven sales techniques\n• **Real-Time Support** - Ask me anything, anytime!",
                inline=False
            )
            
            embed.add_field(
                name="🚀 Just Ask Me",
                value="• \"How do I handle objections?\"\n• \"Give me motivation for today!\"\n• \"What's the best closing technique?\"\n• \"How do I build rapport quickly?\"",
                inline=True
            )
            
            embed.add_field(
                name="💡 Pro Tips",
                value="• I respond to any message here\n• No commands needed - just talk!\n• I remember our conversations\n• Available 24/7 for coaching",
                inline=True
            )
            
            embed.set_footer(text="Ready to dominate? Let's GO! 🔥")
            
            await channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error sending personal assistant welcome: {e}")
    
    async def send_quick_start_guide(self, channel, user):
        """Send welcome message to Practice Arena channel"""
        try:
            embed = discord.Embed(
                title="💪 Welcome to Practice Arena!",
                description=f"**{user.display_name}**, time to sharpen your sales skills with AI customers!",
                color=0x3498db
            )
            
            embed.add_field(
                name="🎯 How to Practice",
                value="Click the personality buttons below to start a practice session. Each AI will challenge you differently!",
                inline=False
            )
            
            # Use persistent view instance to avoid timeout issues
            view = self.bot.persistent_practice_view
            await channel.send(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error updating practice arena welcome: {e}")
    
    async def send_playground_library_welcome(self, channel, user):
        """Send playground library welcome message with interface"""
        try:
            await channel.purge(limit=20)
            
            # Get user's custom personalities count
            custom_count = await self.get_custom_personality_count(user.id)
            
            embed = discord.Embed(
                title="🛠️ AI Playground & Library",
                description="Create, manage, and optimize custom AI personalities for specialized training!",
                color=0x9b59b6
            )
            # Get community personality count
            community_count = await self.get_community_personality_count()
            
            embed.add_field(
                name="🎭 Your Library",
                value=f"Custom Personalities: **{custom_count}**\nCommunity Library: **{community_count} personalities**",
                inline=False
            )
            embed.add_field(
                name="🚀 Getting Started",
                value="Use the buttons below to create your first custom AI or browse your library!",
                inline=False
            )
            
            # Use persistent view instance to avoid timeout issues
            view = self.bot.persistent_playground_view
            await channel.send(embed=embed, view=view)

        except Exception as e:
            logger.error(f"Error updating playground library welcome: {e}")
    
    async def send_deal_submission_welcome(self, channel, user, user_data):
        """Send deal submission welcome message with interface"""
        try:
            await channel.purge(limit=20)
            
            # Use the smart deal submission system with dynamic stats
            from ui.views.deal_submission import SmartDealSubmissionView
            view = SmartDealSubmissionView()
            embed = await view._create_stats_embed(user, channel.guild.id, None)  # No interaction available in system call
            
            await channel.send(embed=embed, view=view)

        except Exception as e:
            logger.error(f"Error updating deal submission welcome: {e}")
    
    async def send_progress_welcome(self, channel, user):
        """Send welcome message to Progress channel"""
        try:
            embed = discord.Embed(
                title="📊 Welcome to My Progress!",
                description=f"**{user.display_name}**, track your journey and see how you stack up!",
                color=0xe74c3c
            )
            
            embed.add_field(
                name="📈 What You'll Find",
                value="• **Your Profile** - Stats & achievements\n• **Leaderboards** - Rankings & competition\n• **Progress Tracking** - Growth over time\n• **Goal Setting** - Targets & milestones",
                inline=False
            )
            
            embed.add_field(
                name="🎯 Quick Stats",
                value="• View your profile\n• Check leaderboards\n• See recent activity\n• Track achievements",
                inline=True
            )
            
            embed.add_field(
                name="🏆 Achievements",
                value="• Deal milestones\n• Practice sessions\n• Consistency streaks\n• Rank achievements",
                inline=True
            )
            
            embed.set_footer(text="Ready to see your progress? Click below!")
            
            # Add progress view
            from ui.views.main_menu import ComprehensiveProgressView
            view = ComprehensiveProgressView()
            
            await channel.send(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error sending progress welcome: {e}")

    async def send_registration_welcome(self, channel, user):
        """Send registration and progress welcome message"""
        try:
            await channel.purge(limit=20)
            
            # Get user's profile information
            user_profile = await self.get_user_profile(user.id)
            
            embed = discord.Embed(
                title="📊 My Progress Hub",
                description="Track your performance, view statistics, and manage your profile!",
                color=0xf39c12
            )
            
            if user_profile:
                embed.add_field(
                    name="👤 Your Profile",
                    value=f"Role: **{user_profile.get('registration', {}).get('role_type', 'Not Set')}**\nNiche: **{user_profile.get('registration', {}).get('niche', 'Not Set')}**\nLevel: **{user_profile.get('registration', {}).get('experience_level', 'Not Set')}**",
                    inline=False
                )
                embed.add_field(
                    name="🎯 Your Niche",
                    value=f"**Selected:** {user_profile.get('registration', {}).get('niche', 'Not Set')}",
                    inline=False
                )
                embed.add_field(
                    name="💰 Your Points",
                    value=f"**Total:** {user_profile.get('deal_stats', {}).get('total_points', 0)}\n**This Month:** {user_profile.get('deal_stats', {}).get('monthly_deals', 0)}",
                    inline=False
                )
                # Get dynamic community personality count
                community_count = await self.get_community_personality_count()
                embed.add_field(
                    name="🎭 Your Personalities",
                    value=f"**Custom:** {user_profile.get('custom_personalities', 0)}\n**Community:** {community_count}",
                    inline=False
                )
            else:
                embed.add_field(
                    name="⚠️ Profile Setup Needed",
                    value="Complete your registration to unlock all features and start tracking your progress!",
                    inline=False
                )
            
            embed.add_field(
                name="🏆 Available Features",
                value="• **Profile** - View/update registration\n• **Stats** - Performance metrics\n• **Leaderboards** - Weekly/monthly rankings\n• **Progress** - Track improvements",
                inline=False
            )
            
            from ui.views.main_menu import ComprehensiveProgressView
            view = ComprehensiveProgressView()
            await channel.send(embed=embed, view=view)

        except Exception as e:
            logger.error(f"Error updating registration welcome: {e}")

    # Helper methods for getting user data
    async def get_custom_personality_count(self, user_id):
        """Get count of user's custom personalities"""
        try:
            # Placeholder implementation - would connect to database
            return 0
        except Exception as e:
            logger.error(f"Error getting custom personality count: {e}")
            return 0
    
    async def get_community_personality_count(self):
        """Get count of community personalities"""
        try:
            # This would query the database for community personalities
            # For now, return realistic count since community library is new
            # 4 built-in personalities (Owl, Bull, Sheep, Tiger) + 0 community personalities
            return 4
        except Exception as e:
            logger.error(f"Error getting community personality count: {e}")
            return 4
    
    async def get_user_deal_stats(self, user_id):
        """Get user's deal statistics"""
        try:
            from core.database_manager import DatabaseManager
            db_manager = DatabaseManager()
            
            # Get all user deals
            all_deals = await db_manager.get_user_deals(user_id)
            
            # Calculate current month deals
            from datetime import datetime, timedelta
            current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            monthly_deals = 0
            total_points = 0
            
            for deal in all_deals:
                # Add to total points
                total_points += deal.get('points_awarded', 0)
                
                # Check if deal is from current month
                try:
                    deal_date = datetime.fromisoformat(deal['deal_date'].replace('Z', '+00:00'))
                    if deal_date >= current_month_start:
                        monthly_deals += 1
                except:
                    # If date parsing fails, skip this deal for monthly count
                    pass
            
            # Calculate success rate (placeholder calculation)
            success_rate = min(100, (len(all_deals) * 10)) if all_deals else 0
            
            return {
                'total_deals': len(all_deals),
                'monthly_deals': monthly_deals,
                'success_rate': success_rate,
                'total_points': total_points
            }
        except Exception as e:
            logger.error(f"Error getting user deal stats: {e}")
            return {'total_deals': 0, 'monthly_deals': 0, 'success_rate': 0, 'total_points': 0}
    
    async def get_user_profile(self, user_id):
        """Get comprehensive user profile data"""
        try:
            registration = await self.db_manager.get_user_registration(user_id)
            
            if not registration:
                return None
            
            profile = {
                'registration': registration,
                'custom_personalities': await self.get_custom_personality_count(user_id),
                'deal_stats': await self.get_user_deal_stats(user_id)
            }
            
            return profile
            
        except Exception as e:
            logger.error(f"Error getting user profile for {user_id}: {e}")
            return None
    
    async def auto_refresh_all_training_zones(self, guild):
        """Auto-refresh all training zones in a guild on bot startup"""
        try:
            # Find all training zone categories in the guild
            training_categories = [cat for cat in guild.categories if "Training Zone" in cat.name]
            
            if not training_categories:
                logger.info(f"No training zones found in {guild.name}")
                return
            
            refreshed_count = 0
            for category in training_categories:
                try:
                    # Basic refresh - could be expanded to update channel messages
                    logger.debug(f"Refreshed training zone: {category.name}")
                    refreshed_count += 1
                except Exception as e:
                    logger.error(f"Error refreshing training zone {category.name}: {e}")
            
            logger.info(f"Auto-refreshed {refreshed_count} training zones in {guild.name}")
            
        except Exception as e:
            logger.error(f"Error auto-refreshing training zones in {guild.name}: {e}")


async def setup(bot):
    """Setup function for the training zone manager cog"""
    await bot.add_cog(TrainingZoneManager(bot)) 
