import json
import asyncio
import discord
from discord import app_commands
from discord.ext import commands

### JSON Utility Functions

def loadJson():
    try:
        with open("ChannelServer.json", "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        data = {}


    if "ListOfSheets" not in data:
        data["ListOfSheets"] = {}
        with open("ChannelServer.json", "w") as f:
            json.dump(data, f, indent=4)

    return data

# Stores Json Data as a variables on runtime.
channelData = loadJson()

# Whenever you want to add a new channel to the variable you can.
def initializeChannel(channel_id):
    channelData["ListOfSheets"][channel_id] = {
        "spreadsheet": "",
        "Rosters": {},
        "Players": {}
    }


### Slash Commands for ChannelServer management

# Config Function
# Needs Permission to use
@app_commands.command(name="set_sheet", description="Connect Draft to a Sheet")
@app_commands.guilds()
async def setspreadsheet(interaction: discord.Interaction, spreadsheet_name: str):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    channel_id = str(interaction.channel_id)
    channel_name = str(interaction.channel)

    if channel_id not in channelData["ListOfSheets"]:
        initializeChannel(channel_id)

    channelData["ListOfSheets"][channel_id]["spreadsheet"] = spreadsheet_name
    with open("ChannelServer.json", "w") as f:
        json.dump(channelData, f, indent=4)

    await interaction.response.send_message(f"Spreadsheet `{spreadsheet_name}` has been linked to #`{channel_name}`", ephemeral=True)


@app_commands.command(name="get_sheet", description="Get Sheet name")
@app_commands.guilds()
async def getspreadsheet(interaction: discord.Interaction):
    channel_id = str(interaction.channel_id)
    channel_name = str(interaction.channel)

    if channel_id not in channelData["ListOfSheets"]:
        msg = f"#`{channel_name}` has no linked spreadsheet"
    else:
        msg = f"#`{channel_name}` is linked to {channelData['ListOfSheets'][channel_id]['spreadsheet']}"

    await interaction.response.send_message(msg, ephemeral=True)

# Config Funtion
# Needs Permission to Run

@app_commands.command(name="add_player", description="Connect Discord User to a Roster")
@app_commands.guilds()
async def setPlayerRoster(interaction: discord.Interaction, member: discord.Member, roster: str):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    channel_id = str(interaction.channel_id)
    user_id = str(member.id)

    if channel_id not in channelData["ListOfSheets"]:
        initializeChannel(channel_id)

    if channelData["ListOfSheets"][channel_id]["Players"].get(user_id, None) == roster:
        # If it player is already the roster member
        msg = f"Player {member.display_name} is already in Roster {roster}."
    
    elif channelData["ListOfSheets"][channel_id]["Players"].get(user_id, None) == None:
        # if the player is not part of any roster
        channelData["ListOfSheets"][channel_id]["Players"][user_id] = roster
        channelData["ListOfSheets"][channel_id]["Rosters"].setdefault(roster, []).append(user_id)

        msg = f"Player {member.display_name} linked to Roster {roster}."

    else:
        # if the player is part of another roster
        oldRoster = channelData["ListOfSheets"][channel_id]["Players"][user_id]
        channelData["ListOfSheets"][channel_id]["Players"][user_id] = roster
        channelData["ListOfSheets"][channel_id]["Rosters"][oldRoster].remove(user_id)
        channelData["ListOfSheets"][channel_id]["Rosters"].setdefault(roster, []).append(user_id)

        msg = f"Player {member.display_name} moved from {oldRoster} to {roster}."



    with open("ChannelServer.json", "w") as f:
        json.dump(channelData, f, indent=4)

    await interaction.response.send_message(msg, ephemeral=True)

# Config Funtion
# Needs Permission to Run

@app_commands.command(name="remove_player", description="Connect Discord User to a Roster")
@app_commands.guilds()
async def removePlayer(interaction: discord.Interaction, member: discord.Member):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    channel_id = str(interaction.channel_id)
    user_id = str(member.id)

    if channel_id not in channelData["ListOfSheets"]:
        await interaction.response.send_message("Channel has not been initialized", ephemeral=True)
        return

    players = channelData["ListOfSheets"][channel_id]["Players"]

    if user_id in players.keys():
        roster = players[user_id]
        del players[user_id]
        channelData["ListOfSheets"][channel_id]["Rosters"][roster].remove(user_id)
        msg = f"Player {member.display_name} removed from Roster {roster}."
    else:
        msg = f"Player {member.display_name} is not on any Roster."

    with open("ChannelServer.json", "w") as f:
        json.dump(channelData, f, indent=4)

    await interaction.response.send_message(msg, ephemeral=True)



@app_commands.command(name="get_players", description="Get players in a roster")
@app_commands.guilds()
async def getPlayerRoster(interaction: discord.Interaction, roster: str):
    channel_id = str(interaction.channel_id)
    channel_name = str(interaction.channel)

    if channel_id not in channelData["ListOfSheets"]:
        msg = f"#`{channel_name}` has no linked spreadsheet"
    
    elif channelData["ListOfSheets"][channel_id]["Rosters"].get(roster,[]) == []:
        msg = f"Roster {roster} is empty"

    else:
        ids = channelData["ListOfSheets"][channel_id]["Rosters"][roster]
        members = await asyncio.gather(*[
            interaction.guild.fetch_member(int(id))
            for id in ids
        ])
        display_names = [member.display_name for member in members if member]
        msg = f"Player(s): {', '.join(display_names)} are on Roster {roster}"

    await interaction.response.send_message(msg, ephemeral=True)


### Code to Throw into Main Bot in case this ever goes wrong
# ### Function for loading in existing data
# def loadJson():
#         # Try to load existing data
#     try:
#         with open("ChannelServer.json", "r") as f:
#             data = json.load(f)
#     except (FileNotFoundError,json.decoder.JSONDecodeError):
#         data = {}

#     # Create ListOfSheets if it doesn't exist
#     if "ListOfSheets" not in data:
#         data["ListOfSheets"] = {}

#     return data

# def initializeChannel(data, channel_id):
#         rosters = {}
#         for i in range(1, 17):
#             rosters[str(i)] = {
#                 "name": f"P{i}",
#                 "players": []
#             }

#         data["ListOfSheets"][channel_id] = {
#             "spreadsheet": "",
#             "Rosters": rosters
#         }



# ### Command for linking a sheet to a channel

# @client.tree.command(name="sheet", description="Connect Draft to a Sheet", guild=discord.Object(id=Test_Guild_Id))
# @commands.has_permissions(manage_messages=True)
# async def setspreadsheet(interaction: discord.Interaction, spreadsheet_name: str):

#     # Stop No Permission Scrubs

#     if not interaction.user.guild_permissions.manage_messages:
#         await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
#         return


#     channel_id = str(interaction.channel_id)
#     channel_name = str(interaction.channel)

#     # Load existing data
#     data = loadJson()

#     # Initialize the channel if it doesn't exist.
#     if channel_id not in data["ListOfSheets"]:
#         initializeChannel(data,channel_id)

#     # Set the SpreadSheet Name
#     data["ListOfSheets"][channel_id]["spreadsheet"] = spreadsheet_name
    
#     # Write to file
#     with open("ChannelServer.json", "w") as f:
#         json.dump(data, f, indent=4)

#     await interaction.response.send_message(
#         f"Spreadsheet `{spreadsheet_name}` has been linked to #`{channel_name}`",ephemeral=True
#     )

# ### Getting the Sheet name 

# @client.tree.command(name="get_sheet", description="Get Sheet name", guild=discord.Object(id=Test_Guild_Id))
# async def setspreadsheet(interaction: discord.Interaction):
#     channel_id = str(interaction.channel_id)
#     channel_name = str(interaction.channel)
#     msg = ""

#     # Load data
#     data = loadJson()

#     # Initialize the channel if it doesn't exist.
#     if channel_id not in data["ListOfSheets"]:
#         msg = f"#`{channel_name}` has no linked spreadsheet"
#     else:
#         msg = f"#`{channel_name}` is linked to {data["ListOfSheets"][channel_id]["spreadsheet"]}"
    
#     await interaction.response.send_message(
#         msg, ephemeral=True
#     )

# ### Sheet for linking a player to a specific roster

# @client.tree.command(name="player", description="Connect Discord User to a Roster", guild=discord.Object(id=Test_Guild_Id))
# @commands.has_permissions(manage_messages=True)
# async def setPlayerRoster(interaction: discord.Interaction, member: discord.Member, roster: str):
    
#     # Stop No Permission Scrubs
#     if not interaction.user.guild_permissions.manage_messages:
#         await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
#         return

    
#     channel_id = str(interaction.channel_id)
#     user_id = member.id

#     # Load existing data
#     data = loadJson()

#     # Initialize the channel if it doesn't exist.
#     if channel_id not in data["ListOfSheets"]:
#         initializeChannel(data,channel_id)

#     # add player if new
#     players = data["ListOfSheets"][channel_id]["Rosters"][roster]["players"]
#     msg = ""
#     if user_id not in players:
#         players.append(user_id)
#         msg = f"Player {member.display_name} linked to Roster {roster}."
#     else:
#         msg = f"Player {member.display_name} is already in Roster {roster}."
#     print(msg)

    
#     # Write to file
#     with open("ChannelServer.json", "w") as f:
#         json.dump(data, f, indent=4)

#     await interaction.response.send_message(
#         msg,ephemeral=True
#     )

# ###Getting Players from a specific roster

# @client.tree.command(name="get_player", description="Get Sheet name", guild=discord.Object(id=Test_Guild_Id))
# async def setspreadsheet(interaction: discord.Interaction, roster: str):
#     channel_id = str(interaction.channel_id)
#     channel_name = str(interaction.channel)
#     msg = ""

#     # Load data
#     data = loadJson()

#     # Initialize the channel if it doesn't exist.
#     if channel_id not in data["ListOfSheets"]:
#         msg = f"#`{channel_name}` has no linked spreadsheet"
#     else:
#         ids = data["ListOfSheets"][channel_id]["Rosters"][roster]["players"]

#         members = await asyncio.gather(*[
#             interaction.guild.fetch_member(int(id))
#             for id in ids
#         ])

#         display_names = [member.display_name for member in members]

#         msg = f"Player(s): {", ".join(display_names)} are on Roster {roster}"

#     await interaction.response.send_message(
#         msg, ephemeral=True
#     )
