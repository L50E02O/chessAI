import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.append(str(Path(__file__).resolve().parents[2]))

import chess
from backend.app.stockfish_engine import StockfishEngine


class _FakeScore:
    def __init__(self, cp=20, mate=None):
        self._cp = cp
        self._mate = mate

    def pov(self, color):
        return self

    def score(self):
        return self._cp

    def mate(self):
        return self._mate


class _FakeResult:
    def __init__(self, move_uci):
        self.move = chess.Move.from_uci(move_uci)


@patch('chess.engine.SimpleEngine.popen_uci')
def test_get_best_move(mock_popen):
    fake_engine = MagicMock()
    fake_engine.play.return_value = _FakeResult('e2e4')
    fake_engine.analyse.return_value = {'score': _FakeScore(cp=34)}
    mock_popen.return_value = fake_engine

    engine = StockfishEngine('stockfish_binary', default_depth=5)
    engine.start()
    engine.set_fen(chess.STARTING_FEN)
    move = engine.get_best_move(depth=2, time_ms=200)

    assert move.uci == 'e2e4'
    assert move.score['cp'] == 34
    fake_engine.play.assert_called_once()
    fake_engine.analyse.assert_called()
    engine.close()
