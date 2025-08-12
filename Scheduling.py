import discord
from discord import app_commands, Interaction
from discord.ext import commands
import json
import re
import gspread
from google.oauth2.service_account import Credentials
import time



# Define scope
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Authorization
creds = Credentials.from_service_account_file("../drafloon-959516a4b9be.json", scopes=scope)
client = gspread.authorize(creds)

schedules = {}

try:
    with open("schedule_data.json", "r") as f:
        schedules = json.load(f)
except FileNotFoundError:
    print("file not fount")

# Save data to schedule
def save_schedule_data():
    with open("schedule_data.json", "w") as f:
        json.dump(schedules, f, indent=2)

# Save The Google Sheet Url and conert it to the key.
@discord.app_commands.command(name="save_schedule_sheet", description="Link a Google Sheet URL to this channel")
@app_commands.describe(sheet_url="Google Sheets URL")
async def save_schedule_sheet(interaction: Interaction, sheet_url: str):
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("You don't have permission.")
        return

    sheet_id = extract_sheet_id(sheet_url)
    if not sheet_id:
        await interaction.response.send_message("Invalid Google Sheets URL.")
        return

    channel_id = str(interaction.channel_id)

    schedules[channel_id] = {
        "spreadsheet_id": sheet_id,
        "schedules" : {},
        "created_channels" : []
    }

    save_schedule_data()

    await interaction.response.send_message(f"Saved Google Sheet for this channel.")

# helper function to get the sheet id
def extract_sheet_id(sheet_url: str):
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url)
    if match:
        return match.group(1)
    return None

@discord.app_commands.command(name="fetch_schedule", description="Fetch the schedule from the linked Google Sheet. Must save a sheet first")
async def update_schedule(interaction: Interaction):
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("You don't have permission.")
        return

    await interaction.response.defer()

    channel_id = str(interaction.channel_id)

    if channel_id not in schedules or "spreadsheet_id" not in schedules[channel_id]:
        await interaction.followup.send("No Google Sheet linked for this channel.  Use /save_schedule_sheet")
        return

    spreadsheet_id = schedules[channel_id]["spreadsheet_id"]
    try:
        sheet = client.open_by_key(spreadsheet_id)
        response = sheet.values_get("Scheduling Code!D2:CD9")
        data = response.get("values", [])

    except Exception as e:
        await interaction.followup.send(f"Failed to open sheet: {e}")
        return

    schedule = get_schedule(data)
    schedules[channel_id]["schedules"] = schedule
    save_schedule_data()


    weeks_count = len(schedule)
    await interaction.followup.send(f"Schedule updated from Google Sheets. Found {weeks_count} week(s).")

# helper function to parse imported data.
def get_schedule(data):
    schedule = {}
    max_cols = 79 

    # Pad rows to max_cols
    for i in range(len(data)):
        row = data[i]
        if len(row) < max_cols:
            row += [''] * (max_cols - len(row))
        data[i] = row

    for week in range(10):
        col_start = week * 8
        first_player = col_start
        second_player = col_start + 6

        games = []
        for r in range(8):
            if r >= len(data):
                break
            p1 = data[r][first_player]
            p2 = data[r][second_player]
            if not p1 or not p2:
                continue
            games.append(f"{p1}-vs-{p2}")

        if games:
            schedule[f"{week+1}"] = games
        else:
            break

    return schedule


@discord.app_commands.command(name="create_channels", description="Create Scheduling Channels for a given week. Must save a sheet and fetch first")
@app_commands.describe(week="Week number")
@app_commands.choices(week=[
    app_commands.Choice(name="1", value="1"),app_commands.Choice(name="2", value="2"),
    app_commands.Choice(name="3", value="3"),app_commands.Choice(name="4", value="4"),
    app_commands.Choice(name="5", value="5"),app_commands.Choice(name="6", value="6"),
    app_commands.Choice(name="7", value="7"),app_commands.Choice(name="8", value="8"),
])
async def schedulingChannels(interaction: Interaction, week: str):
    await interaction.response.defer()

    if not interaction.user.guild_permissions.manage_channels:
        await interaction.followup.send("You don't have permission to use this command.")
        return

    channel_id = str(interaction.channel_id)

    if channel_id not in schedules:
        await interaction.followup.send("No schedule data found for this channel. Use /save_schedule_sheet and /fetch_schedule.")
        return
    
    schedule = schedules[channel_id].get("schedules", {})
    if week not in schedule:
        await interaction.followup.send(f"No schedule found for week {week}.")
        return
    
    matches = schedule[week]
    guild = interaction.guild
    category = interaction.channel.category

    old_channels = schedules[channel_id].get("created_channels", [])
    for id in old_channels:
        channel = guild.get_channel(int(id))
        if channel:
            try:
                await channel.delete(reason="Deleting old scheduling channels")
            except Exception as e:
                print(f"Failed to delete channel {id}: {e}")


    new_channels = []

    for match in matches:
        # Lowercase, replace spaces with dashes, remove invalid chars
        name = match.lower()
        name = name.replace(" ", "-")

        try:
            new_channel = await guild.create_text_channel(
                name,
                category=category,
                reason=f"SchedulingChannels week {week} creation"
            )
            new_channels.append(str(new_channel.id))
        except Exception as e:
            print(f"Failed to create channel {name}: {e}")

    # Save created channels for possible later cleanup
    schedules[channel_id]["created_channels"] = new_channels
    save_schedule_data()
    
    await interaction.followup.send(f"Schedules Sucessfully Created for Week {week}")

@discord.app_commands.command(name="delete_channels", description= "Delete Channels that were created by the bot and saved")
async def deleteChannels(interaction: Interaction):
    await interaction.response.defer()

    if not interaction.user.guild_permissions.manage_channels:
        await interaction.followup.send("You don't have permission to use this command.")
        return

    channel_id = str(interaction.channel_id)

    if channel_id not in schedules:
        await interaction.followup.send("No schedule data found for this channel. use /save_schedule_sheet and /fetch_schedule first")
        return
    
    guild = interaction.guild

    old_channels = schedules[channel_id].get("created_channels", [])
    for id in old_channels:
        channel = guild.get_channel(int(id))
        if channel:
            try:
                await channel.delete(reason="Deleting old scheduling channels")
            except Exception as e:
                print(f"Failed to delete channel {id}: {e}")


    # Save created channels for possible later cleanup
    schedules[channel_id]["created_channels"] = []
    save_schedule_data()
    
    await interaction.followup.send(f"Sucessfully Removed Channels")
