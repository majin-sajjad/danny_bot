import discord
import logging

logger = logging.getLogger(__name__)

class WelcomeButtonView(discord.ui.View):
    """Welcome button view for new users"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label='🚀 Get Started', style=discord.ButtonStyle.primary, custom_id='get_started_button')
    async def get_started_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle the Get Started button click"""
        user = interaction.user
        guild = interaction.guild
        
        try:
            # Check if user already has a training zone
            existing_category = discord.utils.get(guild.categories, name=f"🔒 {user.display_name}'s Training Zone")
            
            if existing_category:
                embed = discord.Embed(
                    title="✅ Training Zone Already Exists!",
                    description=f"You already have a training zone: **{existing_category.name}**",
                    color=0x3498db
                )
                embed.add_field(
                    name="🗂️ Your Channels",
                    value=f"• You have {len(existing_category.channels)} channels ready\n• Check your category on the left sidebar",
                    inline=False
                )
                embed.add_field(
                    name="📝 Complete Registration",
                    value="If you see a 📝registration channel, complete your registration to unlock all features!",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Get TrainingZoneManager cog to create training zone
            training_zone_cog = interaction.client.get_cog('TrainingZoneManager')
            if not training_zone_cog:
                await interaction.response.send_message("❌ Training zone system not available.", ephemeral=True)
                return
            
            # Create user training zone
            await interaction.response.defer(ephemeral=True)
            
            try:
                category = await training_zone_cog.create_user_training_zone(guild, user)
                
                if category:
                    embed = discord.Embed(
                        title="🎉 Training Zone Created!",
                        description=f"Welcome **{user.display_name}**! Your personal training zone has been created.",
                        color=0x00ff88
                    )
                    embed.add_field(
                        name="📝 Next Steps",
                        value="1. **Complete Registration** - Fill out your details in the 📝registration channel\n2. **Choose Your Niche** - Select your sales industry\n3. **Start Training** - Begin with AI customers",
                        inline=False
                    )
                    embed.add_field(
                        name="🗂️ Your Training Zone",
                        value=f"**Category:** {category.name}\n**Channels:** {len(category.channels)} created\n**Status:** Registration pending",
                        inline=False
                    )
                    embed.set_footer(text="Check the left sidebar for your new category!")
                    
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send("❌ Failed to create training zone. Please contact an administrator.", ephemeral=True)
                
            except Exception as e:
                logger.error(f"Error creating training zone for {user.display_name}: {e}")
                await interaction.followup.send("❌ Error creating training zone. Please contact an administrator.", ephemeral=True)
        
        except Exception as e:
            logger.error(f"Welcome button error for {user.display_name}: {e}")
            try:
                await interaction.response.send_message("❌ An error occurred. Please try again.", ephemeral=True)
            except:
                await interaction.followup.send("❌ An error occurred. Please try again.", ephemeral=True) 