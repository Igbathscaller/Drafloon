from bisect import bisect_left
import json
from discord import Interaction,Embed,Color
from discord import app_commands
import asyncio
import GoogleInteraction as ggSheet
import ChannelServer

#region: Loading the Data at Startup + Functions for handling data
#list of Pokemon
with open("pokemon.json", "r") as f:
    pokemon_data = json.load(f)

pokemon_names = sorted(pokemon_data.keys())
# Key for searching
pokemon_names_lower = [name.lower() for name in pokemon_names]

# Load The Json Data
def loadPicksJson():
    try:
        with open("Picks.json", "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        data = {}

    return data

pickData = loadPicksJson()

# Save ChannelData to Json
def savePicksJson():
    with open("Picks.json", "w") as f:
        json.dump(pickData, f, indent=4)

# Whenever you want to add a new channel to the variable you can.
def initializeChannel(channel_id):
    pickData[channel_id] = {
        "Rosters": {}
    }
    savePicksJson()

# Whenever they are updating the channel_id, only initialize the Channel if it doesn't exist
def loadPicks(channel_id: str):
    if channel_id not in pickData:
        initializeChannel(channel_id)

# Timer and Automatic Skipping
# There should only be one timer per channel_id
timers = {}

#endregion

# Autocomplete function (helper function for limiting client options)
async def pokemon_autocomplete(interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:
    if not current:
            return [app_commands.Choice(name=name, value=name) for name in ["Toxapex", "Ampharos"]]

    current = current.lower()
    results = []

    # Use bisect to find the index of the first valid term
    index = bisect_left(pokemon_names_lower, current)

    # Pokemon Names that start with the current input
    while index < len(pokemon_names_lower):
        name_lower = pokemon_names_lower[index]
        name = pokemon_names[index]

        if name_lower.startswith(current):
            results.append(name)
            if len(results) >= 11:
                break
        else:
            break  # No more matches
        index += 1

    # Optionally fill with matches if < 10
    if len(results) < 11:
        for name, name_lower in zip(pokemon_names, pokemon_names_lower):
            if (
                current in name_lower
                and not name_lower.startswith(current)
                and name not in results
            ):
                results.append(name)
                if len(results) >= 11:
                    break

    return [app_commands.Choice(name=name, value=name) for name in results]

# Check whose turn it is
def getTurn(channel_id: str):
    '''
    returns: (str name, int points): 
        name (str): The Pokémon's name.
        points (int): The point value of the Pokémon.
    '''
    channel = ChannelServer.channelData[channel_id]

    turn = channel["Turn"]
    playerCount = channel["Player Count"]
    
    # Turns 0-15 are round 1
    round = turn // playerCount
    
    # the reverse turns are odd (since it is 0-indexed)
    if round % 2:
        return (round, playerCount - turn % playerCount)
    # On the even turns. 
    else:
        return (round, turn % playerCount + 1)

#region: Adding Picks and Viewing them

# adds pick to the roster
def addPick(channel_id: str, team: str, pick: str, backup: str = None, backup2: str = None):
    picks = pickData[channel_id]["Rosters"].get(team, None)
    if picks == None:
        pickData[channel_id]["Rosters"][team] = []
        picks = pickData[channel_id]["Rosters"][team]
    picks.append({
        "Main": pick,
        "Backup_1": backup,
        "Backup_2": backup2
    })
    savePicksJson()

def getPicks(channel_id: str, team: str):
    picks = pickData[channel_id]["Rosters"].get(team, None)
    if picks == None:
        return None
    else:
        return picks

@app_commands.command(name="leave_pick",description="Leave a Pick Privately with the Bot")
@app_commands.describe(pokemon = "Pick a Pokemon", 
                       backup_1 = "If your main choice was sniped", 
                       backup_2 = "If your backup was also sniped")
@app_commands.autocomplete(pokemon=pokemon_autocomplete, backup_1=pokemon_autocomplete, backup_2=pokemon_autocomplete)
@app_commands.guilds()
async def leave_pick(interaction: Interaction, pokemon: str, backup_1: str = None, backup_2: str = None):
    
    # Check if it is actual pokemon (in the list of choices)
    if pokemon not in pokemon_names:
        await interaction.response.send_message("Please pick an actual Pokemon...", ephemeral=True)
        return
    
    if (backup_1 and backup_1 not in pokemon_names) or (backup_2 and backup_2 not in pokemon_names):
        await interaction.response.send_message("Please pick actual Pokemon...", ephemeral=True)
        return

    channel_id = str(interaction.channel_id)

    # Checks if the channel has been initialized
    channel = pickData.get(channel_id, None)
    if not channel:
        await interaction.response.send_message("No associated sheet in channel", ephemeral=True)

    # Team of the person leaving the Draft Pick
    team = ChannelServer.getTeam(channel_id, str(interaction.user.id))

    # Check Team
    if not team:
        await interaction.response.send_message("You are not on a Team", ephemeral=True)
        return

    # Add the pick to the team
    addPick(channel_id, team, pokemon, backup_1, backup_2)
    await interaction.response.send_message(f"You left the following pick(s): {pokemon}", ephemeral=True)

@app_commands.command(name="view_picks",description="View Your Picks Privately")
@app_commands.guilds()
async def view_picks(interaction: Interaction):

    channel_id = str(interaction.channel_id)

    # Checks if the channel has been initialized
    channel = pickData.get(channel_id, None)
    if not channel:
        await interaction.response.send_message("No associated sheet in channel", ephemeral=True)

    # Team of the person making the Draft Pick
    team = ChannelServer.getTeam(channel_id, str(interaction.user.id))

    # Check Team
    if not team:
        await interaction.response.send_message("You are not on a Team", ephemeral=True)
        return

    # Add the pick to the team
    picks = getPicks(channel_id, team)

    embed = Embed(
        title=f"Team {team}",
        color = Color.brand_green()
    )

    text = ["```"]
    for i in range(len(picks)):
        pick = picks[i]
        main = pick["Main"] or "None"
        b1   = pick["Backup_1"]
        b2   = pick["Backup_2"]
        text.append(f"Pick {i+1}: {main}")
        if b1:
            text.append(f"\t└ Backup 1: {b1}")
        if b2:
            text.append(f"\t└ Backup 2: {b2}")
    text.append("```")

    embed.add_field(
        name="Your Left Picks",
        value="\n".join(text),
        inline=False
    )

    await interaction.response.send_message(embed=embed,ephemeral=True)
    # await interaction.response.send_message(embed=embed)

#endregion

#region: Timer Related Functions

# Starting Timer
async def start_timer(interaction: Interaction, timeout = 10):
    
    channel_id = str(interaction.channel_id)

    # End Previous Timer in the Channel 
    channel_id
    if channel_id in timers:
        timers[channel_id].cancel()
    
    # Define a timer 
    async def timer():
        try:
            await asyncio.sleep(timeout)
            await auto_pick(interaction)
        except asyncio.CancelledError:
            print("Timer cancelled cleanly.")
            pass
        except Exception as e:
            print(f"Timer Error: {e}")
            raise
    # Start the timer
    timers[channel_id] = asyncio.create_task(timer())

# End Timer
def end_timer(channel_id: str):
    # Ends the timer in the channel
    if channel_id in timers:
        timers[channel_id].cancel()
        del timers[channel_id]

# Stop Timer Command
@app_commands.command(name="stop_timer",description="Skip the Current Player (mod)")
@app_commands.guilds()
async def stop_timer(interaction: Interaction):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return
    
    channel_id = str(interaction.channel_id)

    end_timer(channel_id)
    await asyncio.sleep(0)

    await interaction.response.send_message("Timer has been stopped.")
#endregion

#region: Skip Related Function

# Skip Helper Function.
def skip(channel_id: str) -> str:
    '''
    returns:
        team (str): the skipped team
    '''
    channel = ChannelServer.channelData.get(channel_id, None)
    # if the channel is not valid
    if not channel:
        return None
    else:
        team = getTurn(channel_id)[1]
        channel["Skipped"].append(team)
        channel["Turn"]+=1
        ChannelServer.saveJson()
        return str(team)

# Automatically Skip
async def auto_skip(interaction: Interaction):
    
    channel_id = str(interaction.channel_id)
    team = skip(channel_id)

    # In case the team has no players or has not been initialized
    skippedPlayers = ChannelServer.channelData[channel_id]["Rosters"].get(team, [])
    mentions = " ".join(f"<@{user_id}>" for user_id in skippedPlayers)

    await interaction.channel.send(f"Team {team}: {mentions} Skipped. Faster Next Time Stupid")
    await start_timer(interaction)

# Manual Skip Command
@app_commands.command(name="skip",description="Skip the Current Player (mod)")
@app_commands.guilds()
async def skip_player(interaction: Interaction):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return
    
    channel_id = str(interaction.channel_id)
    team = skip(channel_id)

    if not team:
        await interaction.response.send_message(f"This Channel has no Associated Sheet")
    else:
        # In case the team has no players or has not been initialized
        skippedPlayers = ChannelServer.channelData[channel_id]["Rosters"].get(team, [])
        mentions = " ".join(f"<@{user_id}>" for user_id in skippedPlayers)
        await interaction.response.send_message(f"Team {team}: {mentions} Skipped.")
        # Start Timer at the end of each action. Only activate timer if we know it'll work.
        await start_timer(interaction)


#endregion

#region: Drafting/Updating the Sheet

# updates Roster directly given that the pokemon is a valid choice, otherwise returns false
async def addToRoster(channel_id: str, pokemon: str, team: int, nextSlot: int, pointsLeft: int, drafted: set):
    '''
    returns: (success: bool, result: str | int)
        success (bool): if adding to Roster was sucessful
        result (str): error message
        result (int): points left
    '''

    # Check if on Draft Board
    pickCost = ggSheet.pointDict[channel_id].get(pokemon,None)

    if not pickCost or pickCost == 99:
        # await interaction.response.send_message(f"You can't draft {pokemon}!")
        return (False, f"You can't draft {pokemon}!")

    # Check if slots open
    if nextSlot == -1:
        # await interaction.followup.send("You can't draft any more Pokemon!")
        return (False, "You can't draft any more Pokemon!")
    # Check if you have enough points
    if pointsLeft < pickCost:
        # await interaction.followup.send(f"You only have {pointsLeft} points left! You can't draft {pokemon}.")
        return (False, f"You only have {pointsLeft} points left! You can't draft {pokemon}.")
    
    # Check if someone else drafted the mon
    if pokemon in drafted:
        # await interaction.followup.send(f"Someone already drafted {pokemon}.")
        return (False, f"Someone already drafted {pokemon}.")


    ggSheet.addPokemon(channel_id, team, nextSlot, pokemon)
    pointsLeft -= pickCost
    return (True, pointsLeft)

# Manual Draft Command
@app_commands.command(name="draft",description="draft a pokemon")
@app_commands.describe(pokemon="Pick a Pokemon")
@app_commands.autocomplete(pokemon=pokemon_autocomplete)
@app_commands.guilds()
async def draft(interaction: Interaction, pokemon: str):
    
    # Check For Errors before starting the draft process
    # Check actual pokemon
    if pokemon not in pokemon_names:
        await interaction.response.send_message("Please pick an actual Pokemon...", ephemeral=True)
        return

    channel_id = str(interaction.channel_id)

    channel = ChannelServer.channelData.get(channel_id, None)
    spreadSheet = ggSheet.spreadDict.get(channel_id, None)

    # Check Spreadsheet
    if not spreadSheet:
        await interaction.response.send_message("This Channel has no Associated Spreadsheet", ephemeral=True)
        return
    
    # Team of the person making the Draft Pick
    team = ChannelServer.getTeam(channel_id, str(interaction.user.id))

    # Check Team
    if not team:
        await interaction.response.send_message("You are not on a Team", ephemeral=True)
        return
    
    ## Check if allowed to draft
    # Turn gives you the team depending on turn number (aka whose turn it is)
    team = int(team)
    (round, turn) = getTurn(channel_id) 
    # There is slightly different incrementing if the player is retaking a skipped turn
    skipped = False

    # Players are allowed to draft if they have been either skipped or it is their turn
    # if it is your turn, you can draft
    if team != turn:
        #  if you have a skip, use skipped turn to draft
        if team in channel["Skipped"]:
            skipped = True
        else:
            await interaction.response.send_message(f"It's not your turn! It's Team {turn}'s turn.")
            return
    
    # Need to access gg sheets so we need thinking time
    await interaction.response.defer(thinking=True)

    drafted = ggSheet.readFullRoster(spreadSheet, 16, 11)
    nextSlot, pointTotal = ggSheet.getNextSlot(spreadSheet, channel_id, team)
    pointsLeft = ggSheet.pointDict[channel_id]["Total"] - pointTotal

    (success, output) = await addToRoster(channel_id, pokemon, team, nextSlot, pointsLeft, drafted)

    if not success:
        # Send Error message on failed draft
        await interaction.followup.send(output)
        return
    else:
        # otherwise save the number of points left
        pointsLeft = output

    # If it is a skip turn, let them take their skipped turn
    if skipped:
        channel["Skipped"].remove(team)
    # Otherwise increment the channel order
    else:
        channel["Turn"] += 1
    
    ChannelServer.saveJson()
    
    image_url = pokemon_data.get(pokemon)
    try:
        embed = Embed(title = f"You drafted {pokemon} for Round {round +1}. You have {pointsLeft} points left!")
        embed.set_image(url=image_url)
        await interaction.followup.send("", embed=embed)
    except Exception as e:
        await interaction.followup.send(f"You drafted {pokemon} for Round {round +1}. You have {pointsLeft} points left!")
        print(f"Error drafting: {e}")
    # Start Timer at the end of each action
    await start_timer(interaction)

# Automatic Draft Function
async def auto_pick(interaction: Interaction):
    channel_id = str(interaction.channel_id)
    channel = ChannelServer.channelData.get(channel_id, None)
    pickList = pickData.get(channel_id, None)
    
    spreadSheet = ggSheet.spreadDict.get(channel_id, None)

    # Check Spreadsheet
    if not spreadSheet:
        await interaction.response.send_message("This Channel has no Associated Spreadsheet", ephemeral=True)
        return

    # Collect the team and turn
    (round, team) = getTurn(channel_id)

    picks = pickList["Rosters"].get(str(team), None)

    # If there are no picks, we will autoskip them
    if not picks:
        await auto_skip(interaction)
        return
    
    # Get the Pokemon and start the draft process
    drafted = ggSheet.readFullRoster(spreadSheet, 16, 11)
    nextSlot, pointTotal = ggSheet.getNextSlot(spreadSheet, channel_id, team)
    pointsLeft = ggSheet.pointDict[channel_id]["Total"] - pointTotal
    pokemon = None

    for pick in picks:
        success, result = await addToRoster(channel_id, pick["Main"], team, nextSlot, pointsLeft, drafted)
        pickIndex += 1
        if success:
            pointsLeft = result
            pokemon = pick["Main"]
            break
        elif pick["Backup_1"]:
            (success, result) = await addToRoster(channel_id, pick["Backup_1"], team, nextSlot, pointsLeft, drafted)
            pointsLeft = result
            pokemon = pick["Backup_1"]
            break
        elif pick["Backup_2"]:
            (success, result) = await addToRoster(channel_id, pick["Backup_2"], team, nextSlot, pointsLeft, drafted)
            pointsLeft = result
            pokemon = pick["Backup_2"]
            break
    # Delete the pick after it has been utilized
    del picks[:pickIndex]
    print(picks)
    savePicksJson()

    if not pokemon:
        await interaction.channel.send("No draftable picks left")
        await auto_skip(interaction)
        return

    # In case the team has no players or has not been initialized
    autoPlayers = ChannelServer.channelData[channel_id]["Rosters"].get(team, [])
    mentions = " ".join(f"<@{user_id}>" for user_id in autoPlayers)
    
    channel["Turn"]+=1
    ChannelServer.saveJson()

    image_url = pokemon_data.get(pokemon)
    try:
        embed = Embed(title = f"Team {team}: {mentions} drafted {pokemon} for Round {round +1}. You have {pointsLeft} points left!")
        embed.set_image(url=image_url)
        await interaction.followup.send("", embed=embed)
    except Exception as e:
        await interaction.followup.send(f"You drafted {pokemon} for Round {round +1}. You have {pointsLeft} points left!")
        print(f"Error drafting: {e}")
    # Start Timer at the end of each action
    await start_timer(interaction)    

#endregion

