import requests
import json
from datetime import datetime, timedelta
import chess.pgn
import io
import time
import os

def get_monthly_archives(username):
    """Get list of monthly game archives for a user"""
    headers = {
        'User-Agent': 'sayali chessbot'  # Replace with your app name/version
    }
    url = f"https://api.chess.com/pub/player/{username}/games/archives"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['archives']
    print(f"Error getting archives: {response.status_code}")
    return []

def get_games_from_archive(archive_url):
    """Get games from a specific monthly archive"""
    headers = {
        'User-Agent': 'sayali chessbot'  # Replace with your app name/version
    }
    response = requests.get(archive_url, headers=headers)
    if response.status_code == 200:
        return response.json()['games']
    print(f"Error getting games from archive: {response.status_code}")
    return []

def extract_fen_from_pgn(pgn_text):
    """Extract all FEN positions from a PGN game"""
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    if not game:
        return []
    
    fen_positions = []
    board = game.board()
    
    # Add initial position
    fen_positions.append(board.fen())
    
    # Add position after each move
    for move in game.mainline_moves():
        board.push(move)
        fen_positions.append(board.fen())
    
    return fen_positions

def main():
    username = "sayali9141"
    games_data = []
    
    # Create output directory if it doesn't exist
    output_dir = "chess_data"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Fetching game archives for {username}...")
    archives = get_monthly_archives(username)
    
    if not archives:
        print("No archives found or error occurred.")
        return
    
    print(f"Found {len(archives)} monthly archives.")
    
    # Process each monthly archive
    for i, archive_url in enumerate(archives):
        archive_name = archive_url.split('/')[-2] + "-" + archive_url.split('/')[-1]
        print(f"Processing archive {i+1}/{len(archives)}: {archive_name}")
        
        monthly_games = get_games_from_archive(archive_url)
        print(f"Found {len(monthly_games)} games in this archive.")
        
        for game in monthly_games:
            try:
                # Extract key game information
                game_data = {
                    'game_url': game['url'],
                    'timestamp': game['end_time'],
                    'time_control': game['time_control'],
                    'date': datetime.fromtimestamp(game['end_time']).strftime('%Y-%m-%d'),
                }
                
                # Add player information
                game_data['white_player'] = game['white']['username']
                game_data['black_player'] = game['black']['username']
                game_data['white_rating'] = game['white'].get('rating', 0)
                game_data['black_rating'] = game['black'].get('rating', 0)
                
                # Add result
                if username.lower() == game['white']['username'].lower():
                    game_data['user_color'] = 'white'
                    game_data['user_result'] = game['white']['result']
                    game_data['opponent'] = game['black']['username']
                else:
                    game_data['user_color'] = 'black'
                    game_data['user_result'] = game['black']['result']
                    game_data['opponent'] = game['white']['username']
                
                # Add PGN and FEN data
                game_data['pgn'] = game['pgn']
                game_data['fen_positions'] = extract_fen_from_pgn(game['pgn'])
                
                # Add game type
                if 'rated' in game:
                    game_data['rated'] = game['rated']
                
                # Optional: Extract opening information if available
                if 'opening' in game:
                    game_data['opening'] = game['opening']
                
                games_data.append(game_data)
            except Exception as e:
                print(f"Error processing game: {e}")
        
        # Be nice to the API - add a delay between archive requests
        time.sleep(2)
    
    # Save all games to a single JSON file
    output_file = os.path.join(output_dir, f'{username}_chess_games.json')
    with open(output_file, 'w') as f:
        json.dump(games_data, f, indent=2)
    
    print(f"\nExtracted {len(games_data)} games!")
    print(f"Data saved to {output_file}")
    
    # Also save a summary file with basic statistics
    summary = {
        'username': username,
        'total_games': len(games_data),
        'date_range': f"{games_data[-1]['date']} to {games_data[0]['date']}" if games_data else "N/A",
        'white_games': sum(1 for g in games_data if g['user_color'] == 'white'),
        'black_games': sum(1 for g in games_data if g['user_color'] == 'black'),
        'wins': sum(1 for g in games_data if g['user_result'] == 'win'),
        'losses': sum(1 for g in games_data if g['user_result'] == 'lose'),
        'draws': sum(1 for g in games_data if g['user_result'] == 'draw'),
    }
    
    summary_file = os.path.join(output_dir, f'{username}_summary.json')
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Summary saved to {summary_file}")

if __name__ == "__main__":
    main()
