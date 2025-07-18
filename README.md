# Drafloon
Draft Automation Bot

- Purpose is expediate the draft process and automate left picks and skipping.

### Draft Command Specifics
#### Order of Checks
- Check if the input is valid (they chose from the options)
- Check if the channel has an associated spreadsheet
- Check if the player is on a team
- Check if the turn of the draft and matches the player's team (allows skipped teams go make up)
- Check if the pokemon is draft legal (99 points are not allowed + not on draft board)
- Check if you have enough slots to draft (Currently hard-coded 11 slots)
- Check if you have enough points to draft the mon
- Check if you someone has drafted the pokemon

## Plan

### Google Sheets
- Possibly allow people to update their own logos and teamNames (optional/low prio)

### Things to Implement
- Locks for taking turns (optional/low prio) 
It seems pretty hard to sync up, but it is theoretically possible for players on the same team to draft at the same time.
- Left Picks should probably limited to max 10 with an optional 2 backups in case of snipe.
- Need to add a way to delete left picks
- Maybe a way to also edit the left picks or replace them, so they don't need to delete and keep readding them
- Needs to add the left picks when skipped or give players an option to set a timer for when to do a left pick
- Probably a way to remove a player from the skipped list in case of manual draft.

## Things that were successfully implemented
#### Discord Interaction
- Command to Link a trades channel with a corresponding spreadsheet (mods only)
- Command to Link a user to a specific team/roster (mods only)
- Command to see the players on a roster
- Command to see associate spreadsheet (might make mod only)

#### Google Sheets
- Ability to view roster
- Ability to update roster
- Stores links to roster of startup so we reduce queries
- Draft command currently takes 3 queries (checks if the pokemon has been seen before, finds the next free slot, updates the sheet)
  - Query can be reduced if we save the pokemon on the board (but this leads to issues if we manually update the board)
  - Same issue arises if we want to update the next free slot.
  - Both issues can be remedied by having an update doc function whenever we make a manual change to the doc. Signficantly reducing query time.
- Loads saved spreadsheets on runtime
- Whenever a spreadsheet is opened, it is saved so it does not need to be re-accessed.

#### Draft Functionality
- Ability to draft picks
- Ability to leave picks
- Automatically starts a timer when you run
- Skips when you don't make a pick by a certain time.
- Saves list of pokemon on startup
