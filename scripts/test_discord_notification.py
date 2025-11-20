#!/usr/bin/env python3
"""
Test Discord notification to verify the setup
"""

import os
import sys
import asyncio
import discord
from discord import Embed
from datetime import datetime
from pathlib import Path

# Add parent directory to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
NOTIFICATION_USER_ID = 690415992362500106

async def send_test_notification():
    """Send a test Discord notification"""
    
    if not DISCORD_TOKEN:
        print("❌ ERROR: DISCORD_BOT_TOKEN not found in environment")
        print("Please set it in your .env file")
        return False
    
    try:
        print(f"🚀 Connecting to Discord...")
        intents = discord.Intents.default()
        client = discord.Client(intents=intents)
        
        @client.event
        async def on_ready():
            try:
                print(f"✅ Connected as {client.user}")
                print(f"📊 Bot is in {len(client.guilds)} server(s)")
                
                # List all servers
                for guild in client.guilds:
                    print(f"   • {guild.name} (ID: {guild.id})")
                
                print(f"\n📬 Attempting to send test message to user {NOTIFICATION_USER_ID}...")
                
                # Try to get user from cache first
                user = client.get_user(NOTIFICATION_USER_ID)
                
                # If not in cache, try to fetch
                if user is None:
                    print(f"   User not in cache, fetching...")
                    try:
                        user = await client.fetch_user(NOTIFICATION_USER_ID)
                    except discord.errors.NotFound:
                        # Try searching in guilds
                        print(f"   User not found directly, searching in servers...")
                        for guild in client.guilds:
                            member = guild.get_member(NOTIFICATION_USER_ID)
                            if member:
                                user = member
                                print(f"   Found user in {guild.name}!")
                                break
                
                if user is None:
                    print(f"❌ ERROR: User {NOTIFICATION_USER_ID} not found")
                    print("   This could mean:")
                    print("   1. The user ID is incorrect")
                    print("   2. The bot doesn't share a server with this user")
                    print("   3. The user has blocked the bot")
                    await client.close()
                    return
                
                embed = Embed(
                    title="🎉 Auto-Commit System Test",
                    description="This is a test notification from your auto-commit bot!",
                    color=0x00FF00,
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name="✅ System Status",
                    value="All systems operational",
                    inline=False
                )
                
                embed.add_field(
                    name="📊 Configuration",
                    value=f"• Target User: {NOTIFICATION_USER_ID}\n• Bot Connected: ✓\n• Notifications: Enabled",
                    inline=False
                )
                
                embed.add_field(
                    name="🔔 What to Expect",
                    value="You'll receive notifications like this for each commit:\n"
                          "• Task ID and description\n"
                          "• Day progress (X/15)\n"
                          "• Feature being implemented\n"
                          "• File modified\n"
                          "• Commit hash",
                    inline=False
                )
                
                embed.add_field(
                    name="🚀 Next Steps",
                    value="Run `python3 scripts/daily_commit_bot.py` to start the automated commits!",
                    inline=False
                )
                
                embed.set_footer(text="Auto-Commit Bot • Test Notification")
                
                await user.send(embed=embed)
                print(f"✅ Test notification sent successfully to user {NOTIFICATION_USER_ID}!")
                print(f"📱 Check your Discord DMs!")
                
            except discord.errors.NotFound:
                print(f"❌ ERROR: User {NOTIFICATION_USER_ID} not found")
                print("Make sure the user ID is correct")
            except discord.errors.Forbidden:
                print(f"❌ ERROR: Cannot send DM to user {NOTIFICATION_USER_ID}")
                print("The user may have DMs disabled or hasn't shared a server with the bot")
            except Exception as e:
                print(f"❌ ERROR sending notification: {e}")
            finally:
                await client.close()
        
        # Run with timeout
        await asyncio.wait_for(client.start(DISCORD_TOKEN), timeout=15)
        
    except asyncio.TimeoutError:
        print("✅ Connection timeout (expected behavior)")
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║        Discord Notification Test                         ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print()
    
    asyncio.run(send_test_notification())
    
    print()
    print("═" * 63)
    print("Test complete!")
    print("═" * 63)

if __name__ == "__main__":
    main()
