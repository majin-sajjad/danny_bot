import discord
from discord.ext import commands
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from core.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class PlaygroundView(discord.ui.View):
    """Main playground interface for creating homeowner personalities"""
    
    def __init__(self):
        super().__init__(timeout=None)  # Make persistent
        
    @discord.ui.button(label="🚪 Create Homeowner Personality", style=discord.ButtonStyle.primary, emoji="🚪", custom_id="playground_create_homeowner")
    async def create_homeowner(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Create a new homeowner personality"""
        try:
            # Defer the interaction immediately to prevent timeout
            await interaction.response.defer(ephemeral=True)
            
            # Create niche selection view
            niche_view = PlaygroundNicheView()
            
            embed = discord.Embed(
                title="🏠 Choose Your Sales Niche",
                description="Select which type of homeowner you want to practice with:",
                color=0x3498db
            )
            
            embed.add_field(
                name="🌐 Fiber Network",
                value="Practice selling high-speed internet packages",
                inline=False
            )
            embed.add_field(
                name="☀️ Solar Energy", 
                value="Practice selling solar panel installations",
                inline=False
            )
            embed.add_field(
                name="🌿 Landscaping",
                value="Practice selling landscaping services",
                inline=False
            )
            
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=niche_view)
            
        except Exception as e:
            logger.error(f"Error starting homeowner creation: {e}")
            
            # Send error message as followup
            embed = discord.Embed(
                title="❌ Error",
                description="There was an error starting the homeowner creation process. Please try again.",
                color=0xe74c3c
            )
            
            try:
                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self)
            except:
                # If edit fails, send as new message
                await interaction.followup.send(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="📊 My Created Homeowners", style=discord.ButtonStyle.secondary, emoji="📊", custom_id="playground_my_homeowners")
    async def my_homeowners(self, interaction: discord.Interaction, button: discord.ui.Button):
        """View user's created homeowners"""
        try:
            # Defer the interaction immediately
            await interaction.response.defer(ephemeral=True)
            
            # Get user's homeowners from database
            from systems.playground.database import PlaygroundDatabase
            db = PlaygroundDatabase()
            homeowners = await db.get_user_homeowners(interaction.user.id)
            
            if not homeowners:
                embed = discord.Embed(
                    title="📊 Your Created Homeowners",
                    description="You haven't created any homeowners yet! Click '🚪 Create Homeowner Personality' to get started.",
                    color=0x95a5a6
                )
            else:
                embed = discord.Embed(
                    title="📊 Your Created Homeowners",
                    description=f"You have created {len(homeowners)} homeowner personalities:",
                    color=0x3498db
                )
                
                for i, homeowner in enumerate(homeowners[:5]):  # Show first 5
                    embed.add_field(
                        name=f"🏠 {homeowner.get('name', 'Unknown')}",
                        value=f"**Niche:** {homeowner.get('niche', 'Unknown').title()}\n**Created:** {homeowner.get('created_at', 'Unknown')[:10]}",
                        inline=True
                    )
                
                if len(homeowners) > 5:
                    embed.add_field(
                        name="📝 Note",
                        value=f"... and {len(homeowners) - 5} more homeowners",
                        inline=False
                    )
            
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self)
            
        except Exception as e:
            logger.error(f"Error viewing homeowners: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Error loading your homeowners. Please try again.",
                color=0xe74c3c
            )
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self)
    
    @discord.ui.button(label="❓ How It Works", style=discord.ButtonStyle.success, emoji="❓", custom_id="playground_show_help")
    async def show_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show playground help information"""
        try:
            # Defer the interaction immediately
            await interaction.response.defer(ephemeral=True)
            
            help_view = PlaygroundHelpView()
            embed = help_view.get_help_embed()
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=help_view)
        except Exception as e:
            logger.error(f"Error showing help: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Error loading help information. Please try again.",
                color=0xe74c3c
            )
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self)

class HomeownerLibraryView(discord.ui.View):
    """View for choosing between personal and community homeowner libraries"""
    
    def __init__(self):
        super().__init__(timeout=None)
        self.db_manager = DatabaseManager()
    
    @discord.ui.button(label="🏠 My Library", style=discord.ButtonStyle.primary, emoji="🏠")
    async def my_library(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show user's personal homeowner library"""
        try:
            # Get user's saved homeowners
            user_homeowners = await self._get_user_homeowners(interaction.user.id)
            
            embed = discord.Embed(
                title="🏠 My Homeowner Library",
                description=f"Your personal homeowner collection ({len(user_homeowners)} homeowners)",
                color=0x3498db
            )
            
            if not user_homeowners:
                embed.add_field(
                    name="📭 No Homeowners Yet",
                    value="You haven't created any homeowner personalities yet!\n\n• Click '🚪 Create Homeowner Personality' to get started\n• Build your personal library of practice partners\n• Save homeowners after practice sessions",
                    inline=False
                )
            else:
                # Show dropdown with user's homeowners
                embed.add_field(
                    name="📋 Your Homeowners",
                    value="Select a homeowner from the dropdown below to view details or start practice:",
                    inline=False
                )
                
                # Create dropdown view
                dropdown_view = MyHomeownerDropdownView(user_homeowners)
                await interaction.response.edit_message(embed=embed, view=dropdown_view)
                return
            
            await interaction.response.edit_message(embed=embed, view=self)
            
        except Exception as e:
            logger.error(f"Error showing my library: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Error accessing your library. Please try again.",
                color=0xe74c3c
            )
            await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="🌍 Community Library", style=discord.ButtonStyle.secondary, emoji="🌍")
    async def community_library(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show community homeowner library"""
        try:
            # Get community homeowners
            community_homeowners = await self._get_community_homeowners()
            
            embed = discord.Embed(
                title="🌍 Community Homeowner Library",
                description=f"Homeowners created by the community ({len(community_homeowners)} homeowners)",
                color=0x9b59b6
            )
            
            if not community_homeowners:
                embed.add_field(
                    name="🔨 Building Community",
                    value="The community library is growing! Be one of the first to contribute by:\n\n• Creating high-quality homeowner personalities\n• Sharing your best homeowners with the community\n• Rating and reviewing others' homeowners",
                    inline=False
                )
            else:
                # Show dropdown with community homeowners
                embed.add_field(
                    name="📋 Community Homeowners",
                    value="Select a homeowner from the dropdown below to view details or start practice:",
                    inline=False
                )
                
                # Create dropdown view
                dropdown_view = CommunityHomeownerDropdownView(community_homeowners)
                await interaction.response.edit_message(embed=embed, view=dropdown_view)
                return
            
            await interaction.response.edit_message(embed=embed, view=self)
            
        except Exception as e:
            logger.error(f"Error showing community library: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Error accessing community library. Please try again.",
                color=0xe74c3c
            )
            await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="🔙 Back to Playground", style=discord.ButtonStyle.secondary, emoji="🔙")
    async def back_to_playground(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go back to main playground view"""
        # Use persistent view instance to avoid timeout issues
        main_view = interaction.client.persistent_playground_view
        
        embed = discord.Embed(
            title="🚪 Lord of the Doors Season 3 - Playground Library",
            description="Create and practice with custom homeowner personalities",
            color=0x9b59b6
        )
        
        embed.add_field(
            name="🎭 What's Available",
            value="• **Create Homeowners** - Design custom personalities\n• **Practice Door Knocking** - Realistic practice scenarios\n• **Build Your Library** - Save your best homeowners",
            inline=False
        )
        
        await interaction.response.edit_message(embed=embed, view=main_view)
    
    async def _get_user_homeowners(self, user_id: int) -> list:
        """Get user's saved homeowners from database"""
        # Mock data for now - would fetch from database
        # Most users will have 0 homeowners initially
        return []
    
    async def _get_community_homeowners(self) -> list:
        """Get community homeowners from database"""
        # Mock data representing the 4 built-in personalities (Owl, Bull, Sheep, Tiger)
        return [
            {"id": 101, "name": "Analytical Annie (Owl)", "niche": "solar", "description": "Asks detailed technical questions, wants data and proof", "creator": "Danny Bot"},
            {"id": 102, "name": "Aggressive Al (Bull)", "niche": "fiber", "description": "Confrontational and challenges everything you say", "creator": "Danny Bot"},
            {"id": 103, "name": "Passive Paul (Sheep)", "niche": "landscaping", "description": "Quiet, goes along with suggestions, rarely objects", "creator": "Danny Bot"},
            {"id": 104, "name": "Dominant Diana (Tiger)", "niche": "solar", "description": "Takes control, wants to be the decision maker", "creator": "Danny Bot"},
        ]

class MyHomeownerDropdownView(discord.ui.View):
    """View with dropdown for user's personal homeowners"""
    
    def __init__(self, homeowners: list):
        super().__init__(timeout=300)
        self.homeowners = homeowners
        self.add_item(MyHomeownerDropdown(homeowners))

class MyHomeownerDropdown(discord.ui.Select):
    """Dropdown for selecting personal homeowners"""
    
    def __init__(self, homeowners: list):
        options = []
        for homeowner in homeowners[:25]:  # Discord limit
            options.append(discord.SelectOption(
                label=homeowner["name"],
                description=f"{homeowner['niche'].title()}: {homeowner['description'][:50]}...",
                value=str(homeowner["id"])
            ))
        
        super().__init__(
            placeholder="Select a homeowner to view or practice with...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.homeowners = homeowners
    
    async def callback(self, interaction: discord.Interaction):
        """Handle homeowner selection"""
        selected_id = int(self.values[0])
        homeowner = next((h for h in self.homeowners if h["id"] == selected_id), None)
        
        if homeowner:
            embed = discord.Embed(
                title=f"🏠 {homeowner['name']}",
                description=f"**Niche:** {homeowner['niche'].title()}\n**Description:** {homeowner['description']}",
                color=0x3498db
            )
            
            embed.add_field(
                name="⚡ Quick Actions",
                value="• Click '🚪 Start Practice' to begin door knocking\n• Click '✏️ Edit' to modify this homeowner\n• Click '🗑️ Delete' to remove from library",
                inline=False
            )
            
            action_view = HomeownerActionView(homeowner)
            await interaction.response.edit_message(embed=embed, view=action_view)

class CommunityHomeownerDropdownView(discord.ui.View):
    """View with dropdown for community homeowners"""
    
    def __init__(self, homeowners: list):
        super().__init__(timeout=300)
        self.homeowners = homeowners
        self.add_item(CommunityHomeownerDropdown(homeowners))

class CommunityHomeownerDropdown(discord.ui.Select):
    """Dropdown for selecting community homeowners"""
    
    def __init__(self, homeowners: list):
        options = []
        for homeowner in homeowners[:25]:  # Discord limit
            options.append(discord.SelectOption(
                label=homeowner["name"],
                description=f"{homeowner['niche'].title()}: {homeowner['description'][:50]}...",
                value=str(homeowner["id"])
            ))
        
        super().__init__(
            placeholder="Select a community homeowner to view or practice with...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.homeowners = homeowners
    
    async def callback(self, interaction: discord.Interaction):
        """Handle community homeowner selection"""
        selected_id = int(self.values[0])
        homeowner = next((h for h in self.homeowners if h["id"] == selected_id), None)
        
        if homeowner:
            embed = discord.Embed(
                title=f"🌍 {homeowner['name']}",
                description=f"**Niche:** {homeowner['niche'].title()}\n**Description:** {homeowner['description']}\n**Created by:** {homeowner['creator']}",
                color=0x9b59b6
            )
            
            embed.add_field(
                name="⚡ Quick Actions",
                value="• Click '🚪 Start Practice' to begin door knocking\n• Click '💾 Save Copy' to add to your library\n• Click '⭐ Rate' to rate this homeowner",
                inline=False
            )
            
            action_view = CommunityHomeownerActionView(homeowner)
            await interaction.response.edit_message(embed=embed, view=action_view)

class HomeownerActionView(discord.ui.View):
    """Actions for personal homeowners"""
    
    def __init__(self, homeowner: dict):
        super().__init__(timeout=300)
        self.homeowner = homeowner
    
    @discord.ui.button(label="🚪 Start Practice", style=discord.ButtonStyle.primary, emoji="🚪")
    async def start_practice(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Start practice with this homeowner"""
        try:
            # Defer the interaction
            await interaction.response.defer()
            
            # Get the playground manager
            playground_manager = interaction.client.get_cog('PlaygroundManager')
            if not playground_manager:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Playground system not available. Please try again later.",
                    color=0xe74c3c
                )
                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)
                return
            
            # Start the practice session in the current channel
            await playground_manager.start_practice_session(
                interaction.user.id,
                self.homeowner,
                interaction.channel
            )
            
            # Create practice session view
            practice_view = PracticeSessionView(self.homeowner['id'], self.homeowner)
            
            embed = discord.Embed(
                title="🚪 Practice Session Started!",
                description=f"You're now practicing with **{self.homeowner['name']}**",
                color=0x00ff88
            )
            
            embed.add_field(
                name="🎯 Your Goal",
                value=f"Try to sell {self.homeowner['niche']} services to this homeowner",
                inline=False
            )
            
            embed.add_field(
                name="🚀 Getting Started",
                value="Use the \"🚪 Knock on Door\" button below to start the conversation!",
                inline=False
            )
            
            # Update with practice session interface
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=practice_view)
            
        except Exception as e:
            logger.error(f"Error starting practice session: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Error starting practice session. Please try again.",
                color=0xe74c3c
            )
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)
    
    @discord.ui.button(label="✏️ Edit", style=discord.ButtonStyle.secondary, emoji="✏️")
    async def edit_homeowner(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Edit this homeowner"""
        embed = discord.Embed(
            title="✏️ Editing Homeowner",
            description=f"Opening editor for **{self.homeowner['name']}**... (Feature coming soon)",
            color=0x3498db
        )
        await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="🗑️ Delete", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def delete_homeowner(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Delete this homeowner"""
        embed = discord.Embed(
            title="🗑️ Homeowner Deleted",
            description=f"**{self.homeowner['name']}** has been removed from your library. (Feature coming soon)",
            color=0xe74c3c
        )
        await interaction.response.edit_message(embed=embed, view=None)

class CommunityHomeownerActionView(discord.ui.View):
    """Actions for community homeowners"""
    
    def __init__(self, homeowner: dict):
        super().__init__(timeout=300)
        self.homeowner = homeowner
    
    @discord.ui.button(label="🚪 Start Practice", style=discord.ButtonStyle.primary, emoji="🚪")
    async def start_practice(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Start practice with this homeowner"""
        try:
            # Defer the interaction
            await interaction.response.defer()
            
            # Get the playground manager
            playground_manager = interaction.client.get_cog('PlaygroundManager')
            if not playground_manager:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Playground system not available. Please try again later.",
                    color=0xe74c3c
                )
                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)
                return
            
            # Start the practice session in the current channel
            await playground_manager.start_practice_session(
                interaction.user.id,
                self.homeowner,
                interaction.channel
            )
            
            # Create practice session view
            practice_view = PracticeSessionView(self.homeowner['id'], self.homeowner)
            
            embed = discord.Embed(
                title="🚪 Practice Session Started!",
                description=f"You're now practicing with **{self.homeowner['name']}**",
                color=0x00ff88
            )
            
            embed.add_field(
                name="🎯 Your Goal",
                value=f"Try to sell {self.homeowner['niche']} services to this homeowner",
                inline=False
            )
            
            embed.add_field(
                name="🚀 Getting Started",
                value="Use the \"🚪 Knock on Door\" button below to start the conversation!",
                inline=False
            )
            
            # Update with practice session interface
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=practice_view)
            
        except Exception as e:
            logger.error(f"Error starting practice session: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Error starting practice session. Please try again.",
                color=0xe74c3c
            )
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)
    
    @discord.ui.button(label="💾 Save Copy", style=discord.ButtonStyle.success, emoji="💾")
    async def save_copy(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Save copy to personal library"""
        embed = discord.Embed(
            title="💾 Saved to Your Library!",
            description=f"A copy of **{self.homeowner['name']}** has been saved to your personal library. (Feature coming soon)",
            color=0x00ff88
        )
        await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="⭐ Rate", style=discord.ButtonStyle.secondary, emoji="⭐")
    async def rate_homeowner(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Rate this homeowner"""
        embed = discord.Embed(
            title="⭐ Rate Homeowner",
            description=f"Rating system for **{self.homeowner['name']}** coming soon!",
            color=0xf39c12
        )
        await interaction.response.edit_message(embed=embed, view=None)

class PlaygroundNicheView(discord.ui.View):
    """Niche selection view for homeowner personality creation"""
    
    def __init__(self):
        super().__init__(timeout=None)  # Make persistent
        
    @discord.ui.button(label="🌐 Fiber Network", style=discord.ButtonStyle.primary, emoji="🌐", custom_id="playground_select_fiber")
    async def select_fiber(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Select fiber niche for homeowner"""
        await self._handle_niche_selection(interaction, "fiber")
    
    @discord.ui.button(label="☀️ Solar Energy", style=discord.ButtonStyle.primary, emoji="☀️", custom_id="playground_select_solar")
    async def select_solar(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Select solar niche for homeowner"""
        await self._handle_niche_selection(interaction, "solar")
    
    @discord.ui.button(label="🌿 Landscaping", style=discord.ButtonStyle.primary, emoji="🌿", custom_id="playground_select_landscaping")
    async def select_landscaping(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Select landscaping niche for homeowner"""
        await self._handle_niche_selection(interaction, "landscaping")
    
    @discord.ui.button(label="🔙 Back to Playground", style=discord.ButtonStyle.secondary, emoji="🔙", custom_id="playground_back_to_main")
    async def back_to_playground(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go back to main playground view"""
        try:
            # Defer the interaction immediately
            await interaction.response.defer(ephemeral=True)
            
            # Create main playground view
            main_view = PlaygroundView()
            
            embed = discord.Embed(
                title="🛠️ Playground Library",
                description="Create and manage custom homeowner personalities for door-to-door sales practice.",
                color=0x9b59b6
            )
            
            embed.add_field(
                name="🚪 Create Homeowner Personality",
                value="Build a custom homeowner with realistic objections and responses",
                inline=False
            )
            
            embed.add_field(
                name="📊 My Created Homeowners",
                value="View and manage your homeowner personalities",
                inline=False
            )
            
            embed.add_field(
                name="❓ How It Works",
                value="Learn how to use the playground system",
                inline=False
            )
            
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=main_view)
            
        except Exception as e:
            logger.error(f"Error going back to playground: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Error returning to playground. Please try again.",
                color=0xe74c3c
            )
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self)
    
    async def _handle_niche_selection(self, interaction: discord.Interaction, niche: str):
        """Handle niche selection and start homeowner creation"""
        try:
            # DO NOT defer the interaction for modals - send modal directly
            modal = HomeownerCreationModal(niche)
            await interaction.response.send_modal(modal)
            
        except Exception as e:
            logger.error(f"Error handling niche selection: {e}")
            # If modal fails, try to send an error message
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Error starting homeowner creation. Please try again.", ephemeral=True)
                else:
                    await interaction.followup.send("❌ Error starting homeowner creation. Please try again.", ephemeral=True)
            except:
                pass  # Ignore any additional errors

class HomeownerCreationModal(discord.ui.Modal):
    """Modal for creating homeowner personalities"""
    
    def __init__(self, niche: str):
        super().__init__(title=f"Create {niche.title()} Homeowner", timeout=None)
        self.niche = niche
        
        # Add text inputs for homeowner details
        self.add_item(discord.ui.TextInput(
            label="Homeowner Name",
            placeholder="e.g., Sarah Johnson",
            max_length=100,
            required=True
        ))
        
        self.add_item(discord.ui.TextInput(
            label="Personality Description",
            placeholder="e.g., Busy working mom, skeptical of sales pitches, values family time",
            style=discord.TextStyle.paragraph,
            max_length=500,
            required=True
        ))
        
        self.add_item(discord.ui.TextInput(
            label="Background Context",
            placeholder="e.g., Lives in suburban neighborhood, has 2 kids, works from home",
            style=discord.TextStyle.paragraph,
            max_length=500,
            required=False
        ))
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle the modal submission"""
        try:
            # Defer the interaction immediately
            await interaction.response.defer(ephemeral=True)
            
            # Get the form data
            homeowner_name = self.children[0].value
            personality_description = self.children[1].value
            background_context = self.children[2].value or "No additional background provided."
            
            # Create homeowner data
            homeowner_data = {
                'name': homeowner_name,
                'niche': self.niche,
                'personality_description': personality_description,
                'background_context': background_context,
                'creator_id': interaction.user.id
            }
            
            # Enhance the personality with AI
            enhanced_description = await self._enhance_personality_with_ai(homeowner_data)
            
            # Save to database
            from systems.playground.database import PlaygroundDatabase
            db = PlaygroundDatabase()
            homeowner_id = await db.create_homeowner(homeowner_data)
            
            # Create success view
            view = HomeownerCreatedView(homeowner_id, homeowner_data)
            
            embed = discord.Embed(
                title="✅ Homeowner Created Successfully!",
                description=f"**{homeowner_name}** has been created and is ready for practice.",
                color=0x00ff88
            )
            
            embed.add_field(
                name="🏠 Homeowner Details",
                value=f"**Name:** {homeowner_name}\n**Niche:** {self.niche.title()}\n**Personality:** {personality_description[:100]}...",
                inline=False
            )
            
            embed.add_field(
                name="🎯 What's Next?",
                value="• Start practicing door-to-door sales\n• Test different sales approaches\n• Build your confidence!",
                inline=False
            )
            
            # Send the success message
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error creating homeowner: {e}")
            
            # Send error message
            embed = discord.Embed(
                title="❌ Error Creating Homeowner",
                description="There was an error creating your homeowner. Please try again.",
                color=0xe74c3c
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    async def _enhance_personality_with_ai(self, homeowner_data: dict) -> str:
        """Enhance the homeowner personality description with AI"""
        try:
            # Import the AI integration
            from systems.playground.ai_integration import PlaygroundAI
            
            # Create AI instance and enhance the personality
            ai = PlaygroundAI()
            
            # Map the data to match what the AI expects
            wizard_data = {
                'name': homeowner_data['name'],
                'description': homeowner_data['personality_description'],
                'behavior': homeowner_data.get('background_context', 'No specific behavior patterns provided.'),
                'niche': homeowner_data['niche']
            }
            
            enhanced_description = await ai.generate_system_prompt(wizard_data)
            
            return enhanced_description
            
        except Exception as e:
            logger.error(f"Error enhancing personality with AI: {e}")
            # Return original description if AI enhancement fails
            return homeowner_data['personality_description']

class HomeownerCreatedView(discord.ui.View):
    """View shown after successfully creating a homeowner"""
    
    def __init__(self, homeowner_id: int, homeowner_data: dict):
        super().__init__(timeout=None)  # Make persistent
        self.homeowner_id = homeowner_id
        self.homeowner_data = homeowner_data
    
    @discord.ui.button(label="🚪 Start Door Knocking Practice", style=discord.ButtonStyle.primary, emoji="🚪", custom_id="playground_start_practice")
    async def start_practice(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Start practicing with the newly created homeowner in the playground library"""
        try:
            # Defer the interaction immediately
            await interaction.response.defer()
            
            # Get the playground manager from the bot
            playground_manager = interaction.client.get_cog('PlaygroundManager')
            if not playground_manager:
                await interaction.followup.edit_message(interaction.message.id, 
                    content="❌ Playground system not available. Please try again later.", 
                    embed=None, view=None)
                return
            
            # Start practice session in the CURRENT playground library channel (no redirection!)
            await playground_manager.start_practice_session(
                interaction.user.id, 
                self.homeowner_data,  # Pass full homeowner data dict
                interaction.channel  # Keep it in the current playground library channel
            )
            
            # Update the message to show the practice has started
            embed = discord.Embed(
                title="🚪 Door Knocking Practice Started!",
                description=f"You're now at the door of **{self.homeowner_data['name']}**",
                color=0x00ff88
            )
            
            embed.add_field(
                name="🎯 Your Mission",
                value=f"Practice your {self.homeowner_data['niche']} sales approach. Start by knocking on their door and introduce yourself!",
                inline=False
            )
            
            embed.add_field(
                name="💡 Pro Tips",
                value="• Be confident but respectful\n• Listen to their objections\n• Build rapport and trust\n• Show genuine value",
                inline=False
            )
            
            embed.add_field(
                name="🏠 About This Homeowner",
                value=f"**Name:** {self.homeowner_data['name']}\n**Niche:** {self.homeowner_data['niche'].title()}\n**Personality:** {self.homeowner_data['personality_description'][:150]}{'...' if len(self.homeowner_data['personality_description']) > 150 else ''}",
                inline=False
            )
            
            embed.add_field(
                name="🚀 Ready to Start?",
                value="**Type your door knock and introduction** in this channel. The homeowner will respond based on their personality!",
                inline=False
            )
            
            embed.set_footer(text="💬 This is live AI conversation practice - type naturally!")
            
            # Remove the view since we're starting the conversation
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)
                
        except Exception as e:
            logger.error(f"Error starting practice: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Error starting practice session. Please try again.",
                color=0xe74c3c
            )
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self)
    
    @discord.ui.button(label="📚 Back to Library", style=discord.ButtonStyle.secondary, emoji="📚", custom_id="playground_back_to_library")
    async def back_to_library(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go back to the homeowner library"""
        try:
            # Defer the interaction immediately
            await interaction.response.defer(ephemeral=True)
            
            # Create main playground view
            main_view = PlaygroundView()
            
            embed = discord.Embed(
                title="🛠️ Playground Library",
                description="Create and manage custom homeowner personalities for door-to-door sales practice.",
                color=0x9b59b6
            )
            
            embed.add_field(
                name="🚪 Create Homeowner Personality",
                value="Build a custom homeowner with realistic objections and responses",
                inline=False
            )
            
            embed.add_field(
                name="📊 My Created Homeowners",
                value="View and manage your homeowner personalities",
                inline=False
            )
            
            embed.add_field(
                name="❓ How It Works",
                value="Learn how to use the playground system",
                inline=False
            )
            
            await interaction.followup.send(embed=embed, view=main_view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error going back to library: {e}")
            await interaction.followup.send("❌ Error returning to library. Please try again.", ephemeral=True)

class PlaygroundPracticeView(discord.ui.View):
    """View for managing an active playground practice session"""
    
    def __init__(self, session_data: Dict[str, Any]):
        super().__init__(timeout=1800)  # 30 minute timeout
        self.session_data = session_data
    
    @discord.ui.button(label="💬 Continue Conversation", style=discord.ButtonStyle.primary, emoji="💬")
    async def continue_conversation(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Continue the door knocking conversation"""
        embed = discord.Embed(
            title="🚪 Door Knocking in Progress",
            description="Continue your conversation with the homeowner in this channel. They will respond based on their personality.",
            color=0x3498db
        )
        
        embed.add_field(
            name="💡 Tips",
            value="• Use your sales approach naturally\n• Handle objections professionally\n• Build rapport and trust\n• Listen for buying signals",
            inline=False
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="🔚 End Practice", style=discord.ButtonStyle.danger, emoji="🔚")
    async def end_practice(self, interaction: discord.Interaction, button: discord.ui.Button):
        """End the current practice session"""
        try:
            # Calculate session duration
            started_at = datetime.fromisoformat(self.session_data['started_at'])
            duration = datetime.now() - started_at
            
            # Show feedback view
            feedback_view = PlaygroundFeedbackView(self.session_data)
            
            embed = discord.Embed(
                title="🎯 Practice Session Complete!",
                description="Your door knocking practice session has ended. Please provide feedback to help improve future homeowner personalities.",
                color=0x00ff88
            )
            
            embed.add_field(
                name="📊 Session Summary",
                value=f"• **Duration:** {duration.seconds // 60} minutes\n• **Homeowner:** {self.session_data['homeowner_data']['name']}\n• **Niche:** {self.session_data['homeowner_data']['niche'].title()}",
                inline=False
            )
            
            await interaction.response.edit_message(embed=embed, view=feedback_view)
            
        except Exception as e:
            logger.error(f"Error ending practice session: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Error ending practice session. Please try again.",
                color=0xe74c3c
            )
            await interaction.response.edit_message(embed=embed, view=self)

class PlaygroundFeedbackView(discord.ui.View):
    """View for collecting feedback after practice sessions"""
    
    def __init__(self, session_data: Dict[str, Any]):
        super().__init__(timeout=600)  # 10 minute timeout for feedback
        self.session_data = session_data
    
    @discord.ui.button(label="📝 Provide Feedback", style=discord.ButtonStyle.primary, emoji="📝")
    async def provide_feedback(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Open feedback modal"""
        modal = PlaygroundFeedbackModal(self.session_data)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="⏭️ Skip Feedback", style=discord.ButtonStyle.secondary, emoji="⏭️")
    async def skip_feedback(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Skip feedback and go to save/delete choice"""
        view = SaveDeleteView(self.session_data, feedback_data=None)
        
        embed = discord.Embed(
            title="🎯 Session Complete!",
            description="Your door-knocking practice session has ended. Would you like to save this homeowner personality?",
            color=0x00ff88
        )
        
        embed.add_field(
            name="💾 Save Personality",
            value="Save this homeowner to your library for future practice sessions",
            inline=True
        )
        
        embed.add_field(
            name="🗑️ Delete Personality",
            value="Remove this homeowner and don't save it",
            inline=True
        )
        
        await interaction.response.edit_message(embed=embed, view=view)

class PlaygroundFeedbackModal(discord.ui.Modal, title="📝 Homeowner Feedback"):
    """Modal for collecting detailed feedback about the homeowner personality"""
    
    def __init__(self, session_data: Dict[str, Any]):
        super().__init__()
        self.session_data = session_data
        
        self.realism_rating = discord.ui.TextInput(
            label="Realism Rating (1-10)",
            placeholder="How realistic was this homeowner? (1=very fake, 10=extremely realistic)",
            min_length=1,
            max_length=2,
            required=True
        )
        
        self.difficulty_rating = discord.ui.TextInput(
            label="Difficulty Rating (1-10)",
            placeholder="How challenging was this homeowner? (1=too easy, 10=very challenging)",
            min_length=1,
            max_length=2,
            required=True
        )
        
        self.homeowner_behavior = discord.ui.TextInput(
            label="Homeowner Behavior Feedback",
            placeholder="How did the homeowner act? Was it realistic for someone who just had their door knocked?",
            style=discord.TextStyle.paragraph,
            min_length=20,
            max_length=500,
            required=True
        )
        
        self.improvements = discord.ui.TextInput(
            label="Suggested Improvements",
            placeholder="What could make them better?",
            style=discord.TextStyle.paragraph,
            min_length=10,
            max_length=500,
            required=False
        )
        
        self.add_item(self.realism_rating)
        self.add_item(self.difficulty_rating)
        self.add_item(self.homeowner_behavior)
        self.add_item(self.improvements)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Process feedback and show save/delete options"""
        try:
            # Validate ratings
            try:
                realism = int(self.realism_rating.value)
                difficulty = int(self.difficulty_rating.value)
                if not (1 <= realism <= 10) or not (1 <= difficulty <= 10):
                    raise ValueError("Ratings must be between 1-10")
            except ValueError:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Please enter valid ratings between 1-10.",
                    color=0xe74c3c
                )
                await interaction.response.edit_message(embed=embed, view=self)
                return
            
            feedback_data = {
                'realism_rating': realism,
                'difficulty_rating': difficulty,
                'behavior_feedback': self.homeowner_behavior.value,
                'improvements': self.improvements.value,
                'timestamp': datetime.now().isoformat()
            }
            
            view = SaveDeleteView(self.session_data, feedback_data)
            
            embed = discord.Embed(
                title="✅ Feedback Received!",
                description="Thank you for your feedback! This will help improve future homeowner personalities.\n\nWould you like to save this homeowner personality?",
                color=0x00ff88
            )
            
            embed.add_field(
                name="📊 Your Ratings",
                value=f"**Realism:** {realism}/10\n**Difficulty:** {difficulty}/10",
                inline=True
            )
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error processing feedback: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Error processing feedback. Please try again.",
                color=0xe74c3c
            )
            await interaction.response.edit_message(embed=embed, view=self)

class SaveDeleteView(discord.ui.View):
    """View for choosing to save or delete a homeowner personality after practice"""
    
    def __init__(self, session_data: Dict[str, Any], feedback_data: Optional[Dict[str, Any]]):
        super().__init__(timeout=300)
        self.session_data = session_data
        self.feedback_data = feedback_data
        self.db_manager = DatabaseManager()
    
    @discord.ui.button(label="💾 Save to My Library", style=discord.ButtonStyle.success, emoji="💾")
    async def save_homeowner(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Save the homeowner to user's library"""
        try:
            # Save homeowner and feedback to database
            homeowner_data = self.session_data['homeowner_data']
            homeowner_data['saved_to_library'] = True
            homeowner_data['practice_feedback'] = self.feedback_data
            
            # This would save to actual database
            # await self.db_manager.save_homeowner_to_library(interaction.user.id, homeowner_data)
            
            # Return to main playground view
            main_view = interaction.client.persistent_playground_view
            
            embed = discord.Embed(
                title="💾 Homeowner Saved!",
                description=f"**{homeowner_data['name']}** has been saved to your homeowner library.",
                color=0x00ff88
            )
            
            embed.add_field(
                name="📚 Access Anytime",
                value="You can practice with this homeowner again by accessing your library in the playground.",
                inline=False
            )
            
            if self.feedback_data:
                embed.add_field(
                    name="📊 Your Feedback",
                    value="Your feedback has been recorded and will help improve the AI homeowner system.",
                    inline=False
                )
            
            embed.add_field(
                name="🎭 What's Next?",
                value="• **Create more homeowners** for varied practice\n• **Try different niches** to expand your skills\n• **Access your library** to practice with saved homeowners",
                inline=False
            )
            
            await interaction.response.edit_message(embed=embed, view=main_view)
            
        except Exception as e:
            logger.error(f"Error saving homeowner: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Error saving homeowner. Please try again.",
                color=0xe74c3c
            )
            await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="🗑️ Delete Homeowner", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def delete_homeowner(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Delete the homeowner personality"""
        try:
            homeowner_data = self.session_data['homeowner_data']
            
            # Return to main playground view
            main_view = interaction.client.persistent_playground_view
            
            embed = discord.Embed(
                title="🗑️ Homeowner Deleted",
                description=f"**{homeowner_data['name']}** has been removed and will not be saved.",
                color=0x95a5a6
            )
            
            embed.add_field(
                name="🔄 Create Another",
                value="You can create new homeowner personalities anytime in the playground.",
                inline=False
            )
            
            if self.feedback_data:
                embed.add_field(
                    name="📊 Feedback Saved",
                    value="Your feedback has been saved and will help improve future homeowner personalities, even though this one was deleted.",
                    inline=False
                )
            
            embed.add_field(
                name="🎭 What's Next?",
                value="• **Create new homeowners** with different personalities\n• **Try different niches** for varied practice\n• **Access your library** to practice with saved homeowners",
                inline=False
            )
            
            await interaction.response.edit_message(embed=embed, view=main_view)
            
        except Exception as e:
            logger.error(f"Error deleting homeowner: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Error deleting homeowner. Please try again.",
                color=0xe74c3c
            )
            await interaction.response.edit_message(embed=embed, view=self)

class PlaygroundHelpView(discord.ui.View):
    """Help view for playground system"""
    
    def __init__(self, page: int = 1):
        super().__init__(timeout=300)
        self.page = page
        self.max_pages = 2
        self.update_buttons()
    
    def get_help_embed(self) -> discord.Embed:
        """Get help embed for current page"""
        if self.page == 1:
            embed = discord.Embed(
                title="❓ Playground Help - Page 1/2",
                description="**Creating Custom Homeowner Personalities**",
                color=0x3498db
            )
            
            embed.add_field(
                name="🎯 What is the Playground?",
                value="The Playground is where you create custom homeowner personalities to practice door-to-door sales. Unlike the Practice Arena's pre-built personalities, here you design your own unique homeowners with specific traits and behaviors.",
                inline=False
            )
            
            embed.add_field(
                name="🚪 How to Create a Homeowner",
                value="1. **Click 'Create Homeowner Personality'**\n2. **Choose your niche** (Fiber, Solar, Landscaping)\n3. **Fill out the personality form**\n4. **AI enhances your creation** with realistic behaviors\n5. **Start practicing** immediately!",
                inline=False
            )
            
            embed.add_field(
                name="📋 Homeowner Details",
                value="• **Name & Demographics** - Age, location, family status\n• **Personality Traits** - Friendly, skeptical, busy, etc.\n• **Objections** - Common concerns they might have\n• **Interests** - What motivates them to buy",
                inline=False
            )
            
        else:  # page == 2
            embed = discord.Embed(
                title="❓ Playground Help - Page 2/2",
                description="**Managing Your Homeowner Library**",
                color=0x3498db
            )
            
            embed.add_field(
                name="📚 Your Library vs Community Library",
                value="• **🏠 My Library** - Your personal homeowner collection\n• **🌍 Community Library** - Homeowners shared by other users\n• **Save & Share** - Add great homeowners to the community\n• **Rate & Review** - Help improve the community collection",
                inline=False
            )
            
            embed.add_field(
                name="🎯 Practice Benefits",
                value="• **Realistic Scenarios** - Practice with diverse personalities\n• **Immediate Feedback** - Get tips after each session\n• **Skill Building** - Improve objection handling\n• **Confidence Boost** - Master different customer types",
                inline=False
            )
            
            embed.add_field(
                name="💡 Pro Tips",
                value="• Create homeowners based on real customers you've met\n• Mix personality types for varied practice\n• Use feedback to improve your homeowners\n• Share your best creations with the community",
                inline=False
            )
            
        return embed
    
    def update_buttons(self):
        """Update button states based on current page"""
        # Update previous button
        self.children[0].disabled = (self.page == 1)
        # Update next button
        self.children[1].disabled = (self.page == self.max_pages)
    
    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.secondary, emoji="◀️", disabled=True)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to previous help page"""
        try:
            if self.page > 1:
                self.page -= 1
                self.update_buttons()
                embed = self.get_help_embed()
                await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            logger.error(f"Error navigating to previous page: {e}")
    
    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary, emoji="▶️")
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to next help page"""
        try:
            if self.page < self.max_pages:
                self.page += 1
                self.update_buttons()
                embed = self.get_help_embed()
                await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            logger.error(f"Error navigating to next page: {e}")
    
    @discord.ui.button(label="🔙 Back to Playground", style=discord.ButtonStyle.primary, emoji="🔙", row=1)
    async def back_to_playground(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go back to main playground view"""
        try:
            main_view = interaction.client.persistent_playground_view
            
            embed = discord.Embed(
                title="🚪 Lord of the Doors Season 3 - Playground Library",
                description="Create and practice with custom homeowner personalities",
                color=0x9b59b6
            )
            
            embed.add_field(
                name="🎭 What's Available",
                value="• **Create Homeowners** - Design custom personalities\n• **Practice Door Knocking** - Realistic practice scenarios\n• **Build Your Library** - Save your best homeowners",
                inline=False
            )
            
            embed.add_field(
                name="🌟 Features",
                value="• **AI-Enhanced Personalities** - Realistic homeowner behavior\n• **Multi-Niche Support** - Fiber, Solar, Landscaping\n• **Feedback System** - Rate and improve homeowners",
                inline=False
            )
            
            await interaction.response.edit_message(embed=embed, view=main_view)
        except Exception as e:
            logger.error(f"Error returning to playground: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Error returning to playground. Please try again.",
                color=0xe74c3c
            )
        await interaction.response.edit_message(embed=embed, view=self) 

class PracticeSessionView(discord.ui.View):
    """View for managing an active practice session"""
    
    def __init__(self, homeowner_id: int, homeowner_data: dict):
        super().__init__(timeout=None)  # Make persistent
        self.homeowner_id = homeowner_id
        self.homeowner_data = homeowner_data
    
    @discord.ui.button(label="🚪 Knock on Door", style=discord.ButtonStyle.primary, emoji="🚪", custom_id="practice_knock_door")
    async def knock_door(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Start the door knocking conversation in the playground channel"""
        try:
            # Defer the interaction immediately
            await interaction.response.defer(ephemeral=True)
            
            # Get the playground manager
            playground_manager = interaction.client.get_cog('PlaygroundManager')
            if not playground_manager:
                await interaction.followup.send("❌ Playground system not available. Please try again later.", ephemeral=True)
                return
            
            # Start the practice session in the current channel
            await playground_manager.start_practice_session(
                interaction.user.id,
                self.homeowner_data,
                interaction.channel
            )
            
            # Send instructions to the user
            embed = discord.Embed(
                title=f"🚪 Door Knocking Practice Started!",
                description=f"You're now at the door of **{self.homeowner_data['name']}**. The conversation will happen right here in this channel!",
                color=0x00ff88
            )
            
            embed.add_field(
                name="🎯 How to Start",
                value="**Type your door knock greeting** right here in this channel. Example:\n\"Hi there! I'm with [Your Company] and I'm in the neighborhood talking to homeowners about solar services. Do you have a few minutes to chat?\"",
                inline=False
            )
            
            embed.add_field(
                name="💡 Pro Tips",
                value="• Be natural and conversational\n• Handle objections professionally\n• Build rapport and trust\n• Listen for buying signals",
                inline=False
            )
            
            embed.set_footer(text=f"{self.homeowner_data['niche'].title()} Practice Session • Type your message to start!")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error starting door knock: {e}")
            await interaction.followup.send("❌ Error starting conversation. Please try again.", ephemeral=True)
    
    @discord.ui.button(label="📋 Session Info", style=discord.ButtonStyle.secondary, emoji="📋", custom_id="practice_session_info")
    async def session_info(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show session information"""
        try:
            # Defer the interaction immediately
            await interaction.response.defer(ephemeral=True)
            
            embed = discord.Embed(
                title="📋 Practice Session Info",
                description=f"Currently practicing with **{self.homeowner_data['name']}**",
                color=0x95a5a6
            )
            
            embed.add_field(
                name="🏠 Homeowner Details",
                value=f"**Name:** {self.homeowner_data['name']}\n**Niche:** {self.homeowner_data['niche'].title()}\n**Personality:** {self.homeowner_data['personality_description'][:150]}...",
                inline=False
            )
            
            embed.add_field(
                name="🎯 Your Goal",
                value=f"Successfully sell {self.homeowner_data['niche']} services to this homeowner",
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error showing session info: {e}")
            await interaction.followup.send("❌ Error loading session info.", ephemeral=True)
    
    @discord.ui.button(label="🔚 End Session", style=discord.ButtonStyle.danger, emoji="🔚", custom_id="practice_end_session")
    async def end_session(self, interaction: discord.Interaction, button: discord.ui.Button):
        """End the practice session"""
        try:
            # Defer the interaction immediately
            await interaction.response.defer(ephemeral=True)
            
            # Get the playground manager and end the session
            playground_manager = interaction.client.get_cog('PlaygroundManager')
            if playground_manager and interaction.user.id in playground_manager.active_practice_sessions:
                del playground_manager.active_practice_sessions[interaction.user.id]
            
            embed = discord.Embed(
                title="🔚 Practice Session Ended",
                description="Your practice session has been ended successfully.",
                color=0x95a5a6
            )
            
            embed.add_field(
                name="🎯 Great Job!",
                value="Practice makes perfect. Keep practicing to improve your door-to-door sales skills!",
                inline=False
            )
            
            embed.add_field(
                name="🌟 What's Next?",
                value="• Create another homeowner personality\n• Try different sales approaches\n• Practice with various objection types",
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            await interaction.followup.send("❌ Error ending session.", ephemeral=True)


class ConversationView(discord.ui.View):
    """View for handling conversation during practice"""
    
    def __init__(self, homeowner_id: int, homeowner_data: dict):
        super().__init__(timeout=None)  # Make persistent
        self.homeowner_id = homeowner_id
        self.homeowner_data = homeowner_data
    
    @discord.ui.button(label="💬 Continue Conversation", style=discord.ButtonStyle.primary, emoji="💬", custom_id="conversation_continue")
    async def continue_conversation(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Continue the conversation (placeholder for now)"""
        try:
            # Defer the interaction immediately
            await interaction.response.defer(ephemeral=True)
            
            embed = discord.Embed(
                title="💬 Conversation System",
                description="This feature is being developed. For now, practice sessions will be enhanced with AI responses.",
                color=0x3498db
            )
            
            embed.add_field(
                name="🔄 Coming Soon",
                value="• Real-time AI conversation\n• Objection handling\n• Sales tracking\n• Performance feedback",
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in conversation: {e}")
            await interaction.followup.send("❌ Error in conversation system.", ephemeral=True)
    
    @discord.ui.button(label="🔙 Back to Session", style=discord.ButtonStyle.secondary, emoji="🔙", custom_id="conversation_back")
    async def back_to_session(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go back to the practice session"""
        try:
            # Defer the interaction immediately
            await interaction.response.defer(ephemeral=True)
            
            # Create practice session view
            practice_view = PracticeSessionView(self.homeowner_id, self.homeowner_data)
            
            embed = discord.Embed(
                title="🚪 Practice Session",
                description=f"Back to practicing with **{self.homeowner_data['name']}**",
                color=0x00ff88
            )
            
            embed.add_field(
                name="🎯 Your Goal",
                value=f"Try to sell {self.homeowner_data['niche']} services to this homeowner",
                inline=False
            )
            
            await interaction.followup.send(embed=embed, view=practice_view, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error going back to session: {e}")
            await interaction.followup.send("❌ Error returning to session.", ephemeral=True) 