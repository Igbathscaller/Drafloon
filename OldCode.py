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

# You can remove guild to allow access to all servers the bot is on, but it takes longer to sync the bot

# This is the testing command

# @client.tree.command(name="hello", description="Say hi to the bot!", guild=discord.Object(id=Guild_Id))
# @commands.has_permissions(manage_messages=True)
# async def hello(interaction: discord.Interaction):

#     if not interaction.user.guild_permissions.manage_messages:
#         await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
#         return

#     await interaction.response.send_message(f"Hello, {interaction.user.mention}!")


# Roster Code is read-only, so I have to parse the formula to get the actual code.
# I should probably make it so that the regex search and cell checking only happens at startup
# This why I can reduce a google sheets interaction by one when reading.

# def updateRoster(spreadSheet: gspread.Spreadsheet, cellCol: int, arrIndex: int, value:str):

#     rosterSheet = spreadSheet.worksheet("Roster Code")

#     # Get the formula string from the formula cell
#     formula = rosterSheet.cell(2, cellCol, value_render_option="FORMULA").value

#     # Regex to extract 'SheetName!ColumnStartRow:ColumnEndRow'
#     match = re.search(r'([a-zA-Z0-9_]+)!\$?([A-Z]+)(\d+):\$?[A-Z]+(\d+)', formula)
#     if not match:
#         print("Could not parse: " + formula)

#     source_sheet_name, column_letter, start_row, end_row = match.groups()
#     start_row, end_row = int(start_row), int(end_row)

#     # Final source cell to update
#     source_row = start_row + arrIndex
#     source_cell = f"{column_letter}{source_row}"

#     # Open the correct worksheet and update the cell
#     source_sheet = spreadSheet.worksheet(source_sheet_name)
#     source_sheet.update_acell(source_cell, value)

#     # print(f"Updated {source_sheet_name}!{source_cell} to '{value}'")


    # # Check if on Draft Board
    # pickCost = ggSheet.pointDict[channel_id].get(pokemon,None)
    # if not pickCost or pickCost == 99:
    #     await interaction.response.send_message(f"You can't draft {pokemon}!")
    #     return
    # # Need to access gg sheets so we need thinking time
    # await interaction.response.defer(thinking=True)
    # (nextSlot, pointTotal) = ggSheet.getNextSlot(spreadSheet, channel_id, team)
    # # Check Points left
    # pointsLeft = ggSheet.pointDict[channel_id]["Total"] - pointTotal
    # # Check if slots open
    # if nextSlot == -1:
    #     await interaction.followup.send("You can't draft any more Pokemon!")
    #     return
    # # Check if you have enough points
    # if pointsLeft < pickCost:
    #     await interaction.followup.send(f"You only have {pointsLeft} points left! You can't draft {pokemon}.")
    #     return
    # # Check if someone else drafted the mon
    # drafted = ggSheet.readFullRoster(spreadSheet, 16, 11)
    # if pokemon in drafted:
    #     await interaction.followup.send(f"Someone already drafted {pokemon}.")
    #     return
    # pointsLeft -= pickCost
    # ggSheet.addPokemon(channel_id, team, nextSlot, pokemon)


    # elif channelData[channel_id]["Rosters"].get(roster,[]) == []:
    #     msg = f"Roster {roster} is empty"

    # else:
    #     ids = channelData[channel_id]["Rosters"][roster]
    #     members = await asyncio.gather(*[
    #         interaction.guild.fetch_member(int(id))
    #         for id in ids
    #     ])
    #     display_names = [member.display_name for member in members if member]
    #     msg = f"Player(s): {', '.join(display_names)} are on Roster {roster}"

    # await interaction.response.send_message(msg, ephemeral=True)

# Combined into another function to reduce calls
# def loadDraftedData(channel_id: str):
#     # This is the removal if statement
#     # If the spreadsheet doesn't exist in spreadDict, I want it cleared from pointDict
#     if channel_id not in spreadDict:
#         draftedData.pop(channel_id, None)
#         return

#     spreadSheet = spreadDict[channel_id]

#     draftedData[channel_id] = readFullRoster(spreadSheet, 16, 11)

# @app_commands.command(name="view_timer", description="Check how much time remains before the auto-pick")
# @app_commands.guilds() 
# async def view_timer(interaction: Interaction):
#     channel_id = str(interaction.channel_id)
#     end_time = end_times.get(channel_id, None)

#     if end_time is None:
#         await interaction.response.send_message("No timer is currently running.", ephemeral=True)
#         return

#     # Convert monotonic-based end time to Unix timestamp
#     now_real = time.time()
#     monotonic = time.monotonic()
#     diff = end_time - monotonic

#     unix_timestamp = int(now_real + diff)
#     await interaction.response.send_message(f"Timer ends <t:{unix_timestamp}:R>", ephemeral=True)

