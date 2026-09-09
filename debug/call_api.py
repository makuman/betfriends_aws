from flask import request
import json
import os
import requests
import boto3
import json
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

CRICAPI_KEY = os.environ["CRICAPI_KEY"]
CRICAPI_SERIES_ID = os.environ["CRICAPI_SERIES_ID"]
S3_BUCKET = os.environ.get("S3_BUCKET", "your-s3-bucket-name")

def read_json_from_s3(bucket_name, file_key):
    s3 = boto3.client('s3')
    try:
        response = s3.get_object(Bucket=bucket_name, Key=file_key)
        data = json.loads(response['Body'].read().decode('utf-8'))
        return data
    except Exception as e:
        print("Error reading JSON file from S3:", e)
        return []

def write_json_to_s3(bucket_name, file_key, data):
    s3 = boto3.client('s3')
    try:
        s3.put_object(Bucket=bucket_name, Key=file_key, Body=json.dumps(data))
        print("JSON data successfully written to S3:", file_key)
    except Exception as e:
        print("Error writing JSON data to S3:", e)

api_url = f"https://api.cricapi.com/v1/currentMatches?apikey={CRICAPI_KEY}&offset=0"

response = requests.get(api_url)
all_posts = response.json()
matches = all_posts["data"]
# match_number= "1"
# json_result = [match for match in matches if match.get("matchType") == "Kolkata" and match_number in match.get("name")]

json_result = [match for match in matches if match.get("matchType") == "t20" and match.get("series_id") == CRICAPI_SERIES_ID and "won" in match.get("status", "").lower()]

def extract_integer(s):
    return int("".join(filter(str.isdigit, s)))

# updated_data =[]

bucket_name = S3_BUCKET
file_key = 'data/match_standing.json'

existing_data = read_json_from_s3(bucket_name, file_key)

for item in json_result:
    match_number = extract_integer(item["name"])
    date = item["date"]
    name = item["name"]
    status = item["status"]
    del item["name"]


    match_exists = any(existing_item["match_number"] == match_number for existing_item in existing_data)

    if not match_exists:
        updated_item = {
            "match_number": match_number,
            "date": date,
            "name": name,
            "status": status,
            "item": item
        }

        existing_data.append(updated_item)
    else:
        print(f"Match ID {match_number} already exists in the JSON file. Skipping...")

write_json_to_s3(bucket_name, file_key, existing_data)

