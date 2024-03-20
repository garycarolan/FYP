#!/usr/bin/env python3
import struct

# A Python chess engine inspired by
# http://en.chessbase.com/post/reconstructing-turing-s-paper-machine

# Modified to act as an agent, global variables modified to be class variables, gets colour at match start

from pst import pst

import chess as c
import math, time
from random import random, expovariate, choice


class Turochamp:
    def __init__(self, colour):
        if colour == 'white':
            self.COMPC = c.WHITE
            self.PLAYC = c.BLACK
        elif colour == 'black':
            self.COMPC = c.BLACK
            self.PLAYC = c.WHITE

        # Piece values
        self.PAWN_VALUE = 1
        self.KNIGHT_VALUE = 3
        self.BISHOP_VALUE = 3.5
        self.ROOK_VALUE = 5
        self.QUEEN_VALUE = 10

        self.MAXPLIES = 1  # Maximum search depth
        self.QPLIES = self.MAXPLIES + 6
        self.PSTAB = 0  # Influence of piece-square table on moves, 0 = none
        self.MATETEST = True  # Include mate and draw detection in the material eval
        # Easy play / random play parameters
        self.MoveError = 0
        # On every move, randomly select the best move or a move inferior by this value (in decipawns)
        self.BlunderError = 0
        # If blundering this move, randomly select the best move or a move inferior by this value (in decipawns)
        self.BlunderPercent = 0  # Percent chance of blundering this move
        self.EasyLearn = 0  # Learn factor: pick from EasyLearn best moves
        self.EasyLambda = 2  # Larger lambda = higher probability of selecting best move
        self.PlayerAdvantage = 0  # Keep the evaluation at least this many decipawns in favor of the player
        self.NODES = 0  # For tracking the number of nodes

    def __call__(self, board_fen: str) -> str:
        b = c.Board(board_fen)
        # Move return and getmove() call is at bottom of file

        def sqrt(n):
            # Used Newton-Raphson to reduce execution time, final result is rounded so won't change outcome
            if n == 0:
                return 0
            x = n
            y = (x + 1) // 2
            while y < x:
                x = y
                y = (x + n // x) // 2
            return round(x)

        def getpos(b):
            "Get positional-play value for a board"
            ppv = 0
            if not len(list(b.legal_moves)) and b.is_checkmate():
                if b.turn == c.WHITE:
                    ppv = -1000
                else:
                    ppv = 1000
            for i in b.piece_map().keys():
                m = b.piece_at(i)
                if m and m.color == self.COMPC:
                    mm = m.piece_type
                    if mm == c.KING and (
                            len(b.pieces(c.PAWN, self.COMPC)) + len(b.pieces(c.PAWN, self.PLAYC))) <= 8:  # endgame is different
                        mm = 8  # for the King
                    if self.COMPC == c.WHITE:
                        j, k = i // 8, i % 8
                        ppv += self.PSTAB * pst[mm][8 * (7 - j) + k] / 100
                    else:
                        ppv += self.PSTAB * pst[mm][i] / 100

                if m and m.piece_type in (c.KING, c.QUEEN, c.ROOK, c.BISHOP, c.KNIGHT) and m.color == self.COMPC:
                    mv_pt, cp_pt = 0, 0
                    a = b.attacks(i)
                    for s in a:
                        e = b.piece_at(s)
                        # empty square
                        if not e:
                            mv_pt += 1
                        # enemy square
                        elif e.color == self.PLAYC:
                            cp_pt += 2
                    ppv += sqrt(mv_pt + cp_pt)
                    if m.piece_type != c.QUEEN and m.piece_type != c.KING:
                        ndef = len(list(b.attackers(self.COMPC, i)))
                        # defended
                        if ndef == 1:
                            ppv += 1
                        # twice defended
                        if ndef > 1:
                            ppv += 1.5
                    # king safety
                    if m.piece_type == c.KING:
                        b2 = c.Board(b.fen())
                        b2.set_piece_at(i, c.Piece(c.QUEEN, self.COMPC))
                        mv_pt, cp_pt = 0, 0
                        a = b2.attacks(i)
                        for s in a:
                            e = b2.piece_at(s)
                            # empty square
                            if not e:
                                mv_pt += 1
                            # enemy square
                            elif e.color == self.PLAYC:
                                cp_pt += 2
                        ppv -= sqrt(mv_pt + cp_pt)
                if m and m.piece_type == c.PAWN and m.color == self.COMPC:
                    # pawn ranks advanced
                    if self.COMPC == c.WHITE:
                        ppv += .2 * (i // 8 - 1)
                    else:
                        ppv += .2 * (6 - i // 8)
                    # pawn defended (other pawns do not count)
                    pawndef = False
                    for att in b.attackers(self.COMPC, i):
                        if b.piece_at(att).piece_type != c.PAWN:
                            pawndef = True
                    if pawndef:
                        ppv += .3
            # black king
            if b.is_check():
                ppv += .5
            for y in b.legal_moves:
                b.push(y)
                if b.is_checkmate():
                    ppv += 1
                b.pop()
            # ppv has been computed as positive = good until here,
            #   finally we add the sign here to be compatible with getval()'s score
            if self.COMPC == c.WHITE:
                return ppv
            else:
                return -ppv

        def getval1(b):
            "Get total piece value of board (White - Black, the usual method)"
            return (
                    self.PAWN_VALUE * len(b.pieces(c.PAWN, c.WHITE)) - len(b.pieces(c.PAWN, c.BLACK))
                    + self.KNIGHT_VALUE * (len(b.pieces(c.KNIGHT, c.WHITE)) - len(b.pieces(c.KNIGHT, c.BLACK)))
                    + self.BISHOP_VALUE * (len(b.pieces(c.BISHOP, c.WHITE)) - len(b.pieces(c.BISHOP, c.BLACK)))
                    + self.ROOK_VALUE * (len(b.pieces(c.ROOK, c.WHITE)) - len(b.pieces(c.ROOK, c.BLACK)))
                    + self.QUEEN_VALUE * (len(b.pieces(c.QUEEN, c.WHITE)) - len(b.pieces(c.QUEEN, c.BLACK)))
            )

        # elected not to use this to avoid run time becoming longer with division operations
        def getval2(b):
            "Get total piece value of board (White / Black, Turing's preferred method)"
            wv = (
                    len(b.pieces(c.PAWN, c.WHITE))
                    + 3 * len(b.pieces(c.KNIGHT, c.WHITE))
                    + 3.5 * len(b.pieces(c.BISHOP, c.WHITE))
                    + 5 * len(b.pieces(c.ROOK, c.WHITE))
                    + 10 * len(b.pieces(c.QUEEN, c.WHITE))
            )
            bv = (
                    len(b.pieces(c.PAWN, c.BLACK))
                    + 3 * len(b.pieces(c.KNIGHT, c.BLACK))
                    + 3.5 * len(b.pieces(c.BISHOP, c.BLACK))
                    + 5 * len(b.pieces(c.ROOK, c.BLACK))
                    + 10 * len(b.pieces(c.QUEEN, c.BLACK))
            )
            return wv / bv

        def getval(b):
            "Get total piece value of board"

            return getval1(b)

        def isdead(b, ml, p):
            "Is the position dead? (quiescence)"
            if p >= self.QPLIES or not len(ml):
                return True
            if b.is_check():
                return False
            x = b.pop()
            if (b.is_capture(x) and len(b.attackers(not b.turn, x.to_square))) or b.is_check():
                b.push(x)
                return False
            else:
                b.push(x)
                return True

        # https://chessprogramming.org/Alpha-Beta
        def searchmax(b, ply, alpha, beta):
            "Search moves and evaluate positions"

            self.NODES += 1
            if self.MATETEST:
                res = b.result(claim_draw=True)
                if res == '0-1':
                    return -1000
                if res == '1-0':
                    return 1000
                if res == '1/2-1/2':
                    return 0
            ml = order(b, ply)
            if ply >= self.MAXPLIES and isdead(b, ml, ply):
                return getval(b)
            if ply >= self.MAXPLIES:
                ml2 = []
                for x in ml:
                    if b.is_capture(x):
                        ml2.append(x)
                if len(ml2) == 0:  # no considerable moves
                    return getval(b)
            else:
                ml2 = ml
            for x in ml2:
                b.push(x)
                t = searchmin(b, ply + 1, alpha, beta)
                b.pop()
                if t >= beta:
                    return beta
                if t > alpha:
                    alpha = t
            return alpha

        def searchmin(b, ply, alpha, beta):
            "Search moves and evaluate positions"

            self.NODES += 1
            if self.MATETEST:
                res = b.result(claim_draw=True)
                if res == '0-1':
                    return -1000
                if res == '1-0':
                    return 1000
                if res == '1/2-1/2':
                    return 0
            ml = order(b, ply)
            if ply >= self.MAXPLIES and isdead(b, ml, ply):
                return getval(b)
            if ply >= self.MAXPLIES:
                ml2 = []
                for x in ml:
                    if b.is_capture(x):
                        ml2.append(x)
                if len(ml2) == 0:  # no considerable moves
                    return getval(b)
            else:
                ml2 = ml
            for x in ml2:
                b.push(x)
                t = searchmax(b, ply + 1, alpha, beta)
                b.pop()
                if t <= alpha:
                    return alpha
                if t < beta:
                    beta = t
            return beta

        def order(b, ply):
            "Move ordering"
            if ply > 0:
                return list(b.legal_moves)
            am, bm = [], []
            for x in b.legal_moves:
                if b.is_capture(x):
                    if b.piece_at(x.to_square):
                        # MVV/LVA sorting (http://home.hccnet.nl/h.g.muller/mvv.html)
                        am.append((x, 10 * b.piece_at(x.to_square).piece_type
                                   - b.piece_at(x.from_square).piece_type))
                    else:  # to square is empty during en passant capture
                        am.append((x, 10 - b.piece_at(x.from_square).piece_type))
                else:
                    am.append((x, b.piece_at(x.from_square).piece_type))
            am.sort(key=lambda m: m[1])
            am.reverse()
            bm = [q[0] for q in am]
            return bm

        def pm():
            if self.COMPC == c.WHITE:
                return 1
            else:
                return -1

        def getindex(ll):
            "Select either the best move or another move if easy play UCI parameters are set"
            if random() < (self.BlunderPercent / 100.):
                err = self.BlunderError / 10.
            else:
                err = self.MoveError / 10.
            if self.EasyLearn > 1:
                ind = int(expovariate(self.EasyLambda))
                return min(ind, len(ll) - 1, self.EasyLearn - 1)
            if err == 0 and self.PlayerAdvantage == 0:
                return 0  # best move
            else:
                vals = [x[2] for x in ll]
                inds = list(zip(vals, range(len(ll))))
                mm = [x for x in inds if (abs(x[0] - vals[0]) < err)]
                if self.COMPC == c.WHITE:
                    ma = [x for x in inds if x[0] <= -self.PlayerAdvantage / 10.]
                else:
                    ma = [x for x in inds if x[0] >= self.PlayerAdvantage / 10.]
                if len(ma) == 0:
                    ma = [x for x in inds if x[0] == 0]
                if self.PlayerAdvantage != 0 and len(ma) > 0:
                    return ma[0][1]
                elif err > 0 and len(mm) > 0:
                    return choice(mm)[1]
                else:
                    return 0

        def getmove(b):
            "Get move list for board"
            lastpos = getpos(b)
            ll = []

            # if not silent:
            # 	print(b.unicode())
            # 	print(getval(b))
            # 	print("FEN:", b.fen())

            #nl = len(list(b.legal_moves))
            cr0 = b.has_castling_rights(self.COMPC)
            #start = time.time()
            for n, x in enumerate(b.legal_moves):
                if b.is_castling(x):  # are we castling now?
                    castle = pm()
                else:
                    castle = 0
                b.push(x)
                p = getpos(b) - lastpos + castle
                cr = b.has_castling_rights(self.COMPC)
                if cr0 == True and cr == True:  # can we still castle later?
                    p += pm()
                for y in b.legal_moves:
                    if b.is_castling(y):  # can we castle in the next move?
                        p += pm()

                if self.COMPC == c.WHITE:
                    t = searchmin(b, 0, -1e6, 1e6)
                else:
                    t = searchmax(b, 0, -1e6, 1e6)
                # if not silent:
                # 	print("(%u/%u) %s %.1f %.2f" % (n + 1, nl, x, p, t))
                ll.append((x, p, t))
                b.pop()
            ll.sort(key=lambda m: m[1] + 1000 * m[2])
            if self.COMPC == c.WHITE:
                ll.reverse()
            i = getindex(ll)
            # print('# %.2f %s' % (ll[i][1] + ll[i][2], [str(ll[i][0])]))
            # print('info depth %d seldepth %d score cp %d time %d nodes %d pv %s' % (MAXPLIES + 1, QPLIES + 1,
            # 	100 * pm () * ll[i][2], 1000 * (time.time() - start), NODES, str(ll[i][0])))
            return str(ll[i][0])

        return getmove(b)


# This and 3ply search further into the game
class Turochamp2ply(Turochamp):
    def __init__(self, colour):
        super().__init__(colour)
        self.MAXPLIES = 2


# Sees knights as more valuable
class TurochampKnight(Turochamp):
    def __init__(self, colour):
        super().__init__(colour)
        self.KNIGHT_VALUE = 5


# Sees bishops as more valuable
class TurochampBishop(Turochamp):
    def __init__(self, colour):
        super().__init__(colour)
        self.BISHOP_VALUE = 5


class Turochamp2plyKnight(Turochamp):
    def __init__(self, colour):
        super().__init__(colour)
        self.MAXPLIES = 2
        self.KNIGHT_VALUE = 5


class Turochamp2plyBishop(Turochamp):
    def __init__(self, colour):
        super().__init__(colour)
        self.MAXPLIES = 2
        self.BISHOP_VALUE = 5
