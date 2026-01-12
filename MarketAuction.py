import json
import discord
from discord import app_commands
from discord.ext import tasks
import time

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
#### auction ->
## ["pokemon"]
## ## [name] -> [bid], [bidder], [bidder_id], [intial], [endtime]
## ["players"]
## ## [id] -> [name], [budget], [mons], [number] 
## ## ## [mons] -> cost
## [secured_mons]
## [info_channel_id]
## [bidding_channel_id]
## [msg_id]
# endregion

# Item Table
# String Function (Channel to String)
def auction_msg():
    
    pokemonList = auction["pokemon"]
    sorted_pokemon = [k for k, v in sorted(pokemonList.items(), key=lambda item: item[1]["endtime"], reverse=False)]

    players = auction["players"]
    
    embeds = []

    playerEmbed = discord.Embed(      
        title  = "Secured Pokemon + Points Left",
        color  = 15410001
    )
    
    # for name, data in sorted(pokemon.items(), key=lambda x: x[1]['bid'], reverse=True):
    #     bid = data["bid"]
    #     bidder = f"{data['bidderName']}" if data["bidderName"] else "None"
    #     line = f"{name:<21}{bid:<8}{bidder[:18]}"
    #     lines.append(line)
    
    for id in players:
        username = players[id]["name"]
        budget = players[id]["budget"]
        pokemon = players[id]["mons"]

        lines = []
        lines.append(f"`{'Pokémon Secured':<16}` | `{'Points':<6}`")
        
        for mon in pokemon:
            lines.append(f"`{mon[:16]:<16}` | `{pokemon[mon]:<6}`")
        lines.append(f"`{'Points Left':<16}` | **{budget}**")

        playerEmbed.add_field(
            name = username,
            value = "\n".join(lines),
            inline= False
        )

    embeds.append(playerEmbed)
    
    # auctionEmbed = discord.Embed(
    #     title = "Currently Auctioned",
    #     color = 2943779
    # )
    
    pokeNum = len(pokemonList)

    # for i in range((pokeNum-1)//15 + 1):

    #     auctionLines = []

    #     if i == pokeNum//15:
    #         for poke in sorted_pokemon[i*15:pokeNum]:
    #             auctionLines.append(f"`{poke[:15]:<15} | {pokemonList[poke]['bidder'][:14]:<14} | {pokemonList[poke]['bid']:<4} |` <t:{pokemonList[poke]['endtime']}:R>")
    #     else:
    #         for poke in sorted_pokemon[i*15: i*15 + 15]:
    #             auctionLines.append(f"`{poke[:15]:<15} | {pokemonList[poke]['bidder'][:14]:<14} | {pokemonList[poke]['bid']:<4} |` <t:{pokemonList[poke]['endtime']}:R>")

    #     auctionEmbed.add_field(
    #         name = f"`{'Pokémon':<15} | {'Highest Bidder':<14} | {'Bid':<4} |` Secure Time",
    #         value = "\n".join(auctionLines),
    #         inline= False
    #     )

    # embeds.append(auctionEmbed)

    # Collect all fields first
    all_fields = []
    for i in range((pokeNum - 1)//15 + 1):
        start = i * 15
        end = pokeNum if i == pokeNum//15 else i * 15 + 15
        auctionLines = [
            f"`{poke[:15]:<15} | {pokemonList[poke]['bidder'][:14]:<14} | {pokemonList[poke]['bid']:<4} |` <t:{pokemonList[poke]['endtime']}:R>"
            for poke in sorted_pokemon[start:end]
        ]
        all_fields.append({
            "name": f"`{'Pokémon':<15} | {'Highest Bidder':<14} | {'Bid':<4} |` Secure Time",
            "value": "\n".join(auctionLines)
        })
    
    # First embed: first 5 fields (or fewer if not enough)
    first_embed = discord.Embed(title="Currently Auctioned", color=2943779)
    for field in all_fields[:5]:
        first_embed.add_field(name=field["name"], value=field["value"], inline=False)
    embeds.append(first_embed)
    
    # Second embed: remaining fields, or empty if none
    second_embed = discord.Embed(title="Currently Auctioned 2", color=2943779)
    remaining_fields = all_fields[5:]
    if remaining_fields:
        for field in remaining_fields:
            second_embed.add_field(name=field["name"], value=field["value"], inline=False)
    else:
        second_embed.description = "No additional Pokémon."
    embeds.append(second_embed)

    return embeds

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
async def setup(interaction: discord.Interaction):

    channel_id = str(interaction.channel_id)
    
    auction["pokemon"]= {} 
    auction["players"]= {}
    auction["msg_id"] = []
    auction["info_channel_id"] = channel_id
    auction["bidding_channel_id"] = None
    auction["secured_mons"] = []

    # Create bidding channel
    info_channel = interaction.channel
    channelOverwrites = info_channel.overwrites
    channelCategory = info_channel.category

    bidding = await interaction.guild.create_text_channel(
        f"{info_channel.name}-bidding",
        overwrites= channelOverwrites,
        category = channelCategory
    )
    
    auction["bidding_channel_id"] = str(bidding.id)
    
    msg = await info_channel.send(
        embeds=auction_msg()
    )

    auction["msg_id"] = msg.id

    saveAuction()
    await interaction.response.send_message("Auction setup complete!", ephemeral=True)

@app_commands.command(name="end_auction")
@app_commands.default_permissions(moderate_members=True)
async def clear(interaction: discord.Interaction):

    channel_id = str(interaction.channel_id)

    # Should check if it is the auction channel
    isInfo = auction.get("info_channel_id") == channel_id

    if not isInfo:
        await interaction.response.send_message("You can't delete auction here", ephemeral=True)
        return

    auction.clear()
    
    saveAuction()

    await interaction.response.send_message("Ended Auction")


@app_commands.command(name="add_player")
@app_commands.default_permissions(moderate_members=True)
@app_commands.describe(
    user="Discord user"
)
async def setplayer(interaction: discord.Interaction, user: discord.User):
    
    # First we need to check if this is a valid channel for setting players
    channel_id = str(interaction.channel_id )

    # Should check if it is the auction channel
    isInfo = auction.get("info_channel_id") == channel_id

    if not isInfo:
        await interaction.response.send_message("You cannot add players here", ephemeral=True)
        return

    player_id = str(user.id)

    players = auction["players"]

    displayName = await getDisplayName(interaction, user)

    players[player_id] = {"name": displayName, "budget": 1500, "mons": {}, "number" : 0}

    saveAuction()

    msg_ids = auction["msg_id"]

    all_embeds = auction_msg()

    # Update embed
    channel = interaction.channel
    for msg_id, embed_obj in zip(msg_ids, all_embeds):
        msg = await channel.fetch_message(msg_id)
        await msg.edit(embed=embed_obj)

    await interaction.response.send_message(
        f"{displayName} has been added.",
        ephemeral=True
    )

# Auction Autocomplete
async def item_autocomplete(interaction: discord.Interaction, current: str):

    return [
        app_commands.Choice(name=key, value=key)
        for key in itemList
        if current.lower() in key.lower()
    ][:25]

@app_commands.command(name="bid")
@app_commands.describe(pokemon="Pokemon Name", amount="Bid amount (they will be rounded down to nearest 5)")
@app_commands.autocomplete(pokemon=item_autocomplete)
async def bid(interaction: discord.Interaction, pokemon: str, amount: int):

    channel_id = str(interaction.channel_id)

    bidder_id = str(interaction.user.id)

    amount = (amount // 5) * 5

    bidding = auction.get("bidding_channel_id") == channel_id

    if not bidding: #Check if is in the correct Channel
        await interaction.response.send_message(
            "Bids must be placed in the bidding channel.",
            ephemeral=True
        )
        return

    info_channel_id = auction["info_channel_id"]
    auctionList = auction["pokemon"]
    players = auction["players"]

    # Check Valid Pokemon
    if pokemon not in itemList:
        await interaction.response.send_message("Invalid Pokemon", ephemeral=True)
        return

    # Check Valid Player
    playerInfo = players.get(bidder_id)
    if not playerInfo:
        await interaction.response.send_message("You aren't cool enough to bid here")
        return
    
    name    = playerInfo["name"]
    budget  = playerInfo["budget"]
    number  = playerInfo["number"]
    secured = auction["secured_mons"]

    # Check Valid Bid
    if amount > budget:
        await interaction.response.send_message(
            f"Your remaining budget is only {budget} points."
        )
        return
    
    # Check Valid Bid
    if amount + (7-number) * 50 > budget:
        await interaction.response.send_message(
            f"You still need to draft {(8-number)} more mons, but you only have {budget} points."
        )
        return
    
    # Check Secured
    if pokemon in secured:
        await interaction.response.send_message(
            f"This pokemon is already secured"
        )
        return

    if pokemon in auctionList:
        if amount <= auctionList[pokemon]['bid']:
            await interaction.response.send_message(
                f"Your bid must exceed the current bid ({auctionList[pokemon]['bid']})."
            )
            return
        
        else: # Successful Overbid
            oldBid = auctionList[pokemon]["bid"]
            oldBidder = auctionList[pokemon]["bidder_id"]
            
            players[oldBidder]["budget"] += oldBid # refund
            players[oldBidder]["number"] -= 1 # one less pokemon
            players[bidder_id]["budget"] -= amount # take new bid
            players[bidder_id]["number"] += 1 # one more pokemon
            
            auctionList[pokemon]["bid"] = amount # update new bid
            auctionList[pokemon]["bidder"] = name 
            auctionList[pokemon]["bidder_id"] = bidder_id

            initial = auctionList[pokemon]["initial"]
            currentTime = int(time.time())
            elapsed = currentTime - initial
            auctionList[pokemon]["endtime"] = int(initial + 0.75 * elapsed + 86400)
            # auctionList[pokemon]["endtime"] = int(initial + 0.75 * elapsed + 240)

            await interaction.response.send_message(
                f"You bid on {pokemon} for {amount}. You have {budget - amount} points left."
            )
            await interaction.followup.send(
                f"<@{oldBidder}>, you got outbid on {pokemon}"
            )


    elif amount < 50:
        await interaction.response.send_message(
            "The minimum bid is 50 points"
            )
        return
    
    else: # sucessful initial bid
        currentTime = int(time.time())
        auctionList[pokemon] = {
            "bid": amount,
            "bidder": name,
            "bidder_id": bidder_id,
            "initial": currentTime,
            "endtime": currentTime + 86400
            # "endtime": currentTime + 240
        }
        playerInfo["budget"] = playerInfo["budget"] - amount
        playerInfo["number"] = playerInfo["number"] + 1
        await interaction.response.send_message(
            f"You bid on {pokemon} for {amount}. You have {budget - amount} points left."
            )

    saveAuction()


    msg_ids = auction["msg_id"]

    all_embeds = auction_msg()

    # Update embed
    channel = interaction.guild.get_channel(int(info_channel_id))
    for msg_id, embed_obj in zip(msg_ids, all_embeds):
        msg = await channel.fetch_message(msg_id)
        await msg.edit(embed=embed_obj)


@app_commands.command(name="peek")
@app_commands.describe(pokemon="Pokemon Name")
@app_commands.autocomplete(pokemon=item_autocomplete)
async def peek_pokemon(interaction: discord.Interaction, pokemon: str):

    pokemonInfo = auction["pokemon"].get(pokemon)

    if pokemonInfo:
        bid = pokemonInfo["bid"]
        bidder = pokemonInfo["bidder"]
        endtime = pokemonInfo["endtime"]
        await interaction.response.send_message(f"{bidder} is currently bidding {bid} on {pokemon}. Secure Time: <t:{endtime}:R>")
    else:
        await interaction.response.send_message(f"{pokemon} is currently not being bid on")

@app_commands.command(name="peek_player")
@app_commands.describe(player = "player")
async def peek_player(interaction: discord.Interaction, player: discord.User):
    
    player_id = str(player.id)

    if player_id in auction["players"]:
        pokemonList = auction["pokemon"]
        filterPokemon = [k for k, v in sorted(pokemonList.items(),key=lambda item: item[1]["bid"],reverse = True)
        if v["bidder_id"] == player_id]

        auctionEmbed = discord.Embed(
            title = f"{auction['players'][player_id]['name']}\'s bids",
            color = 2943779
        )
    
        auctionLines = []

        for poke in filterPokemon:
            auctionLines.append(f"`{poke[:15]:<15} | {pokemonList[poke]['bid']:<4} |` <t:{pokemonList[poke]['endtime']}:R>")

        auctionEmbed.add_field(
            name = f"`{'Pokémon':<15} | {'Bid':<4} |` Secure Time",
            value = "\n".join(auctionLines),
            inline= False
        )

        await interaction.response.send_message(embed = auctionEmbed, ephemeral = True)

    else:
        await interaction.response.send_message("This user is not participating", ephemeral = True)



async def finalize_expired_auctions(client):
    now = int(time.time())
    expired = []

    # Find expired Pokémon
    for mon, data in auction["pokemon"].items():
        if now >= data["endtime"]:
            expired.append(mon)

    bidding_channel_id = auction.get("bidding_channel_id")
    bidding_channel = None
    if bidding_channel_id:
        bidding_channel = client.get_channel(int(bidding_channel_id))

    # Finalize each one
    for mon in expired:
        data = auction["pokemon"].pop(mon)

        bidder_id = data["bidder_id"]
        price = data["bid"]

        player = auction["players"][bidder_id]

        # Add Pokémon to secured mons
        player["mons"][mon] = price

        auction["secured_mons"].append(mon)

        # Send Discord message if channel exists
        if bidding_channel:
            await bidding_channel.send(f"{mon} has been secured by <@{bidder_id}> for {price}!")
    
    if expired:
        info_channel_id = auction.get("info_channel_id")
        msg_ids = auction["msg_id"]
        channel = client.get_channel(int(info_channel_id))
        
        all_embeds = auction_msg()  

        # update info message
        for msg_id, embed_obj in zip(msg_ids, all_embeds):
            msg = await channel.fetch_message(msg_id)
            await msg.edit(embed=embed_obj)  # single embed per message

        saveAuction()


auction_watcher = None

def start_auction_watcher(client):
    global auction_watcher

    @tasks.loop(seconds=30)
    async def watcher_loop():
        # channel_id = int(auction["info_channel_id"])
        # channel = client.get_channel(channel_id)
        # await channel.send("hi")
        if auction:
            await finalize_expired_auctions(client)

    @watcher_loop.before_loop
    async def before_watcher():
        await client.wait_until_ready()

    auction_watcher = watcher_loop
    auction_watcher.start()
