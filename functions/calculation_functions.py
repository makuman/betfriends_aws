
from pymongo import MongoClient
import re
from collections import defaultdict

class CalculationFunctions:

    @staticmethod
    def find_max_document_in_list_of_dicts(list_of_dicts):
        max_document = None
        max_match_number = float('-inf')
        max_date = None

        for doc in list_of_dicts:
            match_number = doc.get('match_number', float('-inf'))
            date = doc.get('date')
            if match_number > max_match_number or (match_number == max_match_number and date > max_date):
                max_document = doc
                max_match_number = match_number
                max_date = date

        return max_document

    # @staticmethod
    # def compare_teams(player_name, poll_responses, winning_teams_collection, poll_collection):
    #     comparison_results = []
    #     # Create a dictionary to map dates to winning teams
    #     winning_teams_dict = {team['date']: team['winner'] for team in winning_teams_collection}
    #
    #     # Iterate over poll_responses to compare teams
    #     for response in poll_responses:
    #         date = response['date']
    #         selected_team = response['response']
    #         # Get the winning team for the current date
    #         winning_team = winning_teams_dict.get(date)
    #
    #         # Find the match number for the current date from the poll collection
    #         match_number = None
    #         for poll in poll_collection:
    #             if poll['player_name'] == player_name and any(
    #                     resp['date'] == date and resp['response'] == selected_team for resp in poll['poll_responses']):
    #                 match_number = next(resp.get('match_number') for resp in poll['poll_responses'] if
    #                                     resp['date'] == date and resp['response'] == selected_team)
    #                 break
    #
    #         # Compare selected team with winning team
    #         score = 1 if selected_team == winning_team else 0
    #         # Append comparison result to the list
    #         comparison_results.append({'date': date, 'match_number': match_number, 'selected_team': selected_team,
    #                                    'winning_team': winning_team, 'score': score})
    #
    #     return comparison_results

    @staticmethod
    def compare_teams(player_name, poll_responses, winning_teams_collection, poll_collection):
        comparison_results = []

        # Create a dictionary to map dates to winning teams
        winning_teams_dict = {team['match_number']: {'status': team['status'], 'match_number': team['match_number']} for
                              team in winning_teams_collection}

        # Iterate over poll_responses to compare teams
        for response in poll_responses:
            date = response['date']
            selected_team = response['response']
            match_number = int(response['match_number'])

            # Remove the "won by [number] runs" part using regex
            selected_team = re.sub(r'\s+won\s+by\s+\d+\s+runs?$', '', selected_team)
            print(f"selected {selected_team}")
            # Get the winning team for the current date
            winning_team_info = winning_teams_dict.get(match_number)
            if winning_team_info:
                winning_team_status = winning_team_info['status']
                print(f"winning_team_status {winning_team_status}")
                match = re.match(r'^(.*?)\s*won\s+by\s+\d+\s+(run|runs|wkt|wkts)?$', winning_team_status)
                if match:
                    # Extract the team name
                    winning_team = match.group(1).strip()
                else:
                    # Use the original winning_team_status string as the team name
                    winning_team = winning_team_status.strip()
            else:
                # Handle case when winning team info is not found
                winning_team = None

            print(f"winning  {winning_team}")
            # Find the match number for the current date from the poll collection
            match_number = None
            for poll in poll_collection:
                if poll['player_name'] == player_name and any(
                        resp['date'] == date and (resp['response']).lower == (selected_team).lower for resp in
                        poll['poll_responses']):
                    match_number = next(resp.get('match_number') for resp in poll['poll_responses'] if
                                        resp['date'] == date and resp['response'] == selected_team)
                    break

            # Compare selected team with winning team
            score = 1 if winning_team and (selected_team.lower() == winning_team.lower()) else 0

            # Append comparison result to the list
            comparison_results.append({'date': date, 'match_number': match_number, 'selected_team': selected_team,
                                       'winning_team': winning_team, 'score': score})

        return comparison_results

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
                        'match_number': match_number,
                        'selected_team': result['selected_team'],
                        'winning_team': result['winning_team'],
                        'score': result['score']
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

    @staticmethod
    def calculate_total_profit(sample_data):
        distinct_match_numbers = set()

        for player_data in sample_data:
            poll_responses = player_data['poll_responses']
            for response in poll_responses:
                match_number = response['match_number']
                distinct_match_numbers.add(match_number)

        # Initialize dictionaries outside the loop
        player_invested_amount = defaultdict(int)
        player_net_return = defaultdict(float)

        for match_number in distinct_match_numbers:
            result = CalculationFunctions.calculate_net_profit(sample_data, match_number)
            for player_data in result:
                player = player_data['player_name']
                invested_amount = 1  # Assuming fixed investment amount for each match
                net_return = player_data['net_profit']  # Corrected variable name

                player_invested_amount[player] += invested_amount
                player_net_return[player] += net_return

        # Calculate net profit for each player
        player_net_profit = defaultdict(float)
        for player in player_invested_amount.keys():
            net_profit = player_net_return[player] - player_invested_amount[player] #- player_net_return[player]
            player_net_profit[player] = round(net_profit, 3)

        # Return the total invested amount, net return, and net profit for each player
        player_results = []
        for player in player_invested_amount.keys():
            player_result = {
                'player': player,
                'invested_amount': player_invested_amount[player],
                'net_return': player_net_return[player],
                'net_profit': player_net_profit[player]
            }
            player_results.append(player_result)

        return player_results


