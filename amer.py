import discord
from discord.ext import commands
import os
import random
import asyncio
from pws import discord_token

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="/", intents=intents)

# Load sounds from 'sounds' directory
sound_map = {}
for category in os.listdir('sounds'):
    category_path = os.path.join('sounds', category)
    if os.path.isdir(category_path):
        for sound_file in os.listdir(category_path):
            if sound_file.startswith('.') or not sound_file.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a')):
                continue
            key = f"{category}-{os.path.splitext(sound_file)[0]}"
            sound_map[key] = os.path.join(category_path, sound_file)

# Helper: Connect to user's voice channel
async def connect_to_user(ctx):
    if ctx.author.voice and ctx.author.voice.channel:
        channel = ctx.author.voice.channel
        if ctx.voice_client is None or not ctx.voice_client.is_connected():
            await channel.connect()
        return ctx.voice_client
    else:
        await ctx.send("You must be in a voice channel!")
        return None

# Play sound command
@bot.command()
async def play(ctx, *, sound: str):
    """Play a sound by name (format: category-soundname)"""
    vc = await connect_to_user(ctx)
    if not vc:
        return
    sound_file = sound_map.get(sound)
    if not sound_file:
        await ctx.send("Sound not found!")
        return
    if vc.is_playing():
        vc.stop()
    vc.play(discord.FFmpegPCMAudio(sound_file))
    await ctx.send(f"Playing: {sound}")

# List available sounds
@bot.command()
async def listsounds(ctx):
    """List all available sounds"""
    msg = "Available sounds:\n" + "\n".join(sound_map.keys())
    await ctx.send(msg)

# Disconnect from voice
@bot.command()
async def leave(ctx):
    """Disconnect the bot from voice"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Disconnected.")
    else:
        await ctx.send("I'm not in a voice channel.")

# Basic error handler
@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f"Error: {str(error)}")

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")

bot.run(discord_token) 