import re
import subprocess
from pathlib import Path
import shlex


def parse_bat_variables(bat_path: Path):
    variables = {}

    with bat_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()

        # Skip comments and empty lines
        if not line or line.startswith("rem") or line.startswith("@echo"):
            continue

        # Match: set key=value
        m = re.match(r"set\s+([^=]+)=(.*)", line, re.IGNORECASE)
        if m:
            key = m.group(1).strip()
            value = m.group(2).strip()
            variables[key] = value

    return variables

def extract_final_command(bat_path: Path):
    with bat_path.open("r", encoding="utf-8") as f:
        content = f.read()

    # Join lines ending with ^
    content = content.replace("^\n", " ")

    # Find the line starting with the executable
    for line in content.splitlines():
        if "room_client_owner.exe" in line:
            return line.strip()

    raise RuntimeError("Could not find executable command in .bat file")

def expand_variables(command: str, variables: dict):
    # Replace %var% with actual values
    for key, value in variables.items():
        command = command.replace(f"%{key}%", value)
    return command


def get_bat_params(bat_path: str):
    bat_path = Path(bat_path)

    vars_dict = parse_bat_variables(bat_path)
    raw_cmd = extract_final_command(bat_path)
    expanded = expand_variables(raw_cmd, vars_dict)

    # Normalize whitespace
    expanded = " ".join(expanded.split())

    # Split into tokens
    parts = shlex.split(expanded)

    # Return ONLY the parameters
    return parts[1:]


