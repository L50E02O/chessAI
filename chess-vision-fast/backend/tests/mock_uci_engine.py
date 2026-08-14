"""Minimal UCI engine for tests. Always replies with e2e4 (cp 57)."""


def main() -> None:
    for line in iter(sys.stdin.readline, ''):
        line = line.strip()
        if line == 'uci':
            print('id name MockEngine 1.0')
            print('id author test')
            print('uciok', flush=True)
        elif line == 'isready':
            print('readyok', flush=True)
        elif line.startswith('go'):
            print('info depth 15 score cp 57 pv e2e4 e7e5', flush=True)
            print('bestmove e2e4', flush=True)
        elif line == 'quit':
            break


if __name__ == '__main__':
    import sys
    main()
