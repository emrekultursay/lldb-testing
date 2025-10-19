"""
Scans all adb-connected Android devices, and creates a self-hosted GitHub runner for each one, registering it
to GitHub Actions for the selected GitHub project.

When to run this script?
- Whenever you connect a new Android device to any of your self-hosted GitHub actions runner machines, run this script
to register a runner for it. This way, you will have a per-Android-device test runner.

Usage Instructions:

1. Decide which GitHub repository you are registering the self-hosted runner for and get the URL. For instance:
  https://github.com/emrekultursay/lldb-testing

2. Go to the "Settings > Actions > Runners > New self-hosted runner" page and copy the token from the CLI command. This
token is short-lived. You cannot store it long-term to re-use it in automation.

3. Pass that token as the `--runner-token` argument when invoking this script. E.g.,

  python3 gh_setup_runners.py \
    --githhub-url=https://github.com/emrekultursay/lldb-testing
    --runner-token=AEB6KDH32PJEABMD7JGIGFTI6U3W4
"""
import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import time
import urllib
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path


def log(message):
  """Logs a timestamped message to the console and log file."""
  timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
  log_entry = f"[{timestamp}] {message}"
  print(log_entry)


def download_and_extract_tar_gz(url: str,
                                target_dir: str | Path) -> bool:
  """
  Downloads and extracts a .tar.gz file from a URL into a target directory.

  Args:
      url: The download URL for the .tar.gz file.
      target_dir: The directory to download the file to and extract its contents.

  Returns:
      True on success, False on failure.
  """
  try:
    # --- Setup Paths ---

    # Ensure target_dir is a Path object for easier handling
    target_dir = Path(target_dir)

    # Ensure the target directory exists
    target_dir.mkdir(parents=True, exist_ok=True)

    # Get filename from URL (e.g., "file.tar.gz")
    url_path = urllib.parse.urlparse(url).path
    filename = Path(url_path).name

    # Create the full path to save the archive (e.g., "target_dir/file.tar.gz")
    save_path = target_dir / filename

    # --- Download Step ---
    print(f"Saving to:   {save_path}")
    urllib.request.urlretrieve(url, save_path)
    print("Download complete.")

    # --- Extract Step ---
    print(f"\nExtracting {save_path}...")

    # Open the .tar.gz file for reading ('r') with gzip ('gz') compression
    with tarfile.open(save_path, 'r:gz') as tar:
      tar.extractall(path=target_dir)

    print(f"Successfully extracted contents to {target_dir}")
    print("\nProcess complete.")
    return True

  except urllib.error.URLError as e:
    print(f"\nDownload Error: {e}", file=sys.stderr)
  except tarfile.TarError as e:
    print(f"\nExtraction Error: {e}", file=sys.stderr)
  except Exception as e:
    print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)

  return False


def setup_runner(serial, args, runner_template_dir):
  log(f"Device {serial}: CONFIGURING GitHub runner")
  runner_dir = Path(args.runner_base_dir) / serial

  if not os.path.exists(runner_dir):
    log(f'Copying template to runner {runner_dir}')
    shutil.copytree(runner_template_dir, runner_dir)

  config_marker_file = runner_dir / '.runner'
  if config_marker_file.exists():
    print(f"Runner in is already configured. Skipping config.")
    return runner_dir

  # Gather all required dynamic info
  device_info = get_device_info(serial)
  abi_labels_string = get_device_abi_labels(serial)

  # Structure the Name for the GitHub UI
  # TODO: Find a way to register ARM32 devices, which is not the primary ABI.
  primary_abi = abi_labels_string.split(',')[0] if abi_labels_string else 'unknownabi'

  runner_name = (
    f"ANDROID"
    f"-{device_info['model']}"
    f"-SDK{device_info['sdk']}"
    f"-{serial}"
  ).replace('__', '_')

  # Define Labels (for job pooling/targeting)
  # TODO(emrekultursay): Add label "tester"
  labels = f"self-hosted,Android-{primary_abi}"

  log(f"Device {serial}: Running config.sh...")
  config_cmd = [
    os.path.join(runner_dir, 'config.sh'),
    '--url', args.github_url,
    '--token', args.runner_token,
    '--name', runner_name,
    '--labels', labels,
    '--unattended',
    '--replace'
  ]
  # Run config.sh and check for errors
  subprocess.run(config_cmd, check=True, cwd=runner_dir, capture_output=True, text=True)
  log(f"Device {serial}: Configuration successful.")

  log(f"Device {serial}: New Runner Name: {runner_name}")
  log(f"Device {serial}: Labels: {labels}")

  return runner_dir


def remove_runner(serial, runner_base_dir, runner_token):
  log(f"Device {serial}: Removing runner from GitHub...")
  runner_dir = Path(runner_base_dir) / serial
  remove_cmd = [
    os.path.join(runner_dir, 'config.sh'),
    'remove',
    '--token', runner_token
  ]
  subprocess.run(remove_cmd, check=True, cwd=runner_dir, capture_output=True, text=True)
  log(f"Device {serial}: Unregistration successful.")

  # 3. Clean up the runner directory
  shutil.rmtree(runner_dir)
  log(f"Device {serial}: Cleaned up directory {runner_dir}.")


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


def get_device_info(serial):
  """Retrieves device model and SDK version for structured naming."""
  info = {}
  props = {
    'model': 'ro.product.model',
    'sdk': 'ro.build.version.sdk'
  }

  for key, prop in props.items():
    try:
      cmd = ['adb', '-s', serial, 'shell', 'getprop', prop]
      result = subprocess.run(cmd, capture_output=True, text=True, check=True)
      info[key] = result.stdout.strip().replace(' ', '_').replace('-', '')
    except Exception as e:
      log(f"Device {serial}: WARNING: Could not retrieve {prop}. {e}")
      info[key] = "unknown"

  return info


def get_device_abi_labels(serial):
  """Retrieves the supported ABIs for a device and formats them as a label string."""
  try:
    abi_cmd = ['adb', '-s', serial, 'shell', 'getprop', 'ro.product.cpu.abilist']
    result = subprocess.run(abi_cmd, capture_output=True, text=True, check=True)

    abi_list_str = result.stdout.strip()

    if not abi_list_str:
      return "generic-android-abi"

    abi_labels = [abi.strip() for abi in abi_list_str.split(',') if abi.strip()]
    return ",".join(abi_labels)

  except Exception as e:
    log(f"Device {serial}: UNEXPECTED ERROR during ABI check: {e}. Using fallback label.")
    return "abi-detection-failed"


def parse_args():
  """Parses command-line arguments."""
  parser = argparse.ArgumentParser(
    description="Dynamic GitHub Android Runner Registration/Configuration Tool.",
    formatter_class=argparse.RawTextHelpFormatter
  )

  parser.add_argument(
    '--github-url',
    # NOT REQUIRED anymore. Given a placeholder default.
    default='https://github.com/emrekultursay/lldb-testing',
    help="The GitHub repository or organization URL."
  )
  parser.add_argument(
    '--runner-token',
    required=True,
    help="The runner registration token obtained from GitHub."
  )
  parser.add_argument(
    '--runner-base-dir',
    default=os.path.expanduser('~/.gh_test_runner/'),
    help="The base directory to store runner files and logs. (Default: /opt/android-runners)"
  )

  return parser.parse_args()  # Return as a dictionary


def main():
  """Main method to register/unregister GitHub runners for Android devices."""
  args = parse_args()

  log("--- Checking ADB devices ---")
  online_serials = get_online_devices()

  # Ensure base directory exists for template and runner instances.
  os.makedirs(args.runner_base_dir, exist_ok=True)

  log("--- Checking runner template dir ---")
  runner_template_dir = Path(args.runner_base_dir) / "template"
  if not os.path.exists(runner_template_dir):
    download_and_extract_tar_gz(
      url='https://github.com/actions/runner/releases/download/v2.329.0/actions-runner-linux-x64-2.329.0.tar.gz',
      target_dir=runner_template_dir)

  log("--- Registering new runners ---")
  for serial in online_serials:
    setup_runner(serial, args, runner_template_dir)

  log("--- Unregistering offline/obsolete runners ---")
  obsolete_runner_dirs = [runner_dir for runner_dir in Path(args.runner_base_dir).iterdir() if
                          runner_dir.name not in online_serials and (runner_dir / '.runner').exists()]
  for runner_dir in obsolete_runner_dirs:
    remove_runner(runner_dir.name, args.runner_base_dir, args.runner_token)


if __name__ == "__main__":
  # Ensure standard output/logs are flushed immediately
  os.environ['PYTHONUNBUFFERED'] = '1'
  main()
