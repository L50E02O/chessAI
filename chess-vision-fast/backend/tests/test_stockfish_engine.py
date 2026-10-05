import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.app import stockfish_engine
from backend.app.stockfish_engine import StockfishEngine

MOCK = [sys.executable, str(Path(__file__).resolve().parent / 'mock_uci_engine.py')]
START_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'


def test_analyze_position_with_mock_engine():
    engine = StockfishEngine(command=MOCK)
    result = engine.analyze_position(START_FEN)
    assert result['uci'] == 'e2e4'
    assert result['score_cp'] == 57
    assert result['score_mate'] is None
    assert result['pv'] == ['e4', 'e5']
    assert result['source'] == 'stockfish'


def test_analyze_position_returns_multipv_lines():
    engine = StockfishEngine(command=MOCK)
    result = engine.analyze_position(START_FEN, multipv=3)
    assert [line['uci'] for line in result['lines']] == ['e2e4', 'd2d4', 'g1f3']
    assert [line['rank'] for line in result['lines']] == [1, 2, 3]
    assert result['lines'][0]['score_cp'] == 57
    assert result['lines'][1]['san'] == 'd4'


def test_analyze_position_nps_none_when_engine_omits_it():
    result = StockfishEngine(command=MOCK).analyze_position(START_FEN)
    assert result['lines'][0]['nps'] is None


def test_engine_name_reads_uci_id():
    assert StockfishEngine(command=MOCK).engine_name() == 'MockEngine 1.0'


def test_find_stockfish_with_configured_path_missing_returns_none(tmp_path, monkeypatch):
    # Isolate from any real Stockfish installed on the machine (app/bin, Program Files, ~/Downloads).
    monkeypatch.setattr(stockfish_engine, 'BIN_DIR', tmp_path / 'bin')
    monkeypatch.setattr(stockfish_engine, 'COMMON_PATHS', [])
    monkeypatch.setattr(stockfish_engine.os.path, 'expanduser', lambda p: str(tmp_path / 'home'))
    missing = str(tmp_path / 'does_not_exist.exe')
    assert stockfish_engine.find_stockfish(configured_path=missing, auto_download=False) is None
