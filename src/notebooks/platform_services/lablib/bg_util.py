#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Defines a singleton class for managing background processes in Python within a Jupyter kernel.

This class ensures that background processes are cleaned up when the kernel exits.
It provides methods to start, kill, and manage background processes.
The class is designed to be used in a Jupyter notebook or similar environment,
where the kernel may be restarted or interrupted.
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
    _processes = {}  # Stores name: Popen_object
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
                shell=True, # Exercise caution if command is from untrusted input
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
