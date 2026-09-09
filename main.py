from flask import Flask, render_template, redirect, request, session, url_for, flash
import requests
from flask import request
import json
import csv
from datetime import datetime
from pymongo import MongoClient
from functions.s3_file_manager import s3_file_manager
from functions.calculation_functions import CalculationFunctions
from functions.user_manager import UserManager
import os
import boto3
import time
import config


app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY

s3_bucketname = config.S3_BUCKET

def is_admin(username):
    users = UserManager.load_users(s3_bucketname,'data/users_login.json')
    return username in users and users[username]['role'] == 'admin'

def authenticate(username, password):
    users = UserManager.load_users(s3_bucketname, 'data/users_login.json')
    return username in users and users[username]['password'] == password
@app.context_processor
def utility_processor():
    return {'is_admin': is_admin}

@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    if is_admin(session['username']):
        return redirect(url_for('admin_dashboard'))
    else:
        match_standing_file = 'data/match_standing.json'
        match_standing_data = s3_file_manager.read_json_file_from_s3(s3_bucketname, match_standing_file)
        max_document = CalculationFunctions.find_max_document_in_list_of_dicts(match_standing_data)
        update_stats()
        dashboard_input = dashboard()

    return render_template("index.html", match=max_document, player_stats=dashboard_input)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if authenticate(username, password):
            session['username'] = username
            session['login_time'] = time.time()  # Record login time
            if is_admin(username):
                return redirect(url_for('admin_dashboard'))  # Redirect admin to dashboard
            return redirect(url_for('home'))  # Redirect regular user to home
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

@app.route("/admin_dashboard", methods=['GET', 'POST'])
def admin_dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    if not is_admin(session['username']):
        return redirect(url_for('home'))

    poll_dates_file = 'data/poll_date.json'
    load_poll_dates = s3_file_manager.read_json_file_from_s3(s3_bucketname, poll_dates_file)

    # Read existing dates from poll_date.json
    filter_dates = load_poll_dates

    if request.method == 'POST':
        # Get the form data
        new_start_date = request.form['new_start_date']
        new_end_date = request.form['new_end_date']

        # Check if the new date range already exists
        if any(date['start_date'] == new_start_date and date['end_date'] == new_end_date for date in filter_dates):
            flash('Date range already exists!', 'error')
        else:
            # Set 'is_active' to False for existing dates
            for date in filter_dates:
                date['is_active'] = False

            # Append new date range with 'is_active' set to True
            new_date = {
                "id": str(len(filter_dates) + 1),
                "start_date": new_start_date,
                "end_date": new_end_date,
                "is_active": True
            }
            filter_dates.append(new_date)

            # Write updated dates back to poll_date.json
            s3_file_manager.write_json_file_to_s3(filter_dates, s3_bucketname, poll_dates_file)

            flash('Date range added successfully!', 'success')

    return render_template('admin_dashboard.html', filter_dates_in=filter_dates)

@app.route("/delete_date", methods=['POST'])
def delete_date():
    if 'username' not in session:
        return redirect(url_for('login'))
    if not is_admin(session['username']):
        return redirect(url_for('home'))

    # Get the date ID to delete from the form data
    date_id = request.form['date_id']

    poll_dates_file = 'data/poll_date.json'
    load_poll_dates = s3_file_manager.read_json_file_from_s3(s3_bucketname, poll_dates_file)

    # Read existing dates from poll_date.json
    filter_dates = load_poll_dates

    # Find the date range with the given ID and remove it
    filter_dates = [date for date in filter_dates if date['id'] != date_id]

    # Write updated dates back to poll_date.json
    s3_file_manager.write_json_file_to_s3(filter_dates, s3_bucketname, poll_dates_file)

    flash('Date range deleted successfully!', 'success')

    # Redirect back to the admin dashboard
    return redirect(url_for('admin_dashboard'))

@app.route("/logout")
def logout():
    session.clear()  # Clear session data
    return redirect(url_for('login'))

@app.route('/schedule')
def schedule():
    match_schedule_file = 'data/ipl_schedule.json'
    match_schedule_data = s3_file_manager.read_json_file_from_s3(s3_bucketname, match_schedule_file)
    data = []
    for row in match_schedule_data:
            data.append(row)
    return render_template('schedule1.html', data=data)

# @app.route('/poll')
# def poll():
#     match_schedule_file = 'data/ipl_schedule.json'
#     match_schedule_data = s3_file_manager.read_json_file_from_s3(s3_bucketname, match_schedule_file)
#
#     # Read poll dates from the JSON file
#     poll_date_file = 'data/poll_date.json'
#     poll_date_data = s3_file_manager.read_json_file_from_s3(s3_bucketname, poll_date_file)
#
#     start_date = None
#     end_date = None
#
#     # Extract start_date and end_date from poll_date_data
#     for item in poll_date_data:
#         if item.get("is_active", False):
#             start_date = datetime.strptime(item["start_date"], "%Y-%m-%d").date()
#             end_date = datetime.strptime(item["end_date"], "%Y-%m-%d").date()
#             break
#
#     # Filter match_schedule_data based on start_date and end_date
#     poll_data = []
#     for document in match_schedule_data:
#         document_date = datetime.strptime(document['DATE'], "%Y-%m-%d").date()
#         if start_date <= document_date <= end_date:
#             poll_data.append({
#                 'date': document['DATE'],
#                 'teams': [document['HOME'], document['AWAY']],
#                 'match_number': document['MATCH_NUMBER']
#             })
#
#     # Prepare selected_options
#     selected_options = [document['teams'][0] for document in poll_data]
#
#     return render_template('poll.html', poll_data=poll_data, selected_options=selected_options, enumerate=enumerate)

@app.route("/poll")
def poll():
    match_schedule_file = "data/ipl_schedule.json"
    match_schedule_data = s3_file_manager.read_json_file_from_s3(s3_bucketname, match_schedule_file)

    # Read poll dates from the JSON file
    poll_date_file = "data/poll_date.json"
    poll_date_data = s3_file_manager.read_json_file_from_s3(s3_bucketname, poll_date_file)

    poll_file_path = 'data/poll.json'
    poll_collection = s3_file_manager.read_json_file_from_s3(s3_bucketname, poll_file_path)
    existing_players = [entry['player_name'] for entry in poll_collection]

    # Get the maximum ID from poll_date_data
    max_id = max(int(item["id"]) for item in poll_date_data)

    is_poll_active = False
    next_poll_end_date = None

    # Iterate over poll_date_data
    for item in poll_date_data:
        start_date = datetime.strptime(item["start_date"], "%Y-%m-%d").date()
        end_date = datetime.strptime(item["end_date"], "%Y-%m-%d").date()
        # print(start_date)
        # print(end_date)
        if item.get("id") == str(max_id):
            if item.get("is_active", True):
                is_poll_active = True
            else:
                next_poll_end_date = end_date
    # print(is_poll_active)
    # print(next_poll_end_date)
    # print(max_id)
    if is_poll_active:
        # Filter match_schedule_data based on start_date and end_date
        poll_data = []
        for document in match_schedule_data:
            document_date = datetime.strptime(document['DATE'], "%Y-%m-%d").date()
            if start_date <= document_date <= end_date:
                poll_data.append({
                    'date': document['DATE'],
                    'teams': [document['HOME'], document['AWAY']],
                    'match_number': document['MATCH_NUMBER']
                })

        # Prepare selected_options
        selected_options = [document['teams'][0] for document in poll_data]

        return render_template('poll.html', poll_data=poll_data, selected_options=selected_options, enumerate=enumerate, existing_players=existing_players)
    else:
        if next_poll_end_date:
            message = f"Polls are closed now. Next polls will open on {next_poll_end_date} 12:00 PM PST to 12:00 AM PST"
        else:
            message = "Polls are closed now. Please check back later for the next polling window."

        return render_template('poll_closed.html', message=message)
# @app.route('/submit_poll', methods=['POST'])
# def submit_poll():
#     # Specify the paths to the local JSON files
#     poll_file_path = 'data/poll.json'
#     poll_collection = s3_file_manager.read_json_file_from_s3(s3_bucketname, poll_file_path)
#
#     player_name = request.form['name']
#
#     # Check if the player has already submitted a poll
#     for entry in poll_collection:
#         if entry['player_name'].lower() == player_name.lower():
#             existing_dates = set(response['date'] for response in entry['poll_responses'])
#             new_dates = set(response['date'] for response in entry['poll_responses'])
#             if existing_dates.intersection(new_dates):
#                 return "You have already submitted the poll for some of the dates."
#             break
#
#     # Update player_polls dictionary with date and poll responses
#     poll_responses = []
#     for key, value in request.form.items():
#         if key.startswith('date_'):
#             poll_date = value
#             match_number = request.form.get(f"match_{key.split('_')[1]}")
#             # Find the corresponding poll response for the date
#             poll_response_key = f"poll_{key.split('_')[1]}"
#             poll_response = request.form[poll_response_key]
#             poll_responses.append({"date": poll_date, "match_number": match_number, "response": poll_response})
#
#     # Insert the poll data into the local JSON file
#     poll_collection.append({"player_name": player_name, "poll_responses": poll_responses})
#     s3_file_manager.write_json_file_to_s3(poll_collection, s3_bucketname, poll_file_path)
#     update_stats()
#
#     return redirect('/')

@app.route('/submit_poll', methods=['POST'])
def submit_poll():
    # Specify the paths to the local JSON files
    poll_file_path = 'data/poll.json'

    # Read existing data from the local JSON file
    poll_collection = s3_file_manager.read_json_file_from_s3(s3_bucketname, poll_file_path)

    # Access form data
    if 'existing_players' in request.form and request.form['existing_players']:
        player_name = request.form['existing_players']
    elif 'new_player_name' in request.form and request.form['new_player_name']:
        player_name = request.form['new_player_name']
    else:
        player_name = "No player name provided"

    # Check if the player has already submitted a poll
    existing_entry = None
    for entry in poll_collection:
        if entry['player_name'].lower() == player_name.lower():
            existing_entry = entry
            break

    if existing_entry:
        existing_dates = set(response['date'] for response in existing_entry['poll_responses'])
        new_dates = set()
        for key, value in request.form.items():
            if key.startswith('date_'):
                new_dates.add(value)
        if existing_dates.intersection(new_dates):
            return "You have already submitted the poll for some of the dates."

        # Append the new poll responses to the existing entry
        for key, value in request.form.items():
            if key.startswith('date_'):
                poll_date = value
                match_number = request.form.get(f"match_{key.split('_')[1]}")
                poll_response_key = f"poll_{key.split('_')[1]}"
                poll_response = request.form[poll_response_key]
                existing_entry['poll_responses'].append(
                    {"date": poll_date, "match_number": match_number, "response": poll_response})
    else:
        # Create a new entry for the player
        poll_responses = []
        for key, value in request.form.items():
            if key.startswith('date_'):
                poll_date = value
                match_number = request.form.get(f"match_{key.split('_')[1]}")
                poll_response_key = f"poll_{key.split('_')[1]}"
                poll_response = request.form[poll_response_key]
                poll_responses.append({"date": poll_date, "match_number": match_number, "response": poll_response})
        poll_collection.append({"player_name": player_name, "poll_responses": poll_responses})

    # Write the updated poll data back to the local JSON file
    s3_file_manager.write_json_file_to_s3(poll_collection, s3_bucketname, poll_file_path)
    update_stats()

    return redirect('/')

def update_stats():
    # Specify the paths to the local JSON files
    poll_file_path = 'data/poll.json'
    players_stats_file_path = 'data/players_stats.json'
    match_standing_file_path = 'data/match_standing.json'

    # Read data from the local JSON files
    poll_collection = s3_file_manager.read_json_file_from_s3(s3_bucketname, poll_file_path)
    match_standing_collection = s3_file_manager.read_json_file_from_s3(s3_bucketname, match_standing_file_path)
    players_stats_collection = s3_file_manager.read_json_file_from_s3(s3_bucketname, players_stats_file_path)

    # Compare selected teams with winning teams and calculate player standings
    for player in poll_collection:
        comparison_results = CalculationFunctions.compare_teams(player['player_name'], player['poll_responses'], match_standing_collection, poll_collection)
        player['comparison_results'] = comparison_results

    # Insert or update player data in players_stats collection
    for player in poll_collection:
        existing_player = next((entry for entry in players_stats_collection if entry['player_name'] == player['player_name']), None)
        if existing_player:
            # Update existing player data
            existing_player.update(player)
        else:
            # Insert new player data
            players_stats_collection.append(player)

    # Write the updated players stats collection to JSON file
    s3_file_manager.write_json_file_to_s3(players_stats_collection, s3_bucketname, players_stats_file_path)

    # Return success message or redirect to another page
    return "PLAYER_STATS_UPDATED"



@app.route('/player_inputs')
def player_inputs():
    # Specify the path to the local JSON file
    players_stats_file_path = 'data/players_stats.json'

    # Read player inputs from the local JSON file
    players_stats = s3_file_manager.read_json_file_from_s3(s3_bucketname, players_stats_file_path)

    update_stats()

    all_players = []
    for player_stat in players_stats:
        player_name = player_stat['player_name']
        comparison_results = player_stat.get('comparison_results', {})  # Handle the case when comparison_results is not present
        player_data = {'player_name': player_name, 'comparison_results': comparison_results}
        all_players.append(player_data)

    return render_template('player_inputs.html', all_players=all_players)

@app.template_filter('enumerate')
def custom_enumerate(iterable):
    return zip(range(len(iterable)), iterable)

# @app.route('/dashboard')
def dashboard():
    # Specify the path to the local JSON file
    players_stats_file_path = 'data/players_stats.json'

    players_stats = s3_file_manager.read_json_file_from_s3(s3_bucketname, players_stats_file_path)
    # Calculate total profit from the player statistics
    player_stats = CalculationFunctions.calculate_total_profit(players_stats)

    return player_stats


if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')