import pandas as pd
import chess
import chess.pgn
import io
import time
import multiprocessing
from agents import *
from pathos.multiprocessing import ProcessingPool as Pool


def play_game_wrapper(args):
    return play_game(*args)


def play_game(white_id, black_id):
    # Special handling for Stockfish agents
    if 'Stockfish' in white_id or 'Stockfish' in black_id:
        engine = chess.engine.SimpleEngine.popen_uci('stockfish/stockfish-windows-x86-64-avx2.exe')
    else:
        engine = None

    # Initialize agents
    if white_id == 'NegativeStockfish':
        white = NegativeStockfish(engine, time_limit_for_stockfish)
    elif white_id == 'Stockfish':
        white = Stockfish(engine, time_limit_for_stockfish)
    else:
        white = AGENT_MAPPING[white_id]()

    if black_id == 'NegativeStockfish':
        black = NegativeStockfish(engine, time_limit_for_stockfish)
    elif black_id == 'Stockfish':
        black = Stockfish(engine, time_limit_for_stockfish)
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
    if engine is not None:
        engine.quit()
    # TODO: we used to pass a string of the game, see if this has any use in main
    return white_id, black_id, outcome, game_duration


# Global Setup Vars
time_limit_for_stockfish = 0.1  # Time limit for each move
AGENT_MAPPING = {
    'Random': Random,
    'SameColor': SameColor,
    'OppositeColor': OppositeColor,
    'CCCP': CCCP,
    'Alphabetical': Alphabetical,
    'Rational_pi': Rational_pi,
    'Rational_e': Rational_e,
    'MinOpptMoves': MinOpptMoves,
    'Upward': Upward,
    # engine passed in during play
    'Stockfish': lambda engine=None: Stockfish(engine, time_limit_for_stockfish),
    'NegativeStockfish': lambda engine=None: NegativeStockfish(engine, time_limit_for_stockfish),
}

if __name__ == "__main__":
    begin_runtime = time.time()  # Capture the start time
    agent_ids = list(AGENT_MAPPING.keys())  # List of agent identifiers
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

