import pandas as pd
import chess
import chess.pgn
import io
import time
from agents import *

def play_game(white: Agent, black: Agent):
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
    game.headers["White"] = type(white).__name__
    game.headers["Black"] = type(black).__name__
    outcome = board.outcome()
    return str(game), outcome, game_duration

if __name__ == "__main__":
    stockfish_path = 'stockfish/stockfish-windows-x86-64-avx2.exe'
    time_limit_for_stockfish = 0.1  # Time limit for each move
    engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)

    agents = [
        Random(),
        SameColor(),
        OppositeColor(),
        CCCP(),
        Alphabetical(),
        Rational_pi(),
        Rational_e(),
        MinOpptMoves(),
        Upward(),
        Stockfish(engine, time_limit_for_stockfish),
        NegativeStockfish(engine, time_limit_for_stockfish),
    ]

    columns = ['Agent', 'Wins', 'Losses', 'Draws', 'Total Games', 'Total Game Lengths']
    results_df = pd.DataFrame(columns=columns)

    for agent in agents:
        new_row = pd.DataFrame([{
            'Agent': type(agent).__name__,
            'Wins': 0,
            'Losses': 0,
            'Draws': 0,
            'Total Games': 0,
            'Total Game Lengths': 0
        }])
        results_df = pd.concat([results_df, new_row], ignore_index=True)

    # TODO: consider multithreading
    for white in agents:
        for black in agents:
            if type(white) != type(black):  # Avoid playing against the same type of agent
                # TODO: outcome is currently unnused but may have some use
                pgn, outcome, game_duration = play_game(white, black)
                print(type(white), 'vs', type(black))

                white_agent_name = type(white).__name__
                black_agent_name = type(black).__name__

                if outcome.winner is None:  # Draw
                    results_df.loc[results_df.Agent == white_agent_name, 'Draws'] += 1
                    results_df.loc[results_df.Agent == black_agent_name, 'Draws'] += 1
                elif outcome.winner:  # White wins
                    results_df.loc[results_df.Agent == white_agent_name, 'Wins'] += 1
                    results_df.loc[results_df.Agent == black_agent_name, 'Losses'] += 1
                else:  # Black wins
                    results_df.loc[results_df.Agent == white_agent_name, 'Losses'] += 1
                    results_df.loc[results_df.Agent == black_agent_name, 'Wins'] += 1

                results_df.loc[results_df.Agent == white_agent_name, 'Total Games'] += 1
                results_df.loc[results_df.Agent == black_agent_name, 'Total Games'] += 1
                results_df.loc[results_df.Agent == white_agent_name, 'Total Game Lengths'] += game_duration
                results_df.loc[results_df.Agent == black_agent_name, 'Total Game Lengths'] += game_duration

    # Calculate the average game length for each agent
    results_df['Average Game Length'] = results_df['Total Game Lengths'] / results_df['Total Games']
    results_df.drop(columns=['Total Game Lengths'], inplace=True)

    print(results_df)

    engine.quit()
