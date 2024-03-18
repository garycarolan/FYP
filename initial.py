import chess
import chess.pgn

import io
import random
import time

from agents import (
  Agent,
  Random,
  SameColor,
  OppositeColor,
  CCCP,
  Alphabetical,
  Rational_pi,
  Rational_e,
  MinOpptMoves,
  Upward,
  Stockfish,
  NegativeStockfish,
)


def play_game(white: Agent, black: Agent):
  board = chess.Board()
  while not board.is_game_over():
    player = white if board.turn else black
    move_uci = player(board.fen())
    move = chess.Move.from_uci(move_uci)
    board.push(move)
  game = chess.pgn.Game.from_board(board)
  game.headers["White"] = type(white).__name__
  game.headers["Black"] = type(black).__name__
  return str(game)


if __name__ == "__main__":
  white = Random()
  black = NegativeStockfish()

  pgn = play_game(white, black)

  game = chess.pgn.read_game(io.StringIO(pgn))
  board = game.board()
  for move in game.mainline_moves():
    board.push(move)
    
  print(board.outcome())