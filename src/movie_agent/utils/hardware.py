"""
Hardware detection and management utilities.

Provides centralized hardware awareness for GPU/CPU detection,
device selection, and hardware capability reporting.
"""
import logging
from typing import Optional, Literal
from enum import Enum

logger = logging.getLogger(__name__)


class DeviceType(str, Enum):
    """Supported device types."""
    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"  # Apple Silicon Metal Performance Shaders
    AUTO = "auto"  # Auto-detect best available


class HardwareInfo:
    """Hardware capability information."""
    
    def __init__(
        self,
        device_type: DeviceType,
        gpu_available: bool = False,
        gpu_name: Optional[str] = None,
        gpu_count: int = 0,
        torch_available: bool = False,
        cuda_available: bool = False,
        mps_available: bool = False,
    ):
        self.device_type = device_type
        self.gpu_available = gpu_available
        self.gpu_name = gpu_name
        self.gpu_count = gpu_count
        self.torch_available = torch_available
        self.cuda_available = cuda_available
        self.mps_available = mps_available
    
    def __repr__(self) -> str:
        return (
            f"HardwareInfo(device={self.device_type.value}, "
            f"gpu_available={self.gpu_available}, "
            f"gpu_name={self.gpu_name or 'N/A'}, "
            f"gpu_count={self.gpu_count})"
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for logging/serialization."""
        return {
            "device_type": self.device_type.value,
            "gpu_available": self.gpu_available,
            "gpu_name": self.gpu_name,
            "gpu_count": self.gpu_count,
            "torch_available": self.torch_available,
            "cuda_available": self.cuda_available,
            "mps_available": self.mps_available,
        }


class HardwareDetector:
    """
    Centralized hardware detection and device management.
    
    Detects available hardware (GPU/CPU) and provides device selection
    with fallback logic.
    """
    
    @staticmethod
    def detect_torch_availability() -> bool:
        """Check if PyTorch is available."""
        try:
            import torch
            return True
        except ImportError:
            return False
    
    @staticmethod
    def detect_cuda_availability() -> bool:
        """Check if CUDA (NVIDIA GPU) is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except (ImportError, AttributeError):
            return False
    
    @staticmethod
    def detect_mps_availability() -> bool:
        """Check if MPS (Apple Silicon GPU) is available."""
        try:
            import torch
            return hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
        except (ImportError, AttributeError):
            return False
    
    @staticmethod
    def get_cuda_info() -> tuple[bool, Optional[str], int]:
        """
        Get CUDA GPU information.
        
        :return: Tuple of (available, gpu_name, gpu_count)
        """
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                gpu_count = torch.cuda.device_count()
                return True, gpu_name, gpu_count
            return False, None, 0
        except (ImportError, AttributeError, RuntimeError):
            return False, None, 0
    
    @staticmethod
    def get_mps_info() -> tuple[bool, Optional[str], int]:
        """
        Get MPS (Apple Silicon) GPU information.
        
        :return: Tuple of (available, device_name, count)
        """
        try:
            import torch
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                # Apple Silicon GPU
                return True, "Apple Silicon GPU (MPS)", 1
            return False, None, 0
        except (ImportError, AttributeError):
            return False, None, 0
    
    @classmethod
    def detect_all(cls) -> HardwareInfo:
        """
        Detect all available hardware capabilities.
        
        :return: HardwareInfo object with detected capabilities
        """
        torch_available = cls.detect_torch_availability()
        cuda_available = cls.detect_cuda_availability()
        mps_available = cls.detect_mps_availability()
        
        gpu_available = cuda_available or mps_available
        gpu_name = None
        gpu_count = 0
        
        if cuda_available:
            _, gpu_name, gpu_count = cls.get_cuda_info()
        elif mps_available:
            _, gpu_name, gpu_count = cls.get_mps_info()
        
        # Determine best device type
        if cuda_available:
            device_type = DeviceType.CUDA
        elif mps_available:
            device_type = DeviceType.MPS
        else:
            device_type = DeviceType.CPU
        
        return HardwareInfo(
            device_type=device_type,
            gpu_available=gpu_available,
            gpu_name=gpu_name,
            gpu_count=gpu_count,
            torch_available=torch_available,
            cuda_available=cuda_available,
            mps_available=mps_available,
        )
    
    @classmethod
    def select_device(
        cls,
        preferred_device: Optional[DeviceType | str] = None,
        fallback_to_cpu: bool = True,
    ) -> str:
        """
        Select the best available device based on preferences.
        
        :param preferred_device: Preferred device type (DeviceType enum or string)
        :param fallback_to_cpu: Whether to fallback to CPU if preferred device unavailable
        :return: Device string ("cuda", "mps", or "cpu")
        """
        if isinstance(preferred_device, str):
            # Convert string to enum
            try:
                preferred_device = DeviceType(preferred_device.lower())
            except ValueError:
                logger.warning(
                    f"Unknown device type '{preferred_device}', using auto-detect"
                )
                preferred_device = DeviceType.AUTO
        
        if preferred_device == DeviceType.CPU:
            return "cpu"
        
        if preferred_device == DeviceType.CUDA:
            if cls.detect_cuda_availability():
                return "cuda"
            elif fallback_to_cpu:
                logger.warning("CUDA requested but not available, falling back to CPU")
                return "cpu"
            else:
                raise RuntimeError("CUDA requested but not available")
        
        if preferred_device == DeviceType.MPS:
            if cls.detect_mps_availability():
                return "mps"
            elif fallback_to_cpu:
                logger.warning("MPS requested but not available, falling back to CPU")
                return "cpu"
            else:
                raise RuntimeError("MPS requested but not available")
        
        # Auto-detect (preferred_device is AUTO or None)
        if cls.detect_cuda_availability():
            return "cuda"
        elif cls.detect_mps_availability():
            return "mps"
        else:
            return "cpu"
    
    @classmethod
    def log_hardware_info(cls, hardware_info: Optional[HardwareInfo] = None) -> None:
        """
        Log hardware information for debugging/monitoring.
        
        :param hardware_info: Optional HardwareInfo object. If None, will detect.
        """
        if hardware_info is None:
            hardware_info = cls.detect_all()
        
        info = hardware_info.to_dict()
        logger.info("Hardware Detection Results:")
        logger.info(f"  Device Type: {info['device_type']}")
        logger.info(f"  PyTorch Available: {info['torch_available']}")
        logger.info(f"  CUDA Available: {info['cuda_available']}")
        logger.info(f"  MPS Available: {info['mps_available']}")
        logger.info(f"  GPU Available: {info['gpu_available']}")
        
        if info['gpu_available']:
            logger.info(f"  GPU Name: {info['gpu_name']}")
            logger.info(f"  GPU Count: {info['gpu_count']}")
        else:
            logger.info("  Using CPU for all operations")


def get_recommended_dtype(device: str) -> str:
    """
    Get recommended data type for a given device.
    
    :param device: Device string ("cuda", "mps", "cpu")
    :return: Recommended dtype string ("float16" for GPU, "float32" for CPU)
    """
    if device in ("cuda", "mps"):
        return "float16"
    return "float32"
