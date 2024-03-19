import chess
import chess.engine

import math
import random
import re

import numpy


class Agent():
  def __call__(self, board_fen: str) -> str:
    # takes board as FEN string; returns move as UCI string
    pass

class Random(Agent):
  def __call__(self, board_fen):
    board = chess.Board(board_fen)
    move = random.choice(list(board.legal_moves))
    return move.uci()

class SameColor(Agent):
  # likes to put white pieces on white squares and vice versa
  def __call__(self, board_fen):
    board = chess.Board(board_fen)
    moves = list(board.legal_moves)
    same_color_moves = [move for move in moves if (move.to_square + move.to_square//8) % 2 == board.turn]
    if same_color_moves:
      move = random.choice(same_color_moves)
    else:
      move = random.choice(moves)
    return move.uci()

class OppositeColor(Agent):
  # likes to put white pieces on black squares and vice versa
  def __call__(self, board_fen):  # Use board_fen instead of board
    board = chess.Board(board_fen)  # Create a chess.Board object from the FEN string
    moves = list(board.legal_moves)
    opp_color_moves = [move for move in moves if (move.to_square + move.to_square // 8) % 2 == 1 - board.turn]
    if opp_color_moves:
      move = random.choice(opp_color_moves)
    else:
      move = random.choice(moves)
    return move.uci()

class CCCP(Agent):
  # checkmate > check > capture > push
  def __call__(self, board_fen):
    board = chess.Board(board_fen)
    moves = list(board.legal_moves)
    scores = [self.score(board_fen, move.uci()) for move in moves]
    best_moves = [m for (m, s) in zip(moves, scores) if s == max(scores)]
    move = random.choice(best_moves)
    return move.uci()

  def score(self, board_fen, move_uci):
    board = chess.Board(board_fen)
    move = chess.Move.from_uci(move_uci)
    board.push(move)
    if board.is_checkmate(): return 3
    if board.is_check(): return 2
    board.pop()
    if board.is_capture(move): return 1
    return 0

class Arithmetic(Agent):
  def __init__(self, const = 0):
    self.const = const % 1

  # TODO: attempted to improve performance, verify it works the same
  def __call__(self, board_fen):
    board = chess.Board(board_fen)
    legal_moves = list(board.legal_moves)
    # Pre-compute the string representations of the moves
    moves_str = [(move, str(move)) for move in legal_moves]
    # Sort the moves based on their pre-computed string representations
    moves_str_sorted = sorted(moves_str, key=lambda x: x[1].lower())
    # Select the move based on the const value
    idx = int(self.const * len(moves_str_sorted))
    selected_move = moves_str_sorted[idx][0]  # Get the move from the (move, string) pair
    return selected_move.uci()

class Alphabetical(Arithmetic):
  def __init__(self):
    super().__init__(const=0)

class Rational_pi(Arithmetic):
  def __init__(self):
    super().__init__(const=math.pi)

class Rational_e(Arithmetic):
  def __init__(self):
    super().__init__(const=math.e)

class MinOpptMoves(Agent):
  def __call__(self, board_fen):
    board = chess.Board(board_fen)
    oppt_moves = []
    moves = list(board.legal_moves)
    for move in moves:
      board.push(move)
      oppt_moves.append(len(list(board.legal_moves)))
      board.pop()
    move = moves[numpy.argmin(oppt_moves)]
    return move.uci()

class Upward(Agent):
  def __call__(self, board_fen):
    board = chess.Board(board_fen)
    move = sorted(board.legal_moves, key=lambda x: x.to_square)[0]
    return move.uci()

class Stockfish(Agent):
  def __init__(self, engine, time_limit = 0.1):
    self.engine = engine
    self.time_limit = time_limit

  def __call__(self, board_fen):
    board = chess.Board(board_fen)
    result = self.engine.play(board, chess.engine.Limit(time=self.time_limit))
    return(result.move.uci())


class NegativeStockfish(Agent):
  def __init__(self, engine, time_limit = 0.1):
    self.engine = engine
    # this analyzes moves individually so same limit as normal Stockfish is excessive w/ very large execution time
    self.time_limit = (time_limit/1000000)

  def __call__(self, board_fen):
    board = chess.Board(board_fen)
    scores = []
    for move in board.legal_moves:
      board.push(move)
      res = self.engine.analyse(board, chess.engine.Limit(time=self.time_limit))
      scores.append(res.get("score"))
      board.pop()

    scores = re.findall("\+?\-?\d+", str(scores))

    # get worst possible move (best move from black's pov)
    index = numpy.argmax([int(s) for s in scores])
    move = list(board.legal_moves)[index]
    return (move.uci())
