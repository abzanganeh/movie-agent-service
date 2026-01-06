"""
LangChain callbacks for fine-grained latency tracking.
"""
from typing import Dict, Any, Optional
from time import time
from langchain_core.callbacks import BaseCallbackHandler


class ToolLatencyCallback(BaseCallbackHandler):
    """
    Callback handler that tracks tool execution latency.
    
    Accumulates execution time for all tools invoked during an agent run.
    Provides precise tool_latency_ms measurement.
    """
    
    def __init__(self):
        super().__init__()
        self._tool_start_times: Dict[str, float] = {}
        self._tool_latencies: Dict[str, float] = {}
        self._total_tool_time: float = 0.0
    
    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: str,
        parent_run_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Record tool start time."""
        tool_name = serialized.get("name", "unknown_tool")
        self._tool_start_times[run_id] = time()
    
    def on_tool_end(
        self,
        output: str,
        *,
        run_id: str,
        parent_run_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Record tool end time and calculate latency."""
        if run_id in self._tool_start_times:
            start_time = self._tool_start_times.pop(run_id)
            latency = time() - start_time
            self._tool_latencies[run_id] = latency
            self._total_tool_time += latency
    
    def on_tool_error(
        self,
        error: Exception,
        *,
        run_id: str,
        parent_run_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Handle tool errors - still record time if start was captured."""
        if run_id in self._tool_start_times:
            start_time = self._tool_start_times.pop(run_id)
            latency = time() - start_time
            self._tool_latencies[run_id] = latency
            self._total_tool_time += latency
    
    def get_total_tool_latency_ms(self) -> int:
        """
        Get total tool execution time in milliseconds.
        
        Returns sum of all tool execution times during the agent run.
        """
        return int(self._total_tool_time * 1000)
    
    def get_tool_latencies(self) -> Dict[str, float]:
        """
        Get per-tool latency breakdown (for debugging/analytics).
        
        Returns dict mapping run_id to latency in seconds.
        """
        return self._tool_latencies.copy()
    
    def reset(self) -> None:
        """Reset all tracking state (useful for reusing callback)."""
        self._tool_start_times.clear()
        self._tool_latencies.clear()
        self._total_tool_time = 0.0

