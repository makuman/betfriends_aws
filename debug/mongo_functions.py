from pymongo import MongoClient

class MongoHandler:
    def __init__(self, connection_string):
        self.client = MongoClient(connection_string)

    def write_to_mongo(self, data, db_name, collection_name):
        """
        Write data to MongoDB collection.

        Args:
        - data: The data to be written to the collection.
        - db_name: Name of the MongoDB database.
        - collection_name: Name of the collection within the database.

        Returns:
        - True if data is successfully written, False otherwise.
        """
        try:
            db = self.client.get_database(db_name)
            collection = db.get_collection(collection_name)
            collection.insert_one(data)
            return True
        except Exception as e:
            print(f"Error writing to MongoDB: {e}")
            return False

    def read_from_mongo(self, db_name, collection_name):
        """
        Read data from MongoDB collection.

        Args:
        - db_name: Name of the MongoDB database.
        - collection_name: Name of the collection within the database.

        Returns:
        - A list containing documents retrieved from the collection.
        """
        try:
            db = self.client.get_database(db_name)
            collection = db.get_collection(collection_name)
            data = list(collection.find())
            return data
        except Exception as e:
            print(f"Error reading from MongoDB: {e}")
            return []
