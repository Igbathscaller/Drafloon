### Code to Throw into Main Bot in case this ever goes wrong
# Draft Commands
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
