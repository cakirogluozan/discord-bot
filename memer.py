import discord
from discord.ext import commands
from discord.ui import Button, View
import os
from pws import discord_token
import asyncio
import time
import logging
import random

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="/", intents=intents)

# --- Updated Sound Data Loading ---
sound_map = {}
categories = {}

# Iterate through items in the 'sounds' directory
for item_name in os.listdir('sounds'):
    item_path = os.path.join('sounds', item_name)
    
    # Check if the item is a directory (this will be our category)
    if os.path.isdir(item_path):
        category_name = item_name  # The directory name is the category
        
        if category_name not in categories:
            categories[category_name] = []
            
        # List files within this category directory
        for sound_filename in os.listdir(item_path):
            # You might want to skip system files like 'Zone.Identifier' if they appear
            if 'Zone' in sound_filename or sound_filename.startswith('.'):
                continue
            
            sound_name_base, sound_ext = os.path.splitext(sound_filename)
            
            # Ensure it's a common audio file type (optional, but good practice)
            if sound_ext.lower() not in ['.mp3', '.wav', '.ogg', '.m4a']: # Add more if needed
                continue

            categories[category_name].append(sound_name_base)
            
            # The key for sound_map should still uniquely identify the sound.
            # Using "category-sound_name_base" format maintains consistency 
            # with how SoundButton and SoundboardView expect to look up sounds.
            full_name_key = f"{category_name}-{sound_name_base}"
            sound_map[full_name_key] = os.path.join(item_path, sound_filename)
            
# Sort categories alphabetically
sorted_categories = sorted(categories.keys())

# Sort sounds within each category
for category in sorted_categories:
    categories[category].sort()
# --- End of Updated Sound Data Loading ---

# Create a mapping of categories to styles
available_styles = [
    discord.ButtonStyle.primary,    # Blurple
    discord.ButtonStyle.success,    # Green
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

# Track voice client connection attempts
connection_attempts = {}

# Connection state tracking
voice_connection_issues = {}

# Track successful voice servers
working_voice_servers = set()

async def force_disconnect_and_wait(guild, wait_time=5):
    """Force disconnect and wait for cleanup"""
    if guild.voice_client:
        try:
            await guild.voice_client.disconnect()
            print(f"Force disconnected from voice channel")
        except Exception as e:
            print(f"Error during force disconnect: {e}")
    
    await asyncio.sleep(wait_time)

async def try_alternative_connection(guild, voice_channel):
    """Try alternative connection methods when standard connection fails"""
    
    # Method 1: Try with different timeout
    try:
        print("Trying alternative connection method 1: Extended timeout")
        await voice_channel.connect(timeout=60.0)
        await asyncio.sleep(2)
        if guild.voice_client and guild.voice_client.is_connected():
            return guild.voice_client
    except Exception as e:
        print(f"Alternative method 1 failed: {e}")
    
    # Method 2: Try with different connection parameters
    try:
        print("Trying alternative connection method 2: Different parameters")
        # Force disconnect first
        if guild.voice_client:
            await guild.voice_client.disconnect()
            await asyncio.sleep(3)
        
        # Try connecting with minimal parameters
        await voice_channel.connect()
        await asyncio.sleep(2)
        if guild.voice_client and guild.voice_client.is_connected():
            return guild.voice_client
    except Exception as e:
        print(f"Alternative method 2 failed: {e}")
    
    return None

async def connect_to_voice_channel(guild, voice_channel, max_retries=3):
    """Improved voice connection with aggressive retry logic and 4006 handling"""
    
    # Check if we've had recent issues with this guild
    guild_id = str(guild.id)
    if guild_id in voice_connection_issues:
        last_issue_time = voice_connection_issues[guild_id]
        if time.time() - last_issue_time < 120:  # Wait 2 minutes between attempts
            raise Exception("Recent voice connection issues detected. Please wait 2 minutes before trying again.")
    
    for attempt in range(max_retries):
        try:
            print(f"Voice connection attempt {attempt + 1}/{max_retries}")
            
            # Force disconnect if already connected
            if guild.voice_client:
                await force_disconnect_and_wait(guild, 3)
            
            # Try to connect with a longer timeout
            await voice_channel.connect(timeout=45.0)
            
            # Wait a moment to ensure connection is stable
            await asyncio.sleep(2)
            
            # Verify connection is working
            if guild.voice_client and guild.voice_client.is_connected():
                print("Voice connection successful!")
                return guild.voice_client
                
        except discord.ConnectionClosed as e:
            print(f"Connection attempt {attempt + 1} failed with code {e.code}")
            
            if e.code == 4006:  # Session timeout/invalid
                print(f"4006 error detected - trying alternative methods")
                
                # Try alternative connection methods
                alt_client = await try_alternative_connection(guild, voice_channel)
                if alt_client:
                    print("Alternative connection method succeeded!")
                    return alt_client
                
                # For 4006, we need to be more aggressive
                await force_disconnect_and_wait(guild, 8)
                
                if attempt < max_retries - 1:
                    wait_time = min(15, 3 ** attempt)  # Cap at 15 seconds
                    print(f"Waiting {wait_time} seconds before retry...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Mark this guild as having issues
                    voice_connection_issues[guild_id] = time.time()
                    raise Exception("Discord voice servers are experiencing issues (4006 error). Please try again in 2 minutes.")
            
            raise e
            
        except discord.ClientException as e:
            if "Already connected to a voice channel" in str(e):
                if guild.voice_client and guild.voice_client.is_connected():
                    return guild.voice_client
            raise e
            
        except Exception as e:
            print(f"Voice connection attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(3)
                continue
            raise e
    
    # Mark this guild as having issues
    voice_connection_issues[guild_id] = time.time()
    raise Exception(f"Failed to connect to voice channel after {max_retries} attempts")

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
                # Use improved connection function
                vc = await connect_to_voice_channel(interaction.guild, voice_channel)

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

            except discord.ConnectionClosed as e:
                error_msg = "❌ Voice connection failed"
                if e.code == 4006:
                    error_msg += " (Discord server issue - please try again in 2 minutes)"
                elif e.code == 4001:
                    error_msg += " (Unauthorized - check bot permissions)"
                else:
                    error_msg += f" (Error code: {e.code})"
                
                print(f"Voice connection error: {str(e)}")  # Debug print
                await interaction.response.send_message(error_msg, ephemeral=True)
                
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

@bot.command(name='memer')
async def memer(ctx):
    global persistent_message_id, persistent_view
    
    # Delete the command message
    try:
        await ctx.message.delete()
    except discord.errors.NotFound:
        pass  # Ignore if the message was already deleted

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

@bot.command()
async def voicefix(ctx):
    """Force disconnect and clear any stuck voice states"""
    global voice_connection_issues
    
    # Clear connection issue tracking for this guild
    guild_id = str(ctx.guild.id)
    if guild_id in voice_connection_issues:
        del voice_connection_issues[guild_id]
        print(f"Cleared connection issue tracking for guild {guild_id}")
    
    if ctx.guild.voice_client:
        try:
            await ctx.guild.voice_client.disconnect()
            await ctx.send("✅ Force disconnected from voice channel and cleared issue tracking!", ephemeral=True)
        except Exception as e:
            await ctx.send(f"❌ Error during disconnect: {str(e)}", ephemeral=True)
    else:
        await ctx.send("✅ No voice client to disconnect! Issue tracking cleared.", ephemeral=True)

@bot.command()
async def clearvoiceissues(ctx):
    """Clear all voice connection issue tracking"""
    global voice_connection_issues
    voice_connection_issues.clear()
    await ctx.send("✅ Cleared all voice connection issue tracking!", ephemeral=True)

@bot.command()
async def voicenetwork(ctx):
    """Test network connectivity to Discord voice servers"""
    import socket
    
    await ctx.send("🌐 Testing network connectivity to Discord voice servers...", ephemeral=True)
    
    # Test Discord API
    try:
        socket.create_connection(("discord.com", 443), timeout=10)
        await ctx.send("✅ Discord API: OK", ephemeral=True)
    except Exception as e:
        await ctx.send(f"❌ Discord API: FAILED - {str(e)}", ephemeral=True)
        return
    
    # Test Discord Gateway
    try:
        socket.create_connection(("gateway.discord.gg", 443), timeout=10)
        await ctx.send("✅ Discord Gateway: OK", ephemeral=True)
    except Exception as e:
        await ctx.send(f"❌ Discord Gateway: FAILED - {str(e)}", ephemeral=True)
    
    # Test specific voice server from logs
    try:
        socket.create_connection(("c-fra16-e2ce8198.discord.media", 443), timeout=10)
        await ctx.send("✅ Voice server c-fra16-e2ce8198.discord.media: OK", ephemeral=True)
    except Exception as e:
        await ctx.send(f"❌ Voice server c-fra16-e2ce8198.discord.media: FAILED - {str(e)}", ephemeral=True)
    
    # Test alternative voice servers
    alternative_servers = [
        "c-fra16-e2ce8199.discord.media",
        "c-fra16-e2ce8200.discord.media",
        "c-fra16-e2ce8201.discord.media"
    ]
    
    for server in alternative_servers:
        try:
            socket.create_connection((server, 443), timeout=10)
            await ctx.send(f"✅ Voice server {server}: OK", ephemeral=True)
        except Exception as e:
            await ctx.send(f"❌ Voice server {server}: FAILED - {str(e)}", ephemeral=True)
    
    await ctx.send("🎯 Network tests complete!", ephemeral=True)

@bot.command()
async def voiceinfo(ctx):
    """Show detailed voice connection information"""
    vc = ctx.guild.voice_client
    if vc:
        status = "Connected" if vc.is_connected() else "Disconnected"
        channel_name = vc.channel.name if vc.channel else "None"
        endpoint = vc.endpoint if hasattr(vc, 'endpoint') else "Unknown"
        
        info = f"🎵 **Voice Client Info:**\n"
        info += f"📡 Status: {status}\n"
        info += f"📺 Channel: {channel_name}\n"
        info += f"🔊 Playing: {vc.is_playing()}\n"
        info += f"🌐 Endpoint: {endpoint}\n"
        info += f"🔗 Latency: {vc.latency:.3f}s" if hasattr(vc, 'latency') else "🔗 Latency: Unknown"
        
        await ctx.send(info, ephemeral=True)
    else:
        await ctx.send("❌ Not connected to any voice channel", ephemeral=True)

@bot.command()
async def voicestatus(ctx):
    """Check the current voice connection status"""
    vc = ctx.guild.voice_client
    if vc:
        status = "Connected" if vc.is_connected() else "Disconnected"
        channel_name = vc.channel.name if vc.channel else "None"
        await ctx.send(f"🎵 **Voice Status:**\n📡 Status: {status}\n📺 Channel: {channel_name}\n🔊 Playing: {vc.is_playing()}", ephemeral=True)
    else:
        await ctx.send("❌ Not connected to any voice channel", ephemeral=True)

@bot.event
async def on_ready():
    print(f"🎉 Logged in as {bot.user}")

@bot.event
async def on_voice_state_update(member, before, after):
    """Handle voice state changes to clean up when users leave"""
    # If the bot is disconnected from voice, reset the playing flag
    if member.id == bot.user.id and before.channel and not after.channel:
        global is_playing
        is_playing = False
        print("Bot disconnected from voice channel, resetting playing flag")

@bot.event
async def on_command_error(ctx, error):
    """Global error handler"""
    if isinstance(error, commands.CommandNotFound):
        return  # Ignore command not found errors
    
    print(f"Command error in {ctx.command}: {error}")
    await ctx.send(f"❌ An error occurred: {str(error)}", ephemeral=True)

bot.run(discord_token)