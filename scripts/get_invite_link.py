#!/usr/bin/env python3
"""
Generate Discord Bot Invite Link

This script helps create the correct OAuth2 URL to invite your bot to Discord servers.
"""

import base64
import os

from dotenv import load_dotenv

load_dotenv()


def generate_invite_link():
    """Generate the correct Discord bot invite link."""

    # Try to get client ID from environment or bot token
    client_id = os.getenv("DISCORD_CLIENT_ID")
    bot_token = os.getenv("DISCORD_BOT_TOKEN")

    if not client_id and bot_token:
        # Extract client ID from bot token (first part before first dot)
        # Bot tokens are format: base64(client_id).random.signature
        token_parts = bot_token.split(".")
        if len(token_parts) >= 1 and token_parts[0]:
            try:
                decoded = base64.b64decode(token_parts[0] + "==")  # Add padding
                client_id = decoded.decode("utf-8")
            except Exception as e:
                print(f"⚠️  Failed to decode client ID from token: {e}")

    if not client_id:
        print("❌ Could not determine bot client ID")
        print("💡 Please add DISCORD_CLIENT_ID to your .env file")
        print("   You can find this in Discord Developer Portal → Your App → General Information")
        return None

    # Calculate required permissions
    permissions = calculate_permissions()

    # Generate OAuth2 URL
    base_url = "https://discord.com/oauth2/authorize"
    params = {
        "client_id": client_id,
        "scope": "bot applications.commands",  # bot scope + slash commands
        "permissions": str(permissions),
    }

    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    invite_url = f"{base_url}?{query_string}"

    return invite_url, client_id


def calculate_permissions():
    """Calculate the permissions integer for bot functionality."""

    # Discord permission bits
    permissions = {
        "send_messages": 2048,  # Send messages in text channels
        "read_messages": 1024,  # Read message history
        "embed_links": 16384,  # Embed links in messages
        "attach_files": 32768,  # Attach files to messages
        "read_message_history": 65536,  # Read message history
        "use_external_emojis": 262144,  # Use external emojis
        "add_reactions": 64,  # Add reactions to messages
        "use_slash_commands": 2147483648,  # Use application commands
        "manage_messages": 8192,  # Manage messages (for moderation)
    }

    # Calculate total permissions
    total = sum(permissions.values())

    print("🔑 Bot Permissions Required:")
    for perm, value in permissions.items():
        print(f"   ✅ {perm}: {value}")
    print(f"   📊 Total: {total}")

    return total


def main():
    """Main function to generate and display invite link."""

    print("🔗 Discord Bot Invite Link Generator")
    print("=====================================")

    result = generate_invite_link()

    if result:
        invite_url, client_id = result

        print(f"\n✅ Your bot's Client ID: {client_id}")
        print("\n🔗 **COPY THIS INVITE LINK:**")
        print(f"{invite_url}")
        print("\n📋 Instructions:")
        print("1. Copy the link above")
        print("2. Paste it in your browser")
        print("3. Select the Discord server to add the bot to")
        print("4. Review and approve the permissions")
        print("5. Click 'Authorize'")

        print("\n⚠️  IMPORTANT:")
        print("- Make sure your bot is RUNNING before inviting it")
        print("- Start your bot with: python -m ultimate_discord_intelligence_bot.setup_cli run discord")
        print("- The bot needs to be online for the invite to work properly")

    else:
        print("\n❌ Could not generate invite link")
        print("💡 Please check your .env configuration")


if __name__ == "__main__":
    main()
