from discord.ui import View, Button
from discord import ButtonStyle, Interaction, Embed, Color, app_commands
import asyncio

import ChannelServer
import DraftCommands as Draft

#region: Adding Picks

# adds pick to the roster
def addPick(channel_id: str, team: str, main: str, 
            backup: str = None, backup2: str = None, slot: int = None):
    picks = Draft.pickData[channel_id]["Rosters"].get(team, None)
    if picks == None:
        Draft.pickData[channel_id]["Rosters"][team] = []
        picks = Draft.pickData[channel_id]["Rosters"][team]
    
    if slot == None:
        picks.append({
            "Main": main,
            "Backup_1": backup,
            "Backup_2": backup2
        })
    else:
        picks.insert(slot - 1,{
            "Main": main,
            "Backup_1": backup,
            "Backup_2": backup2
        })

    Draft.savePicksJson()

def getPicks(channel_id: str, team: str) -> list:
    picks = Draft.pickData[channel_id]["Rosters"].get(team, None)
    if picks == None:
        return []
    else:
        return picks

@app_commands.command(name="leave_pick",description="Leave a Pick Privately with the Bot")
@app_commands.describe(pokemon = "Pick a Pokemon", 
                       backup_1 = "If your main choice was sniped", 
                       backup_2 = "If your backup was also sniped",
                       slot= "if you want it to be a higher priority")
@app_commands.autocomplete(pokemon=Draft.pokemon_autocomplete, backup_1=Draft.pokemon_autocomplete, backup_2=Draft.pokemon_autocomplete)
@app_commands.guilds()
async def leave_pick(interaction: Interaction, pokemon: str, 
                     backup_1: str = None, backup_2: str = None, slot: int = None):
    
    # Check if it is actual pokemon (in the list of choices)
    if pokemon not in Draft.pokemon_names:
        await interaction.response.send_message("Please pick an actual Pokemon...", ephemeral=True)
        return
    
    if (backup_1 and backup_1 not in Draft.pokemon_names) or (backup_2 and backup_2 not in Draft.pokemon_names):
        await interaction.response.send_message("Please pick actual Pokemon...", ephemeral=True)
        return

    channel_id = str(interaction.channel_id)

    # Checks if the channel has been initialized
    channel = Draft.pickData.get(channel_id, None)
    if not channel:
        await interaction.response.send_message("This Channel has no Associated Spreadsheet", ephemeral=True)
        return

    # Team of the person leaving the Draft Pick
    team = ChannelServer.getTeam(channel_id, str(interaction.user.id))

    # Check Team
    if not team:
        await interaction.response.send_message("You are not on a Team", ephemeral=True)
        return
    
    if len(Draft.pickData[channel_id]["Rosters"].get(team, [])) >= 10 :
            await interaction.response.send_message("You can only leave up to 10 picks", ephemeral=True)
            return

    # Add the pick to the team
    addPick(channel_id, team, pokemon, backup_1, backup_2, slot)
    log_pick(str(interaction.user.id), channel_id, "left", [pokemon, backup_1, backup_2])


    await interaction.response.send_message(f"You left the following pick(s): {', '.join(filter(None, [pokemon, backup_1, backup_2]))}", ephemeral=True)

    # update people viewing picks
    await update_leave_pick_messages(channel_id, team)

# endregion

#region: Viewing/Removing picks
# Track active messages by channel_id -> team -> list of messages
active_messages = {}
locks = {}

def add_active_message(channel_id: str, team: str, message):
    if channel_id not in active_messages: 
        # add channel if not there
        active_messages[channel_id] = {}
    if team not in active_messages[channel_id]:
        # add team if not there
        active_messages[channel_id][team] = []
    # append the message
    active_messages[channel_id][team].append(message)

def remove_active_message(channel_id: str, team: str, message):
    try:
        active_messages[channel_id][team].remove(message)
    except (KeyError, ValueError):
        pass

async def get_remove_lock(channel_id: str, team: str) -> asyncio.Lock:
    locks.setdefault(channel_id, {})
    locks[channel_id].setdefault(team, asyncio.Lock())
    return locks[channel_id][team]

# teamName update

async def update_leave_pick_messages(channel_id: str, team: str):
    teamName = ChannelServer.channelData[channel_id]["TeamNames"].get(team, "No Team Name")
    picks = getPicks(channel_id, team)
    embed = picks_embed(team, teamName, picks)
    messages = active_messages.get(channel_id, {}).get(team, [])
    view = RemovePickView(channel_id, team)
    for message in messages:
        try:
            await message.edit(embed=embed, view=view)
        except Exception as e:
            print(f"Failed to update message {message.id}: {e}")

def picks_embed(team: str, teamName: str, picks: list) -> Embed:
    
    embed = Embed(
        title=f"{teamName}",
        color=Color.brand_green()
    )
    if picks:
        text = ["```"]
        for i, pick in enumerate(picks):
            main = pick.get("Main") or "None"
            b1 = pick.get("Backup_1")
            b2 = pick.get("Backup_2")
            text.append(f"Pick {i+1}: {main}")
            if b1:
                text.append(f"\t└ Backup 1: {b1}")
            if b2:
                text.append(f"\t└ Backup 2: {b2}")
        text.append("```")
        embed.add_field(name="Your Left Picks: ", value="\n".join(text), inline=False)
    else:
        embed.add_field(name="Your Left Picks: ", value="You have left no picks", inline=False)
    return embed

# Classes for buttons to Remove.
class RemovePickView(View):
    def __init__(self, channel_id, team):
        super().__init__(timeout=180) # Initialize the View Button
        self.channel_id = channel_id
        self.team = team
        self.message = None

        picks = getPicks(channel_id, team)

        for i in range(len(picks)):
            # Save the index, the 
            self.add_item(RemovePickButton(index=i, channel_id=channel_id, team=team))

    # Remove all tracked messages for this channel+team
    # I have to update this so it only affects the timed out message
    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(view=None)
            except Exception as e:
                print(f"Failed to edit message: {e}")

        # Remove this message from active_messages
        try:
            active_messages[self.channel_id][self.team].remove(self.message)
        except (KeyError, ValueError):
            pass


class RemovePickButton(Button):
    def __init__(self, index, channel_id, team):
        super().__init__(
            label=f"Remove {index+1}",
            style=ButtonStyle.danger
        )
        self.index = index
        self.channel_id = channel_id
        self.team = team

    async def callback(self, interaction: Interaction):  
        lock = await get_remove_lock(self.channel_id, self.team)
        
        async with lock:
            picks = getPicks(self.channel_id, self.team)
            if not (0 <= self.index < len(picks)):
                await interaction.response.send_message("That pick no longer exists.", ephemeral=True)
                return
            
            removed_pick = picks.pop(self.index)
            pokemon = removed_pick.get("Main")
            backup_1 = removed_pick.get("Backup_1")
            backup_2 = removed_pick.get("Backup_2")

            log_pick(str(interaction.user.id), self.channel_id, "removed", [pokemon, backup_1, backup_2])
            # Saves Picks to the Json.
            Draft.savePicksJson()

            # Edit the active messages with updated picks and buttons
            await update_leave_pick_messages(self.channel_id, self.team)

            # Sends Message letting them know it was successful
            await interaction.response.send_message(
                f"Removed Pick {self.index + 1}: {', '.join(filter(None, [pokemon, backup_1, backup_2]))}",
                ephemeral=True
            )


@app_commands.command(name="view_picks",description="View Your Picks Privately and Remove old Picks")
@app_commands.guilds()
async def view_picks(interaction: Interaction):

    channel_id = str(interaction.channel_id)

    # Checks if the channel has been initialized
    channel = Draft.pickData.get(channel_id, None)
    if not channel:
        await interaction.response.send_message("This Channel has no Associated Spreadsheet", ephemeral=True)
        return

    # Team of the person making the Draft Pick
    team = ChannelServer.getTeam(channel_id, str(interaction.user.id))
    teamName = ChannelServer.channelData[channel_id]["TeamNames"].get(team, "No Team Name")

    # Check Team
    if not team:
        await interaction.response.send_message("You are not on a Team", ephemeral=True)
        return

    # get the picks of the team
    picks = getPicks(channel_id, team)

    embed = picks_embed(team, teamName, picks)

    # Build button UI for removing picks
    view = RemovePickView(channel_id, team)

    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    # message = await interaction.response.send_message(embed=embed, view=view)

    sent_message = await interaction.original_response()
    view.message = sent_message
    add_active_message(channel_id, team, sent_message)

@app_commands.command(name="view_picks_mod",description="View Your Picks (Mod Abuse Ver.)")
@app_commands.guilds()
async def view_picks_mod(interaction: Interaction, team: str):

    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    channel_id = str(interaction.channel_id)

    # Checks if the channel has been initialized
    channel = Draft.pickData.get(channel_id, None)
    if not channel:
        await interaction.response.send_message("This Channel has no Associated Spreadsheet", ephemeral=True)
        return

    # Team of the person making the Draft Pick
    roster = ChannelServer.channelData[channel_id]["Rosters"].get(team)

    # Check Team
    if roster == None:
        await interaction.response.send_message("Not a valid team", ephemeral=True)
        return
    
    teamName = ChannelServer.channelData[channel_id]["TeamNames"].get(team, "No Team Name")

    # get the picks of the team
    picks = getPicks(channel_id, team)

    embed = picks_embed(team, teamName, picks)

    # Build button UI for removing picks
    view = RemovePickView(channel_id, team)

    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    # message = await interaction.response.send_message(embed=embed, view=view)

    sent_message = await interaction.original_response()
    view.message = sent_message
    add_active_message(channel_id, team, sent_message)

#endregion

#region: Logging Picks

log_file = "log.txt"

def log_pick(user_id: str, channel_id: str, action: str, names: list):
    names_str = ", ".join(filter(None, names))
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{channel_id} {user_id} {action} {names_str}\n")

# endregion