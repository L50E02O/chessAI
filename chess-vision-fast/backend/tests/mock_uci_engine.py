"""Minimal UCI engine for tests.

Always replies with e2e4 (cp 57) as the best move. Advertises the MultiPV
option like real Stockfish; when the position is the standard start position
and MultiPV > 1 it also emits d2d4 (cp 40) and g1f3 (cp 30).
"""

EXTRA_LINES = [
    'score cp 40 pv d2d4 d7d5',
    'score cp 30 pv g1f3 g8f6',
]


def main() -> None:
    multipv = 1
    position = ''
    for line in iter(sys.stdin.readline, ''):
        line = line.strip()
        if line == 'uci':
            print('id name MockEngine 1.0')
            print('id author test')
            print('option name MultiPV type spin default 1 min 1 max 500')
            print('uciok', flush=True)
        elif line == 'isready':
            print('readyok', flush=True)
        elif line.startswith('setoption name MultiPV value'):
            multipv = int(line.split()[-1])
        elif line.startswith('position'):
            position = line
        elif line.startswith('go'):
            print('info depth 15 multipv 1 score cp 57 pv e2e4 e7e5', flush=True)
            if position.startswith('position startpos') and 'moves' not in position:
                for i, extra in enumerate(EXTRA_LINES[: max(0, multipv - 1)], start=2):
                    print(f'info depth 15 multipv {i} {extra}', flush=True)
            print('bestmove e2e4', flush=True)
        elif line == 'quit':
            break


if __name__ == '__main__':
    import sys
    main()
