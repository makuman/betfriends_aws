
import os
import re
from collections import defaultdict

from dotenv import load_dotenv
from pymongo import MongoClient
from calculation_functions import CalculationFunctions
from mongo_functions import MongoHandler

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

connection_string = os.environ["MONGO_URI"]
client = MongoClient(connection_string)
mongo_handler = MongoHandler(connection_string)
#

# db_name = "MackTestProject"
# collection_name = "match_schedule"
#
# collection = mongo_handler.read_from_mongo(db_name, collection_name)
#
# # Example query using the collection object
# start_date_str = "2024-03-26"
# end_date_str = "2024-03-28"
# filtered_documents = [doc for doc in collection if doc["DATE"] >= start_date_str and doc["DATE"] <= end_date_str]
#
# # You can iterate over "data" to access individual documents
# for document in filtered_documents:
#     print(document)
#


# db_name = "MackTestProject"
# collection_name = "players_stats"
# # data = read_data_from_mongodb(db_name, collection_name)
# data = mongo_handler.read_from_mongo(db_name, collection_name)
#
# for document in data:
#     player_name = document["player_name"]
#     for result in document["comparison_results"]:
#         # print(result)
#     print([player_name, result
#

#
db_name = "MackTestProject"
collection_stats = "players_stats"
data = mongo_handler.read_from_mongo(db_name, collection_stats)


def calculate_net_profit(sample_data, match_number):
    match_players = []

    # Filter players for the given match number
    for player_data in sample_data:
        player_name = player_data["player_name"]
        for result in player_data["comparison_results"]:
            if result["match_number"] == match_number:
                match_players.append({
                    "player_name": player_name,
                    "match_number": match_number,
                    "selected_team": result["selected_team"],
                    "winning_team": result["winning_team"],
                    "score": result["score"]
                })
                break  # Break once match number is found to avoid duplicates

    # Total number of players for the match
    total_players = len(match_players)

    # Calculate the total amount lost by losing players
    losing_players_amount = sum(1 for player in match_players if player["score"] == 0)

    # Calculate the total amount won by winning players
    winning_players_amount = total_players - losing_players_amount

    # Calculate the cumulative amount for winners
    if winning_players_amount != 0:
        loosers_money_cumm = round(losing_players_amount / winning_players_amount, 3)
    else:
        loosers_money_cumm = 0

    # Calculate the net profit for each winning player
    for player in match_players:
        if player["score"] == 1:
            player["net_profit"] = 1 + loosers_money_cumm
        else:
            player["net_profit"] = 0

    return match_players

def calculate_total_profit(sample_data):
    distinct_match_numbers = set()

    for i in sample_data:
        poll_responses = i["poll_responses"]
        for response in poll_responses:
            match_number = response["match_number"]
            distinct_match_numbers.add(match_number)

    # Initialize dictionaries outside the loop
    player_invested_amount = defaultdict(int)
    player_net_profit = defaultdict(float)

    for i in distinct_match_numbers:
        result = calculate_net_profit(sample_data, i)
        for player_data in result:
            player = player_data["player_name"]
            invested_amount = 1  # Assuming fixed investment amount for each match
            net_profit = player_data["net_profit"]

            player_invested_amount[player] += invested_amount
            player_net_profit[player] += net_profit

    # Return the total invested amount and net profit for each player
    player_results = []
    for player in player_invested_amount.keys():
        player_result = {
            "player": player,
            "invested_amount": player_invested_amount[player],
            "net_profit": player_net_profit[player]
        }
        player_results.append(player_result)

    return player_results


# result = calculate_total_profit(data)
# print(result)


db_name = "MackTestProject"
collection_stats = "date_filter"
data = mongo_handler.read_from_mongo(db_name, collection_stats)
start_date = None
end_date = None
for item in data:
    if item["id"] == "1":
        start_date = item["start_date"]
        end_date = item["end_date"]
        break

print(start_date,end_date)


# for player_result in result:
#     print(f"Player: {player_result["player"]}, Invested Amount: {player_result["invested_amount']}, Net Profit: {player_result['net_profit']}")


#
# for x in data:
#     print(data)
# #
# # Print the result
# for player in result:
#     print(f"Player: {player['player_name']}, Match Number: {match_number}, Net Profit: {player['net_profit']}, score: {1}")



# db_name = 'MackTestProject'
# collection_name = 'players_net_earning'
# data = mongo_handler.read_from_mongo(db_name, collection_name)
#
# def calculate_total_invested_and_net_profit(initial_data):
#     player_stats = {}  # Dictionary to store total invested and net profit for each player
#
#     for data in initial_data:
#         player_name = data['player_name']
#         earnings = data['earnings']
#
#         # Initialize total invested and net profit for the player
#         total_invested = 0
#         total_net_profit = 0
#
#         # Calculate total invested and net profit for each match
#         for earning in earnings:
#             total_invested += earning['score']
#             total_net_profit += earning['net_earning']
#
#         # Update player_stats dictionary with total invested and net profit
#         if player_name in player_stats:
#             player_stats[player_name]['total_invested'] += total_invested
#             player_stats[player_name]['total_net_profit'] += total_net_profit
#         else:
#             player_stats[player_name] = {
#                 'total_invested': total_invested,
#                 'total_net_profit': total_net_profit
#             }
#
#     return player_stats
#
#
# player_stats = calculate_total_invested_and_net_profit(data)
# print(player_stats)
# def update_player_stats(poll_collection, winning_team_collection, players_stats_collection):
#     # Iterate over each player's poll responses
#     for player in poll_collection:
#         player_name = player['player_name']
#         poll_responses = player['poll_responses']
#
#         # Initialize variables to store player statistics
#         total_score = 0
#         total_matches = 0
#
#         # Iterate over each poll response to calculate player statistics
#         for response in poll_responses:
#             match_number = response['match_number']
#             selected_team = response['response']
#
#             # Find the corresponding winning team for the date
#             winning_team = next(
#                 (team['status'] for team in winning_team_collection if int(team['match_number']) == int(match_number)), None)
#
#             # If winning team is found, calculate player score
#             if winning_team:
#                 total_matches += 1
#                 if selected_team == winning_team:
#                     total_score += 1
#
#         # Calculate player's win rate
#         win_rate = total_score / total_matches if total_matches > 0 else 0
#
#         # Update or insert player's statistics in the collection
#         existing_player_stats = next(
#             (entry for entry in players_stats_collection if entry['player_name'] == player_name), None)
#         if existing_player_stats:
#             existing_player_stats['total_score'] = total_score
#             existing_player_stats['total_matches'] = total_matches
#             existing_player_stats['win_rate'] = win_rate
#         else:
#             new_player_stats = {
#                 'player_name': player_name,
#                 'total_score': total_score,
#                 'total_matches': total_matches,
#                 'win_rate': win_rate
#             }
#             players_stats_collection.append(new_player_stats)
#
#     return players_stats_collection
# #
#
db_name = 'MackTestProject'
poll_collection_name = 'poll'
winning_team_collection_name = 'winning_teams'
players_stats_collection_name = 'players_stats'
match_standing = 'match_standing'

db_name = 'MackTestProject'
collection_name = 'match_standing'
db = client.get_database(db_name)
collection = db.get_collection(collection_name)

data = list(collection.find())

    # Retrieve all player inputs from the MongoDB collection
poll_collection = mongo_handler.read_from_mongo(db_name, poll_collection_name)
players_stats_collection = mongo_handler.read_from_mongo(db_name, players_stats_collection_name)
match_standing_collection = mongo_handler.read_from_mongo(db_name, match_standing)

# for i in match_standing_collection:
#     print(i)


# #
# def compare_teams(player_name, poll_responses, winning_teams_collection, poll_collection):
#     comparison_results = []
#
#     # Create a dictionary to map dates to winning teams
#     winning_teams_dict = {team['match_number']: {'status': team['status'], 'match_number': team['match_number']} for team in winning_teams_collection}
#
#     # Iterate over poll_responses to compare teams
#     for response in poll_responses:
#         date = response['date']
#         selected_team = response['response']
#         match_number = int(response['match_number'])
#
#         # Remove the "won by [number] runs" part using regex
#         selected_team = re.sub(r'\s+won\s+by\s+\d+\s+runs?$', '', selected_team)
#         print(f"selected {selected_team}")
#         # Get the winning team for the current date
#         winning_team_info = winning_teams_dict.get(match_number)
#         if winning_team_info:
#             winning_team_status = winning_team_info['status']
#             print(f"winning_team_status {winning_team_status}")
#             match = re.match(r'^(.*?)\s*won\s+by\s+\d+\s+(runs|wkts)?$', winning_team_status)
#             if match:
#                 # Extract the team name
#                 winning_team = match.group(1).strip()
#             else:
#                 # Use the original winning_team_status string as the team name
#                 winning_team = winning_team_status.strip()
#         else:
#             # Handle case when winning team info is not found
#             winning_team = None
#
#         print(f"winning  {winning_team}")
#         # Find the match number for the current date from the poll collection
#         match_number = None
#         for poll in poll_collection:
#             if poll['player_name'] == player_name and any(
#                     resp['date'] == date and (resp['response']).lower == (selected_team).lower for resp in poll['poll_responses']):
#                 match_number = next(resp.get('match_number') for resp in poll['poll_responses'] if
#                                     resp['date'] == date and resp['response'] == selected_team)
#                 break
#
#         # Compare selected team with winning team
#         score = 1 if winning_team and (selected_team.lower() == winning_team.lower()) else 0
#
#         # Append comparison result to the list
#         comparison_results.append({'date': date, 'match_number': match_number, 'selected_team': selected_team,
#                                    'winning_team': winning_team, 'score': score})
#
#     return comparison_results
#



# for player in poll_collection:
#     comparison_results = compare_teams(player['player_name'], player['poll_responses'],
#                                                             match_standing_collection,
#                                                             poll_collection)
#     player['comparison_results'] = comparison_results
#     print(comparison_results)

# for x in match_standing_collection:
#     print(x)
#
# for d in poll_collection:
#     print(d)
# def calculate_net_profit(sample_data, match_number):
#     match_players = []
#
#     # Filter players for the given match number
#     for player_data in sample_data:
#         player_name = player_data['player_name']
#         for result in player_data['comparison_results']:
#             if result['match_number'] == match_number:
#                 match_players.append({
#                     'player_name': player_name,
#                     'selected_team': result['selected_team'],
#                     'winning_team': result['winning_team'],
#                     'score': result['score'],
#                     'match_number': result['match_number']
#                 })
#                 break  # Break once match number is found to avoid duplicates
#
#     # Total number of players for the match
#     total_players = len(match_players)
#
#     # Calculate the total amount lost by losing players
#     losing_players_amount = sum(1 for player in match_players if player['score'] == 0)
#
#     # Calculate the total amount won by winning players
#     winning_players_amount = total_players - losing_players_amount
#
#     # Calculate the cumulative amount for winners
#     if winning_players_amount != 0:
#         loosers_money_cumm = round(losing_players_amount / winning_players_amount, 3)
#     else:
#         loosers_money_cumm = 0
#
#     # Calculate the net profit for each winning player
#     for player in match_players:
#         if player['score'] == 1:
#             player['net_profit'] = 1 + loosers_money_cumm
#         else:
#             player['net_profit'] = 0
#
#     return match_players
#
# encountered_match_numbers = set()
#
# for x in players_stats_collection:
#     d = x['poll_responses']
#     for dd in d:
#         match_number = dd['match_number']
#         if match_number not in encountered_match_numbers:
#             print(match_number)
#             encountered_match_numbers.add(match_number)
#
# for i in calculate_net_profit(players_stats_collection,"13"):
#     print(i)
#
# #
# for i in winning_team_collection:
#     print(i)
#
# for i in match_standing_collection:
#     print(i)


# for player in poll_collection:
#     player_name = player['player_name']
#     poll_responses = player['poll_responses']
#     # print(player_name,poll_responses )
#
#     for response in poll_responses:
#         match_number = response['match_number']
#         selected_team = response['response']
#         # print(match_number, selected_team)
#
# winning_team = next(
#                     (team['status'] for team in match_standing_collection if int(team['match_number']) == int(match_number)), None)
# print(winning_team)
#
# for i in match_standing_collection:
#     if i['match_number'] == match_number:
#         print(i)
# print(match_number)
# updated_players_stats_collection = update_player_stats(poll_collection, match_standing_collection,
#                                                            players_stats_collection)
# # #
# for i in updated_players_stats_collection:
#     print(i)


# from flask import Flask, jsonify
# from datetime import datetime, timedelta
#
# app = Flask(__name__)
#
# @app.route('/')
# def index():
#     # Get the current date
#     current_date = datetime.now().date()
#
#     # Define the start and end date range
#     start_date = datetime.strptime('2024-03-26', '%Y-%m-%d').date()
#     end_date = datetime.strptime('2024-03-28', '%Y-%m-%d').date()
#
#     # If the current date is within the range, return the range
#     if start_date <= current_date <= end_date:
#         return jsonify({
#             'start_date': start_date.strftime('%Y-%m-%d'),
#             'end_date': end_date.strftime('%Y-%m-%d')
#         })
#
#     # If the current date is after the end date, switch to the next 3 days
#     elif current_date > end_date:
#         start_date = end_date + timedelta(days=1)
#         end_date = start_date + timedelta(days=2)
#         return jsonify({
#             'start_date': start_date.strftime('%Y-%m-%d'),
#             'end_date': end_date.strftime('%Y-%m-%d')
#         })
#
#     # If the current date is before the start date, return a message
#     else:
#         return 'Schedule has not started yet.'
#
# if __name__ == '__main__':
#     app.run(debug=True)

#
# db_name = 'MackTestProject'
# collection_name = 'match_standing'
# db = client.get_database(db_name)
# collection = db.get_collection(collection_name)
#
# data = list(collection.find())
#
# # max_values_doc = collection.find_one(
# #     {},  # Empty filter to retrieve all documents
# #     sort=[('match_number', -1), ('date', -1)]  # Sort by match_number and date in descending order
# # )
#
# def find_max_document_in_list_of_dicts(list_of_dicts):
#     max_document = None
#     max_match_number = float('-inf')
#     max_date = None
#
#     for doc in list_of_dicts:
#         match_number = doc.get('match_number', float('-inf'))
#         date = doc.get('date')
#         if match_number > max_match_number or (match_number == max_match_number and date > max_date):
#             max_document = doc
#             max_match_number = match_number
#             max_date = date
#
#     return max_document
#
# max_document = find_max_document_in_list_of_dicts(data)
# print(max_document['item']['matchType'])

# print(max_values_doc)
#
# max_match_number = max_values_doc['match_number']
# max_date = max_values_doc['date']
#
# print("Maximum match number:", max_match_number)
# print("Maximum date:", max_date)