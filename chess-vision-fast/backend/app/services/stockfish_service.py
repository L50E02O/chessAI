"""Chess analysis service using local Stockfish. Maintains game context."""
import logging
from typing import Optional

import chess

from ..fen_sanitizer import compute_castling
from ..stockfish_engine import StockfishEngine

logger = logging.getLogger(__name__)


def resolve_active_color(fen: str, turn: Optional[str] = None) -> str:
    if turn in ('w', 'b'):
        return turn
    parts = fen.split()
    if len(parts) > 1 and parts[1] in ('w', 'b'):
        return parts[1]
    return 'w'


def en_passant_from_history(move_history_uci: list) -> str:
    if not move_history_uci:
        return '-'
    fr, to = move_history_uci[-1][:2], move_history_uci[-1][2:4]
    if fr[0] == to[0] and abs(int(fr[1]) - int(to[1])) == 2:
        return to[0] + str((int(fr[1]) + int(to[1])) // 2)
    return '-'


def evaluation_text(score_cp, score_mate) -> str:
    if score_mate is not None:
        side = 'White' if score_mate > 0 else 'Black'
        return f'Checkmate in {abs(score_mate)} move(s) for {side}.'
    if score_cp is None:
        return 'No evaluation available.'
    if score_cp > 300:
        return f'White has a decisive advantage (+{score_cp / 100:.1f}).'
    if score_cp > 100:
        return f'White is better (+{score_cp / 100:.1f}).'
    if score_cp > -100:
        return f'Balanced position ({score_cp / 100:+.1f}).'
    if score_cp > -300:
        return f'Black is better ({score_cp / 100:+.1f}).'
    return f'Black has a decisive advantage ({score_cp / 100:+.1f}).'


class StockfishService:
    def __init__(self, engine: StockfishEngine) -> None:
        self.engine = engine
        self.move_history_uci: list = []
        self.move_history_san: list = []
        self.current_fen: Optional[str] = None

    def analyze_position(self, fen: str, turn: Optional[str] = None, depth: Optional[int] = None) -> dict:
        board = chess.Board(fen.split()[0])
        active = resolve_active_color(fen, turn)
        castling = compute_castling(fen.split()[0])
        ep = en_passant_from_history(self.move_history_uci)
        parts = board.fen().split()
        parts[1] = active
        parts[2] = castling
        parts[3] = ep
        complete = ' '.join(parts)

        result = self.engine.analyze_position(complete, depth=depth)

        b = chess.Board(complete)
        move = chess.Move.from_uci(result['uci'])
        san = b.san(move)
        self.move_history_uci.append(result['uci'])
        self.move_history_san.append(san)
        self.current_fen = complete

        return {
            'uci': result['uci'],
            'san': san,
            'score': {'cp': result['score_cp'], 'mate': result['score_mate']},
            'pv': result['pv'],
            'evaluation_text': evaluation_text(result['score_cp'], result['score_mate']),
            'turn': active,
            'depth': result['depth'],
            'source': 'stockfish',
        }

    def get_context(self) -> dict:
        return {
            'move_history': self.move_history_san,
            'total_moves': len(self.move_history_san),
            'current_fen': self.current_fen,
        }

    def clear_context(self) -> None:
        self.move_history_uci = []
        self.move_history_san = []
        self.current_fen = None
