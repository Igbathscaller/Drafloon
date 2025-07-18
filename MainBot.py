import os
from dotenv import load_dotenv
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

## Sets up updating information in other modules when running ChannelServer
# Handles updating the spreadsheet for other modules
# Handles updating the left picks
def handle_spreadsheet_update(channel_id, sheet_key):
    ggSheet.loadSheet(channel_id, sheet_key)
    ggSheet.loadPoints(channel_id)
    ggSheet.loadWriteCells(channel_id, ChannelServer.channelData[channel_id]["Player Count"])
    Draft.loadPicks(channel_id)

ChannelServer.register_module_callback(handle_spreadsheet_update)

# Loads Spreadsheets from channelData into GG Sheets Interaction
for channel_id, channel in ChannelServer.channelData.items():
        ggSheet.loadSheet(channel_id, channel["spreadsheet"])
        ggSheet.loadPoints(channel_id)
        ggSheet.loadWriteCells(channel_id, ChannelServer.channelData[channel_id]["Player Count"])
        Draft.loadPicks(channel_id)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    try:
        guild = discord.Object(id=Guild_Id)
    
        # Related to saving and storing player and sheet information in the roster.
        client.tree.add_command(ChannelServer.setspreadsheet,   guild=guild) # Has Manage Message Perm
        client.tree.add_command(ChannelServer.getspreadsheet,   guild=guild) 
        client.tree.add_command(ChannelServer.setPlayerRoster,  guild=guild) # Has Manage Message Perm
        client.tree.add_command(ChannelServer.removePlayer,     guild=guild) # Has Manage Message Perm
        client.tree.add_command(ChannelServer.getPlayerRoster,  guild=guild)

        # Draft Commands
        client.tree.add_command(Draft.draft,        guild=guild)
        client.tree.add_command(Draft.skip_player,  guild=guild) # Has Manage Message Perm
        client.tree.add_command(Draft.stop_timer,   guild=guild) # Has Manage Message Perm
        client.tree.add_command(Draft.leave_pick,   guild=guild)
        client.tree.add_command(Draft.view_picks,   guild=guild)


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

