import json
import time

from discord import Interaction,Member,Embed,Color
from discord import app_commands
from re import search
from collections import Counter

# region: JSON Utility Functions
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
        "Paused" : True,
        "Skipped": [],
        "Rosters": {str(i): [] for i in range(1, playerCount + 1)},
        "Players": {},
        "TeamNames": {}
    }

# Allows other modules to know when the Json has been updated
module_callback = None
def register_module_callback(callback):
    global module_callback
    module_callback = callback

# endregion

# region: Helper Function for Draft Commands
def getTeam(channel_id: str, user_id: str):
    channel = channelData.get(channel_id, None)
    if channel == None:
        return None
    return channel["Players"].get(user_id, None)

# Check whose turn it is (This could be moved into Channel Server or GG Sheets)
def getTurn(channel_id: str):
    '''
    returns: (str name, int points): 
        Round (int)
        Team (int) 
    '''
    channel = channelData[channel_id]

    turn = channel.get("Turn", -1)
    playerCount = channel.get("Player Count", 1)
    
    # Turns 0-15 are round 1
    round = turn // playerCount
    
    # the reverse turns are odd (since it is 0-indexed)
    if round % 2:
        return (round, playerCount - turn % playerCount)
    # On the even turns. 
    else:
        return (round, turn % playerCount + 1)

# endregion

# region: Slash Commands for ChannelServer management

# Config Function
# Needs Permission to use
@app_commands.command(name="set_sheet", 
                      description="(mod) Connect Draft to a Sheet. This initializes the channel and no commands before this is done")
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

# endregion

# Config Funtion
# Needs Permission to Run

@app_commands.command(name="player_add", description="(mod) Add Discord Users to a Team, they will be allowed to draft and leave picks for the team")
@app_commands.guilds()
async def setPlayerRoster(  interaction: Interaction, team: str, member: Member, 
                            member2: Member = None,
                            member3: Member = None,
                            member4: Member = None,
                            member5: Member = None,
                            member6: Member = None,
                            member7: Member = None,
                            member8: Member = None,
                          ):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    channel_id = str(interaction.channel_id)
    user_id = str(member.id)

    if channel_id not in channelData:
        await interaction.response.send_message("No Sheet Associated with channel.", ephemeral=True)
        return
    teamName = channelData[channel_id]["TeamNames"].get(team,"No Team Name")

    members = [m for m in [member, member2, member3, member4, member5, member6, member7, member8] if m]

    msgs = []
    for member in members:
        user_id = str(member.id)
        if channelData[channel_id]["Players"].get(user_id) == team:
            # If it player is already the roster member
            msgs.append(f"Player: {member.display_name} is already on `{teamName}`.")
        elif channelData[channel_id]["Players"].get(user_id) == None:
            # if the player is not part of any roster
            channelData[channel_id]["Players"][user_id] = team
            channelData[channel_id]["Rosters"].setdefault(team, []).append(user_id)

            msgs.append(f"Player: {member.display_name} added to `{teamName}`.")
        else:
            # if the player is part of another roster
            oldTeam = channelData[channel_id]["Players"][user_id]
            oldTeamName = channelData[channel_id]["TeamNames"].get(oldTeam,"No Team Name")
            channelData[channel_id]["Players"][user_id] = team
            channelData[channel_id]["Rosters"][oldTeam].remove(user_id)
            channelData[channel_id]["Rosters"].setdefault(team, []).append(user_id)

            msgs.append(f"Player: {member.display_name} moved from `{oldTeamName}` to `{teamName}`.")

    saveJson()

    await interaction.response.send_message("\n".join(msgs), ephemeral=True)

# Config Funtion
# Needs Permission to Run
# Checks if Channel Exists
# Check if player is on team
# Removes player from team if on a team

@app_commands.command(name="player_remove", description="(mod) Remove a Discord User from a Team")
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

# This is for fixing/matching the skipped teams/turn in case of a manual update/change.
@app_commands.command(name="skipped_teams_add", description="(mod) lists a team as skipped. This is for the purposes of manual roster changes")
@app_commands.guilds()
async def addSkipped(  interaction: Interaction, team: str, 
                            team2: str = None,
                            team3: str = None,
                            team4: str = None,
                            team5: str = None,
                            team6: str = None,
                            team7: str = None,
                            team8: str = None,
                          ):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    channel_id = str(interaction.channel_id)

    if channel_id not in channelData:
        await interaction.response.send_message("No Sheet Associated with channel.", ephemeral=True)
        return

    toBeSkipped = [skip for skip in [team, team2, team3, team4, team5, team6, team7, team8] if skip]

    channelData[channel_id]["Skipped"] += toBeSkipped
    channelData[channel_id]["Turn"] += len(toBeSkipped)

    saveJson()

    await interaction.response.send_message(f"added Teams: {', '.join(toBeSkipped)} to skipped list", ephemeral=True)

@app_commands.command(name="players", description="See all the teams and what players are on each team")
@app_commands.checks.cooldown(1, 1, key=lambda i: (i.channel_id))
@app_commands.guilds()
async def getPlayers(interaction: Interaction):
    channel_id = str(interaction.channel_id)
    channel_name = str(interaction.channel)

    if channel_id not in channelData:
        await interaction.response.send_message(f"#`{channel_name}` has no linked spreadsheet")
        return
    
    rosters = channelData[channel_id].get("Rosters", {})
    names = channelData[channel_id].get("TeamNames", {})

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
        
        teamName = names.get(roster, f"Team {roster}: No Name")

        if display_names:
            embed.add_field(name=f"{teamName}", value=", ".join(display_names), inline=False)
        else:
            embed.add_field(name=f"{teamName}", value="It's a ghost town here", inline=False)

    await interaction.response.send_message(embed=embed)

# These are the active skip timers in the Draft Commands.
timers = {}
end_times = {}

# region: Draft Control

@app_commands.command(name="draft_control", description="Control Drafting: pause, resume, refresh, or end the draft/ view the sheet key")
@app_commands.describe(action="Action to perform on the draft")
@app_commands.choices(action=[
    app_commands.Choice(name="View Sheet", value="view"),
    app_commands.Choice(name="Pause Draft", value="pause"),
    app_commands.Choice(name="Resume Draft", value="resume"),
    app_commands.Choice(name="Refresh Draft", value="refresh"),
    app_commands.Choice(name="End Draft", value="kill"),
])
async def draft_control(interaction: Interaction, action: app_commands.Choice[str]):
    if action.value == "pause":
        await pause_draft(interaction)
    elif action.value == "resume":
        await resume_draft(interaction)
    elif action.value == "refresh":
        await refresh_draft(interaction)
    elif action.value == "kill":
        await removeSpreadsheet(interaction)
    elif action.value == "view":
        await getspreadsheet(interaction)
    else:
        await interaction.response.send_message("Invalid action.", ephemeral=True)


# @app_commands.command(name="pause_draft", description="Pause drafting and timers in this channel")
async def pause_draft(interaction: Interaction):

    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    channel_id = str(interaction.channel_id)

    if channel_id in channelData:

        channel = channelData[channel_id]
        channel["Paused"] = True
        saveJson()

        if channel_id in timers:
            timers[channel_id].cancel()
            del timers[channel_id]
            del end_times[channel_id]

        await interaction.response.send_message("Drafting has been paused. Timers are frozen.")
    else:
        await interaction.response.send_message("No Sheet Associated with channel.", ephemeral=True)

# @app_commands.command(name="resume_draft", description="Resume drafting and timers in this channel")
async def resume_draft(interaction: Interaction):

    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    channel_id = str(interaction.channel_id)
    
    if channel_id in channelData:

        channel = channelData[channel_id]
        channel["Paused"] = False
        saveJson()
        if module_callback:
            module_callback(channel_id, channel["spreadsheet"])

        await interaction.response.send_message("Drafting has resumed.")
    else:
        await interaction.response.send_message("Channel not initialized.", ephemeral=True)

# @app_commands.command(name="reload_draft", description="Reload and reimport the data in the draft")
async def refresh_draft(interaction: Interaction):

    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    channel_id = str(interaction.channel_id)
    
    if channel_id in channelData:
        
        if channel_id in timers:
            timers[channel_id].cancel()
            del timers[channel_id]
            del end_times[channel_id]


        channel = channelData[channel_id]

        if module_callback:
            module_callback(channel_id, channel["spreadsheet"])

        await interaction.response.send_message("The Draft has been refreshed.", ephemeral=True)
    else:
        await interaction.response.send_message("Channel not initialized.", ephemeral=True)

# @app_commands.command(name="remove_sheet", description="Removes the sheet and deletes associate information")
# @app_commands.guilds()
async def removeSpreadsheet(interaction: Interaction):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    await interaction.response.defer()

    channel_id = str(interaction.channel_id)
    channel_name = str(interaction.channel)

    if channel_id in channelData:
        del channelData[channel_id]
        saveJson()

    # Updates other modules, Takes longer now that I'm adding more functions
    if module_callback:
        module_callback(channel_id, None)

    await interaction.followup.send(f"#`{channel_name}` has ended the draft", ephemeral=True)



# @app_commands.command(name="get_sheet", description="Get Sheet name")
# @app_commands.guilds()
async def getspreadsheet(interaction: Interaction):

    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    channel_id = str(interaction.channel_id)
    channel_name = str(interaction.channel)

    if channel_id not in channelData:
        msg = f"#`{channel_name}` has no linked spreadsheet"
    else:
        msg = f"#`{channel_name}` is linked to `{channelData[channel_id]['spreadsheet']}`"

    await interaction.response.send_message(msg, ephemeral=True)


# endregion

@app_commands.command(name="turn_info", description= "Shows current turn, draft timer, and skipped players")
@app_commands.checks.cooldown(1, 60, key=lambda i: (i.channel_id))
@app_commands.guilds() 
async def turn_info(interaction: Interaction):
    channel_id = str(interaction.channel_id)
    channel_name = str(interaction.channel)

    if channel_id not in channelData:
        await interaction.response.send_message(f"#`{channel_name}` has no associated draft")
        return
    
    channel = channelData.get(channel_id)
    teamNames = channel["TeamNames"]

    # TIMER
    end_time = end_times.get(channel_id, None)
    if end_time is not None:
        now_real = time.time()
        monotonic = time.monotonic()
        diff = end_time - monotonic
        unix_timestamp = int(now_real + diff)
        timer_text = f"Timer ends <t:{unix_timestamp}:R>"
    else:
        timer_text = "No timer is currently running."

    # TURN
    round,turn = getTurn(channel_id)  # Assuming you store this somewhere
    if round != -1:
        turn = str(turn)
        teamName = teamNames.get(turn, "No Team Name")
        turn_text = f"Round {round+1}; It's **{teamName}**'s turn."
    else:
        turn_text = "No active turn."

    # --- SKIPPED PLAYERS ---
    skipped = channel["Skipped"]
    
    if skipped:
        skippedTeams = []
        skippedDict = Counter(skipped)
        for team, num in skippedDict.items():
            teamName = teamNames.get(team, "No Team Name")
            skippedTeams.append(f"{teamName} has {num} skip(s)")

        skipped_text = "\n".join(skippedTeams)
    else:
        skipped_text = "No Skipped players"

    # --- COMBINE ---
    embed = Embed(title="Turn Information", color=Color.blue())
    embed.add_field(name="Skip Timer", value=timer_text, inline=False)
    embed.add_field(name="Current Round/Turn", value=turn_text, inline=False)
    embed.add_field(name="Skipped Players (they may make up their turn whenever)", value=skipped_text, inline=False)

    await interaction.response.send_message(embed=embed)
