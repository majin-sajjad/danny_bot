import discord
import logging
import aiosqlite
from ui.modals.registration import RegistrationModal

logger = logging.getLogger(__name__)

class RegistrationView(discord.ui.View):
    """View with registration button"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label='📝 Complete Registration', style=discord.ButtonStyle.primary, custom_id='registration_button')
    async def registration_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle registration button click"""
        user = interaction.user
        
        # Check if user is already registered
        try:
            async with aiosqlite.connect('danny_bot.db') as db:
                async with db.execute('SELECT first_name, last_name FROM user_registrations WHERE user_id = ?', (user.id,)) as cursor:
                    existing_registration = await cursor.fetchone()
            
            if existing_registration:
                embed = discord.Embed(
                    title="✅ Already Registered",
                    description=f"You're already registered as **{existing_registration[0]} {existing_registration[1]}**!",
                    color=0x3498db
                )
                embed.add_field(
                    name="Need to Update?",
                    value="Click the button again to update your information.",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
                # Still allow them to update by showing the modal
                await interaction.followup.send("Click the button again if you want to update your information.", ephemeral=True)
                return
            
        except Exception as e:
            logger.error(f"Error checking registration for user {user.id}: {e}")
        
        # Show registration modal
        modal = RegistrationModal()
        await interaction.response.send_modal(modal) 