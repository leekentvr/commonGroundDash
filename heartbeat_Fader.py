from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QTimer, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget, QLabel, QHBoxLayout

class HeartbeatIcon(QWidget):
    """
    Reusable fading-heartbeat animation system.
    Drop anywhere into UI
    """

    def __init__(self, zenoh, key, on_icon, off_icon):
        super().__init__()

        self.label = QLabel()
        self.label.setFixedSize(32, 64)
        self.on_icon = on_icon
        self.off_icon = off_icon

        self.label.setPixmap(QPixmap(off_icon).scaled(32, 64))

        layout = QHBoxLayout(self)
        layout.addWidget(self.label)

        self.fader = HeartbeatFader(self.label)
        self.fader.set_on_missed(self.on_missed)

        zenoh.route(key, self.on_heartbeat)

    def on_heartbeat(self, payload):
        self.label.setPixmap(QPixmap(self.on_icon).scaled(32, 64))
        self.fader.start_heartbeat()

    def on_missed(self):
        self.label.setPixmap(QPixmap(self.off_icon).scaled(32, 64))
        self.fader.effect.setOpacity(1.0)


class HeartbeatFader:
    """
    Reusable fading-heartbeat animation system.
    Attach to ANY widget (QLabel, QPushButton icon, etc.)
    """

    def __init__(self, target_widget, fade_duration=2000, min_opacity=0.3):
        self.target = target_widget

        # Opacity effect
        self.effect = QGraphicsOpacityEffect(self.target)
        self.target.setGraphicsEffect(self.effect)

        # Fade animation
        self.fade_anim = QPropertyAnimation(self.effect, b"opacity")
        self.fade_anim.setDuration(fade_duration)
        self.fade_anim.setStartValue(1.0)
        self.fade_anim.setEndValue(min_opacity)
        self.fade_anim.setEasingCurve(QEasingCurve.Linear)

        # Heartbeat timeout timer
        self.heartbeat_timer = QTimer()
        self.heartbeat_timer.setInterval(fade_duration)
        self.heartbeat_timer.timeout.connect(self._on_timeout)

        # Callback for missed heartbeat
        self.on_missed_callback = None

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def start_heartbeat(self):
        """Call this whenever a heartbeat is received."""
        self.effect.setOpacity(1.0)
        self.fade_anim.stop()
        self.fade_anim.start()
        self.fade_anim.setCurrentTime(0) 
        
        self.heartbeat_timer.stop()
        self.heartbeat_timer.start()

    def stop(self):
        """Stop animation + reset opacity."""
        self.fade_anim.stop()
        self.heartbeat_timer.stop()
        self.effect.setOpacity(1.0)

    def set_on_missed(self, callback):
        """Register a callback for missed heartbeat."""
        self.on_missed_callback = callback

    # ---------------------------------------------------------
    # Internal
    # ---------------------------------------------------------

    def _on_timeout(self):
        if self.on_missed_callback:
            self.on_missed_callback()