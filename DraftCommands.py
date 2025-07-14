import bisect
import discord
from discord import app_commands
import GoogleInteraction as ggSheet
import json

# Import list of Pokemon
with open("pokemon.json", "r") as f:
    pokemon_data = json.load(f)

pokemon_names = sorted(pokemon_data.keys())
# Key for searching
pokemon_names_lower = [name.lower() for name in pokemon_names]


# Testing Pokemon Choosing Command
# Autocomplete function
async def pokemon_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    if not current:
            return [app_commands.Choice(name=name, value=name) for name in ["Toxapex", "Ampharos"]]

    current = current.lower()
    results = []

    # Use bisect to find the index of the first valid term
    index = bisect.bisect_left(pokemon_names_lower, current)

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
async def choose(interaction: discord.Interaction, pokemon: str):
        
    image_url = pokemon_data.get(pokemon)
    try:
        embed = discord.Embed(title = f"You chose {pokemon}!")
        embed.set_image(url=image_url)
        await interaction.response.send_message("", embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"You chose {pokemon}!")
        print(f"Error drafting: {e}")

# Starting the Drafting Process
@app_commands.command(name="draft",description="draft a pokemon")
@app_commands.describe(team="Your Team Number", pokemon="Start typing a name")
@app_commands.autocomplete(pokemon=pokemon_autocomplete)
@app_commands.guilds()
async def draft(interaction: discord.Interaction, pokemon: str, team: int):
    
    await interaction.response.defer(thinking=True)

    nextSlot = ggSheet.getNextSlot(ggSheet.spreadSheet, team)

    if nextSlot == -1:
        await interaction.followup.send("No More Spots. You can't draft any more Pokemon!")
        return

    ggSheet.addPokemon( ggSheet.spreadSheet, team, nextSlot, pokemon)
    
    image_url = pokemon_data.get(pokemon)
    try:
        embed = discord.Embed(title = f"You drafted {pokemon}!")
        embed.set_image(url=image_url)
        await interaction.followup.send("", embed=embed)
    except Exception as e:
        await interaction.followup.send(f"You drafted {pokemon}!")
        print(f"Error drafting: {e}")


### Code to Throw into Main Bot in case this ever goes wrong
# # Testing Pokemon Choosing Command
# # Autocomplete function
# async def pokemon_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
#     if not current:
#             return [app_commands.Choice(name=name, value=name) for name in ["Toxapex"]]

#     current = current.lower()
#     results = []

#     # Use bisect to find the index of the first valid term
#     index = bisect.bisect_left(pokemon_names_lower, current)

#     # Collect prefix matches from that point forward
#     while index < len(pokemon_names_lower):
#         name_lower = pokemon_names_lower[index]
#         name = pokemon_names[index]

#         if name_lower.startswith(current):
#             results.append(name)
#             if len(results) >= 11:
#                 break
#         else:
#             break  # No more matches
#         index += 1

#     # Optionally fill with `contains` matches if < 10
#     if len(results) < 11:
#         for name, name_lower in zip(pokemon_names, pokemon_names_lower):
#             if (
#                 current in name_lower
#                 and not name_lower.startswith(current)
#                 and name not in results
#             ):
#                 results.append(name)
#                 if len(results) >= 11:
#                     break

#     return [app_commands.Choice(name=name, value=name) for name in results]

# # Slash command with autocomplete
# @client.tree.command(
#     name="choose",
#     description="Choose a Pokémon",
#     guild=discord.Object(id=Test_Guild_Id)
# )
# @app_commands.describe(pokemon="Start typing a name")
# @app_commands.autocomplete(pokemon=pokemon_autocomplete)
# async def choose(interaction: discord.Interaction, pokemon: str):
        
#     image_url = pokemon_data.get(pokemon)
#     try:
#         embed = discord.Embed(title = f"You chose {pokemon}!")
#         embed.set_image(url=image_url)
#         await interaction.response.send_message("", embed=embed)
#     except Exception as e:
#         await interaction.response.send_message(f"You chose {pokemon}!")
#         print(f"Error drafting: {e}")

# # Starting the Drafting Process
# @client.tree.command(name="draft",description="draft a pokemon",guild=discord.Object(id=Test_Guild_Id))
# @app_commands.describe(team="Your Team Number", pokemon="Start typing a name")
# @app_commands.autocomplete(pokemon=pokemon_autocomplete)
# async def draft(interaction: discord.Interaction, pokemon: str, team: int):
    
#     await interaction.response.defer(thinking=True)

#     nextSlot = ggSheet.getNextSlot(ggSheet.spreadSheet, team)

#     if nextSlot == -1:
#         await interaction.followup.send("No More Spots. You can't draft any more Pokemon!")
#         return

#     ggSheet.addPokemon( ggSheet.spreadSheet, team, nextSlot, pokemon)
    
#     image_url = pokemon_data.get(pokemon)
#     try:
#         embed = discord.Embed(title = f"You drafted {pokemon}!")
#         embed.set_image(url=image_url)
#         await interaction.followup.send("", embed=embed)
#     except Exception as e:
#         await interaction.followup.send(f"You drafted {pokemon}!")
#         print(f"Error drafting: {e}")