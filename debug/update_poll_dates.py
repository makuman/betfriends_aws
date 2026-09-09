import json
import os
import boto3
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

def load_dates_from_json(bucket_name, file_key):
    s3 = boto3.client('s3')
    try:
        response = s3.get_object(Bucket=bucket_name, Key=file_key)
        data = json.loads(response['Body'].read().decode('utf-8'))
        return data
    except Exception as e:
        print("Error reading JSON file from S3:", e)
        return []

def save_dates_to_json(dates, bucket_name, file_key):
    s3 = boto3.client('s3')
    try:
        s3.put_object(Bucket=bucket_name, Key=file_key, Body=json.dumps(dates))
        print("JSON data successfully written to S3:", file_key)
    except Exception as e:
        print("Error writing JSON data to S3:", e)

def update_dates(bucket_name, file_key):
    # Load existing dates from JSON
    dates = load_dates_from_json(bucket_name, file_key)

    # Find the date range with end_date as today
    today = datetime.now().date()
    for date in dates:
        if datetime.strptime(date['end_date'], '%Y-%m-%d').date() == today:
            # Set is_active to False for old date
            date['is_active'] = False

            # Check if the new date range already exists
            new_start_date = today + timedelta(days=1)
            new_end_date = new_start_date + timedelta(days=2)
            new_date = {
                "start_date": new_start_date.strftime('%Y-%m-%d'),
                "end_date": new_end_date.strftime('%Y-%m-%d'),
            }
            if not any(d['start_date'] == new_date['start_date'] and d['end_date'] == new_date['end_date'] for d in dates):
                # Add new date range if it doesn't exist
                new_date['id'] = str(len(dates) + 1)
                new_date['is_active'] = True
                dates.append(new_date)

            # Save updated dates to JSON on S3
            save_dates_to_json(dates, bucket_name, file_key)
            print(f"New dates added to poll_dates start_date = {new_start_date} and end_date = {new_end_date}")
            break


if __name__ == "__main__":
    # Set your S3 bucket name and file key
    bucket_name = os.environ.get("S3_BUCKET", "your-s3-bucket-name")
    file_key = 'data/poll_date.json'
    update_dates(bucket_name, file_key)
