# 测试指南 - Smart Kazoo v0.4.0 Alpha

> 快速测试不同乐器音色

---

## 🚀 快速开始

### 1. 查找串口
```bash
python demos/realtime/run_usb_audio.py --list-ports
```

### 2. 测试默认音色（长笛）
```bash
python demos/realtime/run_usb_audio.py --port /dev/tty.usbmodem1101 --rate 24000
```

---

## 🎵 音色对比测试

### 长笛 (默认)
```bash
python demos/realtime/run_usb_audio.py --port /dev/tty.usbmodem1101 --rate 24000
```
- **特点**: 明亮、清晰
- **谐波**: 8个
- **适合**: 高音

### 小提琴
```bash
python demos/realtime/run_usb_audio.py --port /dev/tty.usbmodem1101 --rate 24000 --instrument violin
```
- **特点**: 温暖、丰富
- **谐波**: 16个 (1/n衰减)
- **适合**: 全音域

### 单簧管
```bash
python demos/realtime/run_usb_audio.py --port /dev/tty.usbmodem1101 --rate 24000 --instrument clarinet
```
- **特点**: 厚实、圆润
- **谐波**: 12个 (奇数强调)
- **适合**: 中低音

### 纯正弦波
```bash
python demos/realtime/run_usb_audio.py --port /dev/tty.usbmodem1101 --rate 24000 --instrument sine
```
- **特点**: 最简单
- **谐波**: 1个
- **适合**: 测试基准

---

## 📊 检查项

### 性能
- [ ] 延迟 < 100ms
- [ ] 无丢帧
- [ ] CPU < 20%

### 音质
- [ ] 音高准确
- [ ] 无爆音
- [ ] 停止响应快 (<0.2s)

### 稳定性
- [ ] 无自激/啸叫
- [ ] 频率稳定
- [ ] 长时间运行正常

---

## 🐛 常见问题

### 延迟过高
→ 正常范围 80-100ms，固有算法延迟

### 自激/啸叫
→ 降低音量或增加物理距离

### 连接失败
→ 多尝试几次（需要2-3次）

---

## 📝 测试记录

```
日期: ___________
串口: ___________

长笛:   延迟[   ]ms  音质[  ]  自激[  ]
小提琴: 延迟[   ]ms  音质[  ]  自激[  ]
单簧管: 延迟[   ]ms  音质[  ]  自激[  ]

最佳音色: ___________
主要问题: ___________
```

---

**提示**: 用耳机监听可避免声学反馈
