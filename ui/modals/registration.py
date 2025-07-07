import discord
import logging
import aiosqlite
from datetime import datetime

logger = logging.getLogger(__name__)

class RegistrationModal(discord.ui.Modal, title='Complete Your Registration'):
    """Registration form modal"""
    
    def __init__(self):
        super().__init__()
        
    first_name = discord.ui.TextInput(
        label='First Name',
        placeholder='Enter your first name...',
        required=True,
        max_length=50
    )
    
    last_name = discord.ui.TextInput(
        label='Last Name', 
        placeholder='Enter your last name...',
        required=True,
        max_length=50
    )
    
    phone_number = discord.ui.TextInput(
        label='Phone Number',
        placeholder='Enter your phone number...',
        required=True,
        max_length=20
    )
    
    email = discord.ui.TextInput(
        label='Email Address',
        placeholder='Enter your email address...',
        required=True,
        max_length=100
    )
    
    company = discord.ui.TextInput(
        label='Company/Organization',
        placeholder='Enter your company or organization...',
        required=True,
        max_length=100
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission"""
        user = interaction.user
        
        try:
            # Store user data for niche selection
            user_data = {
                'first_name': self.first_name.value,
                'last_name': self.last_name.value,
                'phone_number': self.phone_number.value,
                'email': self.email.value,
                'company': self.company.value or 'Not specified'
            }
            
            # Create niche selection embed
            embed = discord.Embed(
                title="🎯 Choose Your Sales Niche",
                description=f"Almost done, **{user_data['first_name']}**! Please select your industry to complete registration and unlock niche-specific features.",
                color=0x3498db
            )
            
            embed.add_field(
                name="🌐 Fiber Internet",
                value="• 5 deals = 1 point\n• 1 point for set that closes\n• 1 point for close\n• 2 points for self-generated",
                inline=True
            )
            
            embed.add_field(
                name="☀️ Solar Energy",
                value="• 1 point for standard deal\n• 2 points for self-generated deal",
                inline=True
            )
            
            embed.add_field(
                name="🌿 Landscaping",
                value="• 1 point for set\n• 1 point for close\n• 1 point per $50k above $50k",
                inline=True
            )
            
            embed.add_field(
                name="💡 Why This Matters",
                value="Your niche determines:\n• Point calculation systems\n• Deal submission buttons\n• Specialized training content\n• Competition categories",
                inline=False
            )
            
            embed.set_footer(text="Choose your niche from the dropdown below")
            
            # Show niche selection
            from ui.views.niche_selection import NicheSelectionView
            niche_view = NicheSelectionView(user_data)
            await interaction.response.send_message(embed=embed, view=niche_view, ephemeral=True)
            
        except Exception as e:
            print(f"❌ Registration form error for {user.display_name}: {e}")
            error_embed = discord.Embed(
                title="❌ Registration Error",
                description=f"An error occurred while processing your registration: {str(e)}",
                color=0xff0000
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True) 