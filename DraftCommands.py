from bisect import bisect_left
import json
import time
from discord import Interaction,Embed,app_commands

import asyncio
import GoogleInteraction as ggSheet
import ChannelServer

pick_time = 30 # Time in Seconds before auto-pickings
skip_time = 90 # Time in Seconds before auto-skipping

#region: Loading the Data at Startup + Functions for handling data

#list of Pokemon
with open("pokemon.json", "r") as f:
    pokemon_data = json.load(f)

pokemon_names = sorted(pokemon_data.keys())
# Key for searching
pokemon_names_lower = [name.lower() for name in pokemon_names]

# # pickData
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
    # This is the removal if statement
    # If the spreadsheet doesn't exist in spreadDict, I want it cleared from pickData
    if channel_id not in ggSheet.spreadDict:
        pickData.pop(channel_id, None)
        savePicksJson()
        return

    if channel_id not in pickData:
        initializeChannel(channel_id)

#endregion


# Autocomplete function (helper function for limiting client options)
async def pokemon_autocomplete(interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:
    if not current:
            return [app_commands.Choice(name=name, value=name) for name in ["Toxapex", "Ampharos", "Blissey", "Gliscor", "Dondozo", "Alomomola", "Emolga", "Pikachu", "Plusle"]]

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


#region: Timer Related Functions

# Starts the Pick Timer
async def start_pick_timer(interaction: Interaction):
    
    channel_id = str(interaction.channel_id)

    # End Previous Timer in the Channel 
    if channel_id in ChannelServer.timers:
        ChannelServer.timers[channel_id].cancel()
    
    # Define the timer before auto pickking
    async def timer():
        try:
            await asyncio.sleep(pick_time)
            await auto_pick(interaction)
        except asyncio.CancelledError:
            # print("Timer cancelled")
            pass
        except Exception as e:
            print(f"Timer Error: {e}")
            raise
    # Start the timer
    ChannelServer.timers[channel_id] = asyncio.create_task(timer())
    # Compute and save end time (include skip time as well)
    end_time = time.monotonic() + pick_time + skip_time
    ChannelServer.end_times[channel_id] = end_time

# Starts the Skip Timer (meant for after the pick timer runs)
async def start_skip_timer(interaction: Interaction):
    
    channel_id = str(interaction.channel_id)

    # End Previous Timer in the Channel 
    if channel_id in ChannelServer.timers:
        ChannelServer.timers[channel_id].cancel()
    
    # Define a timer 
    async def timer():
        try:
            await asyncio.sleep(skip_time)
            await auto_skip(interaction)
        except asyncio.CancelledError:
            # print("Skip Timer cancelled")
            pass
        except Exception as e:
            print(f"Timer Error: {e}")
            raise
    # Start the timer
    ChannelServer.timers[channel_id] = asyncio.create_task(timer())
    # Compute and save end time (include skip time as well)
    end_time = time.monotonic() + skip_time
    ChannelServer.end_times[channel_id] = end_time


# End Timer
def end_timer(channel_id: str):
    # Ends the timer in the channel
    if channel_id in ChannelServer.timers:
        ChannelServer.timers[channel_id].cancel()
        del ChannelServer.timers[channel_id]
        del ChannelServer.end_times[channel_id]

# Stop Timer Command
@app_commands.command(name="stop_timer", description="(mod) Stops the skip timer")
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
        team = ChannelServer.getTurn(channel_id)[1]
        channel["Skipped"].append(str(team))
        channel["Turn"]+=1
        ChannelServer.saveJson()
        return str(team)

# Automatically Skip
async def auto_skip(interaction: Interaction):
    
    channel_id = str(interaction.channel_id)
    team = skip(channel_id)

    
    teamName = ChannelServer.channelData[channel_id]["TeamNames"].get(team, "No Team Name")
    # In case the team has no players or has not been initialized
    skippedPlayers = ChannelServer.channelData[channel_id]["Rosters"].get(team, [])
    skippedMentions = " ".join(f"<@{user_id}>" for user_id in skippedPlayers)
    await interaction.channel.send(f"`{teamName}`: {skippedMentions} Skipped. Leave Picks Next Time")
    
    # Mention the next players
    round, nextMentions = mention_team_players(channel_id)

    if round < 8:
        await interaction.channel.send("Next Pick: " + nextMentions)

    # After Player has been skipped, start the skip timer
    if round > 0 and round < 8:
        await start_pick_timer(interaction)
    else:
        end_timer(channel_id)

# Manual Skip Command
@app_commands.command(name="skip",description="(mod) Skips the Current Player")
@app_commands.guilds()
async def skip_player(interaction: Interaction):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return
    
    channel_id = str(interaction.channel_id)
    team = skip(channel_id)

    if not team:
        await interaction.response.send_message("This Channel has no Associated Spreadsheet")
    else:
        teamName = ChannelServer.channelData[channel_id]["TeamNames"].get(team, "No Team Name")
        # In case the team has no players or has not been initialized
        skippedPlayers = ChannelServer.channelData[channel_id]["Rosters"].get(team, [])
        skippedMentions = " ".join(f"<@{user_id}>" for user_id in skippedPlayers)
        await interaction.response.send_message(f"`{teamName}`: {skippedMentions} Skipped.")
        
        # Mention the next players
        round, nextMentions = mention_team_players(channel_id)
        if round < 8:
            await interaction.channel.send("Next Pick: " + nextMentions)
        
        # Start Timer at the end of each action. 
        # Only activate timer if the draft is not paused when skipping
        if not ChannelServer.channelData[channel_id]["Paused"] and round > 0 and round < 8:
            await start_pick_timer(interaction)
        else:
            end_timer(channel_id)


#endregion


#region: Drafting/Updating the Sheet

# updates Roster directly given that the pokemon is a valid choice, otherwise returns false
async def addToRoster(channel_id: str, pokemon: str, team: int, nextSlot: int, pointsLeft: int):
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
    drafted = ggSheet.draftedData[channel_id]
    if pokemon in drafted:
        # await interaction.followup.send(f"Someone already drafted {pokemon}.")
        return (False, f"Someone already drafted {pokemon}.")


    ggSheet.addPokemon(channel_id, team, nextSlot, pokemon)
    drafted.add(pokemon)
    pointsLeft -= pickCost
    return (True, pointsLeft)

# Manual Draft Command
@app_commands.command(name="draft",description= "Drafts a Pokemon to your team if it is valid")
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
    

    # Check Paused
    if channel["Paused"]:
        await interaction.response.send_message("This Channel's Draft has been paused", ephemeral=True)
        return


    # Team of the person making the Draft Pick
    team = ChannelServer.getTeam(channel_id, str(interaction.user.id))

    # Check Team
    if not team:
        await interaction.response.send_message("You are not on a Team", ephemeral=True)
        return
    
    teamName = channel["TeamNames"].get(team, "No Team Name")

    ## Check if allowed to draft
    # Turn gives you the team depending on turn number (aka whose turn it is)
    team = int(team)
    (round, turn) = ChannelServer.getTurn(channel_id) 
    # There is slightly different incrementing if the player is retaking a skipped turn
    skipped = False

    # Players are allowed to draft if they have been either skipped or it is their turn
    # if it is your turn, you can draft
    if team != turn:
        #  if you have a skip, use skipped turn to draft
        if str(team) in channel["Skipped"]:
            skipped = True
        else:
            turnName = channel["TeamNames"].get(str(turn), "No Team Name")
            await interaction.response.send_message(f"It's not your turn! It's {turnName}'s turn.")
            return
    
    # Need to access gg sheets so we need thinking time
    await interaction.response.defer(thinking=True)

    nextSlot, pointTotal = ggSheet.getNextSlot(spreadSheet, channel_id, team)
    pointsLeft = ggSheet.pointDict[channel_id]["Total"] - pointTotal

    (success, output) = await addToRoster(channel_id, pokemon, team, nextSlot, pointsLeft)

    if not success:
        # Send Error message on failed draft
        await interaction.followup.send(output)
        return
    else:
        # otherwise save the number of points left
        pointsLeft = output

    # If it is a skip turn, let them take their skipped turn
    if skipped:
        channel["Skipped"].remove(str(team))
    # Otherwise increment the channel order
    else:
        channel["Turn"] += 1
    
    ChannelServer.saveJson()
    
    round, nextMentions = mention_team_players(channel_id)

    image_url = pokemon_data.get(pokemon)
    try:
        embed = Embed(title = f"{teamName} drafted {pokemon} for Round {round +1}. You have {pointsLeft} points left!")
        embed.set_image(url=image_url)
        await interaction.followup.send("", embed=embed)
    except Exception as e:
        await interaction.followup.send(f"`{teamName}` drafted {pokemon} for Round {round +1}. You have {pointsLeft} points left!")

        print(f"Error drafting: {e}")
    # Start Timer at the end of each action
    if skipped:
        return
    if round < 8:
        await interaction.channel.send("Next Pick: " + nextMentions)

    # No Timers Start on the First Round
    if round > 0 and round < 8:
        await start_pick_timer(interaction)
    else:
        end_timer(channel_id)


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
    (round, team) = ChannelServer.getTurn(channel_id)

    picks = pickList["Rosters"].get(str(team), None)
    teamName = channel["TeamNames"].get(str(team), "No Name")

    # If there are no picks, we will autoskip them
    if not picks:
        await interaction.channel.send(f"`{teamName}` left no picks/ran out of picks")
        await start_skip_timer(interaction)
        return
    
    # Get the Pokemon and start the draft process
    nextSlot, pointTotal = ggSheet.getNextSlot(spreadSheet, channel_id, team)
    pointsLeft = ggSheet.pointDict[channel_id]["Total"] - pointTotal
    pokemon = None
    pickIndex = 0

    for pick in picks:
        # Test Main
        success, result = await addToRoster(channel_id, pick["Main"], team, nextSlot, pointsLeft)
        pickIndex += 1
        if success:
            pointsLeft = result
            pokemon = pick["Main"]
            break
        # if backup, test backup
        elif pick["Backup_1"]:
            success, result = await addToRoster(channel_id, pick["Backup_1"], team, nextSlot, pointsLeft)
            if success:
                pointsLeft = result
                pokemon = pick["Backup_1"]
                break
        # if backup, test backup
        elif pick["Backup_2"]:
            (success, result) = await addToRoster(channel_id, pick["Backup_2"], team, nextSlot, pointsLeft)
            if success:
                pointsLeft = result
                pokemon = pick["Backup_2"]
                break

    # Delete the pick after it has been utilized
    del picks[:pickIndex]
    print(picks)
    savePicksJson()

    if not pokemon:
        await interaction.channel.send(f"None of `{teamName}`'s picks left were draftable")
        await start_skip_timer(interaction)
        return 

    # In case the team has no players or has not been initialized
    round, nextMentions = mention_team_players(channel_id)

    
    channel["Turn"]+=1
    ChannelServer.saveJson()

    image_url = pokemon_data.get(pokemon)
    try:
        embed = Embed(title = f"`{teamName}` drafted {pokemon} for Round {round +1}. You have {pointsLeft} points left!")
        embed.set_image(url=image_url)
        await interaction.channel.send("", embed=embed)

    except Exception as e:
        await interaction.channel.send(f"`{teamName}` drafted {pokemon} for Round {round +1}. You have {pointsLeft} points left!")
        print(f"Error drafting: {e}")
    
    # Start Timer at the end of each action
    if round < 8:
        await interaction.channel.send("Next Pick: " + nextMentions)

    # No Timers Start on the First Round
    if round > 0 and round < 8:
        await start_pick_timer(interaction)
    else:
        end_timer(channel_id)

#endregion

#region: Mentioning the next players

def mention_team_players(channel_id: str):
    if channel_id not in ChannelServer.channelData:
        return ""

    round,team = ChannelServer.getTurn(channel_id)
    team = str(team)

    if round == -1:
        return ""

    teamName = ChannelServer.channelData[channel_id]["TeamNames"].get(team, "No Team Name")
    roster = ChannelServer.channelData[channel_id]["Rosters"].get(team, [])

    mentions = [f"<@{user_id}>" for user_id in roster]

    return round, f"`{teamName}`; {', '.join(mentions)}"


#endregion