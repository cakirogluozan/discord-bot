import discord
from discord.ext import commands
from discord.ui import Button, View
import os
from pws import discord_token
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="/", intents=intents)

# Modify the sound map to include categories and create dynamic category styles
sound_map = {}
categories = {}

# First, collect all categories and sort them
for f in os.listdir('sounds'):
    if 'Zone' in f:
        continue
    name = os.path.splitext(f)[0]
    if '-' in name:
        category, sound_name = name.split('-', 1)  # Split only on first '-'
        if category not in categories:
            categories[category] = []
        categories[category].append(sound_name)
        sound_map[name] = os.path.join('sounds', f)

# Sort categories alphabetically
sorted_categories = sorted(categories.keys())

# Sort sounds within each category
for category in sorted_categories:
    categories[category].sort()

# Create a mapping of categories to styles
available_styles = [
    discord.ButtonStyle.primary,    # Blurple
    discord.ButtonStyle.success,    # Green
    discord.ButtonStyle.danger,     # Red
    discord.ButtonStyle.secondary,  # Grey
]

# Assign styles to categories
category_styles = {}
for i, category in enumerate(sorted_categories):
    category_styles[category] = available_styles[i % len(available_styles)]

# Store the persistent message ID and view
persistent_message_id = None
persistent_view = None

# Track if a sound is currently playing
is_playing = False

class SoundButton(Button):
    def __init__(self, label, sound_file, category):
        # Always use grey style for sound buttons
        super().__init__(label=f"🎵 {label}", style=discord.ButtonStyle.secondary)
        self.sound_file = sound_file

    async def callback(self, interaction: discord.Interaction):
        global is_playing
        
        if is_playing:
            await interaction.response.send_message("❌ A sound is already playing!", ephemeral=True)
            return

        user = interaction.user

        if user.voice and user.voice.channel:
            voice_channel = user.voice.channel

            try:
                # Check if bot is already connected to a voice channel
                if interaction.guild.voice_client:
                    # If connected to a different channel, move to the new one
                    if interaction.guild.voice_client.channel != voice_channel:
                        await interaction.guild.voice_client.move_to(voice_channel)
                else:
                    # If not connected, connect to the voice channel
                    await voice_channel.connect()

                # Get the voice client
                vc = interaction.guild.voice_client

                # Verify file exists and print path for debugging
                if not os.path.exists(self.sound_file):
                    await interaction.response.send_message(f"❌ Sound file not found: {self.sound_file}", ephemeral=True)
                    return

                print(f"Playing sound file: {self.sound_file}")  # Debug print

                # Disable all buttons
                for item in self.view.children:
                    item.disabled = True

                # Set playing flag
                is_playing = True
                
                # Play the sound with error handling
                try:
                    vc.play(discord.FFmpegPCMAudio(self.sound_file), 
                           after=lambda e: self.after_playing(e))
                    await interaction.response.send_message(f"🔊 Playing `{self.label}`!", ephemeral=True)
                except Exception as e:
                    print(f"Error playing sound: {str(e)}")  # Debug print
                    is_playing = False
                    for item in self.view.children:
                        item.disabled = False
                    await interaction.response.send_message(f"❌ Error playing sound: {str(e)}", ephemeral=True)

            except Exception as e:
                print(f"Connection error: {str(e)}")  # Debug print
                await interaction.response.send_message(f"❌ Error connecting to voice channel: {str(e)}", ephemeral=True)

        else:
            await interaction.response.send_message("❌ You must be in a voice channel!", ephemeral=True)

    def after_playing(self, error):
        global is_playing
        # Reset playing flag
        is_playing = False
        
        # Re-enable all buttons
        if persistent_view:
            for item in persistent_view.children:
                item.disabled = False

@bot.command()
async def soundboard(ctx):
    global persistent_message_id, persistent_view
    
    # Delete previous bot messages in the channel
    async for message in ctx.channel.history(limit=100):  # Limit to last 100 messages
        if message.author == bot.user:  # Check if message is from our bot
            try:
                await message.delete()
            except discord.errors.NotFound:
                pass  # Ignore if message was already deleted
    
    # Create a new view
    view = View(timeout=None)
    
    # Initialize variables for pagination
    buttons_per_page = 15
    current_page = 0
    current_category = sorted_categories[0]  # Start with first sorted category
    
    # Function to create category buttons
    def create_category_buttons():
        nonlocal current_category
        category_view = View(timeout=None)
        
        # Get sounds for current category
        category_sounds = categories[current_category]
        total_pages = (len(category_sounds) + buttons_per_page - 1) // buttons_per_page
        
        # First row: Category navigation (Red)
        if len(sorted_categories) > 1:
            prev_cat = Button(
                label="◀️ Prev Category", 
                style=discord.ButtonStyle.danger
            )
            next_cat = Button(
                label="Next Category ▶️", 
                style=discord.ButtonStyle.danger
            )
            
            async def prev_category_callback(interaction):
                nonlocal current_category, current_page
                current_idx = sorted_categories.index(current_category)
                current_category = sorted_categories[(current_idx - 1) % len(sorted_categories)]
                current_page = 0
                await update_view(interaction)
                
            async def next_category_callback(interaction):
                nonlocal current_category, current_page
                current_idx = sorted_categories.index(current_category)
                current_category = sorted_categories[(current_idx + 1) % len(sorted_categories)]
                current_page = 0
                await update_view(interaction)
            
            prev_cat.callback = prev_category_callback
            next_cat.callback = next_category_callback
            
            # Add category navigation buttons with an empty button in between
            category_view.add_item(prev_cat)
            empty_button = Button(label="\u200b", style=discord.ButtonStyle.secondary, disabled=True)
            category_view.add_item(empty_button)
            category_view.add_item(next_cat)
        
        # Middle rows: Sound buttons
        start_idx = current_page * buttons_per_page
        end_idx = min(start_idx + buttons_per_page, len(category_sounds))
        
        for i in range(start_idx, end_idx):
            sound_name = category_sounds[i]
            full_name = f"{current_category}-{sound_name}"
            button = SoundButton(
                label=sound_name,
                sound_file=sound_map[full_name],
                category=current_category
            )
            category_view.add_item(button)
        
        # Add empty buttons to complete the last sound row
        remaining_in_row = 3 - (len(category_view.children) % 3)
        if remaining_in_row < 3:
            for _ in range(remaining_in_row):
                empty_button = Button(label="\u200b", style=discord.ButtonStyle.secondary, disabled=True)
                category_view.add_item(empty_button)
        
        # Last row: Page navigation (Green)
        if total_pages > 1:
            prev_page = Button(
                label="◀️ Prev Page", 
                style=discord.ButtonStyle.success
            )
            next_page = Button(
                label="Next Page ▶️", 
                style=discord.ButtonStyle.success
            )
            
            async def prev_page_callback(interaction):
                nonlocal current_page
                current_page = max(0, current_page - 1)
                await update_view(interaction)
                
            async def next_page_callback(interaction):
                nonlocal current_page
                current_page = min(total_pages - 1, current_page + 1)
                await update_view(interaction)
            
            prev_page.callback = prev_page_callback
            next_page.callback = next_page_callback
            
            prev_page.disabled = (current_page == 0)
            next_page.disabled = (current_page == total_pages - 1)
            
            # Add page navigation buttons with an empty button in between
            category_view.add_item(prev_page)
            empty_button = Button(label="\u200b", style=discord.ButtonStyle.secondary, disabled=True)
            category_view.add_item(empty_button)
            category_view.add_item(next_page)
        
        return category_view, total_pages
    
    # Create initial view
    view, total_pages = create_category_buttons()
    
    # Store view globally
    persistent_view = view
    
    # Send the message
    page_info = f" (Page {current_page + 1}/{total_pages})" if total_pages > 1 else ""
    message = await ctx.send(
        f"🎵 **Soundboard Controls**\n📂 Category: ```fix\n{current_category}```{page_info}",
        view=view
    )
    persistent_message_id = message.id
    
    async def update_view(interaction):
        new_view, total_pages = create_category_buttons()
        page_info = f" (Page {current_page + 1}/{total_pages})" if total_pages > 1 else ""
        
        # Create emphasized category display with emojis and formatting
        category_display = f"🎵 **Soundboard Controls**\n📂 Category: ```fix\n{current_category}```{page_info}"
        
        await interaction.response.edit_message(
            content=category_display,
            view=new_view
        )

@bot.command()
async def removesoundboard(ctx):
    global persistent_message_id, persistent_view
    if persistent_message_id:
        try:
            message = await ctx.channel.fetch_message(persistent_message_id)
            await message.delete()
            persistent_message_id = None
            persistent_view = None
            await ctx.send("✅ Soundboard removed!", ephemeral=True)
        except discord.NotFound:
            await ctx.send("❌ Could not find the soundboard message.", ephemeral=True)
    else:
        await ctx.send("❌ No soundboard is currently active.", ephemeral=True)

@bot.command()
async def disconnect(ctx):
    if ctx.guild.voice_client:
        await ctx.guild.voice_client.disconnect()
        await ctx.send("✅ Disconnected from voice channel!", ephemeral=True)
    else:
        await ctx.send("❌ I'm not connected to any voice channel!", ephemeral=True)

@bot.event
async def on_ready():
    print(f"🎉 Logged in as {bot.user}")

bot.run(discord_token)
