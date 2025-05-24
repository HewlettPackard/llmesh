#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Defines a singleton class for managing background processes in Python within a Jupyter kernel.

This class ensures that background processes are cleaned up when the kernel exits.
It provides methods to start, kill, and manage background processes.
The class is designed to be used in a Jupyter notebook or similar environment,
where the kernel may be restarted or interrupted.

Also handles port management, allowing users to find and kill processes using specific ports.
"""

import subprocess
import os
import signal
import atexit
import time


class BackgroundProcessManager:
    """
    Manages background processes, ensuring they are cleaned up on exit.
    This class is designed as a singleton to maintain a single list of processes
    per Python session (Jupyter kernel).
    """
    _instance = None
    _processes: dict[str, subprocess.Popen] = {}
    _atexit_registered = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(BackgroundProcessManager, cls).__new__(cls)
            # Initialize the instance-specific state if needed,
            # but shared state like _processes is class-level.
            if not cls._atexit_registered:
                # Only register atexit if it hasn't been done yet in this session.
                # This handles cases where the module might be reloaded in some environments,
                # though typically atexit handles multiple registrations of the same function gracefully.
                atexit.register(cls._cleanup_all_processes_on_exit)
                cls._atexit_registered = True
                if cls._is_running_in_jupyter():
                    print("BackgroundProcessManager: atexit handler registered for automated cleanup on kernel exit.")
        return cls._instance

    @staticmethod
    def _is_running_in_jupyter():
        """Checks if the code is likely running in a Jupyter/IPython environment."""
        try:
            # This is a common check for IPython/Jupyter environments.
            # __IPYTHON__ is defined by IPython.
            if '__IPYTHON__' in globals(): # type: ignore
                return True
            # Another check specifically for shell type.
            from IPython import get_ipython # type: ignore
            if get_ipython() is not None and get_ipython().__class__.__name__ == 'ZMQInteractiveShell':
                return True # Jupyter notebook or qtconsole
        except ImportError:
            pass # IPython not available
        except NameError:
            pass # __IPYTHON__ not defined
        return False


    def start_process(self, name: str, command: str) -> subprocess.Popen | None:
        """
        Starts a background process.

        Args:
            name: A unique name to identify the process.
            command: The shell command to execute.

        Returns:
            The subprocess.Popen object if successful, None otherwise.
        """
        if name in self._processes:
            existing_process = self._processes[name]
            if existing_process.poll() is None:  # None means process is still running
                print(f"BackgroundProcessManager: Process '{name}' (PID: {existing_process.pid}) is already running. Not starting a new one.")
                return existing_process
            else:
                print(f"BackgroundProcessManager: Process '{name}' was previously registered but has exited. Starting a new one.")

        preexec_fn_to_use = None
        creation_flags_to_use = 0

        if os.name == 'nt':
            creation_flags_to_use = subprocess.CREATE_NEW_PROCESS_GROUP
        else: # POSIX
            preexec_fn_to_use = os.setsid # Make the process a new session leader

        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=preexec_fn_to_use,
                creationflags=creation_flags_to_use
            )
            self._processes[name] = process
            pid_info = f"PID: {process.pid}"
            if os.name != 'nt':
                pid_info += f", PGID: {os.getpgid(process.pid)}"
            print(f"BackgroundProcessManager: Started '{name}' ({pid_info}). Command: {command}")
            if process.returncode is not None:
                print(f"BackgroundProcessManager: Process '{name}' exited immediately with return code {process.returncode}.")
                print(f"BackgroundProcessManager: Warning! Process '{name}' exited with code {process.returncode} immediately after starting.")
                print(f"Error output: {process.stderr.read().decode() if process.stderr else 'No error output available.'}")
            else:
                print(f"BackgroundProcessManager: Process '{name}' started successfully. PID: {process.pid}")
            return process
        except FileNotFoundError:
            print(f"BackgroundProcessManager: Error starting process '{name}'. Command not found: {command.split()[0]}")
        except Exception as e:
            print(f"BackgroundProcessManager: Error starting process '{name}' with command '{command}': {e}")
        return None

    def kill_process(self, name: str, verbose: bool = True) -> None:
        """
        Kills a managed background process by its name.

        Args:
            name: The name of the process to kill.
            verbose: Whether to print detailed messages.
        """
        process = self._processes.get(name)
        if not process:
            if verbose:
                print(f"BackgroundProcessManager: Process '{name}' not found in registered processes.")
            return

        if process.poll() is None:  # None means process is still running
            if verbose:
                print(f"BackgroundProcessManager: Attempting to terminate '{name}' (PID: {process.pid})...")
            try:
                if os.name == 'nt':
                    # Use check_call to ensure it doesn't fail silently if taskkill isn't found
                    # Redirect output of taskkill as it can be verbose
                    subprocess.check_call(
                        ['taskkill', '/F', '/T', '/PID', str(process.pid)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                else: # POSIX
                    pgid = os.getpgid(process.pid)
                    os.killpg(pgid, signal.SIGTERM) # Send SIGTERM to the entire process group
                    try:
                        process.wait(timeout=5) # Wait for the main process
                        if verbose:
                            print(f"BackgroundProcessManager: Process group for '{name}' (PGID: {pgid}) terminated gracefully (SIGTERM).")
                    except subprocess.TimeoutExpired:
                        if verbose:
                            print(f"BackgroundProcessManager: '{name}' (PGID: {pgid}) did not terminate with SIGTERM after 5s. Sending SIGKILL.")
                        os.killpg(pgid, signal.SIGKILL) # Force kill
                        if verbose:
                            print(f"BackgroundProcessManager: Process group for '{name}' (PGID: {pgid}) killed (SIGKILL).")
                if verbose:
                    print(f"BackgroundProcessManager: Successfully initiated termination for '{name}'.")
            except ProcessLookupError: # Process already died
                if verbose:
                    print(f"BackgroundProcessManager: Process '{name}' (PID: {process.pid}) was not found during termination. Already exited.")
            except FileNotFoundError: # e.g. taskkill not found on a misconfigured system
                 if verbose:
                    print(f"BackgroundProcessManager: Error terminating '{name}'. 'taskkill' command not found (Windows).")
            except Exception as e:
                if verbose:
                    print(f"BackgroundProcessManager: Error terminating '{name}': {e}")
        else:
            if verbose:
                print(f"BackgroundProcessManager: Process '{name}' (PID: {process.pid}) was registered but already exited before explicit kill.")

        # Remove from dictionary regardless of how it was terminated or if already dead
        if name in self._processes:
            del self._processes[name]

    @classmethod
    def _cleanup_all_processes_on_exit(cls) -> None:
        """
        Class method called by atexit to clean up all registered processes.
        """
        if not cls._processes:
            return # Nothing to clean up

        # Standard check for running in IPython/Jupyter to provide context
        if cls._is_running_in_jupyter():
            print("BackgroundProcessManager: Kernel/script exiting. Cleaning up all registered background processes...")
        else:
            print("BackgroundProcessManager: Script exiting. Cleaning up all registered background processes...")

        # Create a list of names to avoid issues with modifying dict during iteration
        for name in list(cls._processes.keys()):
            # Need an instance to call the instance method kill_process
            # However, since kill_process modifies cls._processes, we can adapt its logic here
            # or ensure we have an instance. The singleton pattern means _instance should be set.
            if cls._instance:
                cls._instance.kill_process(name, verbose=False) # Less verbose during atexit
            else:
                # Fallback if no instance was explicitly created but atexit is called (should not happen with __new__)
                # This is a simplified version for direct cleanup if _instance is somehow None
                process_obj = cls._processes.get(name)
                if process_obj and process_obj.poll() is None:
                    print(f"BackgroundProcessManager (atexit): Terminating '{name}' (PID: {process_obj.pid})...")
                    try:
                        if os.name == 'nt':
                            subprocess.check_call(['taskkill', '/F', '/T', '/PID', str(process_obj.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        else:
                            pgid = os.getpgid(process_obj.pid)
                            os.killpg(pgid, signal.SIGTERM)
                            time.sleep(0.2) # Brief pause for SIGTERM
                            try: # Check if still alive
                                os.killpg(pgid, 0) # Raises ProcessLookupError if dead
                                os.killpg(pgid, signal.SIGKILL)
                            except ProcessLookupError:
                                pass # Gracefully terminated
                            except Exception:
                                pass # Error sending SIGKILL, not much more to do
                    except Exception as e_atexit:
                        print(f"BackgroundProcessManager (atexit): Error terminating '{name}': {e_atexit}")
        cls._processes.clear()
        if cls._is_running_in_jupyter():
            print("BackgroundProcessManager: Automated cleanup complete.")

    def find_processes_by_port(self, port: int) -> list[tuple[int, str]]:
        """
        Find processes using a specific port.
        
        Args:
            port: The port number to search for.
            
        Returns:
            List of tuples containing (pid, command_name)
        """
        processes = []
        
        try:
            if os.name == 'nt':  # Windows
                # Use netstat to find processes using the port
                cmd = ['netstat', '-ano']
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    lines = result.stdout.splitlines()
                    for line in lines:
                        if f':{port}' in line and 'LISTENING' in line:
                            parts = line.split()
                            if len(parts) >= 5:
                                pid_str = parts[-1]
                                try:
                                    pid = int(pid_str)
                                    # Get process name using tasklist
                                    tasklist_result = subprocess.run(
                                        ['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV', '/NH'],
                                        capture_output=True, text=True
                                    )
                                    if tasklist_result.returncode == 0:
                                        lines = tasklist_result.stdout.strip().split('\n')
                                        if lines and lines[0]:
                                            # Parse CSV output
                                            import csv
                                            from io import StringIO
                                            reader = csv.reader(StringIO(lines[0]))
                                            row = next(reader)
                                            process_name = row[0] if row else f"PID:{pid}"
                                            processes.append((pid, process_name))
                                except (ValueError, IndexError):
                                    continue
            else:  # Linux/Unix
                # Use lsof to find processes using the port
                cmd = ['lsof', '-t', f'-i:{port}', '-sTCP:LISTEN']
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    pids = result.stdout.strip().split('\n')
                    for pid_str in pids:
                        try:
                            pid = int(pid_str)
                            # Get process name using ps
                            ps_result = subprocess.run(
                                ['ps', '-p', str(pid), '-o', 'comm='],
                                capture_output=True, text=True
                            )
                            if ps_result.returncode == 0:
                                process_name = ps_result.stdout.strip()
                                processes.append((pid, process_name))
                        except (ValueError, FileNotFoundError):
                            continue
                            
        except Exception as e:
            print(f"BackgroundProcessManager: Error finding processes on port {port}: {e}")
            
        return processes

    def kill_process_by_port(self, port: int, verbose: bool = True) -> bool:
        """
        Kill all processes using a specific port.
        
        Args:
            port: The port number.
            verbose: Whether to print detailed messages.
            
        Returns:
            True if any processes were killed, False otherwise.
        """
        processes = self.find_processes_by_port(port)
        
        if not processes:
            if verbose:
                print(f"BackgroundProcessManager: No processes found using port {port}")
            return False
        
        killed_any = False
        
        for pid, process_name in processes:
            if verbose:
                print(f"BackgroundProcessManager: Killing {process_name} (PID: {pid}) using port {port}")
            
            try:
                if os.name == 'nt':  # Windows
                    # Use taskkill for Windows
                    result = subprocess.run(
                        ['taskkill', '/F', '/PID', str(pid)],
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        if verbose:
                            print(f"BackgroundProcessManager: Successfully killed {process_name} (PID: {pid})")
                        killed_any = True
                    else:
                        if verbose:
                            print(f"BackgroundProcessManager: Failed to kill {process_name} (PID: {pid}): {result.stderr}")
                else:  # Linux/Unix
                    # Try SIGTERM first, then SIGKILL if needed
                    try:
                        os.kill(pid, signal.SIGTERM)
                        time.sleep(0.5)  # Give process time to terminate gracefully
                        
                        # Check if process still exists
                        try:
                            os.kill(pid, 0)  # Doesn't actually kill, just checks if process exists
                            # Process still exists, use SIGKILL
                            os.kill(pid, signal.SIGKILL)
                            if verbose:
                                print(f"BackgroundProcessManager: Force killed {process_name} (PID: {pid}) with SIGKILL")
                        except ProcessLookupError:
                            # Process already terminated with SIGTERM
                            if verbose:
                                print(f"BackgroundProcessManager: Successfully killed {process_name} (PID: {pid}) with SIGTERM")
                        killed_any = True
                    except ProcessLookupError:
                        if verbose:
                            print(f"BackgroundProcessManager: Process {process_name} (PID: {pid}) was already terminated")
                    except PermissionError:
                        if verbose:
                            print(f"BackgroundProcessManager: Permission denied to kill {process_name} (PID: {pid})")
                            
            except Exception as e:
                if verbose:
                    print(f"BackgroundProcessManager: Error killing {process_name} (PID: {pid}): {e}")
        
        return killed_any

    def clear_port(self, port: int, verbose: bool = True) -> bool:
        """
        Convenience method to clear a port by killing any processes using it.
        
        Args:
            port: The port number to clear.
            verbose: Whether to print detailed messages.
            
        Returns:
            True if any processes were killed, False otherwise.
        """
        if verbose:
            print(f"BackgroundProcessManager: Clearing port {port}...")
        
        result = self.kill_process_by_port(port, verbose)
        
        if result and verbose:
            print(f"BackgroundProcessManager: Port {port} cleared.")
        elif verbose:
            print(f"BackgroundProcessManager: Port {port} was already clear.")
        
        return result


# --- Global instance for easy access ---
# This ensures the BackgroundProcessManager is instantiated when the module is imported,
# which in turn ensures the atexit handler is registered.
_process_manager_singleton = BackgroundProcessManager()

def start_background_process(name: str, command: str) -> subprocess.Popen | None:
    """Convenience function to start a background process."""
    return _process_manager_singleton.start_process(name, command)

def kill_background_process(name: str) -> None:
    """Convenience function to kill a background process."""
    _process_manager_singleton.kill_process(name)

def kill_all_background_processes() -> None:
    """Convenience function to manually kill all registered background processes."""
    print("BackgroundProcessManager: Manually killing all registered processes...")
    # Iterate using a copy of keys as kill_process modifies the dictionary
    for name in list(BackgroundProcessManager._processes.keys()):
        _process_manager_singleton.kill_process(name)
    print("BackgroundProcessManager: Manual cleanup attempt complete.")

def kill_process_by_port(port: int, verbose: bool = True) -> bool:
    """Convenience function to kill processes using a specific port."""
    return _process_manager_singleton.kill_process_by_port(port, verbose)

def clear_port(port: int, verbose: bool = True) -> bool:
    """Convenience function to clear a port by killing any processes using it."""
    return _process_manager_singleton.clear_port(port, verbose)

def find_processes_by_port(port: int) -> list[tuple[int, str]]:
    """Convenience function to find processes using a specific port."""
    return _process_manager_singleton.find_processes_by_port(port)
