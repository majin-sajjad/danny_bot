import discord
from discord.ext import commands
import logging
from core.database_manager import DatabaseManager
from systems.training_zones.manager import TrainingZoneManager

logger = logging.getLogger(__name__)

class RegistrationHandler:
    """Handles the complete user registration flow"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db_manager = DatabaseManager()
        self.training_zone_manager = TrainingZoneManager(bot)
        
        # Track registration sessions
        self.active_registrations = {}  # user_id: registration_data
    
    async def start_registration(self, interaction, user):
        """Start the registration process for a user"""
        try:
            # Check if user is already registered
            existing_registration = await self.db_manager.get_user_registration(user.id)
            
            if existing_registration:
                embed = discord.Embed(
                    title="✅ Already Registered!",
                    description=f"Welcome back, {existing_registration.get('name', user.display_name)}!",
                    color=0x00ff88
                )
                
                # Check if they have a training zone
                guild = interaction.guild
                training_zone = None
                for category in guild.categories:
                    if f"Training Zone - {existing_registration.get('name', user.display_name)}" in category.name:
                        training_zone = category
                        break
                
                if training_zone:
                    practice_channel = None
                    for channel in training_zone.channels:
                        if "💪practice-arena" in channel.name:
                            practice_channel = channel
                            break
                    
                    if practice_channel:
                        embed.add_field(
                            name="🏠 Your Training Zone",
                            value=f"Jump to your practice area: {practice_channel.mention}",
                            inline=False
                        )
                else:
                    # They're registered but no training zone - create one
                    embed.add_field(
                        name="🔄 Setting Up Training Zone",
                        value="Your training zone is being created... Please wait a moment!",
                        inline=False
                    )
                    
                    # Create training zone in background
                    await self.create_training_zone_for_registered_user(guild, user, existing_registration)
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Initialize new registration session
            self.active_registrations[user.id] = {
                'user_id': user.id,
                'step': 'name',
                'data': {}
            }
            
            # Send registration modal
            from ui.modals.registration import RegistrationModal
            modal = RegistrationModal(self)
            await interaction.response.send_modal(modal)
            
        except Exception as e:
            logger.error(f"Error starting registration for {user.id}: {e}")
            await interaction.followup.send("❌ Error starting registration. Please try again later.", ephemeral=True)
    
    async def handle_registration_submission(self, interaction, name, experience, goals):
        """Handle registration form submission"""
        user = interaction.user
        
        try:
            # Validate input
            if not name or len(name.strip()) < 2:
                await interaction.response.send_message("❌ Please provide a valid name (at least 2 characters).", ephemeral=True)
                return
            
            if not experience:
                await interaction.response.send_message("❌ Please select your experience level.", ephemeral=True)
                return
            
            # Store registration data temporarily
            registration_data = {
                'name': name.strip(),
                'experience': experience,
                'goals': goals.strip() if goals else '',
                'user_id': user.id,
                'step': 'niche_selection'
            }
            
            self.active_registrations[user.id] = registration_data
            
            # Show niche selection
            from ui.views.niche_selection import NicheSelectionView
            niche_view = NicheSelectionView(self)
            
            embed = discord.Embed(
                title="🎯 Choose Your Industry/Niche",
                description=f"Hi **{name}**! Please select your primary industry or sales niche:",
                color=0x3498db
            )
            
            embed.add_field(
                name="💡 Why This Matters",
                value="Choosing your niche helps Danny Bot provide personalized training scenarios and industry-specific advice.",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, view=niche_view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error handling registration submission for {user.id}: {e}")
            await interaction.response.send_message("❌ Error processing registration. Please try again.", ephemeral=True)
    
    async def handle_niche_selection(self, interaction, niche):
        """Handle niche selection and complete registration"""
        user = interaction.user
        
        try:
            # Get registration data
            registration_data = self.active_registrations.get(user.id)
            if not registration_data:
                await interaction.response.send_message("❌ Registration session expired. Please start over.", ephemeral=True)
                return
            
            # Complete registration data
            registration_data['niche'] = niche
            registration_data['completed'] = True
            
            # Save to database
            await self.db_manager.save_user_registration(user.id, registration_data)
            await self.db_manager.update_user_registered_name(user.id, registration_data['name'])
            
            # Create training zone
            guild = interaction.guild
            category = await self.training_zone_manager.create_user_training_zone(guild, user, registration_data['name'])
            
            if category:
                # Find practice arena channel
                practice_channel = None
                for channel in category.channels:
                    if "💪practice-arena" in channel.name:
                        practice_channel = channel
                        break
                
                # Success message
                embed = discord.Embed(
                    title="🎉 Registration Complete!",
                    description=f"Welcome to Danny Bot, **{registration_data['name']}**!",
                    color=0x00ff88
                )
                
                embed.add_field(
                    name="✅ Your Profile",
                    value=f"• **Name:** {registration_data['name']}\n• **Experience:** {registration_data['experience']}\n• **Industry:** {niche}",
                    inline=False
                )
                
                if practice_channel:
                    embed.add_field(
                        name="🏠 Your Training Zone",
                        value=f"Your personal training space is ready!\n{practice_channel.mention}",
                        inline=False
                    )
                
                embed.add_field(
                    name="🚀 Next Steps",
                    value="1. Visit your practice arena\n2. Start with a role-play scenario\n3. Explore the playground for AI exercises\n4. Track your progress as you improve!",
                    inline=False
                )
                
                embed.set_footer(text="Danny Bot - Your AI Sales Training Journey Begins Now!")
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
                # Clean up registration session
                if user.id in self.active_registrations:
                    del self.active_registrations[user.id]
                
                logger.info(f"Registration completed for user {user.id} ({registration_data['name']})")
                
            else:
                await interaction.response.send_message("✅ Registration saved, but there was an issue creating your training zone. An admin will assist you shortly.", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error completing registration for {user.id}: {e}")
            await interaction.response.send_message("❌ Error completing registration. Please contact an admin.", ephemeral=True)
    
    async def create_training_zone_for_registered_user(self, guild, user, registration_data):
        """Create training zone for an already registered user"""
        try:
            name = registration_data.get('name', user.display_name)
            category = await self.training_zone_manager.create_user_training_zone(guild, user, name)
            
            if category:
                logger.info(f"Created training zone for registered user {user.id} ({name})")
                
                # Send follow-up message with training zone link
                practice_channel = None
                for channel in category.channels:
                    if "💪practice-arena" in channel.name:
                        practice_channel = channel
                        break
                
                if practice_channel:
                    try:
                        embed = discord.Embed(
                            title="🏠 Training Zone Ready!",
                            description=f"Your personal training space is now available: {practice_channel.mention}",
                            color=0x00ff88
                        )
                        embed.set_footer(text="Welcome back to Danny Bot!")
                        
                        await user.send(embed=embed)
                    except discord.Forbidden:
                        # Can't DM user, that's okay
                        pass
            
        except Exception as e:
            logger.error(f"Error creating training zone for registered user {user.id}: {e}")
    
    def get_registration_status(self, user_id):
        """Get the current registration status for a user"""
        return self.active_registrations.get(user_id)
    
    def cancel_registration(self, user_id):
        """Cancel an active registration session"""
        if user_id in self.active_registrations:
            del self.active_registrations[user_id]
            return True
        return False
    
    async def handle_stuck_registration(self, user_id):
        """Handle users who are stuck in registration process"""
        try:
            # Get user's registration from database
            registration = await self.db_manager.get_user_registration(user_id)
            
            if not registration:
                return False, "User has no registration record"
            
            # Check if they have a training zone
            user = self.bot.get_user(user_id)
            if not user:
                return False, "User not found"
            
            # Get all guilds and check for training zone
            for guild in self.bot.guilds:
                if user in guild.members:
                    training_zone = None
                    name = registration.get('name', user.display_name)
                    
                    for category in guild.categories:
                        if f"Training Zone - {name}" in category.name:
                            training_zone = category
                            break
                    
                    if not training_zone:
                        # Create missing training zone
                        category = await self.training_zone_manager.create_user_training_zone(guild, user, name)
                        if category:
                            return True, f"Created missing training zone for {name}"
                        else:
                            return False, f"Failed to create training zone for {name}"
                    else:
                        return True, f"Training zone already exists for {name}"
            
            return False, "User not found in any guild"
            
        except Exception as e:
            logger.error(f"Error handling stuck registration for {user_id}: {e}")
            return False, f"Error: {str(e)}"
    
    async def get_stuck_users(self):
        """Get list of users who might be stuck in registration"""
        try:
            # This would need to be implemented based on your specific criteria
            # For now, return the known stuck users from the conversation
            stuck_user_names = ["Jenni❤", "Chris Mitchell", "Ryan Butler", "Sara Leon"]
            
            stuck_users = []
            for guild in self.bot.guilds:
                for member in guild.members:
                    # Check if display name matches stuck users
                    if any(name.lower() in member.display_name.lower() for name in stuck_user_names):
                        registration = await self.db_manager.get_user_registration(member.id)
                        if registration:
                            # Check if they have training zone
                            training_zone = None
                            for category in guild.categories:
                                if f"Training Zone - {registration.get('name', member.display_name)}" in category.name:
                                    training_zone = category
                                    break
                            
                            if not training_zone:
                                stuck_users.append({
                                    'user': member,
                                    'name': registration.get('name', member.display_name),
                                    'registration': registration
                                })
            
            return stuck_users
            
        except Exception as e:
            logger.error(f"Error getting stuck users: {e}")
            return []

    async def handle_user_leaving(self, user_id):
        """Handle user leaving the guild"""
        try:
            # Get user's registration from database
            registration = await self.db_manager.get_user_registration(user_id)
            
            if not registration:
                return False, "User has no registration record"
            
            # Check if they have a training zone
            user = self.bot.get_user(user_id)
            if not user:
                return False, "User not found"
            
            # Get all guilds and check for training zone
            for guild in self.bot.guilds:
                if user in guild.members:
                    training_zone = None
                    name = registration.get('name', user.display_name)
                    
                    for category in guild.categories:
                        if f"Training Zone - {name}" in category.name:
                            training_zone = category
                            break
                    
                    if not training_zone:
                        # Create missing training zone
                        category = await self.training_zone_manager.create_user_training_zone(guild, user, name)
                        if category:
                            return True, f"Created missing training zone for {name}"
                        else:
                            return False, f"Failed to create training zone for {name}"
                    else:
                        return True, f"Training zone already exists for {name}"
            
            return False, "User not found in any guild"
            
        except Exception as e:
            logger.error(f"Error handling user leaving: {e}")

async def setup(bot):
    """Setup function for the registration handler cog"""
    await bot.add_cog(RegistrationHandler(bot)) 