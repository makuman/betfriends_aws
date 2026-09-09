import json
import os
import boto3
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

def load_dates_from_s3(bucket_name, file_key):
    try:
        s3 = boto3.client('s3')
        response = s3.get_object(Bucket=bucket_name, Key=file_key)
        return json.loads(response['Body'].read().decode('utf-8'))
    except (boto3.exceptions.ClientError, KeyError) as e:
        print("Error loading JSON file from S3:", e)
        return []

def save_dates_to_s3(dates, bucket_name, file_key):
    try:
        s3 = boto3.client('s3')
        s3.put_object(Bucket=bucket_name, Key=file_key, Body=json.dumps(dates))
        print("JSON data successfully written to S3:", file_key)
    except boto3.exceptions.ClientError as e:
        print("Error writing JSON data to S3:", e)

def update_max_id_is_active_false(bucket_name, file_key):
    # Load the data from S3
    dates = load_dates_from_s3(bucket_name, file_key)

    # Find the maximum ID
    max_id = max(int(date['id']) for date in dates)

    # Update the is_active status to False for the entry with the maximum ID
    for date in dates:
        if date.get('id') == str(max_id):
            date['is_active'] = False
            break

    # Save the updated data back to S3
    save_dates_to_s3(dates, bucket_name, file_key)

if __name__ == "__main__":
    bucket_name = os.environ.get("S3_BUCKET", "your-s3-bucket-name")
    file_key = 'data/poll_date.json'
    update_max_id_is_active_false(bucket_name, file_key)
