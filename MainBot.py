import os
from dotenv import load_dotenv
import json
import discord
from discord import app_commands
from discord.ext import commands
import bisect

import GoogleInteraction as ggSheet
import ChannelServer




# Import Neccessary Variables and Data
load_dotenv()
Test_Guild_Id = os.getenv("Test_Guild_Id")
Token = os.getenv("Discord_Token")

# Import list of Pokemon
with open("pokemon.json", "r") as f:
    pokemon_data = json.load(f)

pokemon_names = sorted(pokemon_data.keys())
# Key for searching
pokemon_names_lower = [name.lower() for name in pokemon_names]



intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

client = commands.Bot(command_prefix="!", intents=intents)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    try:
        guild = discord.Object(id=Test_Guild_Id)
    
        # Related to saving and storing player and sheet information in the roster.
        client.tree.add_command(ChannelServer.setspreadsheet, guild=guild)
        client.tree.add_command(ChannelServer.getspreadsheet, guild=guild)
        client.tree.add_command(ChannelServer.setPlayerRoster, guild=guild)
        client.tree.add_command(ChannelServer.removePlayerRoster, guild=guild)
        client.tree.add_command(ChannelServer.getPlayerRoster, guild=guild)

        synced = await client.tree.sync(guild=guild)

        print(f"Synced {len(synced)} command(s) to guild {guild.id}")
    except Exception as e:
        print(f"Error syncing commands: {e}")

# First slash command 
# Remove guild in the future
# it is connected to specific server for faster testing

# This is the testing command

@client.tree.command(name="hello", description="Say hi to the bot!", guild=discord.Object(id=Test_Guild_Id))
@commands.has_permissions(manage_messages=True)
async def hello(interaction: discord.Interaction):

    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    await interaction.response.send_message(f"Hello, {interaction.user.mention}!")
    

# Testing Pokemon Choosing Command
# Autocomplete function
async def pokemon_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    if not current:
            return [app_commands.Choice(name=name, value=name) for name in ["Toxapex"]]

    current = current.lower()
    results = []

    # Use bisect to find the index of the first valid term
    index = bisect.bisect_left(pokemon_names_lower, current)

    # Collect prefix matches from that point forward
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

    # Optionally fill with `contains` matches if < 10
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
@client.tree.command(
    name="choose",
    description="Choose a Pokémon",
    guild=discord.Object(id=Test_Guild_Id)
)
@app_commands.describe(pokemon="Start typing a name")
@app_commands.autocomplete(pokemon=pokemon_autocomplete)
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
@client.tree.command(name="draft",description="draft a pokemon",guild=discord.Object(id=Test_Guild_Id))
@app_commands.describe(team="Your Team Number", pokemon="Start typing a name")
@app_commands.autocomplete(pokemon=pokemon_autocomplete)
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




client.run(Token)
