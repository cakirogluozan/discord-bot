#!/usr/bin/env python3
"""
Comprehensive voice connection diagnosis script
This will help identify the root cause of 4006 errors
"""

import discord
from discord.ext import commands
import asyncio
import os
import time
import socket
import subprocess
from pws import discord_token

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
async def diagnose(ctx):
    """Run comprehensive voice connection diagnostics"""
    await ctx.send("🔍 Starting voice connection diagnostics...", ephemeral=True)
    
    # Check 1: Basic connectivity
    await ctx.send("📡 Checking basic connectivity...", ephemeral=True)
    try:
        # Test Discord API connectivity
        socket.create_connection(("discord.com", 443), timeout=10)
        await ctx.send("✅ Discord API connectivity: OK", ephemeral=True)
    except Exception as e:
        await ctx.send(f"❌ Discord API connectivity: FAILED - {str(e)}", ephemeral=True)
        return
    
    # Check 2: Voice server connectivity
    await ctx.send("🎵 Testing voice server connectivity...", ephemeral=True)
    try:
        # Test Discord voice servers
        socket.create_connection(("c-fra16-e2ce8198.discord.media", 443), timeout=10)
        await ctx.send("✅ Voice server connectivity: OK", ephemeral=True)
    except Exception as e:
        await ctx.send(f"⚠️ Voice server connectivity: ISSUE - {str(e)}", ephemeral=True)
    
    # Check 3: FFmpeg
    await ctx.send("🎬 Checking FFmpeg installation...", ephemeral=True)
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            await ctx.send("✅ FFmpeg installation: OK", ephemeral=True)
        else:
            await ctx.send("❌ FFmpeg installation: FAILED", ephemeral=True)
    except Exception as e:
        await ctx.send(f"❌ FFmpeg installation: FAILED - {str(e)}", ephemeral=True)
    
    # Check 4: Bot permissions
    await ctx.send("🔐 Checking bot permissions...", ephemeral=True)
    if ctx.guild.me.guild_permissions.connect:
        await ctx.send("✅ Connect permission: OK", ephemeral=True)
    else:
        await ctx.send("❌ Connect permission: MISSING", ephemeral=True)
    
    if ctx.guild.me.guild_permissions.speak:
        await ctx.send("✅ Speak permission: OK", ephemeral=True)
    else:
        await ctx.send("❌ Speak permission: MISSING", ephemeral=True)
    
    # Check 5: Voice channel access
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if channel.permissions_for(ctx.guild.me).connect:
            await ctx.send("✅ Voice channel access: OK", ephemeral=True)
        else:
            await ctx.send("❌ Voice channel access: DENIED", ephemeral=True)
    else:
        await ctx.send("⚠️ Voice channel access: Cannot test (user not in voice)", ephemeral=True)
    
    await ctx.send("🎯 Diagnostics complete! Check the results above.", ephemeral=True)

@bot.command()
async def testconnection(ctx):
    """Test voice connection with detailed logging"""
    if not ctx.author.voice:
        await ctx.send("❌ You must be in a voice channel!", ephemeral=True)
        return
    
    await ctx.send("🔗 Testing voice connection with detailed logging...", ephemeral=True)
    
    voice_channel = ctx.author.voice.channel
    
    for attempt in range(3):
        try:
            await ctx.send(f"🔄 Connection attempt {attempt + 1}/3...", ephemeral=True)
            
            # Force disconnect if already connected
            if ctx.guild.voice_client:
                await ctx.guild.voice_client.disconnect()
                await asyncio.sleep(2)
            
            # Try to connect
            start_time = time.time()
            await voice_channel.connect(timeout=30.0)
            connect_time = time.time() - start_time
            
            await ctx.send(f"✅ Connection successful! (took {connect_time:.2f}s)", ephemeral=True)
            
            # Test if we can actually use the connection
            if ctx.guild.voice_client.is_connected():
                await ctx.send("✅ Voice client is properly connected!", ephemeral=True)
            else:
                await ctx.send("⚠️ Voice client connected but not fully established", ephemeral=True)
            
            # Disconnect
            await ctx.guild.voice_client.disconnect()
            await ctx.send("✅ Test completed successfully!", ephemeral=True)
            return
            
        except discord.ConnectionClosed as e:
            await ctx.send(f"❌ Connection failed with code {e.code}: {str(e)}", ephemeral=True)
            if e.code == 4006:
                await ctx.send("💡 This is a Discord server issue (4006). Try again later.", ephemeral=True)
        except Exception as e:
            await ctx.send(f"❌ Connection failed: {str(e)}", ephemeral=True)
        
        if attempt < 2:
            await asyncio.sleep(5)
    
    await ctx.send("❌ All connection attempts failed!", ephemeral=True)

@bot.event
async def on_ready():
    print(f"🎉 Diagnosis bot logged in as {bot.user}")

if __name__ == "__main__":
    bot.run(discord_token) 