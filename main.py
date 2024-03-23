import pandas as pd
import chess
import chess.pgn
from agents import *
from pyturochamp import *  # has different settings for the turochamp in each class
from pathos.multiprocessing import ProcessingPool as Pool


def play_game_wrapper(args):
    return play_game(*args)


def play_game(white_id, black_id):
    # Other logical code for non-Turochamp agents has been removed
    white = AGENT_MAPPING[white_id]('white')
    black = AGENT_MAPPING[black_id]('black')

    board = chess.Board()
    start_time = time.time()  # Capture the start time
    while not board.is_game_over(claim_draw=True):
        player = white if board.turn else black
        move_uci = player(board.fen())
        move = chess.Move.from_uci(move_uci)
        board.push(move)
    end_time = time.time()  # Capture the end time
    game_duration = end_time - start_time  # Calculate the duration in seconds
    game = chess.pgn.Game.from_board(board)
    game.headers["White"] = white_id
    game.headers["Black"] = black_id
    outcome = board.outcome(claim_draw=True)
    print(white_id, 'vs', black_id)
    print(outcome)
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
    columns = ['Agent', 'Wins', 'Losses', 'Draws by Repetition', 'Draws by Move Rule', 'Other Draws', 'Total Games',
               'Total Game Lengths']
    results_df = pd.DataFrame(columns=columns).set_index('Agent').astype({'Total Game Lengths': 'float64'})

    # Ensure all agents are represented in the DataFrame, even if they don't play
    for agent_id in agent_ids:
        results_df.loc[agent_id] = [0, 0, 0, 0, 0, 0, 0]

    # Process the results
    for white_id, black_id, outcome, game_duration in results:
        if outcome.winner is None:  # Draw
            if outcome.termination == chess.Termination.THREEFOLD_REPETITION:
                results_df.loc[white_id, 'Draws by Repetition'] += 1
                results_df.loc[black_id, 'Draws by Repetition'] += 1
            elif outcome.termination == chess.Termination.FIFTY_MOVES:
                results_df.loc[white_id, 'Draws by Move Rule'] += 1
                results_df.loc[black_id, 'Draws by Move Rule'] += 1
            else:
                results_df.loc[white_id, 'Other Draws'] += 1
                results_df.loc[black_id, 'Other Draws'] += 1
        elif outcome.winner:  # (.winner is an optional and color is bool true for white as defined in chess package)
            results_df.loc[white_id, 'Wins'] += 1
            results_df.loc[black_id, 'Losses'] += 1
        else:  # Black wins
            results_df.loc[black_id, 'Wins'] += 1
            results_df.loc[white_id, 'Losses'] += 1

        # Updating total games and total game lengths for both agents
        for agent_id in [white_id, black_id]:
            results_df.loc[agent_id, 'Total Games'] += 1
            results_df.loc[agent_id, 'Total Game Lengths'] += game_duration

    # Calculate average game lengths
    results_df['Average Game Length'] = results_df['Total Game Lengths'] / results_df['Total Games']

    results_df.to_csv('Results.csv', index=True)
    end_runtime = time.time()  # Capture the end time
    runtime = end_runtime - begin_runtime  # Calculate the duration in seconds
    print('Runtime:', runtime)

