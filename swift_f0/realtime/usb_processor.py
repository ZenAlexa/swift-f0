"""
USB 音频实时处理器

集成 USB 音频接收、音高检测和音色合成。
数据流：ESP32 麦克风 -> USB Serial -> 音高检测 -> 音色变换 -> 音频输出
"""

import numpy as np
import time
from typing import Optional
from dataclasses import dataclass

from swift_f0.core import SwiftF0
from swift_f0.usb_audio import AudioFrameReceiver


@dataclass
class USBProcessorConfig:
    """USB 处理器配置"""
    # 串口设置
    serial_port: str = '/dev/tty.usbmodem1101'  # 修正为正确的默认设备
    baudrate: int = 2000000

    # 音频参数
    input_sample_rate: int = 24000  # ESP32 采样率
    process_sample_rate: int = 16000  # SwiftF0 需要 16kHz

    # 音高检测
    window_size: int = 1024
    confidence_threshold: float = 0.8

    # 合成参数
    synthesis_amplitude: float = 0.3

    # 调试
    debug: bool = False


class USBProcessor:
    """USB 音频处理器 - 核心处理类"""

    def __init__(self, config: USBProcessorConfig):
        self.config = config

        # USB 音频接收器
        self.receiver = AudioFrameReceiver(
            port=config.serial_port,
            baudrate=config.baudrate,
            sample_rate=config.input_sample_rate
        )

        # 音高检测器
        self.pitch_detector = SwiftF0(
            confidence_threshold=config.confidence_threshold
        )

        # 音频缓冲区
        self.window_buffer = np.zeros(config.window_size, dtype=np.float32)

        # 合成状态
        self.synthesis_phase = 0.0
        self.current_freq = 0.0
        self.current_amp = 0.0
        self.target_freq = 0.0
        self.target_amp = 0.0

        # 平滑参数
        self.freq_smooth = 0.9
        self.amp_smooth = 0.95

        # 统计
        self.frames_processed = 0
        self.total_latency = 0.0

    def open(self) -> bool:
        """打开串口连接"""
        success = self.receiver.open()
        if success and self.config.debug:
            print(f"串口已打开: {self.config.serial_port}")
        return success

    def close(self):
        """关闭串口连接"""
        self.receiver.close()
        if self.config.debug:
            print("串口已关闭")

    def resample(self, audio: np.ndarray, from_rate: int, to_rate: int) -> np.ndarray:
        """简单重采样（线性插值）"""
        if from_rate == to_rate:
            return audio

        ratio = to_rate / from_rate
        new_length = int(len(audio) * ratio)

        # 使用线性插值
        x_old = np.arange(len(audio))
        x_new = np.linspace(0, len(audio) - 1, new_length)

        return np.interp(x_new, x_old, audio)

    def process_frame(self, audio_frame: np.ndarray) -> Optional[np.ndarray]:
        """
        处理单个音频帧

        Args:
            audio_frame: 来自 ESP32 的音频数据 (int16)

        Returns:
            处理后的输出音频 (float32)，或 None
        """
        start_time = time.perf_counter()

        # 转换为 float32
        audio_float = audio_frame.astype(np.float32) / 32768.0

        # 重采样到 16kHz (如果需要)
        if self.config.input_sample_rate != self.config.process_sample_rate:
            audio_float = self.resample(
                audio_float,
                self.config.input_sample_rate,
                self.config.process_sample_rate
            )

        # 更新窗口缓冲区
        chunk_size = min(len(audio_float), self.config.window_size)
        self.window_buffer = np.roll(self.window_buffer, -chunk_size)
        self.window_buffer[-chunk_size:] = audio_float[:chunk_size]

        # 检测音高
        try:
            result = self.pitch_detector.detect_from_array(
                self.window_buffer,
                sample_rate=self.config.process_sample_rate
            )

            # 提取音高
            if len(result.pitch_hz) > 0 and result.voicing[-1]:
                self.target_freq = result.pitch_hz[-1]
                self.target_amp = self.config.synthesis_amplitude * result.confidence[-1]
            else:
                self.target_amp = 0.0

        except Exception as e:
            if self.config.debug:
                print(f"音高检测错误: {e}")
            self.target_amp = 0.0

        # 平滑过渡
        self.current_freq = self.freq_smooth * self.current_freq + (1 - self.freq_smooth) * self.target_freq
        self.current_amp = self.amp_smooth * self.current_amp + (1 - self.amp_smooth) * self.target_amp

        # 生成输出音频（正弦波合成）
        output_length = len(audio_frame)

        if self.current_freq > 50 and self.current_amp > 0.01:
            # 生成正弦波
            phase_increment = 2 * np.pi * self.current_freq / self.config.input_sample_rate
            phases = self.synthesis_phase + np.arange(output_length) * phase_increment
            output = self.current_amp * np.sin(phases)

            # 更新相位
            self.synthesis_phase = (self.synthesis_phase + output_length * phase_increment) % (2 * np.pi)
        else:
            # 静音
            output = np.zeros(output_length)

        # 更新统计
        self.frames_processed += 1
        latency = (time.perf_counter() - start_time) * 1000  # ms
        self.total_latency += latency

        return output.astype(np.float32)

    def get_stats(self) -> dict:
        """获取统计信息"""
        receiver_stats = self.receiver.get_stats()

        avg_latency = 0
        if self.frames_processed > 0:
            avg_latency = self.total_latency / self.frames_processed

        return {
            'frames_processed': self.frames_processed,
            'frames_received': receiver_stats['frames_received'],
            'frames_dropped': receiver_stats['frames_dropped'],
            'avg_latency_ms': avg_latency,
            'current_freq': self.current_freq,
            'current_amp': self.current_amp
        }


class RealtimeUSBPlayer:
    """实时 USB 音频播放器"""

    def __init__(self, config: USBProcessorConfig):
        self.processor = USBProcessor(config)
        self.config = config

        # 尝试使用 sounddevice (更好的跨平台支持)
        try:
            import sounddevice as sd
            self.use_sounddevice = True
            self.sd = sd
        except ImportError:
            self.use_sounddevice = False

            # 回退到 pyaudio
            try:
                import pyaudio
                self.pyaudio = pyaudio
                self.p = pyaudio.PyAudio()
                self.stream = None
            except ImportError:
                raise RuntimeError("需要安装 sounddevice 或 pyaudio 用于音频输出")

    def start(self):
        """启动播放器"""
        # 打开串口
        if not self.processor.open():
            raise RuntimeError(f"无法打开串口 {self.config.serial_port}")

        # 初始化音频输出
        if self.use_sounddevice:
            self.stream = self.sd.OutputStream(
                samplerate=self.config.input_sample_rate,
                channels=1,
                dtype='float32',
                blocksize=256,
                latency='low'
            )
            self.stream.start()
        else:
            self.stream = self.p.open(
                format=self.pyaudio.paFloat32,
                channels=1,
                rate=self.config.input_sample_rate,
                output=True,
                frames_per_buffer=256
            )

        print(f"实时播放器已启动")
        print(f"串口: {self.config.serial_port}")
        print(f"采样率: {self.config.input_sample_rate} Hz")

    def run(self):
        """运行主循环"""
        print("\n等待音频数据... 按 Ctrl+C 停止\n")

        # 添加调试计数器
        check_counter = 0
        no_data_counter = 0

        try:
            while True:
                # 接收音频帧
                frame = self.processor.receiver.receive_frame()

                # 调试输出
                check_counter += 1
                if check_counter % 1000 == 0:
                    stats = self.processor.get_stats()
                    print(f"\r检查: {check_counter} | 无数据: {no_data_counter} | "
                          f"接收: {stats['frames_received']} | "
                          f"处理: {stats['frames_processed']}    ",
                          end='', flush=True)

                if frame is not None:
                    # 处理音频
                    output = self.processor.process_frame(frame)

                    if output is not None and len(output) > 0:
                        # 播放输出
                        if self.use_sounddevice:
                            # sounddevice 需要 numpy 数组
                            if self.stream is not None:
                                self.stream.write(output.reshape(-1, 1))
                        else:
                            # pyaudio 需要 bytes
                            if self.stream is not None:
                                self.stream.write(output.tobytes())

                    # 显示状态
                    if self.processor.frames_processed % 50 == 0:
                        stats = self.processor.get_stats()

                        # 显示音高信息
                        if stats['current_freq'] > 50:
                            midi = int(round(69 + 12 * np.log2(stats['current_freq'] / 440)))
                            note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
                            note = note_names[midi % 12]
                            octave = (midi // 12) - 1

                            print(f"\r音高: {stats['current_freq']:6.1f} Hz | "
                                  f"音符: {note}{octave} | "
                                  f"帧: {stats['frames_processed']} | "
                                  f"丢失: {stats['frames_dropped']} | "
                                  f"延迟: {stats['avg_latency_ms']:.1f} ms    ",
                                  end='', flush=True)
                        else:
                            print(f"\r等待音频... | "
                                  f"帧: {stats['frames_processed']} | "
                                  f"丢失: {stats['frames_dropped']}    ",
                                  end='', flush=True)
                else:
                    no_data_counter += 1

                # 短暂休眠
                time.sleep(0.0001)

        except KeyboardInterrupt:
            print("\n\n停止...")

    def stop(self):
        """停止播放器"""
        # 关闭音频流
        if self.use_sounddevice:
            if self.stream is not None:
                self.stream.stop()  # sounddevice OutputStream has stop()
                self.stream.close()
        else:
            if self.stream is not None:
                self.stream.stop_stream()
                self.stream.close()
            if hasattr(self, 'p'):
                self.p.terminate()

        # 关闭串口
        self.processor.close()

        # 显示统计
        stats = self.processor.get_stats()
        print(f"\n统计信息:")
        print(f"  处理帧数: {stats['frames_processed']}")
        print(f"  接收帧数: {stats['frames_received']}")
        print(f"  丢失帧数: {stats['frames_dropped']}")
        print(f"  平均延迟: {stats['avg_latency_ms']:.2f} ms")