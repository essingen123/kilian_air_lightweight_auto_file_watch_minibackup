import os
import time
import signal
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

CONFIG_FILE = "autominibackups_file_watch_config.txt"
BACKUP_FOLDER = "autominibackups"
QUIET_MODE = False
BACKGROUND_MODE = False
PID_FILE = "autominibackups_pids.txt"

# Read config file
def read_config():
    global BACKUP_FOLDER, QUIET_MODE, BACKGROUND_MODE
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            f.write("# Enter files to watch (one per line):\n")
            f.write("# Example: ./file.txt\n")
            f.write("# Example: file.txt\n")
            f.write("# Example: ~/Desktop/file1.txt\n")
            f.write("quiet_mode: false\n")
            f.write("background_mode: false\n")
        print(f"Config file created. Please add files to watch in {CONFIG_FILE} and run the script again.")
        sys.exit(0)

    with open(CONFIG_FILE, "r") as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line.startswith("backup_folder:"):
                BACKUP_FOLDER = line.split(":")[1].strip()
            elif line.startswith("quiet_mode:"):
                QUIET_MODE = line.split(":")[1].strip().lower() == "true"
            elif line.startswith("background_mode:"):
                BACKGROUND_MODE = line.split(":")[1].strip().lower() == "true"

# Create backup folder if it doesn't exist
def create_backup_folder():
    if not os.path.exists(BACKUP_FOLDER):
        os.makedirs(BACKUP_FOLDER)

# File watcher class
class FileWatcher(FileSystemEventHandler):
    def __init__(self, file_path, backup_folder, quiet_mode):
        self.file_path = file_path
        self.backup_folder = backup_folder
        self.quiet_mode = quiet_mode

    def on_modified(self, event):
        if event.src_path == self.file_path:
            if not self.quiet_mode:
                print(f"Saving {self.file_path} to {self.backup_folder}")
            timestamp = time.strftime("%y%m%d%H%M%S")
            filename = os.path.basename(self.file_path)
            name, ext = os.path.splitext(filename)
            backup_filename = f"{name}_autominibackup{timestamp}{ext}"
            backup_path = os.path.join(self.backup_folder, backup_filename)
            with open(self.file_path, "rb") as src, open(backup_path, "wb") as dst:
                dst.write(src.read())

# Watch files
def watch_files(file_path):
    observer = Observer()
    event_handler = FileWatcher(file_path, BACKUP_FOLDER, QUIET_MODE)
    observer.schedule(event_handler, path=os.path.dirname(file_path), recursive=False)
    observer.start()
    return observer

# Clean up old PID file if it exists
def cleanup_pid_file():
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)

# Save PID to file
def save_pid(pid):
    with open(PID_FILE, "a") as f:
        f.write(f"{pid}\n")

# Kill all background processes
def kill_background_processes():
    if os.path.exists(PID_FILE):
        with open(PID_FILE, "r") as f:
            pids = f.readlines()
            for pid in pids:
                pid = int(pid.strip())
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
        os.remove(PID_FILE)

# Main function
def main():
    read_config()
    create_backup_folder()
    cleanup_pid_file()

    observers = []
    with open(CONFIG_FILE, "r") as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                file_path = os.path.expanduser(line)  # Expand user-specific paths
                if not os.path.exists(os.path.dirname(file_path)):
                    print(f"Warning: Directory for file '{file_path}' does not exist. Skipping.")
                    continue
                observer = watch_files(file_path)
                observers.append(observer)
                save_pid(os.getpid())  # Save the current process ID

    if BACKGROUND_MODE:
        print(f"Running in background mode. Use 'pkill -F {PID_FILE}' to stop.")
    else:
        print("File watching started. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            kill_background_processes()

if __name__ == "__main__":
    main()
