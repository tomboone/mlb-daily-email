from datetime import datetime
import statsapi
from dateutil import tz
import requests
from logger import log


# Get all the boxscores for a date
def get_boxscores(date):
    scores = statsapi.schedule(start_date=date, end_date=date)
    games = []  # Empty list to hold games
    for score in scores:
        boxscore = get_boxscore(score['game_id'])
        games.append(boxscore)
    return games


# Get boxscore data for a game
def get_boxscore(game_id):
    box_data = statsapi.boxscore_data(game_id)
    game_data = statsapi.get('game', {'gamePk': game_id})
    box = {
        'status': game_data['gameData']['status']['statusCode'],
        'linescore': game_data['liveData']['linescore'],
        'teams': {
            'away': get_team_box('away', box_data, game_data),
            'home': get_team_box('home', box_data, game_data)
        },
        'info': box_data['gameBoxInfo']
    }
    return box


# Get boxscore data for a single team
def get_team_box(team, box_data, game_data):
    wins = game_data['gameData']['teams'][team]['record']['wins']
    losses = game_data['gameData']['teams'][team]['record']['losses']
    team_box = {
        'name': box_data['teamInfo'][team],
        'record': '{}'.format(wins) + '-' + '{}'.format(losses),
        'batters': box_data['{}Batters'.format(team)],
        'battingTotals': box_data['{}BattingTotals'.format(team)],
        'battingNotes': box_data['{}BattingNotes'.format(team)],
        'info': box_data[team]['info'],
        'pitchers': box_data['{}Pitchers'.format(team)],
        'pitchingTotals': box_data[team]['teamStats']['pitching'],
    }
    return team_box


# Today's games
def get_probables(date):
    schedule = statsapi.schedule(start_date=date, end_date=date)
    probables = []
    for bbgame in schedule:
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('America/New_York')
        utc = datetime.strptime(bbgame['game_datetime'], '%Y-%m-%dT%H:%M:%SZ')
        utc = utc.replace(tzinfo=from_zone)
        eastern = utc.astimezone(to_zone)
        time = datetime.strftime(eastern, '%-I:%M %p')
        probable = {
            'teams': {
                'away': {
                    'name': bbgame['away_name'],
                    'pitcher': bbgame['away_probable_pitcher'],
                },
                'home': {
                    'name': bbgame['home_name'],
                    'pitcher': bbgame['home_probable_pitcher'],
                }
            },
            'time': time
        }
        probables.append(probable)

    return probables


# Standings
def get_standings():
    standings = []  # empty list for division standings
    standings_data = statsapi.standings_data()  # get all division standings
    division = [201, 202, 200, 204, 205, 203]  # division IDs (in proper order)
    for x in division:  # loop through the division IDs
        standings.append(standings_data[x])  # add each division standings to list

    return standings


# League leaders
def get_league_leaders():
    batting = [
        ('battingAverage', 'Batting Average'),
        ('homeRuns', 'Home Runs'),
        ('runsBattedIn', 'Runs Batted In'),
        ('onBasePlusSlugging', 'OPS'),
        ('stolenBases', 'Stolen Bases')
    ]
    pitching = [
        ('wins', 'Wins'),
        ('strikeouts', 'Strikeouts'),
        ('earnedRunAverage', 'ERA'),
        ('walksAndHitsPerInningPitched', 'WHIP'),
        ('saves', 'Saves')
    ]
    leaders = {
        'Batting': {
            'league': {
                'American League': get_leaders('hitting', batting, 103),
                'National League': get_leaders('hitting', batting, 104)
            }
        },
        'Pitching': {
            'league': {
                'American League': get_leaders('pitching', pitching, 103),
                'National League': get_leaders('pitching', pitching, 104)
            }
        }
    }

    return leaders


def get_leaders(group, categories, league):
    leaders = []  # empty list of leaders
    for category in categories:  # loop through categories
        league_leaders = []  # empty list of league hitting leaders
        category_leaders = statsapi.league_leader_data(category[0], statGroup=group, leagueId=league)
        for leader in category_leaders:  # loop through leaders
            league_leaders.append(leader)  # add leader to list
        leaders.append({
            'category': category[1],
            'leaders': league_leaders
        })
    return leaders


def get_transactions(date):
    endpoint = 'https://statsapi.mlb.com/api/v1/transactions'  # MLB API endpoint
    payload = {'date': date, 'sportId': 1}  # payload for API request

    try:  # try to get transactions
        response = requests.get(endpoint, params=payload)  # get transactions
        response.raise_for_status()  # raise exception if status code is not 200
    except requests.exceptions.HTTPError as err:  # catch exception
        log.error(err)  # log error
        return None  # return None
    else:  # if no exception
        transactions_data = response.json()['transactions']  # get transactions data

        transactions_list = []  # empty list for transactions
        for transaction in transactions_data:  # loop through transactions
            transaction_dict = {  # create dictionary for transaction
                'team': parse_txn_for_team(transaction),  # team involved in transaction
                'description': parse_txn_for_description(transaction)  # transaction description
            }
            if transaction_dict['team']['name'] is not None:  # if team is not empty
                transactions_list.append(transaction_dict)  # add transaction to list

    txns = sorted(transactions_list, key=lambda k: k['team']['name'])  # sort list of txns by team name
    for txn in txns:
        txn['description'] = txn['description'].replace(txn['team']['name'] + ' ', '')  # remove team from description
        txn['description'] = txn['description'][0].upper() + txn['description'][1:]  # capitalize description

    teams = []  # empty list for teams
    for txn in txns:  # loop through transactions
        if txn['team']['name'] not in teams:  # if team is not in list
            teams.append(txn['team']['name'])  # add team to list
    transactions = {
        'teams': teams,
        'txns': txns
    }
    return transactions


def parse_txn_for_description(transaction):
    if 'description' in transaction:
        description = transaction['description']
    else:
        description = None
    return description


def parse_txn_for_team(transaction):
    team = None
    if 'toTeam' in transaction:
        team = parse_team(transaction['toTeam']['id'], transaction['toTeam']['name'])
    if 'fromTeam' in transaction and team is not None:
        team = parse_team(transaction['fromTeam']['id'], transaction['fromTeam']['name'])
    return team


def parse_team(team_id, team_name):
    txn_team = {'name': None, 'id': None}  # empty dictionary for team

    if 108 <= team_id <= 121 or \
            133 <= team_id <= 147 or \
            team_id == 158:  # if team is an MLB team
        txn_team['id'] = team_id  # add team ID to dictionary
        txn_team['name'] = team_name  # add team name to dictionary

    return txn_team
