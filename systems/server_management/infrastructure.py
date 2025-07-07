import discord
from discord.ext import commands
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ServerInfrastructure(commands.Cog):
    """Handles server setup and infrastructure management"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def setup_server_infrastructure(self, guild):
        """Setup complete server infrastructure"""
        try:
            # Create server sections in order
            welcome_channel = await self.create_welcome_section(guild)
            community_channels = await self.create_community_section(guild) 
            voice_channels = await self.create_voice_section(guild)
            admin_channels = await self.create_admin_section(guild)
            
            # Setup roles
            await self.create_roles(guild)
            
            # Setup welcome message with Get Started button
            if welcome_channel:
                await self.setup_welcome_message(welcome_channel)
            
            # Setup community channel messages
            await self.setup_community_messages(community_channels)
            
            logger.info(f"Server infrastructure setup completed for {guild.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up server infrastructure: {e}")
            return False
    
    async def create_welcome_section(self, guild):
        """Create welcome section with start here channel"""
        try:
            # Check if welcome section already exists
            welcome_category = discord.utils.get(guild.categories, name="🌟 Welcome to Danny Bot")
            
            if not welcome_category:
                # Create welcome category
                welcome_category = await guild.create_category("🌟 Welcome to Danny Bot")
                logger.info(f"Created welcome category: {welcome_category.name}")
            
            # Check if welcome channel exists
            welcome_channel = discord.utils.get(welcome_category.channels, name="🚀start-here")
            
            if not welcome_channel:
                # Create welcome channel
                welcome_channel = await welcome_category.create_text_channel(
                    "🚀start-here",
                    topic="Start your Danny Bot journey here! Get your personal training zone."
                )
                logger.info(f"Created welcome channel: {welcome_channel.name}")
            
            return welcome_channel
            
        except Exception as e:
            logger.error(f"Error creating welcome section: {e}")
            return None
    
    async def create_community_section(self, guild):
        """Create community section with all specified channels"""
        try:
            # Check if community section exists
            community_category = discord.utils.get(guild.categories, name="💬 Community")
            
            if not community_category:
                community_category = await guild.create_category("💬 Community")
                logger.info(f"Created community category: {community_category.name}")
            
            # Community channels to create (exact names from user specification)
            community_channels = [
                ("📢announcements", "Lord of The Doors Season 3 announcements and updates"),
                ("💬general-chat", "Main community hub for connecting with fellow sales professionals"),
                ("🌐fiber-network", "Fiber internet sales professionals hub"),
                ("☀️solar-central", "Solar energy sales professionals hub"),
                ("🌿landscaping-hub", "Landscaping sales professionals hub"),
                ("💡tips-and-tricks", "Share your best sales strategies and techniques"),
                ("🏆success-stories", "Celebrate wins and share success stories"),
                ("🐛feedback-bugs", "Report bugs and suggest improvements"),
                ("📊public-leaderboard", "Competition rankings and deal tracking"),
                ("🤖authentic-gpt", "AI assistant for the community")
            ]
            
            created_channels = {}
            for channel_name, channel_topic in community_channels:
                existing_channel = discord.utils.get(community_category.channels, name=channel_name)
                if not existing_channel:
                    channel = await community_category.create_text_channel(
                        channel_name,
                        topic=channel_topic
                    )
                    created_channels[channel_name] = channel
                    logger.info(f"Created community channel: {channel.name}")
                else:
                    created_channels[channel_name] = existing_channel
            
            # Setup welcome messages for community channels
            if created_channels:
                await self.setup_community_messages(created_channels)
            
            return created_channels
            
        except Exception as e:
            logger.error(f"Error creating community section: {e}")
            return {}
    
    async def create_voice_section(self, guild):
        """Create voice channels section with organized structure"""
        try:
            voice_category = discord.utils.get(guild.categories, name="🗣️ Voice Channels")
            
            if not voice_category:
                voice_category = await guild.create_category("🗣️ Voice Channels")
                logger.info(f"Created voice category: {voice_category.name}")
            
            # Voice channels to create (from user specification)
            voice_channels = [
                "🎙️ Community Lounge",
                "🗣️ General Voice Chat", 
                "🌐 Fiber Network Voice",
                "☀️ Solar Energy Voice",
                "🌿 Landscaping Voice",
                "📞 Team Meetings",
                "🎭 Roleplay Practice",
                "📚 Study & Training"
            ]
            
            created_voice_channels = {}
            for voice_name in voice_channels:
                existing_voice = discord.utils.get(voice_category.channels, name=voice_name)
                if not existing_voice:
                    voice_channel = await voice_category.create_voice_channel(voice_name)
                    created_voice_channels[voice_name] = voice_channel
                    logger.info(f"Created voice channel: {voice_channel.name}")
                else:
                    created_voice_channels[voice_name] = existing_voice
            
            return created_voice_channels
            
        except Exception as e:
            logger.error(f"Error creating voice section: {e}")
            return {}
    
    async def create_admin_section(self, guild):
        """Create admin section with admin channels"""
        try:
            admin_category = discord.utils.get(guild.categories, name="🔧 Admin Zone")
            
            if not admin_category:
                admin_category = await guild.create_category("🔧 Admin Zone")
                logger.info(f"Created admin category: {admin_category.name}")
            
            # Admin channels to create
            admin_channels = [
                ("📋admin-commands", "Bot commands and server management"),
                ("📊admin-logs", "Bot activity logs and monitoring"),
                ("🔧admin-tools", "Administrative tools and utilities")
            ]
            
            created_admin_channels = {}
            for channel_name, channel_topic in admin_channels:
                existing_channel = discord.utils.get(admin_category.channels, name=channel_name)
                if not existing_channel:
                    channel = await admin_category.create_text_channel(
                        channel_name,
                        topic=channel_topic
                    )
                    created_admin_channels[channel_name] = channel
                    logger.info(f"Created admin channel: {channel.name}")
                else:
                    created_admin_channels[channel_name] = existing_channel
            
            return created_admin_channels
            
        except Exception as e:
            logger.error(f"Error creating admin section: {e}")
            return {}
    
    async def create_roles(self, guild):
        """Create necessary server roles"""
        try:
            roles_to_create = [
                ("🏆 Danny Champion", 0xffd700, True),  # Gold color, mentionable
                ("📈 Top Performer", 0xff6b6b, True),   # Red color, mentionable  
                ("🎯 Sales Pro", 0x4ecdc4, True),       # Teal color, mentionable
                ("🌟 Active Member", 0x45b7d1, True),   # Blue color, mentionable
                ("🆕 New Member", 0x96ceb4, True)       # Green color, mentionable
            ]
            
            created_roles = {}
            for role_name, role_color, mentionable in roles_to_create:
                existing_role = discord.utils.get(guild.roles, name=role_name)
                if not existing_role:
                    role = await guild.create_role(
                        name=role_name,
                        color=discord.Color(role_color),
                        mentionable=mentionable,
                        reason="Danny Bot server setup"
                    )
                    created_roles[role_name] = role
                    logger.info(f"Created role: {role.name}")
                else:
                    created_roles[role_name] = existing_role
            
            return created_roles
            
        except Exception as e:
            logger.error(f"Error creating roles: {e}")
            return {}

    async def setup_welcome_message(self, welcome_channel):
        """Setup the welcome message with Get Started button"""
        try:
            # Delete any existing messages in welcome channel
            await welcome_channel.purge(limit=100)
            
            # Create the exact welcome message from user specification
            embed = discord.Embed(
                title="🎯 Welcome to Lord of The Doors Season 3!",
                description="Your comprehensive AI-powered sales training platform with a thriving community of professionals across Fiber, Solar, and Landscaping industries!",
                color=0x00ff88
            )
            
            embed.add_field(
                name="🚀 What You'll Get:",
                value="• Private AI Training Zones with niche-specific practice\n• Vibrant Community Channels for networking and learning\n• Voice Chat Rooms for real-time discussions\n• Competition Leaderboards and achievement tracking\n• Custom AI Personality Creation tools\n• Professional Progress Tracking and analytics",
                inline=False
            )
            
            embed.add_field(
                name="🌐 Community Features:",
                value="• 📢 Announcements - Latest updates and events\n• 🗣️ Voice Channels - Connect with your niche community\n• 🏆 Success Stories - Share and celebrate wins\n• 💡 Tips & Tricks - Learn from the best\n• 🌐 Fiber Network Hub - Internet sales discussions\n• ☀️ Solar Energy Central - Renewable energy sales\n• 🌿 Landscaping Hub - Outdoor services community",
                inline=False
            )
            
            embed.add_field(
                name="🎯 How It Works:",
                value="• Click Get Started below to create your training zone\n• Complete registration with your niche selection\n• Join community channels and voice chats\n• Start practicing with niche-specific AI customers\n• Share successes and learn from fellow professionals\n• Compete on leaderboards and track your growth!",
                inline=False
            )
            
            embed.add_field(
                name="Ready to join the ultimate sales training community? Let's begin! 🚀",
                value="",
                inline=False
            )
            
            # Send welcome message with Get Started button
            # Use the global singleton instance that's registered as persistent
            from core.bot import _welcome_view_instance
            if _welcome_view_instance is None:
                from ui.views.welcome import WelcomeButtonView
                view = WelcomeButtonView()
            else:
                view = _welcome_view_instance
            
            await welcome_channel.send(embed=embed, view=view)
            
            logger.info(f"Setup welcome message in channel: {welcome_channel.name.replace('🚀', 'start-').replace('🎯', '').replace('🌟', '').strip()}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up welcome message: {e}")
            return False

    async def setup_community_messages(self, community_channels):
        """Setup messages in community channels"""
        try:
            # Define welcome messages for each channel
            channel_messages = {
                "📢announcements": {
                    "embed": discord.Embed(
                        title="📢 Welcome to Announcements!",
                        description="This is your central hub for all Lord of The Doors Season 3 announcements and updates.",
                        color=0x3498db
                    ).add_field(
                        name="What you'll find here:",
                        value="• Competition updates and rule changes\n• New feature announcements\n• Community events and challenges\n• Important deadlines and dates\n• System maintenance notifications",
                        inline=False
                    ).add_field(
                        name="📝 Note:",
                        value="Only administrators can post here, but everyone can react and discuss in other channels!",
                        inline=False
                    )
                },
                "💬general-chat": {
                    "embed": discord.Embed(
                        title="💬 Welcome to General Chat!",
                        description="Your main community hub for connecting with fellow sales professionals!",
                        color=0x2ecc71
                    ).add_field(
                        name="This is the place to:",
                        value="• Introduce yourself to the community\n• Share general sales discussions\n• Network with other professionals\n• Ask quick questions\n• Celebrate wins together\n• Build relationships and connections",
                        inline=False
                    ).add_field(
                        name="🤝 Community Guidelines:",
                        value="Be respectful, supportive, and professional. We're all here to grow together!",
                        inline=False
                    )
                },
                "🌐fiber-network": {
                    "embed": discord.Embed(
                        title="🌐 Welcome to Fiber Network Hub!",
                        description="The dedicated space for fiber internet sales professionals to connect and share expertise.",
                        color=0x9b59b6
                    ).add_field(
                        name="Perfect for discussing:",
                        value="• Fiber internet sales strategies\n• Technical objection handling\n• Competition comparisons\n• Installation timelines\n• Business vs residential approaches\n• Territory management tips",
                        inline=False
                    ).add_field(
                        name="🎯 Fiber Scoring System:",
                        value="• 5 deals = 1 point\n• 1 point for set that closes\n• 1 point for close\n• 2 points for self-generated",
                        inline=False
                    )
                },
                "☀️solar-central": {
                    "embed": discord.Embed(
                        title="☀️ Welcome to Solar Central!",
                        description="Your go-to hub for solar energy sales professionals to share insights and strategies.",
                        color=0xf39c12
                    ).add_field(
                        name="Great for sharing:",
                        value="• Solar sales techniques and scripts\n• Financing options and strategies\n• ROI calculations and presentations\n• Seasonal sales approaches\n• Regulatory updates and incentives\n• Installation process explanations",
                        inline=False
                    ).add_field(
                        name="🎯 Solar Scoring System:",
                        value="• 1 point for standard deal\n• 2 points for self-generated deal",
                        inline=False
                    )
                },
                "🌿landscaping-hub": {
                    "embed": discord.Embed(
                        title="🌿 Welcome to Landscaping Hub!",
                        description="The central meeting place for landscaping sales professionals to grow together.",
                        color=0x27ae60
                    ).add_field(
                        name="Perfect for discussing:",
                        value="• Landscaping project sales strategies\n• Seasonal business approaches\n• Design consultation techniques\n• Material and labor cost discussions\n• Before/after project showcases\n• Equipment and tool recommendations",
                        inline=False
                    ).add_field(
                        name="🎯 Landscaping Scoring System:",
                        value="• 1 point for set\n• 1 point for close\n• 1 point per $50k above $50k",
                        inline=False
                    )
                },
                "💡tips-and-tricks": {
                    "embed": discord.Embed(
                        title="💡 Welcome to Tips & Tricks!",
                        description="Share your best sales strategies, techniques, and hard-won wisdom with the community.",
                        color=0xe74c3c
                    ).add_field(
                        name="Share your expertise on:",
                        value="• Proven sales scripts and approaches\n• Objection handling techniques\n• Time management strategies\n• Lead generation methods\n• Closing techniques that work\n• CRM and organization tips\n• Mindset and motivation advice",
                        inline=False
                    ).add_field(
                        name="🎯 Pro Tip:",
                        value="The best tips come from real experience. Share what's actually worked for you in the field!",
                        inline=False
                    )
                },
                "🏆success-stories": {
                    "embed": discord.Embed(
                        title="🏆 Welcome to Success Stories!",
                        description="Celebrate wins and share success stories to inspire and motivate the entire community!",
                        color=0xf1c40f
                    ).add_field(
                        name="Share your victories:",
                        value="• Big deals you've closed\n• Breakthrough moments\n• Difficult customers you've converted\n• Personal milestones reached\n• Team achievements\n• Lessons learned from challenges\n• How you overcame obstacles",
                        inline=False
                    ).add_field(
                        name="🎉 Remember:",
                        value="Every win, big or small, deserves recognition. Your success inspires others to push harder!",
                        inline=False
                    )
                },
                "🐛feedback-bugs": {
                    "embed": discord.Embed(
                        title="🐛 Welcome to Feedback & Bugs!",
                        description="Help us improve Danny Bot by reporting bugs and suggesting new features.",
                        color=0x95a5a6
                    ).add_field(
                        name="Please report:",
                        value="• Bugs or errors you encounter\n• Feature requests and suggestions\n• UI/UX improvement ideas\n• Training content feedback\n• Performance issues\n• Integration problems",
                        inline=False
                    ).add_field(
                        name="🔧 How to report:",
                        value="Be specific! Include steps to reproduce, expected vs actual behavior, and screenshots if possible.",
                        inline=False
                    )
                },
                "📊public-leaderboard": {
                    "embed": discord.Embed(
                        title="📊 Welcome to Public Leaderboard!",
                        description="Track competition rankings, deal progress, and celebrate top performers in the community!",
                        color=0x8e44ad
                    ).add_field(
                        name="Here you'll find:",
                        value="• Weekly competition standings\n• Monthly tournament results\n• Top performer recognition\n• Deal submission updates\n• Point calculation explanations\n• Ranking change notifications",
                        inline=False
                    ).add_field(
                        name="🏅 Current Competition:",
                        value="Lord of The Doors Season 3 is live! Check your ranking and push for the top spots!",
                        inline=False
                    )
                },
                "🤖authentic-gpt": {
                    "embed": discord.Embed(
                        title="🤖 Welcome to Authentic GPT!",
                        description="Your AI assistant for the community - ask questions, get help, and explore ideas!",
                        color=0x34495e
                    ).add_field(
                        name="How to use:",
                        value="• Ask questions about sales strategies\n• Get help with objection handling\n• Brainstorm ideas for difficult situations\n• Request script writing assistance\n• Analyze market trends\n• Get general business advice",
                        inline=False
                    ).add_field(
                        name="🎯 Pro Tips:",
                        value="Be specific in your questions for better responses. The AI works best with clear, detailed prompts!",
                        inline=False
                    )
                }
            }
            
            # Clean up and send welcome messages to each channel
            for channel_name, channel_obj in community_channels.items():
                if channel_name in channel_messages:
                    message_data = channel_messages[channel_name]
                    
                    # Check if channel needs welcome message refresh (only if empty or has old bot messages)
                    recent_messages = [message async for message in channel_obj.history(limit=5)]
                    
                    # Only purge if channel is empty or contains only bot messages
                    needs_refresh = False
                    if not recent_messages:
                        needs_refresh = True
                    else:
                        # Check if all recent messages are from the bot
                        all_bot_messages = all(msg.author.bot for msg in recent_messages)
                        if all_bot_messages:
                            needs_refresh = True
                    
                    if needs_refresh:
                        # Clear old bot messages and send fresh welcome message
                        await channel_obj.purge(limit=10, check=lambda m: m.author.bot)
                        await channel_obj.send(embed=message_data["embed"])
                        logger.info(f"Refreshed welcome message in {channel_name}")
                    else:
                        # Channel has user messages, just check if welcome message exists
                        has_welcome_message = any(
                            msg.author.bot and msg.embeds and 
                            msg.embeds[0].title and "Welcome to" in msg.embeds[0].title
                            for msg in recent_messages
                        )
                        
                        if not has_welcome_message:
                            # Add welcome message without clearing user messages
                            await channel_obj.send(embed=message_data["embed"])
                            logger.info(f"Added welcome message to {channel_name} (preserving user messages)")
                        else:
                            logger.info(f"Welcome message already exists in {channel_name}")
            
            logger.info("Community channel messages setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up community messages: {e}")
            return False
    
    async def auto_update_welcome_channel(self, guild):
        """Auto-update welcome channel on bot startup"""
        try:
            # Find the welcome channel
            welcome_category = discord.utils.get(guild.categories, name="🌟 Welcome to Danny Bot")
            if not welcome_category:
                logger.info(f"No welcome category found in {guild.name}")
                return
                
            welcome_channel = discord.utils.get(welcome_category.channels, name="🚀start-here")
            if not welcome_channel:
                logger.info(f"No welcome channel found in {guild.name}")
                return
            
            # Refresh the welcome message to fix stale button interactions
            await self.setup_welcome_message(welcome_channel)
            logger.info(f"Welcome channel auto-updated in {guild.name}")
            
        except Exception as e:
            logger.error(f"Error auto-updating welcome channel in {guild.name}: {e}")
    
    async def auto_update_community_channels(self, guild):
        """Auto-update community channels on bot startup"""
        try:
            # Create/update community section
            community_channels = await self.create_community_section(guild)
            
            if community_channels:
                # Also setup welcome messages for all channels (including existing ones)
                all_community_channels = {}
                community_category = discord.utils.get(guild.categories, name="💬 Community")
                if community_category:
                    for channel in community_category.channels:
                        if isinstance(channel, discord.TextChannel):
                            all_community_channels[channel.name] = channel
                
                await self.setup_community_messages(all_community_channels)
                logger.info(f"Community channels auto-updated in {guild.name}")
            else:
                logger.warning(f"No community channels found/created in {guild.name}")
                
        except Exception as e:
            logger.error(f"Error auto-updating community channels in {guild.name}: {e}")

    async def auto_refresh_all_training_zones(self, guild):
        """Auto-refresh all training zones on bot startup"""
        try:
            # Find all training zone categories
            training_zones = [cat for cat in guild.categories if "Training Zone" in cat.name]
            
            for category in training_zones:
                # Extract user from category name (e.g., "🔒 John's Training Zone")
                user_name = category.name.replace("🔒 ", "").replace("'s Training Zone", "")
                
                # Find the user by name
                user = None
                for member in guild.members:
                    if member.display_name == user_name:
                        user = member
                        break
                
                if user:
                    logger.info(f"Auto-refreshing training zone for {user.display_name}")
                    # Refresh each channel in the training zone
                    for channel in category.channels:
                        if isinstance(channel, discord.TextChannel):
                            await self._refresh_channel_ui(channel, user)
                else:
                    logger.warning(f"Could not find user for training zone: {category.name}")
            
            logger.info(f"Auto-refresh completed for {len(training_zones)} training zones")
            return True
            
        except Exception as e:
            logger.error(f"Error auto-refreshing training zones: {e}")
            return False

    async def _refresh_channel_ui(self, channel, user):
        """Refresh UI elements in training zone channels"""
        try:
            # Clean up old messages that might have stale UI components
            await channel.purge(limit=10)
            
            # Send fresh welcome message based on channel type
            if "danny-clone-mentor" in channel.name.lower():
                embed = discord.Embed(
                    title="🤖 Danny Clone Mentor Ready!",
                    description=f"Hello {user.display_name}! I'm your personal AI sales coach.",
                    color=0x00ff88
                )
                embed.add_field(
                    name="💬 How to Use:",
                    value="Simply type your questions or scenarios and I'll provide personalized coaching!",
                    inline=False
                )
                await channel.send(embed=embed)
            
            elif "practice-arena" in channel.name.lower() or "playground" in channel.name.lower():
                embed = discord.Embed(
                    title="🏟️ Practice Arena Ready!",
                    description=f"Welcome back {user.display_name}! Your practice arena is ready for training.",
                    color=0x3498db
                )
                embed.add_field(
                    name="🎯 Practice Options:",
                    value="• Use the playground system to create custom homeowner personalities\n• Practice with different personality types\n• Get realistic objections and responses",
                    inline=False
                )
                await channel.send(embed=embed)
            
            logger.info(f"Refreshed UI for {channel.name} in {user.display_name}'s training zone")
            
        except Exception as e:
            logger.error(f"Error refreshing channel UI for {channel.name}: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle messages in community channels"""
        # Ignore bot messages
        if message.author.bot:
            return
            
        # Check if this is the Authentic GPT channel
        if (message.channel.name == "🤖authentic-gpt" and 
            message.channel.category and 
            message.channel.category.name == "💬 Community"):
            
            try:
                # Show typing indicator
                async with message.channel.typing():
                    # Generate AI response
                    ai_response = await self._generate_authentic_gpt_response(message.content, message.author)
                    
                    if ai_response:
                        # Send response with proper embed handling
                        if isinstance(ai_response, discord.Embed):
                            await message.channel.send(embed=ai_response)
                        else:
                            await message.channel.send(ai_response)
                        
            except Exception as e:
                logger.error(f"Error generating Authentic GPT response: {e}")
                await message.channel.send("❌ I encountered an error processing your request. Please try again!")

    async def _generate_authentic_gpt_response(self, user_message, user):
        """Generate ChatGPT-like response for Authentic GPT channel"""
        try:
            # Import AI response engine
            from ai_response_engine import AIResponseEngine
            
            # Create AI engine instance
            ai_engine = AIResponseEngine()
            
            # Create system prompt for community AI assistant
            system_prompt = f"""You are an AI assistant for a sales training Discord community called 'Lord of The Doors Season 3'. 
            
Your role is to help sales professionals with:
- Sales strategies and techniques
- Objection handling
- Market analysis
- Business development
- Professional growth
- Industry insights

Guidelines:
- Be professional but friendly
- Provide actionable advice
- Use examples when helpful
- Format responses clearly with bullet points and sections
- Keep responses concise but comprehensive
- Always relate advice back to sales success

Current user: {user.display_name}
Community context: This is a competitive sales training environment where professionals share knowledge and compete on leaderboards."""
            
            # Generate response - FIX: Correct parameter order
            response = await ai_engine.generate_response(
                system_prompt,
                user_message,
                max_tokens=800
            )
            
            # Format response with ChatGPT-like styling
            formatted_response = self._format_gpt_response(response, user)
            
            return formatted_response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "❌ I'm experiencing technical difficulties. Please try again in a moment!"

    def _format_gpt_response(self, response, user):
        """Format AI response with ChatGPT-like styling"""
        try:
            # Create embed for better formatting
            embed = discord.Embed(
                title="🤖 Authentic GPT Response",
                description=response,
                color=0x00d4aa  # ChatGPT green color
            )
            
            # Add user footer
            embed.set_footer(
                text=f"Response for {user.display_name}",
                icon_url=user.avatar.url if user.avatar else None
            )
            
            # Add timestamp
            embed.timestamp = discord.utils.utcnow()
            
            return embed
            
        except Exception as e:
            logger.error(f"Error formatting GPT response: {e}")
            # Fallback to simple text format
            return f"🤖 **Authentic GPT Response for {user.display_name}:**\n\n{response}"


async def setup(bot):
    """Setup function for the server infrastructure cog"""
    await bot.add_cog(ServerInfrastructure(bot)) 