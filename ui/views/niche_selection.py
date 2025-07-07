import discord
import logging
import aiosqlite

logger = logging.getLogger(__name__)

class NicheSelectionView(discord.ui.View):
    """View for selecting user's niche after basic registration"""
    
    def __init__(self, user_data):
        super().__init__(timeout=300)
        self.user_data = user_data
        
    @discord.ui.select(
        placeholder="Select your niche/industry...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(
                label="🌐 Fiber Internet",
                value="fiber",
                description="Fiber optic internet sales (5 deals = 1 pt, sets & closes)",
                emoji="🌐"
            ),
            discord.SelectOption(
                label="☀️ Solar Energy",
                value="solar", 
                description="Solar panel sales (1 pt standard, 2 pts self-gen)",
                emoji="☀️"
            ),
            discord.SelectOption(
                label="🌿 Landscaping",
                value="landscaping",
                description="Landscaping services (1 pt set/close + value tiers)",
                emoji="🌿"
            )
        ]
    )
    async def niche_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        """Handle niche selection"""
        selected_niche = select.values[0]
        
        # Update user data with selected niche
        self.user_data['niche'] = selected_niche
        
        # Save complete registration to database
        await self._save_registration(interaction, self.user_data)
        
    async def _save_registration(self, interaction: discord.Interaction, user_data):
        """Save the complete registration with niche to database"""
        user = interaction.user
        
        try:
            # Save registration to database
            async with aiosqlite.connect('danny_bot.db') as db:
                await db.execute('''
                    INSERT OR REPLACE INTO user_registrations 
                    (user_id, first_name, last_name, phone_number, email, company, niche)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user.id,
                    user_data['first_name'],
                    user_data['last_name'], 
                    user_data['phone_number'],
                    user_data['email'],
                    user_data['company'],
                    user_data['niche']
                ))
                
                await db.commit()
            
            # Update AI name memory for Danny Pessy AI
            bot = interaction.client
            if hasattr(bot, 'db_manager'):
                await bot.db_manager.update_user_registered_name(
                    user.id, 
                    user_data['first_name'], 
                    user_data['last_name']
                )
                logger.info(f"Updated AI name memory for user {user.id}: {user_data['first_name']} {user_data['last_name']}")
            
            # Set user's nickname to real name
            full_name = f"{user_data['first_name']} {user_data['last_name']}"
            try:
                await user.edit(nick=full_name)
                nickname_status = f"✅ **Nickname updated:** {full_name}"
            except discord.Forbidden:
                nickname_status = "⚠️ **Nickname:** Could not update (permissions)"
            except Exception as e:
                nickname_status = f"⚠️ **Nickname:** Error updating ({str(e)})"
            
            # Get niche info for display
            niche_info = {
                'fiber': {
                    'name': '🌐 Fiber Internet',
                    'points': '5 deals = 1 point, 1 pt set that closes, 1 pt close, 2 pts self-gen'
                },
                'solar': {
                    'name': '☀️ Solar Energy', 
                    'points': '1 point standard deal, 2 points self-generated'
                },
                'landscaping': {
                    'name': '🌿 Landscaping',
                    'points': '1 pt set, 1 pt close, 1 pt per $50k above $50k'
                }
            }
            
            selected_niche_info = niche_info[user_data['niche']]
            
            # Success response
            success_embed = discord.Embed(
                title="✅ Registration Complete!",
                description=f"Welcome to Danny Bot, **{full_name}**!",
                color=0x00ff88
            )
            success_embed.add_field(
                name="📝 Your Information",
                value=f"**Name:** {full_name}\n**Phone:** {user_data['phone_number']}\n**Email:** {user_data['email']}\n**Company:** {user_data['company']}",
                inline=True
            )
            success_embed.add_field(
                name="🎯 Your Niche",
                value=f"**Industry:** {selected_niche_info['name']}\n**Points:** {selected_niche_info['points']}",
                inline=True
            )
            success_embed.add_field(
                name="🚀 What's Next?",
                value="• Complete your training zone setup\n• Start practicing with AI customers\n• Submit deals to earn points\n• Climb the leaderboards!",
                inline=False
            )
            success_embed.add_field(
                name="👤 Profile Status",
                value=nickname_status,
                inline=False
            )
            success_embed.set_footer(text="Your training zone is being finalized...")
            
            await interaction.response.send_message(embed=success_embed, ephemeral=True)
            
            # Trigger training zone completion if user has a category
            guild = interaction.guild
            user_category = discord.utils.get(guild.categories, name=f"🔒 {user.display_name}'s Training Zone")
            
            if user_category:
                # Get TrainingZoneManager cog to complete training zone
                training_zone_cog = interaction.client.get_cog('TrainingZoneManager')
                if training_zone_cog:
                    try:
                        await training_zone_cog.complete_training_zone_after_registration(guild, user, user_category, user_data)
                        logger.info(f"Training zone completed for {user.display_name}")
                    except Exception as e:
                        logger.error(f"Error completing training zone for {user.display_name}: {e}")
                        
        except Exception as e:
            logger.error(f"Registration save error for {user.display_name}: {e}")
            error_embed = discord.Embed(
                title="❌ Registration Error", 
                description=f"An error occurred while saving your registration: {str(e)}",
                color=0xe74c3c
            )
            try:
                await interaction.response.send_message(embed=error_embed, ephemeral=True)
            except:
                await interaction.followup.send(embed=error_embed, ephemeral=True) 