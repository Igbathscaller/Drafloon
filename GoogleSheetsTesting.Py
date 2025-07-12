import gspread
from google.oauth2.service_account import Credentials

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
sheet = client.open(sheetName).worksheet("Raw Stats")

# Read a cell
value = sheet.cell(1, 2).value
print(value)
