import os
from dotenv import load_dotenv
import json
import discord
from discord.ext import commands

import DraftCommands as Draft
import ChannelServer


# Import Neccessary Variables and Data
load_dotenv()
Test_Guild_Id = os.getenv("Test_Guild_Id")
Token = os.getenv("Discord_Token")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

client = commands.Bot(command_prefix="!", intents=intents)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    try:
        guild = discord.Object(id=Test_Guild_Id)
    
        # Related to saving and storing player and sheet information in the roster.
        client.tree.add_command(ChannelServer.setspreadsheet, guild=guild)
        client.tree.add_command(ChannelServer.getspreadsheet, guild=guild)
        client.tree.add_command(ChannelServer.setPlayerRoster, guild=guild)
        client.tree.add_command(ChannelServer.removePlayer, guild=guild)
        client.tree.add_command(ChannelServer.getPlayerRoster, guild=guild)

        # Draft Commands
        client.tree.add_command(Draft.choose, guild=guild)
        client.tree.add_command(Draft.draft, guild=guild)

        synced = await client.tree.sync(guild=guild)

        print(f"Synced {len(synced)} command(s) to guild {guild.id}")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@client.event
async def close():
    print("Bot is shutting down... Saving JSON data.")
    with open("ChannelServer.json", "w") as f:
        json.dump(ChannelServer.channelData, f, indent=4)
    await super(commands.Bot, client).close()


# First slash command 
# Remove guild in the future
# it is connected to specific server for faster testing

# This is the testing command

@client.tree.command(name="hello", description="Say hi to the bot!", guild=discord.Object(id=Test_Guild_Id))
@commands.has_permissions(manage_messages=True)
async def hello(interaction: discord.Interaction):

    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    await interaction.response.send_message(f"Hello, {interaction.user.mention}!")

try:
    client.run(Token)
finally:
    print("Saving data before shutdown...")
    with open("ChannelServer.json", "w") as f:
        json.dump(ChannelServer.channelData, f, indent=4)

