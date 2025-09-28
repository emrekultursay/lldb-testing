import lldb
import subprocess
import sys
import time

def run_debugging_session(serial, package):
    """
    Runs a debugging session using the LLDB Python API.

    Args:
        serial: The serial of the Android device to connect to.
    """
    # 1. Create a new debugger instance.
    debugger = lldb.SBDebugger.Create()
    if not debugger:
        print("Error: Failed to create SBDebugger.")
        return

    # 2. Tell the debugger to be in synchronous mode.
    # This means commands will block until they are finished.
    debugger.SetAsync(False)

    # 3. Select and set the platform to 'remote-android'.
    # This is required for debugging on an Android device.
    platform = lldb.SBPlatform('remote-android')
    if not platform:
        print("Error: Failed to create 'remote-android' platform.")
        return

    debugger.SetSelectedPlatform(platform)
    print("Platform set to 'remote-android'.")

    # 4. Connect to the remote platform using the ConnectRemote API.
    # This establishes the connection to the remote debug server.
    platform_connect_options = lldb.SBPlatformConnectOptions(
        f"unix-abstract-connect://[{serial}]/{package}-0/platform-156393867851.sock")
    print(f"Connecting to URL: {platform_connect_options.GetURL()}")

    connect_error = platform.ConnectRemote(platform_connect_options)
    if connect_error.Fail():
        print(f"Error: Failed to connect to remote platform: {connect_error.GetCString()}")
        return
    #ebugger.HandleCommand(f"platform connect {platform_connect_options.GetURL()}")
    print("Connected to remote platform successfully.")

    error = lldb.SBError()
    processes = platform.GetAllProcesses(error)
    if error.Fail():
      print(f"Error")
      return
    pid = 0
    for i in range(0, processes.GetSize()):
      info = lldb.SBProcessInfo()
      if processes.GetProcessInfoAtIndex(i, info) and info.GetName() == "app_process64":
          pid = info.GetProcessID()
      else:
        print("Not match, process: " + info.GetName())
    if pid == 0:
      print("cannot find pid")
      return
    print("pid = " + str(pid))


    # . Attach to the process by its PID.
    error = lldb.SBError()
    target = debugger.CreateTarget('.')
    attach_info = lldb.SBAttachInfo()
    attach_info.SetProcessID(pid)
    process = platform.Attach(attach_info, debugger, target, error)

    if not process or error.Fail():
        print(f"Error: Failed to attach to process with PID {pid}: {error.GetCString()}")
        return

    print(f"Attached to process with PID {process.GetProcessID()}.")

    time.sleep(10)

    # 7. We will now enter the debugger's command loop to allow for interactive debugging.
    # This is a common practice when attaching to a long-running process.
    #debugger.SetInputFile(sys.stdin)
    #debugger.SetOutputFile(sys.stdout)
    #debugger.SetErrorFile(sys.stderr)
    #debugger.HandleCommand("process continue")
    for i in range(1, 10):
      if process.is_stopped:
        break
      else:
        print("Process is not stopped")
        time.sleep(1)


    print("Getting stack backtrace")
    debugger.HandleCommand("bt")

    # The script will now wait for the user to quit the LLDB session.
    print("Exiting.")

def get_serial():
  cmd = [
      "adb",
      "devices",
  ]
  result = subprocess.run(cmd, check=True, capture_output=True)
  out = result.stdout.decode('utf-8')
  devices = list(filter(str.strip, out.splitlines()[1:]))
  print(f'Devices found: {str(devices)}')
  if len(devices) == 0:
    print('No devices found!')
    exit(1)

  found = False
  for device in devices:
    parts = device.split()
    if len(parts) != 2:
      print(f'Failed to parse device line: "{device}", skipping device.')
      continue

    serial, state = parts[0], parts[1]
    if state != 'device':
      continue
    found = True
    break

  if not found:
    print('No online devices found')
    exit(1)

  print(f'Using device serial = {serial}')
  return serial


def get_pid():
  return 1234


def install_apk():
  print('Installing APK: [not implemented]...')
  pass


def run_as(serial, package, cmd):
  new_cmd = [
      "adb",
      "-s",
      serial,
      "shell",
      "run-as",
      package
  ] + cmd
  print("Launching command: " + str(cmd))
  return subprocess.Popen(new_cmd)

def launch_lldb_server(serial, package):
  print('Launching lldb-server on device...')
  cmd = [
      f"/data/data/{package}/lldb/bin/start_lldb_server.sh",
      f"/data/data/{package}/lldb",
      "unix-abstract",
      f"/{package}-0",
      "platform-156393867851.sock",
      "\"lldb process:gdb-remote packets\""
  ]
  process = run_as(serial, package, cmd)
  time.sleep(1)
  return process

def launch_app(serial, package, activity):
  print('Stopping and re-launching app...')
  cmd = [
      "adb",
      "-s",
      serial,
      "shell",
      "am",
      "force-stop",
      package
  ]
  subprocess.run(cmd, check=True)
  cmd = [
      "adb",
      "-s",
      serial,
      "shell",
      "am",
      "start",
      activity,
      "-a",
      "android.intent.action.MAIN",
      "-c",
      "android.intent.category.LAUNCHER"
  ]
  subprocess.run(cmd, check=True)

def push_file(serial, local_path, remote_path):
  cmd = [
      "adb",
      "-s",
      serial,
      "push",
      local_path,
      remote_path
  ]
  subprocess.run(cmd, check=True)


def push_lldb_server(serial, package):
  print('Pushing lldb-server to device...')
  push_file(
      serial,
      "build-arm64-v8a/out/bin/lldb-server",
      "/data/local/tmp/")
  push_file(
      serial,
      "start_lldb_server.sh",
      "/data/local/tmp/")

  for subcmd in [
      "mkdir -p lldb/bin",
      "cp /data/local/tmp/lldb-server lldb/bin",
      "cp /data/local/tmp/start_lldb_server.sh lldb/bin/",
      "chmod +x lldb/bin/lldb-server",
      "chmod +x lldb/bin/start_lldb_server.sh",
  ]:
    return_code = run_as(serial, package, [subcmd]).wait()
    assert return_code == 0


def kill_lldb_server(serial, package):
  run_as(serial, package, ["pkill", "-9", "lldb-server"]).wait()

if __name__ == '__main__':
  serial = get_serial()
  #package = "com.example.myapplication"
  package = "com.example.hellojni"
  activity = f"{package}/{package}.MainActivity"
  install_apk()
  launch_app(serial, package, activity)
  kill_lldb_server(serial, package)
  push_lldb_server(serial, package)
  process = launch_lldb_server(serial, package)
  try:
    print("This is where the debug session will start")
    #run_debugging_session(serial, package)
    time.sleep(1000)
  finally:
    print("Killing all lldb-server processes on device")
    kill_lldb_server(serial, package)
