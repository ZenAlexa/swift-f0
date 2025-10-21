"""
USB Audio module - 从 ESP32 接收音频数据

这个模块来自 xiaozhi-esp32 项目，用于通过 USB Serial 接收音频流。
"""

from .receiver import AudioFrameReceiver

__all__ = ['AudioFrameReceiver']