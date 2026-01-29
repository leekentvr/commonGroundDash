import subprocess
import os

class ProcessManager:
    def __init__(self, log_callback, get_roomname_callback):
        self.log = log_callback
        self.get_roomname = get_roomname_callback
        self.processes = []   # store running processes

    def run_exe(self, exe_path, add_room, identifier):
        if not os.path.exists(exe_path):
            self.log(f"[ERROR] exe file not found: {exe_path}")
            return
        
        try:
            if(add_room):
                roomname = self.get_roomname()  # <-- dynamic reload
                self.proc = subprocess.Popen(
                    [exe_path, f"--roomname={roomname}"],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                self.proc = subprocess.Popen(
                    [exe_path],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )

            if(identifier != "se"):
                self.processes.append({
                    "proc": self.proc,
                    "id": identifier
                })

            self.log(f"[INFO] Started {identifier} (PID={self.proc.pid})")
        except Exception as e:
            self.log(f"[ERROR] Failed to run exe: {e}")

    def stop_exe_by_id(self, identifier):
        for entry in self.processes:
            if entry["id"] == identifier:
                if(identifier == "SVR"): # SteamVR is special case
                    self.stop_steamvr()
                proc = entry["proc"]
                if proc.poll() is None:
                    proc.terminate()
                    self.log(f"[INFO] Terminated {identifier}")
                self.processes.remove(entry)
                return

        self.log(f"[WARN] No process found with id '{identifier}'")

    def toggle(self, exe_path, add_room, identifier):
        if self.is_running(identifier):
            self.stop_exe_by_id(identifier)
            return False   # now stopped
        else:
            self.run_exe(exe_path, add_room, identifier)
            return True    # now running
        
    def is_running(self, identifier):
        for entry in self.processes:
            if entry["id"] == identifier and entry["proc"].poll() is None:
                return True
        return False
    
    def stop_steamvr(self):
        processes = [
            "vrserver.exe",
            "vrcompositor.exe",
            "vrdashboard.exe",
            "vrmonitor.exe"
        ]
        for p in processes:
            subprocess.call(["taskkill", "/F", "/IM", p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


