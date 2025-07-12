import os
from dotenv import load_dotenv
import discord
from discord import app_commands
from discord.ext import commands

load_dotenv()
Test_Guild_Id = os.getenv("Test_Guild_Id")
print(Test_Guild_Id)
Token = os.getenv("Discord_Token")


intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix="!", intents=intents)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    try:
        guild = discord.Object(id=Test_Guild_Id)
        synced = await client.tree.sync(guild=guild)
        print(f"Synced {len(synced)} command(s) to guild {guild.id}")
    except Exception as e:
        print(f"Error syncing commands: {e}")



#First slash command 
# Remove guild in the future
# it is connected to specific server for faster testing

@client.tree.command(name="hello", description="Say hi to the bot!", guild=discord.Object(id=Test_Guild_Id))
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello, {interaction.user.mention}!")



client.run(Token)
