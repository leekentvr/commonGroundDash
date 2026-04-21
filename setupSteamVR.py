import json
import os
from os import path
import subprocess
import shutil
import stat

# Where merged frozen versions are stored
FROZEN_DIR = r"C:\CommonGround\1.1 SteamVR"

# Where SteamVR actually runs from
RUNTIME_DIR = r"C:\Program Files (x86)\Steam\steamapps\common\SteamVR"

# -----------------------------
# HELPERS
# -----------------------------

def run(cmd):
    print("Running:", cmd)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"SteamCMD failed ({result.returncode})")
    return result


def remove_path(path):
    if os.path.exists(path):
        print("Deleting:", path)
        if os.path.isfile(path):
            os.remove(path)
        else:
            shutil.rmtree(path, ignore_errors=True)


def make_readonly(path):
    for root, dirs, files in os.walk(path):
        for f in files:
            os.chmod(os.path.join(root, f), stat.S_IREAD)


def make_writable(path):
    for root, dirs, files in os.walk(path):
        for f in files:
            os.chmod(os.path.join(root, f), stat.S_IWRITE)


# -----------------------------
# CLEANUP
# -----------------------------

def clean_steamvr_traces():
    """Remove all SteamVR traces so the frozen version works cleanly."""
    paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\openvr"),
        os.path.expandvars(r"%APPDATA%\Steam\config\steamvr.vrsettings"),
        os.path.expandvars(r"%APPDATA%\Steam\steamapps\common\SteamVR"),
        os.path.join(RUNTIME_DIR, "..", "config", "steamvr.vrsettings"),
        RUNTIME_DIR
    ]

    for p in paths:
        remove_path(p)

# -----------------------------
# NULL DRIVER CONFIG
# -----------------------------
def apply_null_driver_config(runtime_dir):
    # -----------------------------
    # 1. Patch user override config
    # -----------------------------
    cfg_dir = os.path.join(runtime_dir, "config")
    os.makedirs(cfg_dir, exist_ok=True)

    make_writable(runtime_dir)

    user_cfg_path = os.path.join(cfg_dir, "steamvr.vrsettings")

    user_cfg = {
        "steamvr": {
            "forcedDriver": "null",
            "activateMultipleDrivers": True,
            "requireHmd": False,
            "forcedHmd": "null",
            "enableHomeApp": False
        }
    }

    with open(user_cfg_path, "w") as f:
        json.dump(user_cfg, f, indent=2)

    # -----------------------------
    # 2. Patch null driver default
    # -----------------------------
    null_cfg_path = os.path.join(
        runtime_dir,
        "drivers",
        "null",
        "resources",
        "settings",
        "default.vrsettings"
    )

    null_cfg = {
        "driver_null": {
        "enable": True,
        "loadPriority": -999,
        "serialNumber": "Null Serial Number",
        "modelNumber": "Null Model Number",
        "windowX": 0,
        "windowY": 0,
        "windowWidth": 216,
        "windowHeight": 120,
        "renderWidth": 151,
        "renderHeight": 168,
        "secondsFromVsyncToPhotons": 0.01111111,
        "displayFrequency": 90.0
    }
    }

    with open(null_cfg_path, "w") as f:
        json.dump(null_cfg, f, indent=2)

    # -----------------------------
    # 3. Patch global SteamVR defaults
    # -----------------------------
    global_cfg_path = os.path.join(
        runtime_dir,
        "resources",
        "settings",
        "default.vrsettings"
    )

    if os.path.exists(global_cfg_path):
        with open(global_cfg_path, "r") as f:
            global_cfg = json.load(f)
    else:
        global_cfg = {}

    if "steamvr" not in global_cfg:
        global_cfg["steamvr"] = {}

    global_cfg["steamvr"]["forcedDriver"] = "null"
    global_cfg["steamvr"]["requireHmd"] = False
    global_cfg["steamvr"]["activateMultipleDrivers"] = True

    with open(global_cfg_path, "w") as f:
        json.dump(global_cfg, f, indent=2)


# -----------------------------
# INSTALL / DEPLOY
# -----------------------------

def install_frozen_version():
    remove_path(RUNTIME_DIR)
    runtime_src = path.join(FROZEN_DIR, "runtime")
    content_src = path.join(FROZEN_DIR, "contents")

    if not path.isdir(runtime_src):
        raise RuntimeError(f"Missing runtime folder: {runtime_src}")
    if not path.isdir(content_src):
        raise RuntimeError(f"Missing contents folder: {content_src}")

    # Copy base runtime tree first
    shutil.copytree(runtime_src, RUNTIME_DIR, dirs_exist_ok=True)

    # Merge contents tree into runtime tree
    shutil.copytree(content_src, RUNTIME_DIR, dirs_exist_ok=True)

    print("Frozen SteamVR deployed to runtime:", RUNTIME_DIR)

# -----------------------------
# PUBLIC FUNCTIONS
# -----------------------------

def setup_steamvr():
    print("=== Cleaning old SteamVR traces ===")
    clean_steamvr_traces()

    print("=== Installing frozen SteamVR version ===")
    install_frozen_version()

    print("=== Applying null driver configuration ===")
    apply_null_driver_config(RUNTIME_DIR)

    print("=== Locking runtime ===")
    make_readonly(RUNTIME_DIR)

    print("Setup complete. SteamVR is frozen and null-driver enabled.")

def unfreeze():
    print("=== Unlocking SteamVR runtime ===")
    make_writable(RUNTIME_DIR)
    print("Runtime unlocked. SteamVR will update normally on next launch.")

def get_steamvr_version(runtime_dir):
    candidates = [
        os.path.join(runtime_dir, "bin", "version.txt"),
        os.path.join(runtime_dir, "SteamVR", "bin", "version.txt"),
        os.path.join(runtime_dir, "steamapps", "common", "SteamVR", "bin", "version.txt"),
    ]

    for version_file in candidates:
        if os.path.exists(version_file):
            with open(version_file, "r", encoding="utf-8", errors="ignore") as f:
                line = f.readline().strip()
                return line if line else None
    return None


def is_null_driver_enabled(runtime_dir):
    cfg_path = os.path.join(runtime_dir, "config", "steamvr.vrsettings")
    if not os.path.exists(cfg_path):
        return False

    try:
        with open(cfg_path, "r") as f:
            cfg = json.load(f)
        if cfg.get("steamvr", {}).get("forcedDriver", "") != "null":
            return False
    except Exception:
        return False

    null_cfg_path = os.path.join(
        runtime_dir,
        "drivers",
        "null",
        "resources",
        "settings",
        "default.vrsettings"
    )

    if not os.path.exists(null_cfg_path):
        return False

    try:
        with open(null_cfg_path, "r") as f:
            null_cfg = json.load(f)
        return bool(null_cfg.get("driver_null", {}).get("enable", False))
    except Exception:
        return False


def get_runtime_status(runtime_dir):
    version = get_steamvr_version(runtime_dir)
    null_enabled = is_null_driver_enabled(runtime_dir)
    print({"version": version, "null_driver_enabled": null_enabled})
    #return (version is not "1762827110") and null_enabled
    return (version is not None) and null_enabled
