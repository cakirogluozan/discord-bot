#!/usr/bin/env python3
"""
Network connectivity test for Discord voice
"""

import socket
import subprocess
import asyncio
import discord
from discord.ext import commands
from pws import discord_token

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
async def networktest(ctx):
    """Test network connectivity to Discord services"""
    await ctx.send("🌐 Starting network connectivity tests...", ephemeral=True)
    
    # Test 1: Discord API
    try:
        socket.create_connection(("discord.com", 443), timeout=10)
        await ctx.send("✅ Discord API (discord.com:443): OK", ephemeral=True)
    except Exception as e:
        await ctx.send(f"❌ Discord API: FAILED - {str(e)}", ephemeral=True)
    
    # Test 2: Discord Gateway
    try:
        socket.create_connection(("gateway.discord.gg", 443), timeout=10)
        await ctx.send("✅ Discord Gateway (gateway.discord.gg:443): OK", ephemeral=True)
    except Exception as e:
        await ctx.send(f"❌ Discord Gateway: FAILED - {str(e)}", ephemeral=True)
    
    # Test 3: Discord Voice Servers (common endpoints)
    voice_servers = [
        "c-fra16-e2ce8198.discord.media",
        "c-fra16-e2ce8199.discord.media", 
        "c-fra16-e2ce8200.discord.media",
        "c-fra16-e2ce8201.discord.media"
    ]
    
    for server in voice_servers:
        try:
            socket.create_connection((server, 443), timeout=10)
            await ctx.send(f"✅ Voice server {server}: OK", ephemeral=True)
        except Exception as e:
            await ctx.send(f"❌ Voice server {server}: FAILED - {str(e)}", ephemeral=True)
    
    # Test 4: UDP ports (for voice)
    udp_ports = [443, 80, 3478, 3479, 5349, 5350]
    for port in udp_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)
            sock.connect(("8.8.8.8", port))
            sock.close()
            await ctx.send(f"✅ UDP port {port}: OK", ephemeral=True)
        except Exception as e:
            await ctx.send(f"❌ UDP port {port}: FAILED - {str(e)}", ephemeral=True)
    
    await ctx.send("🎯 Network tests complete!", ephemeral=True)

@bot.command()
async def pingtest(ctx):
    """Test ping to Discord servers"""
    await ctx.send("🏓 Testing ping to Discord servers...", ephemeral=True)
    
    servers = ["discord.com", "gateway.discord.gg", "c-fra16-e2ce8198.discord.media"]
    
    for server in servers:
        try:
            result = subprocess.run(['ping', '-c', '3', server], 
                                  capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                # Extract average ping
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'avg' in line:
                        await ctx.send(f"✅ {server}: {line.strip()}", ephemeral=True)
                        break
            else:
                await ctx.send(f"❌ {server}: Ping failed", ephemeral=True)
        except Exception as e:
            await ctx.send(f"❌ {server}: Error - {str(e)}", ephemeral=True)

@bot.command()
async def traceroute(ctx):
    """Test traceroute to Discord"""
    await ctx.send("🛤️ Testing traceroute to Discord...", ephemeral=True)
    
    try:
        result = subprocess.run(['traceroute', '-m', '15', 'discord.com'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            # Send first few lines
            lines = result.stdout.split('\n')[:10]
            await ctx.send(f"📊 Traceroute to discord.com:\n```\n{chr(10).join(lines)}\n```", ephemeral=True)
        else:
            await ctx.send("❌ Traceroute failed", ephemeral=True)
    except Exception as e:
        await ctx.send(f"❌ Traceroute error: {str(e)}", ephemeral=True)

@bot.event
async def on_ready():
    print(f"🎉 Network test bot logged in as {bot.user}")

if __name__ == "__main__":
    bot.run(discord_token) 