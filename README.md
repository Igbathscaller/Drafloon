# Drafloon
Draft Automation Bot

- Purpose is expediate the draft process and automate left picks and skipping.

## Plan
### Discord Bot (what information to store)
- Link a trades channel with its corresponding spreadsheet (limit only to mods)
- Command to link a user to a specific team/roster (limit only to mods)
- *Update when more things need to be stored*
- List of Pokemon
- Update the Json File and discord file to allow easier access to ids.
- **Update the code so that it only reads the JSON file once, still update it on each write/update to the JSON variable**

### Discord Bot (player commands and functionality)
- Add the ability to draft and leave picks
  - For leaving picks we can start with a ranked system that goes to the next one if it is taken
  - We can add more specific functionality in case something is sniped or taken
  - Can possibly do it with an app but this would be significantly more implementation time (I also only have a 1 cpu server, so I want to limit commands)

#### Draft Command Specifics
##### Order of Errors
- Check if the input is valid (they chose from the options)
- Check if the channel has an associated spreadsheet
- Check if the player is on a team
- Check if the turn of the draft and matches the player's team (allows skipped teams go make up)
- Check if the pokemon is draft legal (99 points are not allowed + not on draft board)
- Check if you have enough slots to draft (Currently hard-coded 11 slots)
- Check if you have enough points to draft the mon
- Check if you someone has drafted the pokemon


### Google Sheets
- Only needs access to the roster page
- Possibly allow people to update their own logos and teamNames


### Things to Implement QOL/ Prevent bad actors
- Locks for taking turns. 
It seems pretty hard to sync up, but it is theoretically possible for players on the same team to draft at the same time.
- Left Picks should probably limited to max 10 with an optional 2 backups in case of snipe.
- Should I make a seperate Json File for it? I dont think storing in memory is that great.


### Order of Modules to prevent Circular Imports
1. Mainbot (Highest Level, nothing imports this)
2. DraftCommands
3. GoogleInteraction
4. ChannelServer (Cannot import any modules)
