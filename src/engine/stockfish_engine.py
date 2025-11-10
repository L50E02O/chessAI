"""Engine wrapper. Tries to use python-stockfish or the bundled binary; falls back to a mock.
Keep this module as the single contract point.

Contract (small):
- get_best_move_for_fen(fen: str, depth: int=15) -> str | None
"""
import os
import shutil
import subprocess

from src.utils.config import STOCKFISH_PATH


def _try_python_stockfish(fen: str, depth: int = 15):
    sf = None
    try:
        from stockfish import Stockfish
        sf = Stockfish(path=STOCKFISH_PATH if os.path.exists(STOCKFISH_PATH) else None)
        sf.set_fen_position(fen)
        sf.set_depth(depth)
        best = sf.get_best_move()
        return best
    except Exception as e:
        print(f"Error in python-stockfish: {str(e)}")
        return None
    finally:
        # Clean up stockfish instance
        if sf:
            try:
                del sf
            except:
                pass


def _try_cli_stockfish(fen: str, depth: int = 10):
    if not os.path.exists(STOCKFISH_PATH):
        print(f"❌ Stockfish not found at: {STOCKFISH_PATH}")
        return None
    
    p = None
    stdin_handle = None
    stdout_handle = None
    stderr_handle = None
    
    try:
        # Use simple UCI commands
        # On Windows, we need to handle stdin/stdout more carefully
        import sys
        if sys.platform == 'win32':
            # Windows-specific: use creationflags to avoid console window
            p = subprocess.Popen(
                [STOCKFISH_PATH], 
                stdin=subprocess.PIPE, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
        else:
            p = subprocess.Popen(
                [STOCKFISH_PATH], 
                stdin=subprocess.PIPE, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
        
        stdin_handle = p.stdin
        stdout_handle = p.stdout
        stderr_handle = p.stderr
        
        # Check if process started correctly
        if p.poll() is not None:
            # Process already terminated
            error_output = stderr_handle.read() if stderr_handle else "Unknown error"
            print(f"❌ Stockfish process terminated immediately. Error: {error_output}")
            return None
        
        # Send UCI commands
        stdin_handle.write('uci\n')
        stdin_handle.flush()
        
        # Wait for uciok with timeout
        import time
        start = time.time()
        uci_ok = False
        while time.time() - start < 2:
            if p.poll() is not None:
                # Process died
                error_output = stderr_handle.read() if stderr_handle else "Process terminated"
                print(f"❌ Stockfish process died during UCI handshake. Error: {error_output}")
                return None
            
            line = stdout_handle.readline()
            if not line:
                time.sleep(0.1)  # Small delay if no output
                continue
            if 'uciok' in line.lower():
                uci_ok = True
                break
        
        if not uci_ok:
            print(f"⚠️ Stockfish did not respond with 'uciok' within timeout")
            # Try to read any error messages
            try:
                error_output = stderr_handle.read(1000) if stderr_handle else ""
                if error_output:
                    print(f"   Error output: {error_output[:200]}")
            except:
                pass
            return None
        
        # Validate FEN before sending to Stockfish to prevent crashes
        try:
            import chess
            try:
                test_board = chess.Board(fen)
            except Exception as fen_error:
                print(f"❌ Invalid FEN for Stockfish: {str(fen_error)}")
                return None
        except ImportError:
            # python-chess not available, skip validation
            pass
        
        # Set position and calculate with movetime limit
        try:
            stdin_handle.write(f'position fen {fen}\n')
            stdin_handle.flush()
        except (BrokenPipeError, OSError) as e:
            print(f"❌ Error writing to Stockfish: {str(e)}")
            return None
        
        try:
            stdin_handle.write(f'go depth {depth} movetime 2000\n')  # Max 2 seconds
            stdin_handle.flush()
        except (BrokenPipeError, OSError) as e:
            print(f"❌ Error sending go command to Stockfish: {str(e)}")
            return None
        
        best_move = None
        start = time.time()
        output_lines = []
        
        while time.time() - start < 5:  # 5 second total timeout
            if p.poll() is not None:
                # Process died during calculation
                try:
                    if stderr_handle:
                        error_output = stderr_handle.read(1000)
                    else:
                        error_output = "Process terminated"
                except:
                    error_output = "Process terminated (could not read stderr)"
                
                print(f"❌ Stockfish process died during calculation.")
                if error_output and error_output.strip():
                    print(f"   Error: {error_output[:200]}")
                if output_lines:
                    print(f"   Last output: {output_lines[-3:]}")
                return None
            
            try:
                line = stdout_handle.readline()
                if not line:
                    time.sleep(0.05)  # Small delay if no output
                    continue
                
                output_lines.append(line.strip())
                if line.startswith('bestmove'):
                    parts = line.split()
                    if len(parts) >= 2:
                        best_move = parts[1]
                        if best_move == '(none)':
                            print("⚠️ Stockfish returned 'none' as best move (checkmate/stalemate?)")
                            return None
                    break
                elif line.startswith('error'):
                    # Stockfish reported an error
                    print(f"❌ Stockfish error: {line.strip()}")
                    return None
            except (BrokenPipeError, OSError) as e:
                print(f"❌ Error reading from Stockfish: {str(e)}")
                return None
        
        if not best_move:
            print("⚠️ Stockfish did not return a best move within timeout")
            # Try to read any remaining output
            try:
                if stdout_handle and not stdout_handle.closed:
                    remaining = stdout_handle.read(500)
                    if remaining:
                        print(f"   Last output: {remaining[:200]}")
            except:
                pass
        
        return best_move
        
    except FileNotFoundError:
        print(f"❌ Stockfish executable not found at: {STOCKFISH_PATH}")
        return None
    except PermissionError:
        print(f"❌ Permission denied executing Stockfish at: {STOCKFISH_PATH}")
        return None
    except Exception as e:
        print(f"❌ Error in Stockfish CLI: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        # Properly close handles and terminate process (Windows-safe)
        # Close in reverse order: stdin first, then stdout, then stderr
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
        import time
        time.sleep(0.1)
        
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
                    except subprocess.TimeoutExpired:
                        # Force kill if terminate didn't work
                        try:
                            p.kill()
                            p.wait(timeout=1)
                        except:
                            pass
            except Exception as e:
                # Ignore errors during cleanup
                pass


def get_best_move_for_fen(fen: str, depth: int = 10) -> str:
    """Return best move string like 'e2e4' or algebraic like 'Nf3'. Could be None if not found."""
    # Try CLI method first
    ans = _try_cli_stockfish(fen, depth)
    if ans:
        return ans
    
    # Fallback to python-stockfish if available
    ans = _try_python_stockfish(fen, depth)
    if ans:
        return ans
    
    # Last resort: check if file exists and show helpful message
    if not os.path.exists(STOCKFISH_PATH):
        print(f'❌ Stockfish not found at: {STOCKFISH_PATH}')
        print('   Please update STOCKFISH_PATH in src/utils/config.py')
    else:
        print('⚠️ Stockfish CLI error occurred. Check error messages above.')
    
    print('   Returning mock move Nf3')
    return 'Nf3'
