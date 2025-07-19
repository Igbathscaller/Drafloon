import re
import gspread
from gspread.utils import rowcol_to_a1
from google.oauth2.service_account import Credentials

# Define scope
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Authorization
creds = Credentials.from_service_account_file("../drafloon-959516a4b9be.json", scopes=scope)
client = gspread.authorize(creds)

# What Sheets you need
# Roster Code - to update the roster and read it
# Draft Code - to get the number of points of each pokemon

# Initialize SpreadSheet Dictionary
spreadDict = {}

# Open the Spreadsheets by key and adds it to the dictionary
def loadSheet(channelID:str, spreadsheetKey:str):
    spreadDict[channelID] = client.open_by_key(spreadsheetKey)

# Initialize Pokemon Points Dictionary
pointDict = {}

# Get Spreadsheets by key and adds points to the dictionary
def loadPoints(channelID:str):
    sheet = spreadDict[channelID].worksheet("Draft Code")
    pokemon = sheet.col_values(2)[1:]    # pokemon
    points  = sheet.col_values(4)[1:]    # points
    
    points = list(map(safe_int, points))

    pointDict[channelID] = dict(zip(pokemon, points))
    pointDict[channelID]["Total"] = safe_int(sheet.cell(1,6).value)
    # pointDict[channelID][pokemon_name] -> points

# Initialize Update Dictionary
writeCellDict = {}

# Get Spreadsheets by key and adds points to the dictionary
def loadWriteCells(channelID:str, teamCount: int):
    rosterSheet = spreadDict[channelID].worksheet("Roster Code")
    
    # clear and initialize the elements
    writeCellDict[channelID] = {}

    # Get all the formulas in one call
    formulas = rosterSheet.get(f"B2:{rowcol_to_a1(2, 1 + teamCount)}", value_render_option='FORMULA')
    formulas = formulas[0]

    # range(teamCount) is 0 indexed
    for team in range(teamCount):    
        # Get the formula string from the formula cell
        formula = formulas[team]

        # Regex to extract 'SheetName!ColumnStartRow:ColumnEndRow'
        match = re.search(r'([a-zA-Z0-9_]+)!\$?([A-Z]+)(\d+):\$?[A-Z]+(\d+)', formula)
        if not match:
            print("Could not parse: " + formula)

        source_sheet_name, column_letter, start_row, end_row = match.groups()

        # The teams are 1-indexed for the purpose of the bot
        writeCellDict[channelID][team + 1] = {
            "sheet":source_sheet_name,
            "col":  column_letter,
            "start":int(start_row),
            "end":  int(end_row)
        }
    # writeCellDict[channelID][teamNum] -> {sheet}!{col}{start}:{col}{end}


# Helper Function
def safe_int(value):
    try:
        return int(value)
    except ValueError:
        return 0

### Roster Access Functionality 

def readRosterCell(spreadSheet: gspread.Spreadsheet, roster: int, row: int):

    rosterSheet = spreadSheet.worksheet("Roster Code")

    #Get
    result = rosterSheet.cell(row + 1,roster + 1).value

    return(result)

def readRosterRange(spreadSheet: gspread.Spreadsheet, roster: int, rows: range):

    rosterSheet = spreadSheet.worksheet("Roster Code")

    #Get
    result = rosterSheet.range(rows[0]+1, roster+1, rows[-1]+1, roster+1)

    return(result)

# returns all pokemon on the roster as a set
def readFullRoster(spreadSheet: gspread.Spreadsheet, rosters: int, pokemon: int) -> set:

    rosterSheet = spreadSheet.worksheet("Roster Code")

    result = rosterSheet.range(6, 2, 6 + pokemon, rosters)

    return {cell.value for cell in result}

# New Method to update Roster, this method utilizes a dictionary loaded at startup
def updateRoster(channelID: str, team: int, arrIndex: int, value:str):

    spreadSheet = spreadDict[channelID]
    writeCell   = writeCellDict[channelID][team]
    sheet_name  = writeCell["sheet"]
    col_letter  = writeCell["col"]
    start_row   = writeCell["start"]

    # Final source cell to update
    source_row = start_row + arrIndex
    source_cell = f"{col_letter}{source_row}"

    # Open the correct worksheet and update the cell
    source_sheet = spreadSheet.worksheet(sheet_name)
    source_sheet.update_acell(source_cell, value)

    # print(f"Updated {source_sheet_name}!{source_cell} to '{value}'")



#Roster Functions

def updateCoach(channelID: str, team: int, name:str):
    updateRoster(channelID, team, 0, name)

def updateTeamName(channelID: str, team: int, name:str):
    updateRoster(channelID, team, 1, name)

def updateTZ(channelID: str, team: int, tz:str):
    updateRoster(channelID, team, 2, tz)

def addPokemon(channelID: str, team: int, draftNum: int, pokemon:str):
    updateRoster(channelID, team, draftNum+3, pokemon)

def removePokemon(channelID: str, team: int, draftNum: int):
    updateRoster(channelID, team, draftNum+3, "-")

def getTeamInfo(spreadSheet: gspread.spreadsheet, roster: int):
    teamInfo = readRosterRange(spreadSheet, roster, range(3))
    return (f"Coach: {teamInfo[0].value}\n"
            f"Team Name: {teamInfo[1].value}\n"
            f"Time Zone: {teamInfo[2].value}")

def getPokemon(spreadSheet: gspread.spreadsheet, roster: int):
    return list(map(lambda x: x.value, readRosterRange(spreadSheet, roster, range(5,16))))

# Returns (index of next slot, point total)
def getNextSlot(spreadSheet: gspread.spreadsheet, channel_id: str, roster: int):
    rosterList = readRosterRange(spreadSheet, roster, range(5,16))
    
    pointTotal = 0
    for i in range(11):
        if rosterList[i].value in ("-","",None):
            return (i+1, pointTotal)
        else:
            pointTotal += pointDict[channel_id].get(rosterList[i].value, 0)
    return (-1, pointTotal)

# Testing Functions Now

# loadSheet("1","1GMJELKMakvgJwIjnmydQksq4pCx7al04CF3HiL777Io")
# loadPoints("1")
# loadWriteCells("1",16)
