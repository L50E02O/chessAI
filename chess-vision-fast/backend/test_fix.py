"""Test de reparacion de FEN"""
import sys
sys.path.insert(0, '.')

from app.gemini_detector import GeminiDetector

d = GeminiDetector('t', 't')

# FEN problematico - primera fila suma 10 en lugar de 8
fen = 'r6knr/pp3pp1/2n1b3/2p5/8/3P1P2/PPP3PP/RNB1K1NR w KQkq - 0 1'
print(f'Original: {fen}')
print(f'Primera fila: r6knr = r(1) + 6 + k(1) + n(1) + r(1) = 10')

fixed = d._try_fix_fen(fen)
print(f'\nCorregido: {fixed}')

valid = d._validate_fen(fixed)
print(f'Valido: {valid}')

if valid:
    import chess
    try:
        b = chess.Board(fixed)
        print('\nTablero:')
        print(b)
    except Exception as e:
        print(f'Error: {e}')
