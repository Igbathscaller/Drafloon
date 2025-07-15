from bisect import bisect_left
import json
from discord import Interaction,Embed
from discord import app_commands
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

# Slash command with autocomplete
@app_commands.command(name="choose",description="Choose a Pokémon")
@app_commands.describe(pokemon="Start typing a name")
@app_commands.autocomplete(pokemon=pokemon_autocomplete)
@app_commands.guilds()
async def choose(interaction: Interaction, pokemon: str):
        
    image_url = pokemon_data.get(pokemon)
    try:
        embed = Embed(title = f"You chose {pokemon}!")
        embed.set_image(url=image_url)
        await interaction.response.send_message("", embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"You chose {pokemon}!")
        print(f"Error drafting: {e}")

# Starting the Drafting Process
# We need to check that the channel has a sheet associated
# We need to check that the player has an associated team
# We need to check it is the player's turn
# We need to check that they have enough points + enough slots + non duplicate.

@app_commands.command(name="draft",description="draft a pokemon")
@app_commands.describe(pokemon="Start typing a name")
@app_commands.autocomplete(pokemon=pokemon_autocomplete)
@app_commands.guilds()
async def draft(interaction: Interaction, pokemon: str):
    
    # Check For Errors before starting the draft process
    # Check actual pokemon
    if pokemon not in pokemon_names:
        await interaction.response.send_message("Please pick an actual Pokemon...", ephemeral=True)
        return

    channel_id = interaction.channel_id

    spreadSheet = ggSheet.spreadDict.get(str(channel_id), None)

    # Check Spreadsheet
    if not spreadSheet:
        await interaction.response.send_message("This Channel has no Associated Spreadsheet", ephemeral=True)
        return

    team = ChannelServer.getTeam(str(channel_id), str(interaction.user.id))

    # Check Team
    if not team:
        await interaction.response.send_message("You are not on a team", ephemeral=True)
        return
    
    # Check if on Draft Board
    pickCost = ggSheet.pointDict[str(channel_id)].get(pokemon,None)

    if not pickCost or pickCost == 99:
        await interaction.response.send_message(f"You can't draft {pokemon}!")
        return

    # Need to access gg sheets so we need thinking time
    await interaction.response.defer(thinking=True)
    
    team = int(team)

    (nextSlot, pointTotal) = ggSheet.getNextSlot(spreadSheet, str(channel_id), team)
    
    # Check Points left
    pointsLeft = ggSheet.pointDict[str(channel_id)]["Total"] - pointTotal

    # Check if slots open
    if nextSlot == -1:
        await interaction.followup.send("You can't draft any more Pokemon!")
        return
    # Check if you have enough points
    if pointsLeft < pickCost:
        await interaction.followup.send(f"You only have {pointsLeft} points left! You can't draft {pokemon}.")
        return
    # Check if someone else drafted the mon
    drafted = ggSheet.readFullRoster(spreadSheet,16,11)
    if pokemon in drafted:
        await interaction.followup.send(f"Someone already drafted {pokemon}.")
        return

    pointsLeft -= pickCost

    ggSheet.addPokemon(spreadSheet, team, nextSlot, pokemon)
    
    image_url = pokemon_data.get(pokemon)
    try:
        embed = Embed(title = f"You drafted {pokemon}. You have {pointsLeft} points left!")
        embed.set_image(url=image_url)
        await interaction.followup.send("", embed=embed)
    except Exception as e:
        await interaction.followup.send(f"You drafted {pokemon}. You have {pointsLeft} points left!")
        print(f"Error drafting: {e}")

