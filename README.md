# Drafloon
Draft Automation Bot

- Purpose is expediate the draft process and automate left picks and skipping.
- Also has the ability to create weekly schedule channel after importing a sheet.

## How to SetUp

To Describe in the Future

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
- Set/Update/Create/Delete Scheduling Channels

### Channel Management Command Details
- Set_Sheet must be run before all commands except Scheduling related commands.
- All Drafts start as paused after setting the sheet. To allow players to draft, you must unpause the draft. No other functionality is prevented by pausing the draft.
- The bot stores a local copy of all pokemon drafted, and determines the turn by counting the number of pokemon and skipped players. In case of a manual update, use Draft_Control Refresh in order to refresh the data.
- Since turn is determined by the number of pokemon and skipped players, you should add and remove all skipped players appropriately, so it tracks the turn correctly.
- Players must be assigned to a team so they can access the draft and leaving pick functionality.
- Teams are denoted by their *draft number*, not their actual name. No command accepts actual Team Names as an input. (Can be changed in the future with Autocomplete).

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

### Leave/View_Picks Details
- You can leave up to 10 picks with up to 2 backups, and you can optionally select a higher priority.
- It performs the same checks as the Draft Command to determine if it is a valid draft.
- You can delete/remove picks by using the View Picks Command.
- All View_Picks Embeds are synced, and when a pick is removed, it is removed for all users viewing picks (including mods).

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
