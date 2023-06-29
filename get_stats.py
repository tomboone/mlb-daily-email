from datetime import datetime
import statsapi
from dateutil import tz


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
