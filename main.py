# main.py
import sys
import json
import os
from pathlib import Path

from PySide6.QtWidgets import ( # type: ignore
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QListWidget, QLabel, QComboBox, 
    QGroupBox
)
from PySide6.QtCore import QFileSystemWatcher, Signal, QPropertyAnimation, QTimer
from PySide6.QtGui import QPixmap, QIcon
from toggleProcessButton import ToggleProcessButton
from zenoh_manager import ZenohManager
from process_manager import ProcessManager
from heartbeat_Fader import HeartbeatIcon




class Dashboard(QWidget):
    roomname = "null"
    room_changed = Signal(str)
    number_of_devices = 0
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Common Ground Dashboard")
        self.resize(500, 400)

        self.setWindowIcon(QIcon("assets/logologomini.png"))
        self.stylesheet = self.load_stylesheet("style.qss")
        self.setStyleSheet(self.stylesheet)

        self.commonground_path = r"C:\\CommonGround\\"
        
        # -----------------------------
        # Signals and Watchers
        # -----------------------------
        self.config_watcher = QFileSystemWatcher([self.commonground_path + r"cgconfig.cfg"])
        self.config_watcher.fileChanged.connect(self.on_config_changed)
        self.room_changed.connect(self.update_room_status)

        self.roomname = self.getRoomName()

        self.processManager = ProcessManager(
            log_callback=lambda msg: self.list_widget.addItem(msg),
            get_roomname_callback=self.getRoomName
        )

        self.zenoh = ZenohManager()
        self.zenoh.message_received.connect(self.on_message)

        main_layout = QVBoxLayout()

        # -----------------------------
        # region 1. Configuration Group
        # -----------------------------
        config_group = QGroupBox("Configuration and Calibration")
        config_layout_v = QVBoxLayout()

        self.open_config_btn = QPushButton("Open Config File")
        self.open_config_btn.setMinimumSize(0,52)
        self.open_config_btn.clicked.connect(self.open_config_file)

        config_layout_hTOP = QHBoxLayout()
        self.svr_btn = ToggleProcessButton(
            label_start="Start SteamVR",
            label_stop="Stop SteamVR",
            manager=self.processManager,
            exe_path=self.commonground_path + r"1. SteamVR\SteamVR\bin\win64\\vrstartup.exe",
            add_room=False,
            identifier="SVR",
            onIcon=None,
            offIcon=None,
            heartbeat_key=""
        )

        self.calib_btn = ToggleProcessButton(
            label_start="Start Calibration App",
            label_stop="Stop Calibration App",
            manager=self.processManager,
            exe_path=self.commonground_path + r"1. TrackerApp\Builds\\CameraCalibration.exe",
            add_room=False,
            identifier="CA", 
            onIcon=None,
            offIcon=None,
            heartbeat_key=""
        )
    
        config_layout_v.addWidget(self.open_config_btn)
        config_layout_hTOP.addWidget(self.svr_btn)
        config_layout_hTOP.addWidget(self.calib_btn)
        config_layout_v.addLayout(config_layout_hTOP)
        
   
        config_group.setLayout(config_layout_v)
        main_layout.addWidget(config_group)
        # -----------------------------
        # region 1.5. Current Configuration Group
        # -----------------------------

        current_group = QGroupBox("Current Configuration")

        self.room_icon_label = QLabel()
        self.room_icon_label.setFixedSize(32, 32) 

        self.room_status_label = QLabel("Checking...")
        self.room_status_label.setStyleSheet("font-weight: bold;")

        config_layout_h = QHBoxLayout()
        config_layout_h.addStretch()
        config_layout_h.addWidget(QLabel("Current room '" + self.roomname + "'   "))
        config_layout_h.addWidget(self.room_icon_label)
        config_layout_h.addWidget(self.room_status_label)
        config_layout_h.addStretch()

        current_group.setLayout(config_layout_h)
        main_layout.addWidget(current_group)

        # endregion

        # -----------------------------
        # region 2. Device Processor Group
        # -----------------------------
        device_group = QGroupBox("Device Processor")
        device_layout = QVBoxLayout()

        self.dp_btn = ToggleProcessButton(
            label_start="Start Device Processor",
            label_stop="Stop Device Processor",
            manager=self.processManager,
            exe_path=self.commonground_path + r"2. DeviceProcessing\\HelloKinect.exe",
            add_room=True,
            identifier="DP", 
            onIcon="greenHeart.png",
            offIcon="redStop.png",
            heartbeat_key="cg/" + self.roomname + "/dp/hb"
        )

        self.zenoh.route(self.dp_btn.heartbeat_key, self.dp_btn.on_heartbeat)

        device_layout.addWidget(self.dp_btn)
        device_group.setLayout(device_layout)
        main_layout.addWidget(device_group)
        # endregion

        # -----------------------------
        # region 3. Unity App Group
        # -----------------------------
        unity_group = QGroupBox("Unity Commonground App")
        unity_layout = QVBoxLayout()
        
        self.ua_btn = ToggleProcessButton(
            label_start="Start Unity Commonground App",
            label_stop="Stop Unity Commonground App",
            manager=self.processManager,
            exe_path=self.commonground_path + r"3. CommonGroundSF\CommonGroundSF.exe", 
            add_room=False,
            identifier="ua", 
            onIcon="greenHeart.png",
            offIcon="redStop.png",
            heartbeat_key="cg/" + self.roomname + "/cg/hb"
        )

        self.zenoh.route(self.ua_btn.heartbeat_key, self.ua_btn.on_heartbeat)

        unity_layout.addWidget(self.ua_btn)
        unity_group.setLayout(unity_layout)
        main_layout.addWidget(unity_group)
        # endregion

        # -----------------------------
        # region 4. Middleware Processor Group
        # -----------------------------
        middleware_group = QGroupBox("Middleware Processor")
        middleware_layout = QHBoxLayout()

        middle_exe_path = os.path.join(
            self.commonground_path,
            "5. RoomClient Middleware",
            "start_avatar_manager.bat"
        )

        self.mp_btn = ToggleProcessButton(
            label_start="Start Middleware Processor",
            label_stop="Stop Middleware Processor",
            manager=self.processManager,
            exe_path=middle_exe_path,
            add_room=False,
            identifier="mw", 
            onIcon="greenHeart.png",
            offIcon="redStop.png",
            heartbeat_key="cg/" + self.roomname + "/mw/mw/hb"
        )
        self.zenoh.route(self.mp_btn.heartbeat_key, self.mp_btn.on_heartbeat)

        self.cg_hb_icon = HeartbeatIcon(self.zenoh, "cg/" + self.roomname + "/mw/cg/hb", "assets/" + "greenHeartBottom.png", "assets/" + "redStopBottom.png")
        self.cg_hb_icon.setFixedSize(64, 74)

        self.server_hb_icon = HeartbeatIcon(self.zenoh, "cg/" + self.roomname + "/mw/se/hb", "assets/" + "greenHeartTop.png", "assets/" + "redStopTop.png")
        self.server_hb_icon.setFixedSize(64, 74)

        middleware_layout.addWidget(self.mp_btn)
        middleware_layout.addWidget(self.cg_hb_icon)
        middleware_layout.addWidget(self.server_hb_icon)

        middleware_group.setLayout(middleware_layout)
        main_layout.addWidget(middleware_group)
        #endregion
        
        # -----------------------------
        # region 5. Server Group
        # -----------------------------
        server_group = QGroupBox("Server")
        server_layout = QHBoxLayout()

        # TODO: trigger server heartbeat from start

        self.start_server_btn = QPushButton("Start Server")
        self.start_server_btn.clicked.connect(lambda: self.processManager.run_exe(
            exe_path=os.path.join(
                self.commonground_path,
                "4. ServerStartStop",
                "start-ec2.bat"
            ),
            add_room=False,
            identifier="se"
        ))

        self.stop_server_btn = QPushButton("Stop Server")
        self.stop_server_btn.clicked.connect(lambda: self.processManager.run_exe(
            exe_path=os.path.join(
                self.commonground_path,
                "4. ServerStartStop",
                "stop-ec2.bat"
            ),
            add_room=False,
            identifier="se"
        ))

        server_layout.addWidget(self.start_server_btn)
        server_layout.addWidget(self.stop_server_btn)

        server_group.setLayout(server_layout)
        main_layout.addWidget(server_group)
        #endregion

        # -----------------------------
        # region 6. Publisher Group
        # -----------------------------
        pub_group = QGroupBox("Publisher")
        pub_layout = QHBoxLayout()

        self.key_selector = QComboBox()
        self.key_selector.addItems([
            "cg/OneCam/hb",
            "module/logs/debug"
        ])

        self.input = QLineEdit()
        self.input.setPlaceholderText("Type a message")

        send_btn = QPushButton("Publish")
        send_btn.clicked.connect(self.publish)

        pub_layout.addWidget(self.input)
        pub_layout.addWidget(send_btn)
        pub_layout.addWidget(QLabel("Select Key:"))
        pub_layout.addWidget(self.key_selector)
        pub_group.setLayout(pub_layout)
        # main_layout.addWidget(pub_group)
        # endregion

        # -----------------------------
        # region 7. Zenoh Debugging Group
        # -----------------------------
        self.log_group = QGroupBox("Received Messages")
        log_layout = QVBoxLayout()

        self.list_widget = QListWidget()
        self.list_widget.addItem(f"[SYSTEM] Room Name: {self.roomname}")

        log_layout.addWidget(self.list_widget)
        self.log_group.setLayout(log_layout)
        #main_layout.addWidget(self.log_group)    

        self.set_groupbox_visible(self.log_group, False)
        # endregion

        # -----------------------------
        # Final Layout
        # -----------------------------
        self.setLayout(main_layout)

        # Subscribe to all keys
        for key in [self.key_selector.itemText(i) for i in range(self.key_selector.count())]:
            self.zenoh.subscribe(key)
        self.room_changed.emit(self.roomname)

    def load_stylesheet(self,path):
        with open(path, "r") as f:
            return f.read()

    def on_message(self, key, payload):
        self.list_widget.addItem(f"[{key}] {payload}")


    def publish(self):
        key = self.key_selector.currentText()
        msg = self.input.text().strip()
        if msg:
            self.zenoh.publish(key, msg)
            self.input.clear()

    def getRoomName(self):
        try:
            with open(self.commonground_path + r"cgconfig.cfg") as f:
                cfg = json.load(f)
            return cfg.get("roomID", "null")
        except (OSError, json.JSONDecodeError):
            return "null"
        
    def getAreaManagerID(self):
        try:
            with open(self.commonground_path + r"cgconfig.cfg") as f:
                cfg = json.load(f)
            return cfg.get("areaManagerID", "null")
        except (OSError, json.JSONDecodeError):
            return "null"

    def on_config_changed(self, path):
        new_room = self.getRoomName()
        self.roomname = new_room
        self.list_widget.addItem(f"[SYSTEM] Config changed. New roomname: {new_room}")
        self.room_changed.emit(new_room)
        # QFileSystemWatcher stops watching if the file is replaced; re-add path defensively.
        if path not in self.config_watcher.files():
            self.config_watcher.addPath(path)

    def get_room_file_info(self, roomname: str):
        filepath = os.path.join(self.commonground_path, "CalibrationFiles", f"{roomname}.txt")
        if not os.path.exists(filepath):
            return False, 0, filepath
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                # Found a room in the config
                line_count = sum(1 for line in f if line.strip()) - 1  # and subtract header
                path = Path(self.commonground_path) / "5. RoomClient Middleware" / "start_avatar_manager.bat"
                self.update_bat_file(path, roomname=self.getRoomName(), areaManagerID=self.getAreaManagerID())

        except Exception:
            return False, 0, filepath
        return True, line_count, filepath
    
    def update_bat_file(self, path, roomname, areaManagerID):
        with open(path, "r") as f:
            lines = f.readlines()
        new_lines = []
        for line in lines:
            if line.strip().startswith("set zenoh_key_expr="):
                new_lines.append(f"set zenoh_key_expr={roomname}\n")
            elif line.strip().startswith("set area_manager_id="):
                new_lines.append(f"set area_manager_id={areaManagerID}\n")
            else:
                new_lines.append(line)

        with open(path, "w") as f:
            f.writelines(new_lines)

    def open_config_file(self):
        config_path = Path(self.commonground_path) / "cgconfig.cfg"
        if config_path.exists():
            import webbrowser
            webbrowser.open(str(config_path))
        else:
            self.list_widget.addItem(f"[ERROR] Config file not found: {config_path}")

    def animate_status_change(self, widget):
        anim = QPropertyAnimation(widget, b"windowOpacity")
        anim.setDuration(1000)
        anim.setStartValue(0.3)
        anim.setEndValue(1.0)
        anim.start()
        # Keep a reference so it doesn't get garbage collected
        self._last_anim = anim

    def set_groupbox_visible(self, groupbox, visible):
        for child in groupbox.findChildren(QWidget):
            child.setVisible(visible)


    def update_room_status(self, roomname: str):
        exists, line_count, filepath = self.get_room_file_info(self.getRoomName())

        if exists: # Room is good, update other config files
            self.room_icon_label.setPixmap(QPixmap("assets/greenHeart.png"))
            self.room_status_label.setText(f"   {line_count} devices in room file.")
            self.room_status_label.setStyleSheet("color: Limegreen;")
        else:
            self.room_icon_label.setPixmap(QPixmap("assets/redStop.png"))
            self.room_status_label.setText("   No room file found.")
            self.room_status_label.setStyleSheet("color: red;")

        self.animate_status_change(self.room_status_label)

def closeEvent(self, event):
    # Stop timers
    for timer in self.findChildren(QTimer):
        timer.stop()

    QApplication.quit()

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("assets/logomini.png"))
    ui = Dashboard()
    ui.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()