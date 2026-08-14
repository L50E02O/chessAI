import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.app.stockfish_engine import StockfishEngine

MOCK = [sys.executable, str(Path(__file__).resolve().parent / 'mock_uci_engine.py')]


def test_analyze_position_with_mock_engine():
    engine = StockfishEngine(command=MOCK)
    result = engine.analyze_position('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
    assert result['uci'] == 'e2e4'
    assert result['score_cp'] == 57
    assert result['score_mate'] is None
    assert result['pv'] == ['e4', 'e5']
    assert result['source'] == 'stockfish'


def test_find_stockfish_with_configured_path_missing_returns_none():
    from backend.app.stockfish_engine import find_stockfish
    assert find_stockfish(configured_path=str(Path(__file__).resolve().parent / 'does_not_exist.exe'), auto_download=False) is None
