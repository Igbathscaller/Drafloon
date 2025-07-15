import json
import asyncio
from discord import Interaction,Member
from discord import app_commands
from re import search

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

# Allows other modules to know when the Json has been updated
spreadsheet_callback = None
def register_spreadsheet_callback(callback):
    global spreadsheet_callback
    spreadsheet_callback = callback

# Whenever you want to add a new channel to the variable you can.
def initializeChannel(channel_id, playerCount):
    channelData["ListOfSheets"][channel_id] = {
        "spreadsheet": "",
        "Player Count": playerCount,
        "Turn": 0,
        "Skipped": [],
        "Rosters": {},
        "Players": {}
    }

# Helper Function for Draft Commands
def getTeam(channel_id: str, user_id: str):
    channel = channelData["ListOfSheets"].get(channel_id, None)
    if channel == None:
        return None
    return channel["Players"].get(user_id, None)

def getSheet(channel_id: str):
    channel = channelData["ListOfSheets"].get(channel_id, None)
    if channel == None:
        return None
    return channel["spreadsheet"]



### Slash Commands for ChannelServer management

# Config Function
# Needs Permission to use
@app_commands.command(name="set_sheet", description="Connect Draft to a Sheet")
@app_commands.guilds()
@app_commands.describe(spreadsheet_url= "spreadsheet URL", player_count="number of players, defaults to 16")
async def setspreadsheet(interaction: Interaction, spreadsheet_url: str, player_count: app_commands.Range[int, 1, None] = 16):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    channel_id = str(interaction.channel_id)
    channel_name = str(interaction.channel)

    # Convert URL to SpreadSheet Key
    match = search(r"/d/([a-zA-Z0-9-_]+)", spreadsheet_url)
    if not match:
        await interaction.response.send_message("Invalid Google Sheets URL provided.", ephemeral=True)
        return
    
    spreadsheet_key = match.group(1)

    if channel_id not in channelData["ListOfSheets"]:
        initializeChannel(channel_id, player_count)

    channelData["ListOfSheets"][channel_id]["spreadsheet"] = spreadsheet_key
    with open("ChannelServer.json", "w") as f:
        json.dump(channelData, f, indent=4)

    # Testing call back
    if spreadsheet_callback:
        spreadsheet_callback(channel_id, spreadsheet_key)

    await interaction.response.send_message(f"Spreadsheet `{spreadsheet_url}` has been linked to #`{channel_name}`", ephemeral=True)


@app_commands.command(name="get_sheet", description="Get Sheet name")
@app_commands.guilds()
async def getspreadsheet(interaction: Interaction):
    channel_id = str(interaction.channel_id)
    channel_name = str(interaction.channel)

    if channel_id not in channelData["ListOfSheets"]:
        msg = f"#`{channel_name}` has no linked spreadsheet"
    else:
        msg = f"#`{channel_name}` is linked to {channelData['ListOfSheets'][channel_id]['spreadsheet']}"

    await interaction.response.send_message(msg, ephemeral=True)

# Config Funtion
# Needs Permission to Run

@app_commands.command(name="add_player", description="Add a Discord User to a Team")
@app_commands.guilds()
async def setPlayerRoster(interaction: Interaction, member: Member, team: str):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    channel_id = str(interaction.channel_id)
    user_id = str(member.id)

    if channel_id not in channelData["ListOfSheets"]:
        initializeChannel(channel_id)

    if channelData["ListOfSheets"][channel_id]["Players"].get(user_id, None) == team:
        # If it player is already the roster member
        msg = f"Player {member.display_name} is already in Roster {team}."
    
    elif channelData["ListOfSheets"][channel_id]["Players"].get(user_id, None) == None:
        # if the player is not part of any roster
        channelData["ListOfSheets"][channel_id]["Players"][user_id] = team
        channelData["ListOfSheets"][channel_id]["Rosters"].setdefault(team, []).append(user_id)

        msg = f"Player {member.display_name} linked to Roster {team}."

    else:
        # if the player is part of another roster
        oldTeam = channelData["ListOfSheets"][channel_id]["Players"][user_id]
        channelData["ListOfSheets"][channel_id]["Players"][user_id] = team
        channelData["ListOfSheets"][channel_id]["Rosters"][oldTeam].remove(user_id)
        channelData["ListOfSheets"][channel_id]["Rosters"].setdefault(team, []).append(user_id)

        msg = f"Player {member.display_name} moved from Team {oldTeam} to Team {team}."



    with open("ChannelServer.json", "w") as f:
        json.dump(channelData, f, indent=4)

    await interaction.response.send_message(msg, ephemeral=True)

# Config Funtion
# Needs Permission to Run
# Checks if Channel Exists
# Check if player is on team
# Removes player from team if on a team

@app_commands.command(name="remove_player", description="Connect Discord User to a Roster")
@app_commands.guilds()
async def removePlayer(interaction: Interaction, member: Member):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    channel_id = str(interaction.channel_id)
    user_id = str(member.id)

    if channel_id not in channelData["ListOfSheets"]:
        await interaction.response.send_message("Channel has not been initialized", ephemeral=True)
        return

    players = channelData["ListOfSheets"][channel_id]["Players"]

    if user_id in players.keys():   # Check if on a team
        roster = players[user_id]   # Get the team
        del players[user_id]        # Delete player from user id
        channelData["ListOfSheets"][channel_id]["Rosters"][roster].remove(user_id) # Remove player from the team
        msg = f"Player {member.display_name} removed from Roster {roster}."
    else:
        msg = f"Player {member.display_name} is not on any Roster."

    with open("ChannelServer.json", "w") as f:
        json.dump(channelData, f, indent=4)

    await interaction.response.send_message(msg, ephemeral=True)



@app_commands.command(name="get_players", description="Get players in a roster")
@app_commands.guilds()
async def getPlayerRoster(interaction: Interaction, roster: str):
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




