import json
import asyncio
from discord import Interaction,Member,Embed,Color
from discord import app_commands
from re import search

### JSON Utility Functions

def loadJson():
    try:
        with open("ChannelServer.json", "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        data = {}

    return data

# Save ChannelData to Json
def saveJson():
    with open("ChannelServer.json", "w") as f:
        json.dump(channelData, f, indent=4)

# Stores Json Data as a variables on runtime.
channelData = loadJson()

# Whenever you want to add a new channel to the variable you can.
def initializeChannel(channel_id, playerCount):
    channelData[channel_id] = {
        "spreadsheet": "",
        "Player Count": playerCount,
        "Turn": 0,
        "Skipped": [],
        "Rosters": {},
        "Players": {}
    }

# Allows other modules to know when the Json has been updated
module_callback = None
def register_module_callback(callback):
    global module_callback
    module_callback = callback



# Helper Function for Draft Commands
def getTeam(channel_id: str, user_id: str):
    channel = channelData.get(channel_id, None)
    if channel == None:
        return None
    return channel["Players"].get(user_id, None)

def getSheet(channel_id: str):
    channel = channelData.get(channel_id, None)
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

    await interaction.response.defer(ephemeral=True)

    channel_id = str(interaction.channel_id)
    channel_name = str(interaction.channel)

    # Convert URL to SpreadSheet Key
    match = search(r"/d/([a-zA-Z0-9-_]+)", spreadsheet_url)
    if not match:
        await interaction.response.send_message("Invalid Google Sheets URL provided.", ephemeral=True)
        return
    
    spreadsheet_key = match.group(1)

    if channel_id not in channelData:
        initializeChannel(channel_id, player_count)

    channelData[channel_id]["spreadsheet"] = spreadsheet_key
    saveJson()

    # Updates other modules, Takes longer now that I'm adding more functions
    if module_callback:
        module_callback(channel_id, spreadsheet_key)

    await interaction.followup.send(f"Spreadsheet `{spreadsheet_url}` has been linked to #`{channel_name}`", ephemeral=True)


@app_commands.command(name="remove_sheet", description="Removes the sheet and deletes associate information")
@app_commands.guilds()
async def removeSpreadsheet(interaction: Interaction):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    channel_id = str(interaction.channel_id)
    channel_name = str(interaction.channel)

    if channel_id in channelData:
        del channelData[channel_id]
        saveJson()

    # Updates other modules, Takes longer now that I'm adding more functions
    if module_callback:
        module_callback(channel_id, None)

    await interaction.followup.send(f"#`{channel_name}` has been reset", ephemeral=True)



@app_commands.command(name="get_sheet", description="Get Sheet name")
@app_commands.guilds()
async def getspreadsheet(interaction: Interaction):
    channel_id = str(interaction.channel_id)
    channel_name = str(interaction.channel)

    if channel_id not in channelData:
        msg = f"#`{channel_name}` has no linked spreadsheet"
    else:
        msg = f"#`{channel_name}` is linked to `{channelData[channel_id]['spreadsheet']}`"

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

    if channel_id not in channelData:
        await interaction.response.send_message("No Sheet Associated with channel.", ephemeral=True)
        return


    if channelData[channel_id]["Players"].get(user_id, None) == team:
        # If it player is already the roster member
        msg = f"Player {member.display_name} is already on Team {team}."
    
    elif channelData[channel_id]["Players"].get(user_id, None) == None:
        # if the player is not part of any roster
        channelData[channel_id]["Players"][user_id] = team
        channelData[channel_id]["Rosters"].setdefault(team, []).append(user_id)

        msg = f"Player {member.display_name} added to Team {team}."

    else:
        # if the player is part of another roster
        oldTeam = channelData[channel_id]["Players"][user_id]
        channelData[channel_id]["Players"][user_id] = team
        channelData[channel_id]["Rosters"][oldTeam].remove(user_id)
        channelData[channel_id]["Rosters"].setdefault(team, []).append(user_id)

        msg = f"Player {member.display_name} moved from Team {oldTeam} to Team {team}."

    saveJson()

    await interaction.response.send_message(msg, ephemeral=True)

# Config Funtion
# Needs Permission to Run
# Checks if Channel Exists
# Check if player is on team
# Removes player from team if on a team

@app_commands.command(name="remove_player", description="Remove a Discord User from a Team")
@app_commands.guilds()
async def removePlayer(interaction: Interaction, member: Member):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    channel_id = str(interaction.channel_id)
    user_id = str(member.id)

    if channel_id not in channelData:
        await interaction.response.send_message("Channel has not been initialized", ephemeral=True)
        return

    players = channelData[channel_id]["Players"]

    if user_id in players.keys():   # Check if on a team
        roster = players[user_id]   # Get the team
        del players[user_id]        # Delete player from user id
        channelData[channel_id]["Rosters"][roster].remove(user_id) # Remove player from the team
        msg = f"Player {member.display_name} removed from Team {roster}."
    else:
        msg = f"Player {member.display_name} is not on any Team."

    saveJson()

    await interaction.response.send_message(msg, ephemeral=True)



@app_commands.command(name="view_players", description="Get all the players involved")
@app_commands.guilds()
async def getPlayers(interaction: Interaction):
    channel_id = str(interaction.channel_id)
    channel_name = str(interaction.channel)

    if channel_id not in channelData:
        await interaction.response.send_message(f"#`{channel_name}` has no linked spreadsheet")
    
    rosters = channelData[channel_id].get("Rosters", {})
    if not rosters:
        await interaction.response.send_message("No teams found.", ephemeral=True)
        return
    
    embed = Embed(
        title=f"Teams for #{channel_name}",
        color= Color.blue()
    )

    for roster, ids in rosters.items():

        members = []
        for member_id in ids:
            member = await interaction.guild.fetch_member(int(member_id))
            members.append(member)

        display_names = [member.display_name for member in members if member]
        
        if display_names:
            embed.add_field(name=f"Team {roster}", value=", ".join(display_names), inline=False)
        else:
            embed.add_field(name=f"Team {roster}", value="It's a ghost town here", inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)





