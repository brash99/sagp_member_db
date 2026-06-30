from pathlib import Path

RAW_DIR = Path("raw")
OUTPUT_DIR = Path("output")

GOOGLE_CONTACT_FIELDS = [
    "First Name", "Middle Name", "Last Name", "Name Prefix", "Name Suffix",
    "Organization Name", "Organization Title", "Notes", "E-mail 1 - Value",
    "E-mail 2 - Value", "Phone 1 - Value", "Phone 2 - Value",
    "Address 1 - Formatted", "Address 1 - City", "Address 1 - Region",
    "Address 1 - Postal Code", "Address 1 - Country"
]

REGION_FROM_FILE = {
    "PA.csv": "PA",
    "NJ.csv": "NJ",
    "NYD.csv": "NYD",
    "NYU.csv": "NYU",
    "SAGP Canada.csv": "Canada",
    "SAGP World Other.csv": "World Other",
    "SAGP W pd.csv": "World Paid",
    "SAGP Two Paid.csv": "Two Paid",
    "contacts.csv": "Master Contacts",
}
