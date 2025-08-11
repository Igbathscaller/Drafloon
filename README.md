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
- lock check for skipping command or at the very least not starting a timer when draft is paused.
- a way to remove a player from the skipped lis
- autoskip and autopause should have timers edited. Implement a way to call timer to autopick and after failing an autopick, it autoskips.
- small change (edit max drafted to 8 or a variable amount. 8 is fine for now)

## How to SetUp

To Do

## Current Commands and Functionality

### Player/Open Commands
- Draft
- Leave_Pick
- View_Picks
- Turn_Info
- View_Players

### Mod/Management Commands
- Set_Sheet (initializes a channel for functionality)
- Draft_Control (view,pause,resume,refresh,end)
- add/remove Players
- add/remove Skipped (for manual additions to drafting)
- Skip
- View_Picks_Mod (view players picks)
- Stop Timer
- Set/Update/Create/Delete Channels

#### Discord Interaction

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
