import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.app.services.stockfish_service import (
    StockfishService,
    compute_castling,
    en_passant_from_history,
    evaluation_text,
)
from backend.app.stockfish_engine import StockfishEngine

MOCK = [sys.executable, str(Path(__file__).resolve().parent / 'mock_uci_engine.py')]


def test_evaluation_text_mate():
    assert evaluation_text(None, 3) == 'Checkmate in 3 move(s) for White.'
    assert evaluation_text(None, -2) == 'Checkmate in 2 move(s) for Black.'


def test_evaluation_text_cp():
    assert 'decisive advantage' in evaluation_text(450, None)
    assert 'better' in evaluation_text(-150, None)
    assert 'Balanced' in evaluation_text(50, None)


def test_compute_castling():
    assert compute_castling('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR') == 'KQkq'
    assert compute_castling('r3k3/8/8/8/8/8/8/R3K3') == 'Qq'
    assert compute_castling('4k3/8/8/8/8/8/8/4K3') == '-'


def test_en_passant_from_history():
    assert en_passant_from_history([]) == '-'
    assert en_passant_from_history(['e2e4']) == 'e3'
    assert en_passant_from_history(['e7e5']) == 'e6'
    assert en_passant_from_history(['g1f3']) == '-'


def test_service_analyze_position_builds_context():
    engine = StockfishEngine(command=MOCK)
    service = StockfishService(engine)
    result = service.analyze_position('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR')
    assert result['uci'] == 'e2e4'
    assert result['san'] == 'e4'
    assert result['score'] == {'cp': 57, 'mate': None}
    assert result['evaluation_text'] == 'Balanced position (+0.6).'
    assert result['source'] == 'stockfish'
    assert service.get_context()['total_moves'] == 1


def test_service_clear_context():
    engine = StockfishEngine(command=MOCK)
    service = StockfishService(engine)
    service.analyze_position('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR')
    service.clear_context()
    assert service.get_context()['total_moves'] == 0
