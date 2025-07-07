import os
import logging
import discord
from discord.ext import commands
import aiosqlite
from core.admin_logger import AdminLogger
from core.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

# Global variable for welcome view singleton
_welcome_view_instance = None

class DannyBot(commands.Bot):
    """Main Discord bot class with modular architecture"""
    
    def __init__(self):
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        intents.guild_messages = True
        intents.dm_messages = True
        intents.reactions = True
        
        super().__init__(
            command_prefix=os.getenv('BOT_PREFIX', '!'),
            intents=intents,
            help_command=None
        )
        self.owner_id = int(os.getenv('BOT_OWNER_ID', 0))
        
        # Initialize core managers
        self.admin_logger = AdminLogger(self)
        self.db_manager = DatabaseManager()
        
        # Initialize bot attributes
        self.active_practice_channels = {}
        self._processing_users_global = set()
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        global _welcome_view_instance
        
        logger.info("Setting up Danny Bot...")
        
        # Initialize database
        await self.db_manager.init_database()
        
        # Setup persistent views
        await self._setup_persistent_views()
        
        # Load modular command cogs
        extensions = [
            'commands.admin_commands',
            'commands.user_commands',
            'systems.leaderboard.manager',
            'systems.playground.manager',
            'systems.training_zones.manager',
            'systems.server_management.infrastructure'  # Add this to auto-refresh welcome messages
        ]
        
        for extension in extensions:
            try:
                await self.load_extension(extension)
                logger.info(f"Loaded extension: {extension}")
            except Exception as e:
                logger.error(f"Failed to load extension {extension}: {e}")
        
        # Register persistent views for UI components
        await self._register_persistent_views()
        
        # Sync commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
        
        logger.info("DannyBot setup completed successfully!")
    
    async def _setup_persistent_views(self):
        """Setup persistent views for the bot"""
        global _welcome_view_instance
        
        try:
            # Import views here to avoid circular imports
            from ui.views.welcome import WelcomeButtonView
            from ui.views.registration import RegistrationView
            from ui.views.main_menu import MainMenuView
            # Note: Only import views that are actually needed and exist
            # Removed problematic imports that don't exist or cause issues
            
            # Remove any existing WelcomeButtonView instances
            existing_views = [view for view in self.persistent_views if isinstance(view, WelcomeButtonView)]
            for view in existing_views:
                self.remove_view(view)
                logger.info(f"Removed existing WelcomeButtonView {id(view)}")
            
            # Create single global instance
            if _welcome_view_instance is None:
                _welcome_view_instance = WelcomeButtonView()
                logger.info(f"Created new WelcomeButtonView instance {id(_welcome_view_instance)}")
            
            self.add_view(_welcome_view_instance)
            logger.info(f"WelcomeButtonView registered successfully - Instance: {id(_welcome_view_instance)}")
            
            # Add persistent registration view
            self.add_view(RegistrationView())
            logger.info("RegistrationView registered successfully")
            
            # Register ONLY truly persistent views (timeout=None)
            self.add_view(MainMenuView())  # ✅ timeout=None - persistent
            logger.info("MainMenuView registered successfully")
            
            # Register training zone views as persistent (timeout=None)
            from ui.views.practice import PracticePersonalityView
            from ui.views.playground import PlaygroundView, PlaygroundNicheView, HomeownerCreatedView, PracticeSessionView, ConversationView
            
            # Create persistent instances that can be reused
            self.persistent_practice_view = PracticePersonalityView()
            self.persistent_playground_view = PlaygroundView()
            
            self.add_view(self.persistent_practice_view)  # ✅ timeout=None - persistent
            logger.info("PracticePersonalityView registered successfully")
            
            self.add_view(self.persistent_playground_view)  # ✅ timeout=None - persistent
            logger.info("PlaygroundView registered successfully")
            
            # Add new persistent playground views
            self.add_view(PlaygroundNicheView())  # ✅ timeout=None - persistent
            logger.info("PlaygroundNicheView registered successfully")
            
            # Note: HomeownerCreatedView, PracticeSessionView, and ConversationView are created dynamically
            # as they need specific data, but they are persistent (timeout=None)
            
            # Note: SmartDealSubmissionView is already persistent and registered above
            
            logger.info("All persistent views registered successfully")
            
        except Exception as e:
            logger.error(f"Failed to register views: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def _register_persistent_views(self):
        """Register persistent views for UI components"""
        # Implementation of _register_persistent_views method
        pass
    
    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f"Bot logged in as {self.user.name} (ID: {self.user.id})")
        
        # Auto-refresh all server components to ensure buttons work after restart
        for guild in self.guilds:
            try:
                await self._auto_refresh_server(guild)
            except Exception as e:
                logger.error(f"Error refreshing guild {guild.name}: {e}")
    
    async def _auto_refresh_server(self, guild):
        """Auto-refresh server components during startup to ensure buttons work"""
        try:
            logger.info(f"Auto-refreshing server components for {guild.name}...")
            
            # 1. Fix missing registration messages first
            training_zone_cog = self.get_cog('TrainingZoneManager')
            if training_zone_cog:
                fixed_registrations = 0
                for category in guild.categories:
                    if "Training Zone" in category.name:
                        registration_channel = discord.utils.get(category.channels, name="📝registration")
                        
                        if registration_channel:
                            # Check if registration channel is missing messages
                            messages = [message async for message in registration_channel.history(limit=10)]
                            has_registration_message = False
                            
                            for message in messages:
                                if (message.author == guild.me and message.embeds and 
                                    any("registration" in (embed.title or "").lower() or 
                                        "welcome to your personal training zone" in (embed.title or "").lower()
                                        for embed in message.embeds)):
                                    has_registration_message = True
                                    break
                            
                            if not has_registration_message:
                                # Find the user this training zone belongs to
                                target_user = None
                                for member in guild.members:
                                    if category.permissions_for(member).read_messages and member != guild.me:
                                        target_user = member
                                        break
                                
                                if target_user:
                                    logger.info(f"Auto-restoring registration message for {target_user.display_name}")
                                    await training_zone_cog.send_registration_setup_message(
                                        registration_channel, target_user, category
                                    )
                                    fixed_registrations += 1
                
                if fixed_registrations > 0:
                    logger.info(f"Auto-fixed {fixed_registrations} missing registration messages")
            
            # 2. Refresh training zone UI components
            refreshed_channels = 0
            if training_zone_cog:
                for category in guild.categories:
                    if "Training Zone" in category.name:
                        target_user = None
                        for member in guild.members:
                            if category.permissions_for(member).read_messages and member != guild.me:
                                target_user = member
                                break
                        
                        if target_user:
                            for channel in category.text_channels:
                                if channel.name != "📝registration":  # Skip registration channels
                                    await self._refresh_channel_ui(channel, target_user)
                                    refreshed_channels += 1
                
                if refreshed_channels > 0:
                    logger.info(f"Auto-refreshed {refreshed_channels} training zone channels")
            
            # 3. Refresh server infrastructure (welcome and community channels)
            infrastructure_cog = self.get_cog('ServerInfrastructure')
            if infrastructure_cog:
                await infrastructure_cog.auto_update_welcome_channel(guild)
                await infrastructure_cog.auto_update_community_channels(guild)
                logger.info("Auto-updated welcome and community channels")
            
            # 4. Auto-refresh training zones
            if training_zone_cog:
                await training_zone_cog.auto_refresh_all_training_zones(guild)
                logger.info("Auto-refreshed training zones")
            
            # 5. Auto-refresh public leaderboard
            leaderboard_cog = self.get_cog('LeaderboardManager')
            if leaderboard_cog:
                await leaderboard_cog.display.auto_refresh_public_leaderboard(guild.id)
                logger.info("Auto-refreshed public leaderboard")
            
            logger.info(f"Auto-refresh completed for {guild.name}")
            
        except Exception as e:
            logger.error(f"Error in auto-refresh for {guild.name}: {e}")
    
    async def _refresh_channel_ui(self, channel, user):
        """Refresh UI for a specific channel without deleting content"""
        try:
            channel_name = channel.name.lower()
            
            # Delete only interface/button messages and completion messages, preserve everything else
            def is_interface_message(message):
                if message.attachments or (hasattr(message, 'thread') and message.thread):
                    return False
                if message.author != channel.guild.me:
                    return False
                
                if message.embeds:
                    for embed in message.embeds:
                        title = (embed.title or "").lower()
                        desc = (embed.description or "").lower()
                        content = title + " " + desc
                        
                        if any(keyword in content for keyword in [
                            "welcome", "getting started", "what i do", "just ask me",
                            "practice arena", "playground", "deal submission", "my progress",
                            "tutorial", "button", "click", "use the buttons",
                            "practice session complete", "session summary", "next steps",
                            "try a different personality", "practice a new niche", "duration:",
                            "personality:", "niche:", "review your progress"
                        ]):
                            return True
                return False
            
            # Delete only interface messages
            await channel.purge(limit=50, check=is_interface_message)
            
            # Send fresh welcome message based on channel type
            training_zone_cog = self.get_cog('TrainingZoneManager')
            if training_zone_cog:
                if 'danny-clone-mentor' in channel_name or 'assistant' in channel_name:
                    await training_zone_cog.send_personal_assistant_welcome(channel, user)
                elif 'practice-arena' in channel_name or 'practice' in channel_name:
                    await training_zone_cog.send_quick_start_guide(channel, user)
                elif 'playground' in channel_name or 'library' in channel_name:
                    await training_zone_cog.send_playground_library_welcome(channel, user)
                elif 'deal-submission' in channel_name or 'deals' in channel_name:
                    user_data = await self.db_manager.get_user_registration(user.id)
                    await training_zone_cog.send_deal_submission_welcome(channel, user, user_data or {})
                elif 'progress' in channel_name:
                    await training_zone_cog.send_progress_welcome(channel, user)
                    
        except Exception as e:
            logger.error(f"Error refreshing channel UI for {channel.name}: {e}")
    
    async def on_member_join(self, member):
        """Handle member join events"""
        try:
            # Log to admin
            await self.admin_logger.log_member_join(member)
            logger.info(f"Member joined: {member.display_name} ({member.id})")
        except Exception as e:
            logger.error(f"Error handling member join: {e}")
    
    async def on_member_remove(self, member):
        """Handle member leave events"""
        try:
            # Log to admin
            await self.admin_logger.log_member_leave(member)
            logger.info(f"Member left: {member.display_name} ({member.id})")
        except Exception as e:
            logger.error(f"Error handling member leave: {e}")
    
    async def on_command_error(self, ctx, error):
        """Global command error handler"""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
            return
        
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ Command on cooldown. Try again in {error.retry_after:.1f} seconds.")
            return
        
        # Log other errors
        logger.error(f"Command error in {ctx.command}: {error}")
        await ctx.send("❌ An error occurred while processing the command.") 