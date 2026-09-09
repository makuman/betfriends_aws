import os
from flask import Flask
from pymongo import MongoClient
from dotenv import load_dotenv
import csv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# app = Flask(__name__)
client = MongoClient(os.environ["MONGO_URI"])

db = client.get_database("MackTestProject")
collection = db.get_collection("match_schedule")
# Read data from CSV file and insert into MongoDB
with open("data/ipl_data.csv", "r") as file:
    reader = csv.DictReader(file)
    for row in reader:
        # Convert keys to strings and remove any None keys
        cleaned_row = {str(key): value for key, value in row.items() if key is not None}
        # Insert each row as a document into the collection
        collection.insert_one(cleaned_row)

print("Data inserted into MongoDB successfully.")