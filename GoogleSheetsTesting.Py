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
sheet = client.open(sheetName).worksheet("Sprite Gallery")
doc = sheet.get("B3:D1199")

data = {}

for pokemon in doc:
    data[pokemon[0]]= pokemon[2]

# data = {}
# for each in doc:
#     data["pokemon"] = doc

with open("Pokemon.json", "w") as f:
     json.dump(data, f, indent=4)


