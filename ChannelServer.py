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

    return data

def initializeChannel(data, channel_id):
    rosters = {str(i): {"name": f"P{i}", "players": []} for i in range(1, 17)}
    data["ListOfSheets"][channel_id] = {
        "spreadsheet": "",
        "Rosters": rosters
    }


### Slash Commands for ChannelServer management

@app_commands.command(name="link_sheet", description="Connect Draft to a Sheet")
async def setspreadsheet(interaction: discord.Interaction, spreadsheet_name: str):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    channel_id = str(interaction.channel_id)
    channel_name = str(interaction.channel)
    data = loadJson()

    if channel_id not in data["ListOfSheets"]:
        initializeChannel(data, channel_id)

    data["ListOfSheets"][channel_id]["spreadsheet"] = spreadsheet_name
    with open("ChannelServer.json", "w") as f:
        json.dump(data, f, indent=4)

    await interaction.response.send_message(f"Spreadsheet `{spreadsheet_name}` has been linked to #`{channel_name}`", ephemeral=True)


@app_commands.command(name="get_sheet", description="Get Sheet name")
@app_commands.guilds()
async def getspreadsheet(interaction: discord.Interaction):
    channel_id = str(interaction.channel_id)
    channel_name = str(interaction.channel)
    data = loadJson()

    if channel_id not in data["ListOfSheets"]:
        msg = f"#`{channel_name}` has no linked spreadsheet"
    else:
        msg = f"#`{channel_name}` is linked to {data['ListOfSheets'][channel_id]['spreadsheet']}"

    await interaction.response.send_message(msg, ephemeral=True)


@app_commands.command(name="add_player", description="Connect Discord User to a Roster")
@app_commands.guilds()
async def setPlayerRoster(interaction: discord.Interaction, member: discord.Member, roster: str):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    channel_id = str(interaction.channel_id)
    user_id = member.id
    data = loadJson()

    if channel_id not in data["ListOfSheets"]:
        initializeChannel(data, channel_id)

    players = data["ListOfSheets"][channel_id]["Rosters"][roster]["players"]
    if user_id not in players:
        players.append(user_id)
        msg = f"Player {member.display_name} linked to Roster {roster}."
    else:
        msg = f"Player {member.display_name} is already in Roster {roster}."

    with open("ChannelServer.json", "w") as f:
        json.dump(data, f, indent=4)

    await interaction.response.send_message(msg, ephemeral=True)

@app_commands.command(name="remove_player", description="Connect Discord User to a Roster")
@app_commands.guilds()
async def removePlayerRoster(interaction: discord.Interaction, member: discord.Member, roster: str):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    channel_id = str(interaction.channel_id)
    user_id = member.id
    data = loadJson()

    if channel_id not in data["ListOfSheets"]:
        initializeChannel(data, channel_id)

    players = data["ListOfSheets"][channel_id]["Rosters"][roster]["players"]
    if user_id in players:
        players.remove(user_id)
        msg = f"Player {member.display_name} removed from Roster {roster}."
    else:
        msg = f"Player {member.display_name} is not in Roster {roster}."

    with open("ChannelServer.json", "w") as f:
        json.dump(data, f, indent=4)

    await interaction.response.send_message(msg, ephemeral=True)



@app_commands.command(name="get_players", description="Get players in a roster")
@app_commands.guilds()
async def getPlayerRoster(interaction: discord.Interaction, roster: str):
    channel_id = str(interaction.channel_id)
    channel_name = str(interaction.channel)
    data = loadJson()

    if channel_id not in data["ListOfSheets"]:
        msg = f"#`{channel_name}` has no linked spreadsheet"
    else:
        ids = data["ListOfSheets"][channel_id]["Rosters"][roster]["players"]
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
