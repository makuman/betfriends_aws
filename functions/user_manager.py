from .s3_file_manager import s3_file_manager
class UserManager:
    @staticmethod
    def load_users(bucket_name, filename):
        try:
            data = s3_file_manager.read_json_file_from_s3(bucket_name, filename)
            return data
        except Exception as e:
            print(f"Error loading user data from S3: {e}")
            return {}

    @staticmethod
    def save_users(users, bucket_name, filename):
        try:
            s3_file_manager.write_json_file_to_s3(users, bucket_name, filename)
        except Exception as e:
            print(f"Error saving user data to S3: {e}")

    # @staticmethod
    # def authenticate(username, password, bucket_name, filename):
    #     users = UserManager.load_users(bucket_name, filename)
    #     return username in users and users[username]['password'] == password
