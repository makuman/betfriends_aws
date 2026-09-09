import boto3
import json

class s3_file_manager:
    def __init__(self):
        pass

    @staticmethod
    def read_json_file_from_s3(bucket_name, filename):
        try:
            s3 = boto3.client('s3')
            response = s3.get_object(Bucket=bucket_name, Key=filename)
            data = response['Body'].read().decode('utf-8')
            return json.loads(data)
        except Exception as e:
            print(f"Error reading JSON file from S3: {e}")
            return []

    @staticmethod
    def write_json_file_to_s3(data, bucket_name, filename):
        try:
            s3 = boto3.client('s3')
            s3.put_object(Bucket=bucket_name, Key=filename, Body=json.dumps(data))
            print(f"JSON file '{filename}' uploaded to S3 successfully.")
        except Exception as e:
            print(f"Error writing JSON file to S3: {e}")

# Example usage:
# s3_file_manager = S3FileManager()
# data = s3_file_manager.read_json_file_from_s3('your-bucket-name', 'your-file.json')
# s3_file_manager.write_json_file_to_s3(data, 'your-bucket-name', 'new-file.json')