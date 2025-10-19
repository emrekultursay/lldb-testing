import argparse
import os
import subprocess
import time


# --- HELPER FUNCTIONS ---


def log(message):
  log_file = "/tmp/manager.log"

  """Logs a timestamped message to the console and log file."""
  timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
  # Use the configured log file path from the global CONFIG

  log_entry = f"[{timestamp}] {message}"
  print(log_entry)
  # Ensure the directory exists before writing the log
  os.makedirs(os.path.dirname(log_file), exist_ok=True)
  with open(log_file, 'a') as f:
    f.write(log_entry + '\n')


def get_online_devices():
  """Returns a list of serial IDs for all currently online ADB devices."""
  try:
    result = subprocess.run(
      ['adb', 'devices'],
      capture_output=True,
      text=True,
      check=True
    )

    devices = []
    for line in result.stdout.splitlines():
      if line.strip() and line != "List of devices attached":
        parts = line.split()
        if len(parts) == 2 and parts[1] == 'device':
          devices.append(parts[0])
    return devices
  except FileNotFoundError:
    log("ERROR: 'adb' command not found. Ensure ADB is in your system PATH.")
    return []
  except Exception as e:
    log(f"ERROR executing adb devices: {e}")
    return []


# --- RUNNER MANAGEMENT ---


def start_runner(serial, args):
  """Registers and starts a GitHub runner for a given device serial."""
  log(f"Device {serial}: STARTING GitHub runner")

  try:
    runner_dir = os.path.join(args.runner_base_dir, serial)

    # 6. Start Runner (runs the process in the background)
    log(f"Device {serial}: Executing run.sh in background...")

    runner_process = subprocess.Popen(
      [os.path.join(runner_dir, 'run.sh')],
      cwd=runner_dir,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL
    )

    log(f"Device {serial}: Runner started with PID {runner_process.pid}.")
    return runner_process

  except subprocess.CalledProcessError as e:
    log(f"Device {serial}: ERROR during configuration/run.sh. Output: {e.stderr.strip()}")
    return None
  except Exception as e:
    log(f"Device {serial}: CRITICAL ERROR during startup: {e}")
    return None


def stop_runner(serial, runner_process):
  """Stops the runner process and removes the runner from GitHub."""
  log(f"Device {serial}: STOPPING GitHub runner (PID {runner_process.pid}).")

  try:
    # Kill the running process
    runner_process.terminate()
    try:
      runner_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
      log(f"Device {serial}: Process not terminated gracefully, forcing kill.")
      runner_process.kill()

    log(f"Device {serial}: Process terminated.")
  except subprocess.CalledProcessError as e:
    log(f"Device {serial}: ERROR during de-registration. Output: {e.stderr.strip()}. Continuing cleanup.")
  except Exception as e:
    log(f"Device {serial}: CRITICAL ERROR during shutdown: {e}")


# --- ARGPARSE SETUP ---

def parse_args():
  parser = argparse.ArgumentParser(
    description="Dynamic GitHub Android Runner Manager.",
    formatter_class=argparse.RawTextHelpFormatter
  )
  parser.add_argument(
    '--github-url',
    default='https://github.com/emrekultursay/lldb-testing',
    help="The GitHub repository or organization URL."
  )
  parser.add_argument(
    '--runner-base-dir',
    default=os.path.expanduser('~/.gh_test_runner/'),
    help="The base directory to store runner files and logs. (Default: /opt/android-runners)"
  )
  parser.add_argument(
    '--poll-interval-seconds',
    type=int,
    default=15,
    help="How often (in seconds) to check for connected devices. (Default: 15)"
  )
  return parser.parse_args()  # Return as a dictionary


# --- MAIN LOOP ---

def main():
  """Main loop to monitor devices and manage runners."""
  args = parse_args()

  log("--- Dynamic Runner Manager Starting ---")
  log(f"GitHub URL: {args.github_url}")
  log(f"Base Dir: {args.runner_base_dir}")
  log(f"Poll Interval: {args.poll_interval_seconds} seconds")

  # Dictionary to track active runners: {serial_id: subprocess_object}
  active_runners = {}

  while True:
    try:
      log("--- Checking ADB devices ---")
      online_serials = get_online_devices()

      # Identify New Devices (Start Runners)
      for serial in online_serials:
        if serial not in active_runners:
          runner = start_runner(serial, args)
          if runner:
            active_runners[serial] = runner

      # Identify Disconnected Devices (Stop Runners)
      serials_to_stop = []
      for serial, process in active_runners.items():
        if serial not in online_serials:
          log(f"Device {serial}: Status changed from active to offline/disconnected.")
          serials_to_stop.append((serial, process))

      for serial, process in serials_to_stop:
        try:
          stop_runner(serial, process)
        finally:
          del active_runners[serial]

      log(f"Active Runners: {list(active_runners.keys())}")

    except Exception as e:
      log(f"An unexpected error occurred in main loop: {e}")

    time.sleep(args.poll_interval_seconds)


if __name__ == "__main__":
  # Ensure standard output/logs are flushed immediately
  os.environ['PYTHONUNBUFFERED'] = '1'
  main()
