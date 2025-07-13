import re
import gspread
from gspread.utils import ValueRenderOption
from google.oauth2.service_account import Credentials
import json

# Define scope
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Path to your service account key JSON
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

    print(f"Updated {source_sheet_name}!{source_cell} to '{value}'")


def addPokemon(spreadSheet: gspread.spreadsheet, roster: int, draftNum: int, pokemon:str):
    updateRoster(spreadSheet, roster+1, draftNum+3, pokemon)

def removePokemon(spreadSheet: gspread.spreadsheet, roster: int, draftNum: int):
    updateRoster(spreadSheet, roster+1, draftNum+3, "-")


def getPokemon(spreadSheet: gspread.spreadsheet, roster: int, draftNum: int):
    return readRoster(spreadSheet, roster, draftNum+4)

print(getPokemon(spreadSheet, 1, 1))
print(getPokemon(spreadSheet, 1, 2))
print(getPokemon(spreadSheet, 1, 3))
