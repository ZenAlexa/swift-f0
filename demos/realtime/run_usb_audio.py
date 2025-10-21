#!/usr/bin/env python3
"""
运行 USB 音频实时处理

从 ESP32 接收音频 -> 音高检测 -> 音色合成 -> 扬声器输出
"""

import sys
import os
import argparse

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from swift_f0.realtime.usb_processor import USBProcessorConfig, RealtimeUSBPlayer


def list_serial_ports():
    """列出可用的串口设备"""
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()

        print("\n可用的串口设备:")
        print("-" * 40)

        port_list = []
        for port in ports:
            print(f"  {port.device}")
            print(f"    描述: {port.description}")
            port_list.append(port.device)

        if not ports:
            print("  未找到串口设备")

        print("-" * 40)
        return port_list

    except ImportError:
        print("需要安装 pyserial: pip install pyserial")
        return []


def main():
    parser = argparse.ArgumentParser(
        description='USB 音频实时处理 - ESP32 麦克风输入 + SwiftF0 音高检测 + 音色合成'
    )

    parser.add_argument(
        '--port', '-p',
        type=str,
        help='串口设备 (例如: /dev/tty.usbmodem1101 或 COM3)'
    )
    parser.add_argument(
        '--baudrate',
        type=int,
        default=2000000,
        help='波特率 (默认: 2000000)'
    )
    parser.add_argument(
        '--rate', '-r',
        type=int,
        default=24000,
        help='音频采样率 (默认: 24000)'
    )
    parser.add_argument(
        '--list-ports',
        action='store_true',
        help='列出可用串口'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='显示调试信息'
    )

    args = parser.parse_args()

    # 列出串口
    if args.list_ports:
        list_serial_ports()
        return 0

    # 自动检测串口
    if not args.port:
        ports = list_serial_ports()

        # 查找可能的设备
        for port in ports:
            if 'usb' in port.lower() or 'serial' in port.lower():
                args.port = port
                print(f"\n自动选择串口: {args.port}")
                break

        if not args.port:
            print("\n错误: 未指定串口，也未能自动检测")
            print("请使用 --port 参数指定串口")
            return 1

    # 创建配置
    config = USBProcessorConfig(
        serial_port=args.port,
        baudrate=args.baudrate,
        input_sample_rate=args.rate,
        debug=args.debug
    )

    # 创建播放器
    try:
        player = RealtimeUSBPlayer(config)

        print("\n" + "="*60)
        print("SwiftF0 USB 音频实时处理")
        print("="*60)
        print("数据流: ESP32 麦克风 -> USB -> 音高检测 -> 音色合成 -> 扬声器")
        print("="*60)

        # 启动
        player.start()

        # 运行主循环
        player.run()

    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\n错误: {e}")
        return 1
    finally:
        if 'player' in locals():
            player.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())