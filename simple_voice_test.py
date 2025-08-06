#!/usr/bin/env python3
"""
Minimal voice connection test
This will help isolate if the issue is with our bot code or Discord's servers
"""

import discord
from discord.ext import commands
import asyncio
import time
from pws import discord_token

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
async def simpletest(ctx):
    """Minimal voice connection test"""
    if not ctx.author.voice:
        await ctx.send("❌ You must be in a voice channel!")
        return
    
    voice_channel = ctx.author.voice.channel
    
    try:
        await ctx.send("🔄 Attempting to connect...", ephemeral=True)
        
        # Simple connection attempt
        await voice_channel.connect()
        
        await ctx.send("✅ Connected successfully!", ephemeral=True)
        
        # Wait a moment
        await asyncio.sleep(3)
        
        # Disconnect
        await ctx.guild.voice_client.disconnect()
        await ctx.send("✅ Disconnected successfully!", ephemeral=True)
        
    except Exception as e:
        await ctx.send(f"❌ Connection failed: {str(e)}", ephemeral=True)

@bot.command()
async def stayconnected(ctx):
    """Stay connected for a longer period to test stability"""
    if not ctx.author.voice:
        await ctx.send("❌ You must be in a voice channel!")
        return
    
    voice_channel = ctx.author.voice.channel
    
    try:
        await ctx.send("🔄 Connecting and staying for 30 seconds...", ephemeral=True)
        
        # Connect
        await voice_channel.connect()
        
        # Stay connected for 30 seconds
        for i in range(30):
            if not ctx.guild.voice_client or not ctx.guild.voice_client.is_connected():
                await ctx.send(f"❌ Lost connection after {i} seconds!", ephemeral=True)
                return
            await asyncio.sleep(1)
        
        # Disconnect
        await ctx.guild.voice_client.disconnect()
        await ctx.send("✅ Successfully stayed connected for 30 seconds!", ephemeral=True)
        
    except Exception as e:
        await ctx.send(f"❌ Connection failed: {str(e)}", ephemeral=True)

@bot.event
async def on_voice_state_update(member, before, after):
    """Log voice state changes"""
    if member.id == bot.user.id:
        if before.channel and not after.channel:
            print(f"Bot disconnected from {before.channel.name}")
        elif not before.channel and after.channel:
            print(f"Bot connected to {after.channel.name}")

@bot.event
async def on_ready():
    print(f"🎉 Simple test bot logged in as {bot.user}")

if __name__ == "__main__":
    bot.run(discord_token) 