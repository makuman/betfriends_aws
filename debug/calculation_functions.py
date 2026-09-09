
from pymongo import MongoClient
class CalculationFunctions:

    @staticmethod
    def find_max_document_in_list_of_dicts(list_of_dicts):
        max_document = None
        max_match_number = float("-inf")
        max_date = None

        for doc in list_of_dicts:
            match_number = doc.get("match_number", float("-inf"))
            date = doc.get("date")
            if match_number > max_match_number or (match_number == max_match_number and date > max_date):
                max_document = doc
                max_match_number = match_number
                max_date = date

        return max_document

    @staticmethod
    def compare_teams(player_name, poll_responses, winning_teams_collection, poll_collection):
        comparison_results = []
        # Create a dictionary to map dates to winning teams
        winning_teams_dict = {team["date"]: team["winner"] for team in winning_teams_collection}

        # Iterate over poll_responses to compare teams
        for response in poll_responses:
            date = response["date"]
            selected_team = response["response"]
            # Get the winning team for the current date
            winning_team = winning_teams_dict.get(date)

            # Find the match number for the current date from the poll collection
            match_number = None
            for poll in poll_collection:
                if poll["player_name"] == player_name and any(
                        resp["date"] == date and resp["response"] == selected_team for resp in poll["poll_responses"]):
                    match_number = next(resp.get("match_number") for resp in poll["poll_responses"] if
                                        resp["date"] == date and resp["response"] == selected_team)
                    break

            # Compare selected team with winning team
            score = 1 if selected_team == winning_team else 0
            # Append comparison result to the list
            comparison_results.append({"date": date, "match_number": match_number, "selected_team": selected_team,
                                       "winning_team": winning_team, "score": score})

        return comparison_results

    @staticmethod
    def update_player_stats(poll_collection, winning_team_collection, players_stats_collection):
        # Iterate over each player"s poll responses
        for player in poll_collection:
            player_name = player["player_name"]
            poll_responses = player["poll_responses"]

            # Initialize variables to store player statistics
            total_score = 0
            total_matches = 0

            # Iterate over each poll response to calculate player statistics
            for response in poll_responses:
                match_number = response["match_number"]
                selected_team = response["response"]

                # Find the corresponding winning team for the date
                winning_team = next(
                    (team["winner"] for team in winning_team_collection if team["match_number"] == match_number), None)

                # If winning team is found, calculate player score
                if winning_team:
                    total_matches += 1
                    if selected_team == winning_team:
                        total_score += 1

            # Calculate player's win rate
            win_rate = total_score / total_matches if total_matches > 0 else 0

            # Update or insert player's statistics in the collection
            existing_player_stats = next(
                (entry for entry in players_stats_collection if entry['player_name'] == player_name), None)
            if existing_player_stats:
                existing_player_stats['total_score'] = total_score
                existing_player_stats['total_matches'] = total_matches
                existing_player_stats['win_rate'] = win_rate
            else:
                new_player_stats = {
                    'player_name': player_name,
                    'total_score': total_score,
                    'total_matches': total_matches,
                    'win_rate': win_rate
                }
                players_stats_collection.append(new_player_stats)

        return players_stats_collection

    @staticmethod
    def calculate_net_profit(sample_data, match_number):
        match_players = []

        # Filter players for the given match number
        for player_data in sample_data:
            player_name = player_data['player_name']
            for result in player_data['comparison_results']:
                if result['match_number'] == match_number:
                    match_players.append({
                        'player_name': player_name,
                        'selected_team': result['selected_team'],
                        'winning_team': result['winning_team'],
                        'score': result['score'],
                        'match_number': result['match_number']
                    })
                    break  # Break once match number is found to avoid duplicates

        # Total number of players for the match
        total_players = len(match_players)

        # Calculate the total amount lost by losing players
        losing_players_amount = sum(1 for player in match_players if player['score'] == 0)

        # Calculate the total amount won by winning players
        winning_players_amount = total_players - losing_players_amount

        # Calculate the cumulative amount for winners
        if winning_players_amount != 0:
            loosers_money_cumm = round(losing_players_amount / winning_players_amount, 3)
        else:
            loosers_money_cumm = 0

        # Calculate the net profit for each winning player
        for player in match_players:
            if player['score'] == 1:
                player['net_profit'] = 1 + loosers_money_cumm
            else:
                player['net_profit'] = 0

        return match_players

    @staticmethod
    def write_net_profit_to_mongo(net_profit_data, db_name, collection_name,connection_string):
        client = MongoClient(connection_string)
        db = client.get_database(db_name)
        collection = db.get_collection(collection_name)

        for player_data in net_profit_data:
            player_name = player_data['player_name']
            net_profit = player_data['net_profit']
            match_number = player_data['match_number']

            # Check if document exists for the player
            existing_doc = collection.find_one({'player_name': player_name})

            # Construct the new earnings data
            earnings_data = {'match_number': match_number, 'net_earning': net_profit, 'score': 1}

            if existing_doc:
                # Check if the 'earnings' field exists, if not, create it
                if 'earnings' in existing_doc:
                    # Update existing document with new earnings data
                    update_query = {'$push': {'earnings': earnings_data}}
                    update_result = collection.update_one({'player_name': player_name}, update_query)
                    print(f"Updated document for {player_name}: {update_result.modified_count} document(s) modified")
                else:
                    # Add 'earnings' field and push the new earnings data
                    update_query = {'$set': {'earnings': [earnings_data]}}
                    update_result = collection.update_one({'player_name': player_name}, update_query)
                    print(f"Updated document for {player_name}: {update_result.modified_count} document(s) modified")
            else:
                # Create a new document for the player with earnings data
                insert_result = collection.insert_one({'player_name': player_name, 'earnings': [earnings_data]})
                print(f"Inserted document for {player_name}: {insert_result.inserted_id}")


    @staticmethod
    def calculate_total_invested_and_net_profit(initial_data):
        player_stats = {}  # Dictionary to store total invested and net profit for each player

        for data in initial_data:
            player_name = data['player_name']
            earnings = data['earnings']

            # Initialize total invested and net profit for the player
            total_invested = 0
            total_net_profit = 0

            # Calculate total invested and net profit for each match
            for earning in earnings:
                total_invested += earning['score']
                total_net_profit += earning['net_earning']

            # Update player_stats dictionary with total invested and net profit
            if player_name in player_stats:
                player_stats[player_name]['total_invested'] += total_invested
                player_stats[player_name]['total_net_profit'] += total_net_profit
            else:
                player_stats[player_name] = {
                    'total_invested': total_invested,
                    'total_net_profit': total_net_profit
                }

        return player_stats


