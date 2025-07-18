from bisect import bisect_left
import json
from discord import Interaction,Embed
from discord import app_commands
import asyncio
import GoogleInteraction as ggSheet
import ChannelServer


# Import list of Pokemon
with open("pokemon.json", "r") as f:
    pokemon_data = json.load(f)

pokemon_names = sorted(pokemon_data.keys())
# Key for searching
pokemon_names_lower = [name.lower() for name in pokemon_names]

# Testing Pokemon Choosing Command
# Autocomplete function
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

# Skip Helper Function.
def skip(channel_id: str):
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
    
# Manually end timer
def end_timer(channel_id: str, team: str):
    key = (channel_id, team)
    if key in timers:
        timers[key].cancel()
        del timers[key]


# Starting the Drafting Process
# We need to check that the channel has a sheet associated
# We need to check that the player has an associated team
# We need to check it is the player's turn
# We need to check that they have enough points + enough slots + non duplicate.

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
    channel = ChannelServer.channelData.get(channel_id, None)
    # There is slightly different incrementing if the player is retaking a skipped turn
    skipped = False

    # Players are allowed to draft if they have been either skipped or it is their turn
    # if it is your turn, you can draft
    if team != turn:
        #  if you have a skip, use skipped turn to draft
        if team in channel["Skipped"]:
            skipped = True
            # channel["Skipped"].remove(team)
            # turn -= 1
        else:
            await interaction.response.send_message(f"It's not your turn! It's Team {turn}'s turn.")
            return

    # Check if on Draft Board
    pickCost = ggSheet.pointDict[channel_id].get(pokemon,None)

    if not pickCost or pickCost == 99:
        await interaction.response.send_message(f"You can't draft {pokemon}!")
        return

    # Need to access gg sheets so we need thinking time
    await interaction.response.defer(thinking=True)
    
    (nextSlot, pointTotal) = ggSheet.getNextSlot(spreadSheet, channel_id, team)
    
    # Check Points left
    pointsLeft = ggSheet.pointDict[channel_id]["Total"] - pointTotal

    # Check if slots open
    if nextSlot == -1:
        await interaction.followup.send("You can't draft any more Pokemon!")
        return
    # Check if you have enough points
    if pointsLeft < pickCost:
        await interaction.followup.send(f"You only have {pointsLeft} points left! You can't draft {pokemon}.")
        return
    # Check if someone else drafted the mon
    drafted = ggSheet.readFullRoster(spreadSheet, 16, 11)
    if pokemon in drafted:
        await interaction.followup.send(f"Someone already drafted {pokemon}.")
        return

    pointsLeft -= pickCost

    ggSheet.addPokemon(channel_id, team, nextSlot, pokemon)
            
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

# Timer and Automatic Skipping
timers = {}

async def start_timer(interaction: Interaction, timeout = 10):
    
    channel_id = str(interaction.channel_id)
    
    team = getTurn(channel_id)[1]
    # End Previous Timer in the Channel 
    key = (channel_id, team)
    if key in timers:
        timers[key].cancel()
    # Define a timer 
    async def timer():
        try:
            await asyncio.sleep(timeout)
            await auto_skip(interaction)
        except asyncio.CancelledError:
            print("Timer cancelled cleanly.")
            pass
        except Exception as e:
            print(f"Timer Error: {e}")
            raise
    # Start the timer
    timers[key] = asyncio.create_task(timer())

# Manual Skip
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

# Automatically Skip
async def auto_skip(interaction: Interaction):
    
    channel_id = str(interaction.channel_id)
    team = skip(channel_id)

    # In case the team has no players or has not been initialized
    skippedPlayers = ChannelServer.channelData[channel_id]["Rosters"].get(team, [])
    mentions = " ".join(f"<@{user_id}>" for user_id in skippedPlayers)

    await interaction.channel.send(f"Team {team}: {mentions} Skipped. Faster Next Time Stupid")
    await start_timer(interaction)

@app_commands.command(name="stop_timer",description="Skip the Current Player (mod)")
@app_commands.guilds()
async def stop_timer(interaction: Interaction):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return
    
    channel_id = str(interaction.channel_id)
    team = getTurn(channel_id)[1]

    end_timer(channel_id, team)
    await asyncio.sleep(0)

    await interaction.response.send_message("Timer has been stopped.")


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

# adds 
def addPick(channel_id: str, team: str, pick: str, backup: str = None, backup2: str = None):
    picks = pickData[channel_id]["Rosters"].get(team, None)
    if picks == None:
        pickData[channel_id]["Rosters"][team] = []
        picks = pickData[channel_id]["Rosters"][team]
    picks.append({
        "Left_Pick": pick,
        "Backup_1": backup,
        "Backup_2": backup2
    })
    savePicksJson()


@app_commands.command(name="leave_pick",description="leave a pick")
@app_commands.describe(pokemon="Pick a Pokemon")
@app_commands.autocomplete(pokemon=pokemon_autocomplete)
@app_commands.guilds()
async def leave_pick(interaction: Interaction, pokemon: str):
    
    # Check For Errors before starting the draft process
    # Check actual pokemon
    if pokemon not in pokemon_names:
        await interaction.response.send_message("Please pick an actual Pokemon...", ephemeral=True)
        return

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
    addPick(channel_id, team, pokemon)
    await interaction.response.send_message(f"You left the following pick(s): {pokemon}", ephemeral=True)


    


