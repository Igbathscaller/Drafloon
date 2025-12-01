import json
import discord
from discord import app_commands


# region: JSON Utility Functions
def loadAuction():
    try:
        with open("MarketAuction.json", "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        data = {}

    return data

# Save Auction to Json
def saveAuction():
    with open("MarketAuction.json", "w") as f:
        json.dump(auction, f, indent=4)

# Stores Json Data as a variables on runtime.
auction = loadAuction()

# Load JSON with list of auctionable mons
with open("auctionMons.json") as f:
    itemList = json.load(f)

# endregion

# region: Json Setup
#### auction[channel_id] ->
## ["pokemon"]
## ## [name] -> [bid], [bidderSlot], [bidderName]
## ["players"]
## ## [slot] -> [user], [name], [budget], [items] 
## ["player"]
## ## [player_id] -> [slot], [displayName]
## [channel]
## [player_count] 
## [player_list_msg] 
## [item_list_msg]  
## [bidding_channel] 
## [bidding]
## [info_channel]
# endregion

# Item Table
# String Function (Channel to String)
def item_table_embed(channel_id: str):
    lines = []
    header = f"{'Item Name':<21}{'Bid':<8}{'Bidder':<18}"
    lines.append(header)
    lines.append("-" * len(header))
    
    auction_items = auction[channel_id]["pokemon"]
    
    for name, data in sorted(auction_items.items(), key=lambda x: x[1]['bid'], reverse=True):
        bid = data["bid"]
        bidder = f"{data['bidderName']}" if data["bidderName"] else "None"
        line = f"{name:<21}{bid:<8}{bidder[:18]}"
        lines.append(line)

    embed=discord.Embed(
        title="Auction Items",
        description= "```\n" + "\n".join(lines) + "\n```" ,
        color=discord.Color.gold()
    )

    return embed

# Player Table
# channel_id -> embed
def player_table_embed(channel_id: str):
    currentAuction = auction[channel_id]
    
    player_count = currentAuction["player_count"]
    players = currentAuction["players"]

    embed = discord.Embed(
        title="Auction Players",
        description=f"{player_count} players",
        color=discord.Color.blue()
    )

    lines = []
    lines.append(f"{'Slot':<6}{'Player':<20}{'Budget':<8}")
    lines.append("-" * 50)

    for i in range(1, player_count + 1):
        username = players[str(i)]["name"]
        budget = players[str(i)]["budget"]
        items = players[str(i)]["items"]

        user_str = f"{username}" if username else "Unassigned"
        items_str = ", ".join(items) if items else "---"

        lines.append(f"{i:<6}{user_str:<20}{budget:<8}")
        lines.append(f"+ {items_str}")
        

    embed.description = "```\n" + "\n".join(lines) + "\n```"
    return embed

# Display Name
async def getDisplayName(interaction, user):
    
    member = interaction.guild.get_member(user.id)
    if member is None:
        # Only fetch if missing (slow: API call)
        try:
            member = await interaction.guild.fetch_member(user.id)
        except:
            member = None

    # Pick best name
    display_name = (
        member.display_name if member else
        user.global_name if user.global_name else
        user.name
    )

    return display_name


# Json, creates two marks, original index and new index
@app_commands.command(name="setup_auction")
@app_commands.default_permissions(moderate_members=True)
@app_commands.describe(player_count="Number of players (default 16)")
async def setup(interaction: discord.Interaction, player_count: int = 16):

    channel_id = str(interaction.channel_id)
    
    auction[channel_id] = {
        "pokemon": {}, # Updates Later
        "players": {}, # Updates Later 
        "player":  {}, # Updates Later
        "player_count": player_count,   # Done Now
        "player_list_msg": None,    # Has to be updated
        "item_list_msg": None,      # Has to be updated
        "bidding": False,               # Done Now
        "info_channel": channel_id,     # Done Now
        "bidding_channel": None         # Updates Later
    }

    players = {str(i): 
               {"name": None,
                "budget": 1000, 
                "items": []}
               for i in range(1, player_count + 1)}

    player = {}

    auction[channel_id]["players"] = players
    auction[channel_id]["player"] = player

    auction_items = {
        name: {
            "bid": 0,
            "bidderSlot": None,
            "bidderName": None
        }
        for name in itemList
    }

    auction[channel_id]["pokemon"] = auction_items

    # Create bidding channel
    info_channel = interaction.channel
    channelOverwrites = info_channel.overwrites
    channelCategory = info_channel.category

    bidding = await interaction.guild.create_text_channel(
        f"{info_channel.name}-bidding",
        overwrites= channelOverwrites,
        category = channelCategory
    )
    
    auction[channel_id]["bidding_channel"] = str(bidding.id)

    # create a link from the bidding channel to the info channel
    auction[str(bidding.id)] = {
        "bidding": True,                # Done Now (is this neccessary?)
        "info_channel": channel_id,     # Done Now
    }

    # Send the two messages
    player_list_msg = await info_channel.send(
        embed=player_table_embed(channel_id)
        )
    
    item_list_msg = await info_channel.send(
        embed=item_table_embed(channel_id)
    )

    auction[channel_id]["player_list_msg"] = player_list_msg.id
    auction[channel_id]["item_list_msg"] = item_list_msg.id

    saveAuction()
    await interaction.response.send_message("Auction setup complete!", ephemeral=True)

@app_commands.command(name="end_auction")
@app_commands.default_permissions(moderate_members=True)
async def clear(interaction: discord.Interaction):

    channel_id = str(interaction.channel_id)

    # Should check if it is an auction channel, if it is bidding it is false
    isInfo = not auction.get(channel_id, {}).get("bidding", True)

    if not isInfo:
        await interaction.response.send_message("You cannot set players here", ephemeral=True)
        return

    bidding_id = auction[channel_id]["bidding_channel"] # to be deleted
    item_msg_id = auction[channel_id]["player_list_msg"]
    player_msg_id = auction[channel_id]["item_list_msg"]

    channel = interaction.channel
    msg1 = await channel.fetch_message(item_msg_id)
    msg2 = await channel.fetch_message(player_msg_id)
    bidding = await interaction.guild.fetch_channel(int(bidding_id))

    await msg1.delete()
    await msg2.delete()
    await bidding.delete()

    del auction[channel_id]
    del auction[bidding_id]
    
    saveAuction()

    await interaction.response.send_message("Deleted Auction")


@app_commands.command(name="setplayer")
@app_commands.describe(
    user="Discord user",
    slot="Player slot number"
)
async def setplayer(interaction: discord.Interaction, user: discord.User, slot: int):
    
    # First we need to check if this is a valid channel for setting players

    channel_id = str(interaction.channel_id)

    # Should check if it is an auction channel, if it is bidding it is false
    isInfo = not auction.get(channel_id, {}).get("bidding", True)

    if not isInfo:
        await interaction.response.send_message("You cannot set players here", ephemeral=True)
        return

    player_count = auction[channel_id]["player_count"]
    players = auction[channel_id]["players"]
    player = auction[channel_id]["player"]

    if slot < 1 or slot > player_count:
        await interaction.response.send_message("Invalid slot.", ephemeral=True)
        return

    slot = str(slot)

    player[str(user.id)] = slot

    displayName = await getDisplayName(interaction, user)

    players[slot]["name"] = displayName
    player_list_msg = auction[channel_id]["player_list_msg"]

    # Update embed
    channel = interaction.channel
    msg = await channel.fetch_message(player_list_msg)
    await msg.edit(embed=player_table_embed(channel_id))

    saveAuction()

    await interaction.response.send_message(
        f"Player {slot} set to {user.mention}.",
        ephemeral=True
    )

# Auction Autocomplete
async def item_autocomplete(interaction: discord.Interaction, current: str):
    # use the keys of your dictionary
    keys = itemList.keys()

    return [
        app_commands.Choice(name=key, value=key)
        for key in keys
        if current.lower() in key.lower()
    ][:25]

@app_commands.command(name="bid")
@app_commands.describe(pokemon="Item number", amount="Bid amount")
@app_commands.autocomplete(pokemon=item_autocomplete)
async def bid(interaction: discord.Interaction, pokemon: str, amount: int):

    bidding_id = str(interaction.channel_id)

    bidding = auction.get(bidding_id, {}).get("bidding", False)

    if not bidding:
        await interaction.response.send_message(
            "Bids must be placed in the bidding channel.",
            ephemeral=True
        )
        return

    channel_id = str(auction[bidding_id]["info_channel"])
    auction_items = auction[channel_id]["pokemon"]
    player = auction[channel_id]["player"]
    players = auction[channel_id]["players"]

    # Check Valid Pokemon
    if pokemon not in auction_items:
        await interaction.response.send_message("Invalid Pokemon", ephemeral=True)
        return

    # Check Valid Player
    slot = player.get(str(interaction.user.id))
    if not slot:
        await interaction.response.send_message("You aren't cool enough to bid here")
        return
    
    name = players[slot]["name"]
    budget = players[slot]["budget"]

    # Check Valid Bid
    if amount <= auction_items[pokemon]["bid"]:
        await interaction.response.send_message(
            f"Your bid must exceed the current bid ({auction_items[pokemon]['bid']}).",
            ephemeral=True
        )
        return
    
    if amount > budget:
        await interaction.response.send_message(
            f"Your remaining budget is only {budget}.",
            ephemeral=True
        )
        return

    # Get Old Bidder
    oldBid = auction_items[pokemon]["bid"]
    oldSlot = auction_items[pokemon]["bidderSlot"]

    # Set new Bidder
    auction_items[pokemon]["bid"] = amount
    auction_items[pokemon]["bidderSlot"] = slot
    auction_items[pokemon]["bidderName"] = name

    # Return Bid to Old Bidder Budget and removes Pokemon if previous bidder existed
    if oldSlot:
        players[oldSlot]["budget"] += oldBid
        players[oldSlot]["items"].remove(pokemon)

    # Deduct Bid From Bidder Budget
    players[slot]["budget"] -= amount
    players[slot]["items"].append(pokemon)

    item_msg_id = auction[channel_id]["item_list_msg"]
    player_msg_id = auction[channel_id]["player_list_msg"]

    channel = interaction.guild.get_channel(int(channel_id))
    item_msg = await channel.fetch_message(item_msg_id)
    player_msg = await channel.fetch_message(player_msg_id)

    await item_msg.edit(embed= item_table_embed(channel_id))

    await player_msg.edit(embed= player_table_embed(channel_id))

    saveAuction()

    await interaction.response.send_message(
        f"You bid on {pokemon} for {amount}!"
    )
