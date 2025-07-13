import re
import gspread
from google.oauth2.service_account import Credentials

# Define scope
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Authorization
creds = Credentials.from_service_account_file("../drafloon-959516a4b9be.json", scopes=scope)
client = gspread.authorize(creds)


# Open a sheet by name
sheetName = "ACORP Draft Testing"
spreadSheet = client.open(sheetName)

def readRoster(spreadSheet: gspread.Spreadsheet, roster: int, row: int):

    rosterSheet = spreadSheet.worksheet("Roster Code")

    #Get
    result = rosterSheet.cell(row + 1,roster + 1).value

    return(result)

def readRosterRange(spreadSheet: gspread.Spreadsheet, roster: int, rows: range):

    rosterSheet = spreadSheet.worksheet("Roster Code")

    #Get
    result = rosterSheet.range(rows[0]+1, roster+1, rows[-1]+1, roster+1)

    return(result)


#Roster Code is read-only, so I have to parse the formula to get the actual code.

def updateRoster(spreadSheet: gspread.Spreadsheet, cellCol: int, arrIndex: int, value:str):

    rosterSheet = spreadSheet.worksheet("Roster Code")

    # Get the formula string from the formula cell
    formula = rosterSheet.cell(2, cellCol, value_render_option="FORMULA").value

    # Regex to extract 'SheetName!ColumnStartRow:ColumnEndRow'
    match = re.search(r'([a-zA-Z0-9_]+)!\$?([A-Z]+)(\d+):\$?[A-Z]+(\d+)', formula)
    if not match:
        print("Could not parse: " + formula)

    source_sheet_name, column_letter, start_row, end_row = match.groups()
    start_row, end_row = int(start_row), int(end_row)

    # Final source cell to update
    source_row = start_row + arrIndex
    source_cell = f"{column_letter}{source_row}"

    # Open the correct worksheet and update the cell
    source_sheet = spreadSheet.worksheet(source_sheet_name)
    source_sheet.update_acell(source_cell, value)

    # print(f"Updated {source_sheet_name}!{source_cell} to '{value}'")


#All Usable Functions

def updateCoach(spreadSheet: gspread.spreadsheet, roster: int, name:str):
    updateRoster(spreadSheet, roster+1, 0, name)

def updateTeamName(spreadSheet: gspread.spreadsheet, roster: int, name:str):
    updateRoster(spreadSheet, roster+1, 1, name)

def updateTZ(spreadSheet: gspread.spreadsheet, roster: int, tz:str):
    updateRoster(spreadSheet, roster+1, 2, tz)

def getTeamInfo(spreadSheet: gspread.spreadsheet, roster: int):
    teamInfo = readRosterRange(spreadSheet, roster, range(3))
    return (f"Coach: {teamInfo[0].value}\n"
            f"Team Name: {teamInfo[1].value}\n"
            f"Time Zone: {teamInfo[2].value}")

def addPokemon(spreadSheet: gspread.spreadsheet, roster: int, draftNum: int, pokemon:str):
    updateRoster(spreadSheet, roster+1, draftNum+3, pokemon)

def addPokemon(spreadSheet: gspread.spreadsheet, roster: int, draftNum: int, pokemon:str):
    updateRoster(spreadSheet, roster+1, draftNum+3, pokemon)

def removePokemon(spreadSheet: gspread.spreadsheet, roster: int, draftNum: int):
    updateRoster(spreadSheet, roster+1, draftNum+3, "-")

def getPokemon(spreadSheet: gspread.spreadsheet, roster: int, draftNum: int):
    return readRoster(spreadSheet, roster, draftNum+4)

def getNextSlot(spreadSheet: gspread.spreadsheet, roster: int):
    rosterList = readRosterRange(spreadSheet, roster, range(4,16))
    for i in range(12):
        if rosterList[i].value in ("-",None,""):
            return i
    return -1
