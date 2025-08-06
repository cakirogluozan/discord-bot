# Discord Voice Connection Troubleshooting Guide

## Error Code 4006 - Session Timeout/Invalid

This error typically occurs when:
1. Network connectivity issues
2. Discord server problems
3. Bot permissions issues
4. Voice client state conflicts

## Solutions

### 1. Check Bot Permissions
Make sure your bot has these permissions:
- Connect to voice channels
- Speak in voice channels
- Use voice activity

### 2. Use the New Commands
The updated bot now includes these helpful commands:

- `/voicefix` - Force disconnect and clear stuck voice states + clear issue tracking
- `/voicestatus` - Check current voice connection status
- `/disconnect` - Disconnect from voice channel
- `/clearvoiceissues` - Clear all voice connection issue tracking

### 3. Run Comprehensive Diagnostics
Use the diagnosis script to identify the root cause:
```bash
python diagnose_voice.py
```
Then use these commands in Discord:
- `!diagnose` - Run comprehensive voice connection diagnostics
- `!testconnection` - Test voice connection with detailed logging

### 4. Common Fixes

#### If you're getting 4006 errors:
1. Try `/voicefix` to force disconnect and clear issue tracking
2. Wait 60 seconds (the bot now enforces a 1-minute cooldown)
3. Try connecting again
4. If it persists, use `!diagnose` to check connectivity

#### If the bot seems stuck:
1. Use `/disconnect` 
2. Wait a moment
3. Try playing a sound again

#### If nothing works:
1. Restart the bot
2. Check your internet connection
3. Try a different voice channel
4. Check Discord's status page for service issues

## Technical Details

The updated code includes:
- **Aggressive retry logic** with up to 5 attempts for 4006 errors
- **Connection issue tracking** to prevent spam attempts
- **Force disconnect** before reconnection attempts
- **Longer timeouts** (30 seconds) for voice connections
- **Better error messages** for specific Discord error codes
- **Connection state management** and automatic cleanup

## Debug Information

The bot now provides more detailed error messages:
- **4006**: Discord server issue - please try again in a few minutes
- **4001**: Unauthorized - check permissions
- **Other codes**: Specific error information

## Network Issues

If you're on a restricted network:
- Check if Discord voice ports are blocked
- Try using a VPN
- Contact your network administrator

## Advanced Troubleshooting

### Using the Diagnosis Script
1. Run `python diagnose_voice.py`
2. Use `!diagnose` in Discord to check:
   - Discord API connectivity
   - Voice server connectivity  
   - FFmpeg installation
   - Bot permissions
   - Voice channel access

### Connection Issue Tracking
The bot now tracks connection issues per guild and enforces a 1-minute cooldown between attempts. Use `/clearvoiceissues` to reset this.

### Force Disconnect Strategy
The bot now forces a complete disconnect before attempting new connections, which helps resolve stuck voice states.

## Still Having Issues?

1. **Run diagnostics**: Use `!diagnose` to check all connectivity
2. **Test basic connection**: Use `!testconnection` to isolate the problem
3. **Check logs**: Look for detailed error messages in the console
4. **Restart the bot**: Sometimes a fresh start helps
5. **Check Discord status**: Visit status.discord.com for service issues
6. **Try different voice channel**: Some channels may have issues
7. **Wait and retry**: 4006 errors are often temporary Discord server issues 