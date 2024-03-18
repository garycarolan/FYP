# Elo World

This repository contains a few algorithms for playing chess, written in Python 3. Most of them are terrible at winning, but have other interesting properties. Based on the video ["30 Weird Chess Algorithms: Elo World"](https://www.youtube.com/watch?v=DpXy041BIlA) by Tom 7.

## Installation

```
git clone https://github.com/mdnestor/eloworld.git
pip install -r requirements.txt
python3 main.py
```

## Agents

Agents are implemented in `agents.py` as callable classes that take the board as a [FEN](https://en.wikipedia.org/wiki/Forsyth%E2%80%93Edwards_Notation) string and return a move in [UCI](https://en.wikipedia.org/wiki/Universal_Chess_Interface) format.

### Implemented

- `Random` - selects a move uniformly at random from the set of legal moves.
- `Upward` - moves the pieces upward.
- `Alphabetical` - selects the first move ordered alphabetically according to the UCI notation.
- `SameColor` - moves white pieces to white squares, and black pieces to black squres.
- `OppositeColor` - moves white pieces to black squares, and... yeah, you get it.
- `MinOpptMoves` - selects the move which results in the opponent having the least number of legal moves.
- `CCCP` - checkmate, check, capture, push - in order of preference.
- `Arithmetic(const: float)` - orders moves alphabetically by UCI, then selects index using a constant between 0 and 1. Alphabetical is a special case with const. = 0.
- `Rational_pi`: arithmetic agent with const. = pi.
- `Rational_e` - arithmetic agent with const. = e.
- `Stockfish` - the classic Stockfish engine. Requires separate installation.
- `NegativeStockfish` - orders the moves via Stockfish's preferences, and selects the worst one. Basically tries to lose.

### Not implemented
- `Huddle` - moves pieces closes to their own king.
- `Swarm` - moves pieces towards the enemy king.
- `SymMirrorY` - prefers the board to be vertically symmetrical.
- `SymMirrorX` - prefers the board to be horizontally symmetrical.
- `ReverseStarting` - attempts to swap the starting positions of white and black.
