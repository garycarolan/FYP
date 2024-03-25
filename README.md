# Elo World

This repository is based on the repository https://github.com/mdnestor/eloworld.git, which was based on the video ["30 Weird Chess Algorithms: Elo World"](https://www.youtube.com/watch?v=DpXy041BIlA) by Tom 7.

Algorithm implementations from this repository are included but non-functional in the current version. Stockfish files are also included for convenience. None of these algorithms are in the "AGENT_MAPPING" dictionary by default.

The default configuration uses different variations of the "Turochamp" implementation from https://github.com/mdoege/TUROjs.git, with some modifications for performance and compatibility.

Tournament data is output to a .csv file, example tournament data from previous and current versions of the project is available in the `project_output_data` file. This data was further processed in Excel, and may include data columns from previous versions, it is not indicative of the current default output.

These third party resources were implemented without permision, solely for academic use.

## Installation

```
git clone https://github.com/garycarolan/FYP.git
pip install -r requirements.txt
python3 main.py
```

## Agents

All agent classes take the board as a [FEN](https://en.wikipedia.org/wiki/Forsyth%E2%80%93Edwards_Notation) string and return a move in [UCI](https://en.wikipedia.org/wiki/Universal_Chess_Interface) format.

Agents which are derived from Turochamp are implemented in the `pyturochamp.py` class, which are currently the only functional agents. Some of these are dependent on the `pst.py` class, which adds positional consideration for different pieces.

Other agents are implemented in `agents.py`, if re-introduction is desired: they would require different input parameters in the AGENT_MAPPING dictionary in main.py, as well as handling code based on dictionary ID in play_game (currently all agents are expected to be Turochamp derived).
