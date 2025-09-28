from discord import Interaction, app_commands

# Slash command: react_search
@app_commands.command(name="pickem_reacts", description="React to the last N messages with :one: and :two:")
@app_commands.describe(limit="How many previous messages to react to (max 20)")
@app_commands.guilds()
async def pickem(interaction: Interaction, limit: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return
    
    if limit <= 0:
        await interaction.response.send_message("Limit must be a positive integer.", ephemeral=True)
        return
    if limit > 20:
        limit = 20

    # Send an ephemeral acknowledgement
    try:
        await interaction.response.send_message(f"Reacting to the last {limit} messages...", ephemeral=True)
    except Exception:
        pass

    channel = interaction.channel
    if channel is None:
        await interaction.followup.send("Could not determine the channel to read messages from.", ephemeral=True)
        return

    success = 0
    failed = 0

    try:
        async for msg in channel.history(limit=limit):
            for emoji in ("1️⃣", "2️⃣"):
                try:
                    await msg.add_reaction(emoji)
                    success += 1
                except Exception as e:
                    failed += 1
    except Exception as e:
        # Try to edit the ephemeral response with an error message; if that's not available, send an ephemeral followup.
        try:
            await interaction.edit_original_response(content=f"Error while reading message history or reacting: {e}")
        except Exception:
            pass
        return

    summary = f"Reacted to up to {limit} messages: {success} reactions added, {failed} failures."

    # Edit the original ephemeral response with the final summary so nothing visible is posted in the channel
    try:
        await interaction.edit_original_response(content=summary)
    except Exception:
        # As a fallback, send an ephemeral followup
        try:
            await interaction.followup.send(summary, ephemeral=True)
        except Exception:
            pass