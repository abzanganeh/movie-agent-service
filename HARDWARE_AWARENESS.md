# Hardware Awareness Implementation

This document describes the hardware awareness features added to the Movie Agent Service.

## Overview

The codebase now includes comprehensive hardware detection and configuration options for GPU/CPU usage across all components that can benefit from hardware acceleration.

## Features

### 1. Centralized Hardware Detection (`utils/hardware.py`)

- **HardwareDetector**: Detects available hardware (CUDA, MPS/Apple Silicon, CPU)
- **Device Selection**: Intelligent device selection with fallback logic
- **Hardware Info Logging**: Detailed hardware capability reporting
- **Support for**:
  - NVIDIA CUDA GPUs
  - Apple Silicon MPS (Metal Performance Shaders)
  - CPU fallback

### 2. Configuration Options

New configuration options in `MovieAgentConfig`:

```python
device: Optional[Literal["auto", "cpu", "cuda", "mps"]] = "auto"
force_cpu: bool = False
log_hardware_info: bool = True
faiss_gpu_enabled: bool = False
```

### 3. Environment Variables

You can configure hardware settings via environment variables:

```bash
# Device selection (auto-detect by default)
DEVICE=auto          # Options: auto, cpu, cuda, mps
FORCE_CPU=false      # Force CPU even if GPU available

# FAISS GPU acceleration
FAISS_GPU_ENABLED=false  # Enable GPU for vector operations (requires faiss-gpu)

# Logging
LOG_HARDWARE_INFO=true   # Log hardware info on startup
```

### 4. Component Updates

#### BLIP Vision Tool
- Automatically detects and uses GPU when available
- Respects `device` and `force_cpu` configuration
- Uses `float16` on GPU for memory efficiency, `float32` on CPU
- Falls back gracefully to CPU if GPU unavailable

#### FAISS Vector Store
- Optional GPU acceleration support (requires `faiss-gpu` package)
- Automatically falls back to CPU if GPU unavailable
- Configured via `faiss_gpu_enabled` in config

#### Service Initialization
- Logs hardware information on startup (if `log_hardware_info=True`)
- Reports detected GPUs, device selection, and configuration

## Usage Examples

### Basic Usage (Auto-detect)

```python
from movie_agent import MovieAgentApp, MovieAgentConfig

config = MovieAgentConfig()  # Uses auto-detection
app = MovieAgentApp(config)
app.initialize()
```

### Force CPU Mode

```python
config = MovieAgentConfig(
    device="cpu",
    force_cpu=True  # Explicitly force CPU
)
```

### Enable FAISS GPU

```python
config = MovieAgentConfig(
    faiss_gpu_enabled=True  # Requires faiss-gpu package
)
```

### Manual Device Selection

```python
config = MovieAgentConfig(
    device="cuda"  # Force CUDA (will error if not available unless force_cpu=True)
)
```

## Hardware Detection Output

When `log_hardware_info=True`, you'll see output like:

```
INFO - Hardware Detection Results:
INFO -   Device Type: cuda
INFO -   PyTorch Available: True
INFO -   CUDA Available: True
INFO -   MPS Available: False
INFO -   GPU Available: True
INFO -   GPU Name: NVIDIA GeForce RTX 3080
INFO -   GPU Count: 1
INFO - Device configuration: device=auto, force_cpu=False, faiss_gpu=False
```

## Requirements

### GPU Support

- **CUDA**: Requires PyTorch with CUDA support and compatible NVIDIA GPU
- **MPS**: Requires PyTorch with MPS support (macOS with Apple Silicon)
- **FAISS GPU**: Requires `faiss-gpu` package (separate from `faiss-cpu`)

### Installation

```bash
# For CUDA GPU support
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# For FAISS GPU (optional, only if faiss_gpu_enabled=True)
pip install faiss-gpu

# For CPU-only (default)
pip install torch faiss-cpu
```

## Fallback Behavior

The system gracefully handles missing hardware:

1. If GPU requested but unavailable → Falls back to CPU (unless `force_cpu=False` and explicit device specified)
2. If FAISS GPU enabled but not available → Falls back to CPU FAISS with warning
3. If PyTorch not available → Vision tool will raise error on initialization (expected)

## Benefits

1. **Automatic Optimization**: Automatically uses best available hardware
2. **Flexibility**: Can force CPU mode for testing/debugging
3. **Visibility**: Logs hardware usage for monitoring
4. **Graceful Degradation**: Falls back to CPU if GPU unavailable
5. **Configuration**: Centralized hardware configuration through config/environment

## Notes

- GPU acceleration primarily benefits vision model inference (BLIP)
- FAISS GPU acceleration benefits vector similarity search at scale
- Most operations (LLM API calls, basic data processing) are already CPU-optimized
- GPU usage is optional - CPU performance is acceptable for most use cases
