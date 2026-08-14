# Piece templates

The 12 PNGs in this directory are the chess.com default "neo" piece set
(150px), downloaded from:

    https://images.chesscomfiles.com/chess-themes/pieces/neo/150/

Used as template-matching references to classify pieces detected in
chess.com screenshots. FEN mapping: `w` = white, `b` = black; the letter
is the piece type (`P N B R Q K`).

License: chess.com piece images are provided for chess UI purposes. Re-run
`backend/scripts/download_pieces.py` to regenerate.
