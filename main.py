import pandas as pd
import chess
import chess.pgn
from agents import *
from pyturochamp import *  # has different settings for the turochamp in each class
from pathos.multiprocessing import ProcessingPool as Pool


def play_game_wrapper(args):
    return play_game(*args)


def play_game(white_id, black_id):
    # Special handling for Stockfish agents
    # if 'Stockfish' in white_id or 'Stockfish' in black_id:
    #     engine = chess.engine.SimpleEngine.popen_uci('stockfish/stockfish-windows-x86-64-avx2.exe')
    # else:
    #     engine = None
    # Initialize agents
    if white_id in AGENT_MAPPING:
        if 'Turochamp' in white_id:  # For Turochamp variants, pass the colour
            white = AGENT_MAPPING[white_id]('white')
        # elif white_id == 'Stockfish':  # For Stockfish, pass the engine
        #     white = AGENT_MAPPING[white_id](engine)
        else:
            white = AGENT_MAPPING[white_id]()

    if black_id in AGENT_MAPPING:
        if 'Turochamp' in black_id:  # For Turochamp variants, pass the colour
            black = AGENT_MAPPING[black_id]('black')
        # elif black_id == 'Stockfish':  # For Stockfish, pass the engine
        #     black = AGENT_MAPPING[black_id](engine)
        else:
            black = AGENT_MAPPING[black_id]()


    board = chess.Board()
    start_time = time.time()  # Capture the start time
    while not board.is_game_over():
        player = white if board.turn else black
        move_uci = player(board.fen())
        move = chess.Move.from_uci(move_uci)
        board.push(move)
    end_time = time.time()  # Capture the end time
    game_duration = end_time - start_time  # Calculate the duration in seconds
    game = chess.pgn.Game.from_board(board)
    game.headers["White"] = white_id
    game.headers["Black"] = black_id
    outcome = board.outcome()
    print(white_id, 'vs', black_id)
    # Close the local engine for Stockfish agents
    # if engine is not None:
    #     engine.quit()
    return white_id, black_id, outcome, game_duration


# time_limit_for_stockfish = 0.00001  # Time limit for each move, reduced to bring closer to turochamp
AGENT_MAPPING = {
    'Turochamp': lambda colour='none': Turochamp(colour),
    'Turochamp2ply': lambda colour='none': Turochamp2ply(colour),
    'Turochamp2plyKnight': lambda colour='none': Turochamp2plyKnight(colour),
    'Turochamp2plyBishop': lambda colour='none': Turochamp2plyBishop(colour),
    'TurochampKnight': lambda colour='none': TurochampKnight(colour),
    'TurochampBishop': lambda colour='none': TurochampBishop(colour),
}

if __name__ == "__main__":
    begin_runtime = time.time()  # Capture the start time
    agent_ids = list(AGENT_MAPPING.keys())  # List of agent identifiers
    # Note: each agent gets one game as white and one game as black against the other agent
    games_to_play = [(white_id, black_id) for white_id in agent_ids for black_id in agent_ids if white_id != black_id]
    pool = Pool()  # Using Pathos Pool for better serialization

    # Execute the games in parallel using multiprocessing
    results = pool.map(play_game_wrapper, games_to_play)
    pool.close()
    pool.join()

    # Table Setup
    columns = ['Agent', 'Wins', 'Losses', 'Draws', 'Total Games', 'Total Game Lengths']
    results_df = pd.DataFrame(columns=columns).set_index('Agent').astype({'Total Game Lengths': 'float64'})

    # Ensure all agents are represented in the DataFrame, even if they don't play
    for agent_id in agent_ids:
        results_df.loc[agent_id] = [0, 0, 0, 0, 0]

    # Process the results
    for white_id, black_id, outcome, game_duration in results:
        if outcome.winner is None:  # Draw
            results_df.loc[white_id, 'Draws'] += 1
            results_df.loc[black_id, 'Draws'] += 1
        elif outcome.winner:  # White wins
            results_df.loc[white_id, 'Wins'] += 1
            results_df.loc[black_id, 'Losses'] += 1
        else:  # Black wins
            results_df.loc[black_id, 'Wins'] += 1
            results_df.loc[white_id, 'Losses'] += 1

        # Update total games and total game lengths for both agents
        for agent_id in [white_id, black_id]:
            results_df.loc[agent_id, 'Total Games'] += 1
            results_df.loc[agent_id, 'Total Game Lengths'] += game_duration

    # Calculate average game lengths
    results_df['Average Game Length'] = results_df['Total Game Lengths'] / results_df['Total Games']

    results_df.to_csv('Results.csv', index=True)
    end_runtime = time.time()  # Capture the end time
    runtime = end_runtime - begin_runtime  # Calculate the duration in seconds
    print('Runtime:', runtime)

