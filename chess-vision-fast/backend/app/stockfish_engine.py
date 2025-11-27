import asyncio
import logging
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from threading import Thread
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


def _open_stockfish_sync(path: str) -> SimpleEngine:
    """
    Abre Stockfish de forma sincrona, compatible con Windows + FastAPI threads.
    Crea un event loop dedicado en un thread separado para evitar conflictos.
    """
    result = [None, None]  # [engine, exception]
    
    def run_in_thread():
        try:
            if sys.platform == 'win32':
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                engine = SimpleEngine.popen_uci(path)
                result[0] = engine
            finally:
                pass  # No cerramos el loop, el engine lo necesita
        except Exception as e:
            result[1] = e
    
    thread = Thread(target=run_in_thread)
    thread.start()
    thread.join(timeout=10)
    
    if result[1]:
        raise result[1]
    if result[0] is None:
        raise RuntimeError('Timeout al iniciar Stockfish')
    return result[0]


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
        self.engine = _open_stockfish_sync(str(self.path))

    def set_fen(self, fen: str) -> None:
        self.board = chess.Board(fen)

    def get_best_move(self, depth: Optional[int] = None, time_ms: Optional[int] = None) -> MoveResult:
        self.start()
        if not self.engine:
            raise RuntimeError('Stockfish no pudo iniciarse')
        _depth = depth or self.default_depth
        # Timeout maximo de 5 segundos para evitar cuelgues
        _time = min((time_ms or 500) / 1000, 5.0) if time_ms else 2.0
        limit = Limit(depth=_depth, time=_time)
        result = self.engine.play(self.board, limit=limit)
        san = self.board.san(result.move)
        score = self.engine.analyse(self.board, limit=Limit(depth=min(_depth, 10), time=1.0))['score']
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
