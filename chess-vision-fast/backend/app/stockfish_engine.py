import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import chess
from chess.engine import Limit, SimpleEngine

logger = logging.getLogger(__name__)


@dataclass
class MoveResult:
    uci: str
    san: str
    best_move: str
    score: Dict[str, Optional[int]]


class StockfishEngine:
    def __init__(self, path: Path, default_depth: int = 12) -> None:
        self.path = Path(path)
        self.default_depth = default_depth
        self.engine: Optional[SimpleEngine] = None
        self.board = chess.Board()

    def start(self) -> None:
        if self.engine:
            return
        logger.info('Iniciando Stockfish desde %s', self.path)
        self.engine = SimpleEngine.popen_uci(str(self.path))

    def set_fen(self, fen: str) -> None:
        self.board = chess.Board(fen)

    def get_best_move(self, depth: Optional[int] = None, time_ms: Optional[int] = None) -> MoveResult:
        self.start()
        if not self.engine:
            raise RuntimeError('Stockfish no pudo iniciarse')
        _depth = depth or self.default_depth
        limit = Limit(depth=_depth, time=(time_ms or 500) / 1000 if time_ms else None)
        result = self.engine.play(self.board, limit=limit)
        san = self.board.san(result.move)
        score = self.engine.analyse(self.board, limit=limit)['score']
        cp = score.pov(self.board.turn).score()
        mate = score.pov(self.board.turn).mate()
        return MoveResult(
            uci=result.move.uci(),
            san=san,
            best_move=result.move.uci(),
            score={'cp': cp, 'mate': mate},
        )

    def close(self) -> None:
        if self.engine:
            self.engine.quit()
            self.engine = None
