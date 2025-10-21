# SwiftF0 Documentation

Welcome to the SwiftF0 documentation. SwiftF0 is a fast and accurate fundamental frequency (F0) detector with advanced music processing capabilities.

## 📚 Documentation Overview

### Getting Started
- [README](../README.md) - Project overview and quick start guide
- [Installation Guide](guides/installation.md) - Detailed installation instructions
- [Quick Start Tutorial](guides/quick_start.md) - Your first pitch detection

### User Guides
- [Basic Usage](guides/basic_usage.md) - Core functionality guide
- [Advanced Features](guides/advanced_features.md) - Timbre transformation and auto-tuning
- [API Reference](api/reference.md) - Complete API documentation

### Technical Documentation
- [Architecture Overview](technical/architecture.md) - System design and algorithms
- [Project Structure](project_structure.md) - Repository organization
- [Edge Deployment Analysis](technical/edge_deployment_analysis.md) - Hardware deployment options
- [Hardware Comparison](technical/hardware_comparison.md) - Platform selection guide

### Development
- [Migration Guide](guides/migration_guide.md) - Upgrading between versions
- [Changelog](changelog.md) - Version history and release notes
- [Contributing](guides/contributing.md) - How to contribute to the project

### Research & Reports
- [AI Kazoo Roadmap](research/ai_kazoo_roadmap.md) - Hardware project phases
- [Streaming Research Brief](research/v1.0streaming_research_brief.md) - Real-time processing research
- [Embedded Interface Report](research/embedded_interface_technical_report.md) - Hardware interface analysis
- [Project Summary](research/project_summary.md) - Executive summary and Q&A

## 🎯 Quick Links by Use Case

### For Musicians
- Start with the [Quick Start Tutorial](guides/quick_start.md)
- Learn about [Timbre Transformation](guides/advanced_features.md#timbre-transformation)
- Explore [Auto-Tuning](guides/advanced_features.md#auto-tuning)

### For Developers
- Read the [Architecture Overview](technical/architecture.md)
- Check the [API Reference](api/reference.md)
- Review [Code Examples](../demos/README.md)

### For Hardware Engineers
- Study the [Edge Deployment Analysis](technical/edge_deployment_analysis.md)
- Compare platforms in [Hardware Comparison](technical/hardware_comparison.md)
- Follow the [AI Kazoo Roadmap](research/ai_kazoo_roadmap.md)

### For Product Managers
- Review the [Project Summary](research/project_summary.md)
- Track progress in [AI Kazoo Roadmap](research/ai_kazoo_roadmap.md)
- Check the [Changelog](changelog.md) for releases

## 📦 Library Features

### Core Capabilities
- **Pitch Detection**: CNN-based F0 detection (46.875 - 2093.75 Hz)
- **Note Segmentation**: Convert continuous pitch to discrete notes
- **MIDI Export**: Standard MIDI file generation

### Advanced Features
- **128 GM Instruments**: Full General MIDI instrument support
- **Auto-Tuning**: Automatic pitch correction with key detection
- **Transposition**: Pitch shifting by semitones
- **Kazoo Optimization**: Special mode for kazoo-like instruments
- **Batch Processing**: Generate multiple versions efficiently

## 🚀 Performance

- **Latency**: ~150ms for 5-second audio
- **Accuracy**: ±10 cents pitch precision
- **Memory**: 350MB typical usage
- **Model Size**: 389KB ONNX model

## 📋 Requirements

- Python 3.8+
- onnxruntime >= 1.12.0
- numpy >= 1.21.0
- Optional: librosa, mido, matplotlib

## 🛠️ Installation

```bash
# Basic installation
pip install swift-f0

# Full installation with all features
pip install swift-f0[full]
```

## 📖 Navigation Guide

Use the sidebar to navigate through documentation sections, or use these entry points:

1. **New Users**: Start with [README](../README.md) → [Quick Start](guides/quick_start.md) → [Basic Usage](guides/basic_usage.md)
2. **Developers**: [Architecture](technical/architecture.md) → [API Reference](api/reference.md) → [Examples](../demos/README.md)
3. **Researchers**: [Technical Reports](research/) → [Architecture](technical/architecture.md)

## 📬 Support

- GitHub Issues: [Report bugs or request features](https://github.com/your-org/swift-f0/issues)
- Discussions: [Ask questions and share ideas](https://github.com/your-org/swift-f0/discussions)

---

*Last updated: October 2024 | Version 0.1.2*