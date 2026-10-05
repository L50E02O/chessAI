import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import io

import numpy as np
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.stockfish_service import StockfishService
from backend.app.stockfish_engine import StockfishEngine
from backend.app.api import routes
from tests.helpers.board_renderer import render_board

MOCK = [sys.executable, str(Path(__file__).resolve().parent / 'mock_uci_engine.py')]
client = TestClient(app)


def _png_bytes(fen):
    img = render_board(fen)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


def test_detect_endpoint():
    routes._chess_service = StockfishService(StockfishEngine(command=MOCK))
    files = {'file': ('board.png', _png_bytes('4k3/8/8/8/8/8/8/4K3 w - - 0 1'), 'image/png')}
    response = client.post('/api/detect', files=files)
    assert response.status_code == 200
    data = response.json()
    assert '4k3/8/8/8/8/8/8/4K3' in data['fen']
    assert data['orientation'] in ('w-bottom', 'w-top')


def test_best_move_endpoint():
    routes._chess_service = StockfishService(StockfishEngine(command=MOCK))
    response = client.post('/api/best_move', json={'fen': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'})
    assert response.status_code == 200
    data = response.json()
    assert data['uci'] == 'e2e4'
    assert data['san'] == 'e4'
    assert data['source'] == 'stockfish'
    assert data['score_text'] == '+0.57'
    assert [line['uci'] for line in data['lines']] == ['e2e4', 'd2d4', 'g1f3']


def test_engine_endpoint_reports_engine_name():
    routes._chess_service = StockfishService(StockfishEngine(command=MOCK, depth=12))
    response = client.get('/api/engine')
    assert response.status_code == 200
    assert response.json() == {'name': 'MockEngine 1.0', 'depth': 12}


def test_engine_endpoint_reports_error_when_engine_missing():
    routes._chess_service = StockfishService(
        StockfishEngine(command=[sys.executable, str(Path(__file__).resolve().parent / 'nope.py')])
    )
    data = client.get('/api/engine').json()
    assert data['name'] is None
    assert data['error']


def test_detect_and_move_endpoint():
    routes._chess_service = StockfishService(StockfishEngine(command=MOCK))
    files = {'file': ('board.png', _png_bytes('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'), 'image/png')}
    response = client.post('/api/detect_and_move', files=files)
    assert response.status_code == 200
    data = response.json()
    assert data['fen'].startswith('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR')
    assert data['best_move'] == 'e2e4'
    assert data['overlay_image_base64']
    assert data['squares']


def test_context_endpoint():
    routes._chess_service = StockfishService(StockfishEngine(command=MOCK))
    client.post('/api/clear_context')
    response = client.get('/api/context')
    assert response.status_code == 200
    assert response.json()['total_moves'] == 0


from backend.app.fen_sanitizer import INVALID_FEN_MESSAGE


def test_best_move_invalid_fen_returns_clear_error():
    routes._chess_service = StockfishService(StockfishEngine(command=MOCK))
    response = client.post('/api/best_move', json={'fen': 'not a fen at all'})
    assert response.status_code == 200
    data = response.json()
    assert data['uci'] is None
    assert data['error'] == INVALID_FEN_MESSAGE


def test_detect_returns_fen_warnings_on_castling_prune():
    routes._chess_service = StockfishService(StockfishEngine(command=MOCK))
    files = {'file': ('board.png', _png_bytes('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQkq - 0 1'), 'image/png')}
    response = client.post('/api/detect', files=files)
    assert response.status_code == 200
    data = response.json()
    assert data['fen_warnings']
    assert 'K' not in data['fen'].split()[2]  # K pruned (h1 empty)


def test_detect_and_move_includes_fen_warnings():
    routes._chess_service = StockfishService(StockfishEngine(command=MOCK))
    files = {'file': ('board.png', _png_bytes('4k3/8/8/8/8/8/4P3/4K3 w - - 0 1'), 'image/png')}
    response = client.post('/api/detect_and_move', files=files)
    assert response.status_code == 200
    data = response.json()
    assert 'fen_warnings' in data
    assert isinstance(data['fen_warnings'], list)
