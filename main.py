import pandas as pd
import chess
import io
from agents import *

def play_game(white: Agent, black: Agent, engine, time_limit):
    board = chess.Board()
    move_count = 0
    while not board.is_game_over():
        player = white if board.turn else black
        move_uci = player(board.fen(), engine, time_limit)
        move = chess.Move.from_uci(move_uci)
        board.push(move)
        move_count += 1
    game = chess.pgn.Game.from_board(board)
    game.headers["White"] = type(white).__name__
    game.headers["Black"] = type(black).__name__
    outcome = board.outcome()
    return str(game), outcome, move_count / 2  # Average length of the game in full moves

if __name__ == "__main__":
    stockfish_path = 'stockfish/stockfish-windows-x86-64-avx2.exe'  # Adjust the path to your Stockfish engine
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
        results_df = results_df.append({
            'Agent': type(agent).__name__, 'Wins': 0, 'Losses': 0, 'Draws': 0, 'Total Game Lengths': 0
        }, ignore_index=True)

    for white in agents:
        for black in agents:
            if type(white) != type(black):  # Avoid playing against the same type of agent
                pgn, outcome, avg_game_length = play_game(white, black, engine, time_limit_for_stockfish)

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
                results_df.loc[results_df.Agent == white_agent_name, 'Total Game Lengths'] += avg_game_length
                results_df.loc[results_df.Agent == black_agent_name, 'Total Games'] += 1
                results_df.loc[results_df.Agent == black_agent_name, 'Total Game Lengths'] += avg_game_length

    results_df['Average Game Length'] = results_df['Total Game Lengths'] / results_df['Total Games']
    results_df.drop(columns=['Total Game Lengths'], inplace=True)

    print(results_df)

    engine.quit()
