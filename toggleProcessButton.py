from PySide6.QtWidgets import QPushButton, QGraphicsOpacityEffect, QLabel
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QTimer, QSize


class ToggleProcessButton(QPushButton):
    def __init__(self, label_start, label_stop, manager, exe_path, add_room, identifier, onIcon, offIcon, heartbeat_key):
        super().__init__(label_start)

        self.label_start = label_start
        self.label_stop = label_stop
        self.manager = manager
        self.exe_path = exe_path
        self.add_room = add_room
        self.identifier = identifier
        self.onIcon = onIcon
        self.offIcon = offIcon
        self.heartbeat_key = heartbeat_key or None

        self.icon_label = QLabel(self)
        self.icon_label.setFixedSize(32, 32)
        self.icon_label.move(15, 10)  # adjust position as needed
        self.setIconSize(QSize(32, 32))
        self.setFixedHeight(52)

        self.set_icon(self.offIcon)
        self.running = False
        self.pending = False

        if self.heartbeat_key:
            self._init_heartbeat_system()

        self.clicked.connect(self.on_click)


    # ---------------------------------------------------------
    # Heartbeat fade system
    # ---------------------------------------------------------
    def _init_heartbeat_system(self):
        self.effect = QGraphicsOpacityEffect(self.icon_label)
        self.icon_label.setGraphicsEffect(self.effect)

        self.fade_anim = QPropertyAnimation(self.effect, b"opacity")
        self.fade_anim.setDuration(2000)
        self.fade_anim.setStartValue(1.0)
        self.fade_anim.setEndValue(0.3)
        self.fade_anim.setEasingCurve(QEasingCurve.Linear)

        self.heartbeat_timer = QTimer()
        self.heartbeat_timer.setInterval(2000)
        self.heartbeat_timer.timeout.connect(self.on_missed_heartbeat)

    def set_icon(self, filename):
        if not filename:
            self.icon_label.clear()
            return

        pix = QPixmap("assets/" + filename).scaled(32, 32)
        self.icon_label.setPixmap(pix)

    # ---------------------------------------------------------
    # User click → toggle process
    # ---------------------------------------------------------
    def on_click(self):
        started = self.manager.toggle(
            self.exe_path,
            self.add_room,
            self.identifier
        )

        if started:
            # Process launched, but not confirmed
            self.pending = True
            self.setText("Starting…")
            self.set_icon(self.offIcon)

            # verify process didn't instantly die
            QTimer.singleShot(800, self.verify_process_alive)

        else:
            # User stopped it
            self.pending = False
            self.reset_ui()


    def verify_process_alive(self):
        if self.pending and not self.manager.is_running(self.identifier):
            # It died before sending heartbeat
            self.pending = False
            self.reset_ui()

    # ---------------------------------------------------------
    # Force stop (used by user stop + heartbeat failure)
    # ---------------------------------------------------------
    def force_stop(self):
        self.manager.stop_exe_by_id(self.identifier)
        self.reset_ui()

    def reset_ui(self):
        self.pending = False
        self.setText(self.label_start)
        self.set_icon(self.offIcon)

        if self.has_heartbeat():
            self.effect.setOpacity(1.0)
            self.fade_anim.stop()
            self.heartbeat_timer.stop()




    # ---------------------------------------------------------
    # Heartbeat handling
    # ---------------------------------------------------------

    def on_heartbeat(self, payload=None):
        if not self.has_heartbeat():
            return

        # First heartbeat
        if self.pending:
            self.pending = False
            self.setText(self.label_stop)
            self.set_icon(self.onIcon)

        # Now we are in RUNNING state → start fade
        self.effect.setOpacity(1.0)
        self.fade_anim.stop()
        self.fade_anim.start()
        self.heartbeat_timer.stop()
        self.heartbeat_timer.start()


    def on_missed_heartbeat(self):
        if not self.has_heartbeat():
            return

        if not self.pending:
            self.force_stop()


    def has_heartbeat(self):
        return self.heartbeat_key is not None and self.effect is not None

