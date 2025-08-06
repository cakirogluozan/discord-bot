#!/usr/bin/env python3
"""
Simple voice connection test script
Run this to test basic voice connectivity
"""

import discord
from discord.ext import commands
import asyncio
import os
from pws import discord_token

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
async def testvoice(ctx):
    """Test basic voice connection"""
    if not ctx.author.voice:
        await ctx.send("❌ You must be in a voice channel!")
        return
    
    try:
        # Try to connect
        voice_channel = ctx.author.voice.channel
        await voice_channel.connect(timeout=20.0)
        await ctx.send("✅ Successfully connected to voice channel!")
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Disconnect
        await ctx.guild.voice_client.disconnect()
        await ctx.send("✅ Successfully disconnected from voice channel!")
        
    except discord.ConnectionClosed as e:
        await ctx.send(f"❌ Connection failed with code {e.code}: {str(e)}")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.event
async def on_ready():
    print(f"🎉 Test bot logged in as {bot.user}")

if __name__ == "__main__":
    bot.run(discord_token) 