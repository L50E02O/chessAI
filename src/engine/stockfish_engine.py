"""Engine wrapper. Tries to use python-stockfish or the bundled binary; falls back to a mock.
Keep this module as the single contract point.

Contract (small):
- get_best_move_for_fen(fen: str, depth: int=15) -> str | None
"""
import os
import shutil
import subprocess
import time
import sys
from typing import Optional

from src.utils.config import STOCKFISH_PATH, STOCKFISH_DOWNLOAD_URL
from src.utils.helpers import short_log


def _find_stockfish() -> Optional[str]:
    """
    Tries to find Stockfish executable in common locations.
    Returns path if found, None otherwise.
    """
    # First check the configured path
    if os.path.exists(STOCKFISH_PATH):
        return STOCKFISH_PATH
    
    # Common Windows locations
    common_paths = [
        r"C:\Program Files\Stockfish\stockfish.exe",
        r"C:\Program Files (x86)\Stockfish\stockfish.exe",
        os.path.expanduser(r"~\Downloads\stockfish-windows-x86-64-avx2\stockfish\stockfish-windows-x86-64-avx2.exe"),
        os.path.expanduser(r"~\Downloads\stockfish\stockfish.exe"),
        os.path.expanduser(r"~\Desktop\stockfish.exe"),
        r"C:\stockfish\stockfish.exe",
    ]
    
    # Also check in Downloads folder for common variations
    downloads = os.path.expanduser("~/Downloads")
    if os.path.exists(downloads):
        for root, dirs, files in os.walk(downloads):
            # Limit search depth to avoid long searches
            depth = root[len(downloads):].count(os.sep)
            if depth > 2:
                continue
            
            for file in files:
                if file.lower() in ['stockfish.exe', 'stockfish-windows-x86-64-avx2.exe']:
                    path = os.path.join(root, file)
                    if os.path.isfile(path):
                        return path
    
    # Check common paths
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    # As a last resort on Windows, attempt to download automatically
    if sys.platform == 'win32':
        try:
            dl = _download_and_extract_stockfish()
            if dl and os.path.exists(dl):
                return dl
        except Exception as e:
            short_log(f"⚠️ Auto-download failed: {str(e)[:120]}")

    return None


def _download_and_extract_stockfish(url: str = STOCKFISH_DOWNLOAD_URL) -> Optional[str]:
    """Download and extract Stockfish for Windows into external/ and return the exe path.

    Uses only stdlib (urllib, zipfile). Safe to call multiple times; skips download if already present.
    """
    import urllib.request
    import zipfile

    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    external_dir = os.path.join(root, 'external')
    os.makedirs(external_dir, exist_ok=True)

    zip_path = os.path.join(external_dir, 'stockfish-win-avx2.zip')
    extract_dir = os.path.join(external_dir, 'stockfish_win')
    os.makedirs(extract_dir, exist_ok=True)

    # If an exe already exists in extract_dir, return it
    for dirpath, _, files in os.walk(extract_dir):
        for fn in files:
            if fn.lower().startswith('stockfish') and fn.lower().endswith('.exe'):
                return os.path.join(dirpath, fn)

    short_log('⬇️ Downloading Stockfish (Windows AVX2)...')
    short_log(f'   {url}')
    try:
        urllib.request.urlretrieve(url, zip_path)
    except Exception as e:
        raise RuntimeError(f'Failed to download Stockfish: {e}')

    short_log('📦 Extracting Stockfish...')
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extract_dir)
    except Exception as e:
        raise RuntimeError(f'Failed to extract Stockfish zip: {e}')
    finally:
        try:
            os.remove(zip_path)
        except Exception:
            pass

    # Find exe after extraction
    for dirpath, _, files in os.walk(extract_dir):
        for fn in files:
            if fn.lower().startswith('stockfish') and fn.lower().endswith('.exe'):
                exe_path = os.path.join(dirpath, fn)
                short_log(f'✅ Stockfish ready: {exe_path}')
                return exe_path

    raise RuntimeError('Stockfish executable not found after extraction.')


def _try_python_stockfish(fen: str, depth: int = 15) -> Optional[str]:
    """
    Tries to use python-stockfish library.
    Returns best move or None on error.
    """
    sf = None
    try:
        from stockfish import Stockfish
        
        # Try to find Stockfish path
        stockfish_path = STOCKFISH_PATH if os.path.exists(STOCKFISH_PATH) else None
        if not stockfish_path:
            stockfish_path = _find_stockfish()
        
        # Initialize Stockfish
        try:
            if stockfish_path:
                sf = Stockfish(path=stockfish_path)
            else:
                # Let python-stockfish try to find it automatically
                sf = Stockfish()
        except Exception as init_error:
            short_log(f"⚠️ Could not initialize python-stockfish: {str(init_error)[:100]}")
            return None
        
        # Check if Stockfish object was created successfully
        if sf is None:
            return None
        
        # Set position and get move
        try:
            sf.set_fen_position(fen)
            sf.set_depth(depth)
            best = sf.get_best_move()
            return best
        except Exception as move_error:
            short_log(f"⚠️ Error getting move from python-stockfish: {str(move_error)[:100]}")
            return None
            
    except ImportError:
        # python-stockfish not installed
        return None
    except Exception as e:
        error_msg = str(e)
        # Suppress AttributeError during cleanup (known issue with python-stockfish)
        if 'AttributeError' not in str(type(e).__name__) and '_stockfish' not in error_msg:
            short_log(f"⚠️ Error in python-stockfish: {error_msg[:100]}")
        return None
    finally:
        # Clean up stockfish instance carefully
        if sf is not None:
            try:
                # Try to properly close if method exists
                if hasattr(sf, 'quit'):
                    try:
                        sf.quit()
                    except:
                        pass
            except:
                pass
            try:
                # Delete the object, but ignore AttributeError during cleanup
                del sf
            except (AttributeError, TypeError):
                # Known issue: python-stockfish sometimes has cleanup issues
                pass


def _validate_fen_strict(fen: str):
    """
    Validates FEN string strictly before sending to Stockfish.
    Returns (is_valid, error_message)
    """
    if not fen or not isinstance(fen, str):
        return False, "FEN is empty or not a string"
    
    # Check basic structure
    parts = fen.strip().split()
    if len(parts) < 4:
        return False, f"FEN must have at least 4 parts, got {len(parts)}"
    
    # Validate position part (first part)
    position = parts[0]
    rows = position.split('/')
    if len(rows) != 8:
        return False, f"FEN must have 8 rows, got {len(rows)}"
    
    # Validate each row has exactly 8 squares
    for i, row in enumerate(rows):
        square_count = 0
        for char in row:
            if char.isdigit():
                square_count += int(char)
            elif char in 'rnbqkpRNBQKP':
                square_count += 1
            else:
                return False, f"Row {8-i} contains invalid character: '{char}'"
        
        if square_count != 8:
            return False, f"Row {8-i} has {square_count} squares, must be 8"
    
    # Check for exactly one king of each color
    white_kings = position.count('K')
    black_kings = position.count('k')
    if white_kings != 1:
        return False, f"Must have exactly 1 white king, found {white_kings}"
    if black_kings != 1:
        return False, f"Must have exactly 1 black king, found {black_kings}"
    
    # Use python-chess for final validation if available
    try:
        import chess
        try:
            board = chess.Board(fen)
            # Additional check: ensure the position is legal
            if board.is_checkmate() or board.is_stalemate():
                # These are valid positions, just terminal
                pass
        except ValueError as e:
            return False, f"python-chess validation failed: {str(e)}"
    except ImportError:
        # python-chess not available, basic validation passed
        pass
    
    return True, None


def _try_cli_stockfish(fen: str, depth: int = 10) -> Optional[str]:
    """
    Improved Stockfish CLI communication with better error handling.
    """
    # Try to find Stockfish if configured path doesn't exist
    stockfish_path = STOCKFISH_PATH if os.path.exists(STOCKFISH_PATH) else _find_stockfish()
    
    if not stockfish_path or not os.path.exists(stockfish_path):
        if not os.path.exists(STOCKFISH_PATH):
            short_log(f"❌ Stockfish not found at: {STOCKFISH_PATH}")
            found_path = _find_stockfish()
            if found_path:
                short_log(f"💡 Found Stockfish at: {found_path}")
                short_log(f"   Update STOCKFISH_PATH in src/utils/config.py to use this path")
                stockfish_path = found_path
            else:
                short_log(f"💡 Tip: Download Stockfish from https://github.com/official-stockfish/Stockfish/releases/latest/download/stockfish-windows-x86-64-avx2.zip")
                short_log(f"   Then update STOCKFISH_PATH in src/utils/config.py")
                return None
        else:
            return None
    
    # Strict FEN validation before attempting to use Stockfish
    is_valid, error_msg = _validate_fen_strict(fen)
    if not is_valid:
        short_log(f"❌ Invalid FEN rejected before Stockfish: {error_msg}")
        return None
    
    p = None
    stdin_handle = None
    stdout_handle = None
    stderr_handle = None
    
    try:
        # Use simple UCI commands
        # On Windows, we need to handle stdin/stdout more carefully
        if sys.platform == 'win32':
            # Windows-specific: use creationflags to avoid console window
            p = subprocess.Popen(
                [stockfish_path], 
                stdin=subprocess.PIPE, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                bufsize=1,  # Line buffered
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
        else:
            p = subprocess.Popen(
                [stockfish_path], 
                stdin=subprocess.PIPE, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                bufsize=1  # Line buffered
            )
        
        stdin_handle = p.stdin
        stdout_handle = p.stdout
        stderr_handle = p.stderr
        
        # Check if process started correctly
        time.sleep(0.1)  # Give process a moment to start
        if p.poll() is not None:
            # Process already terminated
            try:
                error_output = stderr_handle.read(1000) if stderr_handle else "Unknown error"
            except:
                error_output = "Could not read error"
            short_log(f"❌ Stockfish process terminated immediately. Error: {error_output[:200]}")
            return None
        
        # Send UCI commands
        try:
            stdin_handle.write('uci\n')
            stdin_handle.flush()
        except (BrokenPipeError, OSError, ValueError) as e:
            short_log(f"❌ Error sending UCI command: {str(e)}")
            return None
        
        # Wait for uciok with timeout
        start = time.time()
        uci_ok = False
        while time.time() - start < 3:  # Increased timeout
            if p.poll() is not None:
                # Process died
                try:
                    error_output = stderr_handle.read(1000) if stderr_handle else "Process terminated"
                except:
                    error_output = "Process terminated (could not read stderr)"
                short_log(f"❌ Stockfish process died during UCI handshake. Error: {error_output[:200]}")
                return None
            
            try:
                line = stdout_handle.readline()
                if not line:
                    time.sleep(0.1)  # Small delay if no output
                    continue
                if 'uciok' in line.lower():
                    uci_ok = True
                    break
            except (BrokenPipeError, OSError) as e:
                short_log(f"❌ Error reading UCI response: {str(e)}")
                return None
        
        if not uci_ok:
            short_log(f"⚠️ Stockfish did not respond with 'uciok' within timeout")
            return None
        
        # Set position and calculate with movetime limit
        try:
            stdin_handle.write(f'position fen {fen}\n')
            stdin_handle.flush()
        except (BrokenPipeError, OSError, ValueError) as e:
            short_log(f"❌ Error writing position to Stockfish: {str(e)}")
            return None
        
        try:
            # Use both depth and movetime for safety
            stdin_handle.write(f'go depth {depth} movetime 3000\n')  # Max 3 seconds
            stdin_handle.flush()
        except (BrokenPipeError, OSError, ValueError) as e:
            short_log(f"❌ Error sending go command to Stockfish: {str(e)}")
            return None
        
        best_move = None
        start = time.time()
        output_lines = []
        max_wait_time = 6  # Increased total timeout
        
        while time.time() - start < max_wait_time:
            if p.poll() is not None:
                # Process died during calculation
                try:
                    if stderr_handle:
                        error_output = stderr_handle.read(1000)
                    else:
                        error_output = "Process terminated"
                except:
                    error_output = "Process terminated (could not read stderr)"
                
                short_log(f"❌ Stockfish process died during calculation.")
                if error_output and error_output.strip():
                    short_log(f"   Error: {error_output[:200]}")
                if output_lines:
                    short_log(f"   Last output: {output_lines[-3:]}")
                return None
            
            try:
                line = stdout_handle.readline()
                if not line:
                    time.sleep(0.05)  # Small delay if no output
                    continue
                
                line = line.strip()
                output_lines.append(line)
                
                if line.startswith('bestmove'):
                    parts = line.split()
                    if len(parts) >= 2:
                        best_move = parts[1]
                        if best_move == '(none)':
                            short_log("⚠️ Stockfish returned 'none' as best move (checkmate/stalemate?)")
                            return None
                    break
                elif line.startswith('error'):
                    # Stockfish reported an error
                    short_log(f"❌ Stockfish error: {line}")
                    return None
            except (BrokenPipeError, OSError) as e:
                short_log(f"❌ Error reading from Stockfish: {str(e)}")
                return None
        
        if not best_move:
            short_log("⚠️ Stockfish did not return a best move within timeout")
            # Try to read any remaining output
            try:
                if stdout_handle and not stdout_handle.closed:
                    remaining = stdout_handle.read(500)
                    if remaining:
                        short_log(f"   Last output: {remaining[:200]}")
            except:
                pass
        
        return best_move
        
    except FileNotFoundError:
        short_log(f"❌ Stockfish executable not found at: {stockfish_path}")
        return None
    except PermissionError:
        short_log(f"❌ Permission denied executing Stockfish at: {stockfish_path}")
        return None
    except Exception as e:
        short_log(f"❌ Error in Stockfish CLI: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        # Properly close handles and terminate process (Windows-safe)
        # Close in reverse order: stdin first, then stdout, then stderr
        cleanup_success = False
        max_cleanup_time = 2.0
        cleanup_start = time.time()
        
        try:
            if stdin_handle and not stdin_handle.closed:
                try:
                    # Try to send quit command
                    stdin_handle.write('quit\n')
                    stdin_handle.flush()
                except (BrokenPipeError, OSError, ValueError):
                    pass
                finally:
                    try:
                        stdin_handle.close()
                    except:
                        pass
        except:
            pass
        
        # Give process a moment to process quit command
        time.sleep(0.15)
        
        try:
            if stdout_handle and not stdout_handle.closed:
                stdout_handle.close()
        except:
            pass
        
        try:
            if stderr_handle and not stderr_handle.closed:
                stderr_handle.close()
        except:
            pass
        
        # Ensure process is terminated
        if p:
            try:
                if p.poll() is None:
                    # Process still running, terminate it
                    p.terminate()
                    try:
                        p.wait(timeout=1)
                        cleanup_success = True
                    except subprocess.TimeoutExpired:
                        # Force kill if terminate didn't work
                        try:
                            p.kill()
                            p.wait(timeout=0.5)
                            cleanup_success = True
                        except:
                            pass
                else:
                    cleanup_success = True
            except Exception:
                # Ignore errors during cleanup
                pass


def get_best_move_for_fen(fen: str, depth: int = 10) -> Optional[str]:
    """
    Return best move string like 'e2e4' or algebraic like 'Nf3'. 
    Returns None if not found or on error.
    """
    if not fen:
        short_log("❌ Empty FEN provided to Stockfish")
        return None
    
    # Validate FEN first
    is_valid, error_msg = _validate_fen_strict(fen)
    if not is_valid:
        short_log(f"❌ FEN validation failed: {error_msg}")
        return None
    
    # Try CLI method first (more reliable)
    ans = _try_cli_stockfish(fen, depth)
    if ans:
        return ans
    
    # Fallback to python-stockfish if available
    ans = _try_python_stockfish(fen, depth)
    if ans:
        return ans
    
    # Last resort: check if file exists and show helpful message
    found_path = _find_stockfish()
    if not os.path.exists(STOCKFISH_PATH) and not found_path:
        short_log(f'❌ Stockfish not found at: {STOCKFISH_PATH}')
        short_log('💡 To fix this:')
        short_log('   1. Download Stockfish from https://github.com/official-stockfish/Stockfish/releases/latest/download/stockfish-windows-x86-64-avx2.zip')
        short_log('   2. Extract it to a folder (e.g., C:\\stockfish\\stockfish.exe)')
        short_log('   3. Update STOCKFISH_PATH in src/utils/config.py with the correct path')
    elif found_path and not os.path.exists(STOCKFISH_PATH):
        short_log(f'💡 Found Stockfish at: {found_path}')
        short_log('   Update STOCKFISH_PATH in src/utils/config.py to use this automatically')
    else:
        short_log('⚠️ Stockfish CLI error occurred. Check error messages above.')
    
    # Don't return mock move - return None to indicate failure
    return None
