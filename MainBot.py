import os
from dotenv import load_dotenv
import json
import discord
from discord.ext import commands

import ChannelServer
import DraftCommands as Draft
import GoogleInteraction as ggSheet


# Import Neccessary Variables and Data
load_dotenv()
Guild_Id = os.getenv("Guild_Id")
Token = os.getenv("Discord_Token")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

client = commands.Bot(command_prefix="!", intents=intents)


## Sets up the GG Sheets Interaction
# Handles updating the spreadsheet for other modules
def handle_spreadsheet_update(channel_id, sheet_key):
    ggSheet.loadSheet(channel_id, sheet_key)
    ggSheet.loadPoints(channel_id)
    ggSheet.loadWriteCells(channel_id, ChannelServer.channelData[channel_id]["Player Count"])

ChannelServer.register_spreadsheet_callback(handle_spreadsheet_update)

# Loads Spreadsheets from channelData into GG Sheets Interaction
for channel_id, info in ChannelServer.channelData.items():
        ggSheet.loadSheet(channel_id, info["spreadsheet"])
        ggSheet.loadPoints(channel_id)
        ggSheet.loadWriteCells(channel_id, ChannelServer.channelData[channel_id]["Player Count"])


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    try:
        guild = discord.Object(id=Guild_Id)
    
        # Related to saving and storing player and sheet information in the roster.
        client.tree.add_command(ChannelServer.setspreadsheet, guild=guild)
        client.tree.add_command(ChannelServer.getspreadsheet, guild=guild)
        client.tree.add_command(ChannelServer.setPlayerRoster, guild=guild)
        client.tree.add_command(ChannelServer.removePlayer, guild=guild)
        client.tree.add_command(ChannelServer.getPlayerRoster, guild=guild)

        # Draft Commands
        client.tree.add_command(Draft.draft, guild=guild)

        synced = await client.tree.sync(guild=guild)

        print(f"Synced {len(synced)} command(s) to guild {guild.id}")
    except Exception as e:
        print(f"Error syncing commands: {e}")

# @client.event
# async def close():
#     print("Bot is shutting down... Saving JSON data.")
#     with open("ChannelServer.json", "w") as f:
#         json.dump(ChannelServer.channelData, f, indent=4)
#     await super(commands.Bot, client).close()

try:
    client.run(Token)
finally:
    print("Shutting Down...")
    # print("Saving data before shutdown...")
    # with open("ChannelServer.json", "w") as f:
    #     json.dump(ChannelServer.channelData, f, indent=4)

