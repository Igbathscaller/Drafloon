import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import time

import ChannelServer
import DraftCommands as Draft
import GoogleInteraction as ggSheet
import LeftPicks as Picks
import Scheduling


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
    ChannelServer.channelData[channel_id]["TeamNames"] = ggSheet.loadPointsDraftedTeams(channel_id)
    ggSheet.loadWriteCells(channel_id, ChannelServer.channelData.get(channel_id, {}).get("Player Count", 0))
    Draft.loadPicks(channel_id)
    if channel_id in ChannelServer.channelData:
        ChannelServer.channelData[channel_id]["Turn"] = len(ggSheet.draftedData[channel_id]) + len(ChannelServer.channelData[channel_id]["Skipped"])
    ChannelServer.saveJson()

# region: debug with timer version
# def handle_spreadsheet_update_debug(channel_id, sheet_key):
#     start = time.perf_counter()
#     ggSheet.loadSheet(channel_id, sheet_key)
#     end = time.perf_counter()
#     print(f"loadSheet took {end - start:.6f} seconds", ggSheet.spreadDict)

#     start = time.perf_counter()
#     ggSheet.loadPointsDraftedTeams(channel_id)
#     end = time.perf_counter()
#     print(f"loadPoints took {end - start:.6f} seconds")

#     start = time.perf_counter()
#     ggSheet.loadWriteCells(channel_id, ChannelServer.channelData.get(channel_id, {}).get("Player Count", 0))
#     end = time.perf_counter()
#     print(f"loadWriteCells took {end - start:.6f} seconds", ggSheet.writeCellDict)

#     start = time.perf_counter()
#     Draft.loadPicks(channel_id)
#     end = time.perf_counter()
#     print(f"loadPicks took {end - start:.6f} seconds", Draft.pickData)
# endregion

ChannelServer.register_module_callback(handle_spreadsheet_update)

# Loads Spreadsheets from channelData into GG Sheets Interaction
for channel_id, channel in ChannelServer.channelData.items():

    ggSheet.loadSheet(channel_id, channel["spreadsheet"])
    ChannelServer.channelData[channel_id]["TeamNames"] = ggSheet.loadPointsDraftedTeams(channel_id)
    ggSheet.loadWriteCells(channel_id, ChannelServer.channelData[channel_id]["Player Count"])
    Draft.loadPicks(channel_id)
    ChannelServer.channelData[channel_id]["Turn"] = len(ggSheet.draftedData[channel_id]) + len(ChannelServer.channelData[channel_id]["Skipped"])
    
ChannelServer.saveJson()

# region: debug
# print(ChannelServer.channelData)
# print(ggSheet.spreadDict)
# print(ggSheet.pointDict)
# print(ggSheet.draftedData)
# print(ggSheet.writeCellDict)
# print(Draft.pickData)
# endregion

# Starts the Bot and it is the list of all commands.
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    try:
        guild = discord.Object(id=Guild_Id)
    
        # Related to saving and storing player and sheet information in the roster.
        client.tree.add_command(ChannelServer.setspreadsheet,   guild=guild) # Has Manage Message Perm
        client.tree.add_command(ChannelServer.removeSpreadsheet,guild=guild) # Has Manage Message Perm
        client.tree.add_command(ChannelServer.getspreadsheet,   guild=guild) 
        client.tree.add_command(ChannelServer.setPlayerRoster,  guild=guild) # Has Manage Message Perm
        client.tree.add_command(ChannelServer.removePlayer,     guild=guild) # Has Manage Message Perm
        client.tree.add_command(ChannelServer.getPlayers,       guild=guild)
        client.tree.add_command(ChannelServer.draft_control,    guild=guild) # Has Manage Message Perm
        client.tree.add_command(ChannelServer.view_timer,       guild=guild)

        # Draft Commands
        client.tree.add_command(Draft.draft,        guild=guild)
        client.tree.add_command(Draft.skip_player,  guild=guild) # Has Manage Message Perm
        client.tree.add_command(Draft.stop_timer,   guild=guild) # Has Manage Message Perm
        
        # Pick Commands
        client.tree.add_command(Picks.leave_pick,       guild=guild)
        client.tree.add_command(Picks.view_picks,       guild=guild)
        client.tree.add_command(Picks.view_picks_mod,   guild=guild) # Has Manage Message Perm

        # Scheduling Commands
        client.tree.add_command(Scheduling.save_schedule_sheet, guild=guild) # Has Manage Channel Perms
        client.tree.add_command(Scheduling.update_schedule,     guild=guild) # Has Manage Channel Perms
        client.tree.add_command(Scheduling.schedulingChannels,  guild=guild) # Has Manage Channel Perms
        client.tree.add_command(Scheduling.deleteChannels,      guild=guild) # Has Manage Channel Perms


        synced = await client.tree.sync(guild=guild)

        print(f"Synced {len(synced)} command(s) to guild {guild.id}")
    except Exception as e:
        print(f"Error syncing commands: {e}")


try:
    client.run(Token)
finally:
    print("Shutting Down...")

