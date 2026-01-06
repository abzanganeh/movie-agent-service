"""
Tests for LangChain callback handlers.
"""
import pytest
from time import sleep
from src.movie_agent.agent.callbacks import ToolLatencyCallback


class TestToolLatencyCallback:
    """Tests for ToolLatencyCallback."""

    def test_callback_tracks_tool_execution_time(self):
        """Test that callback accurately tracks tool execution time."""
        callback = ToolLatencyCallback()
        
        # Simulate tool start
        callback.on_tool_start(
            serialized={"name": "test_tool"},
            input_str="test input",
            run_id="run_1"
        )
        
        # Simulate some work
        sleep(0.1)  # 100ms
        
        # Simulate tool end
        callback.on_tool_end(
            output="test output",
            run_id="run_1"
        )
        
        # Check that latency was tracked
        total_ms = callback.get_total_tool_latency_ms()
        assert total_ms >= 100  # Should be at least 100ms
        assert total_ms < 200   # Should be less than 200ms (with some overhead)
    
    def test_callback_tracks_multiple_tools(self):
        """Test that callback tracks multiple tool executions."""
        callback = ToolLatencyCallback()
        
        # Simulate first tool
        callback.on_tool_start(
            serialized={"name": "tool_1"},
            input_str="input_1",
            run_id="run_1"
        )
        sleep(0.05)  # 50ms
        callback.on_tool_end(output="output_1", run_id="run_1")
        
        # Simulate second tool
        callback.on_tool_start(
            serialized={"name": "tool_2"},
            input_str="input_2",
            run_id="run_2"
        )
        sleep(0.05)  # 50ms
        callback.on_tool_end(output="output_2", run_id="run_2")
        
        # Total should be sum of both
        total_ms = callback.get_total_tool_latency_ms()
        assert total_ms >= 100  # At least 100ms (50 + 50)
        assert total_ms < 200   # Less than 200ms
    
    def test_callback_handles_tool_errors(self):
        """Test that callback tracks time even when tool errors."""
        callback = ToolLatencyCallback()
        
        callback.on_tool_start(
            serialized={"name": "failing_tool"},
            input_str="input",
            run_id="run_1"
        )
        sleep(0.05)  # 50ms
        
        # Simulate error
        callback.on_tool_error(
            error=Exception("Tool failed"),
            run_id="run_1"
        )
        
        # Should still track the time
        total_ms = callback.get_total_tool_latency_ms()
        assert total_ms >= 50
        assert total_ms < 150
    
    def test_callback_reset(self):
        """Test that callback can be reset for reuse."""
        callback = ToolLatencyCallback()
        
        # Track some time
        callback.on_tool_start(
            serialized={"name": "tool"},
            input_str="input",
            run_id="run_1"
        )
        sleep(0.01)
        callback.on_tool_end(output="output", run_id="run_1")
        
        assert callback.get_total_tool_latency_ms() > 0
        
        # Reset
        callback.reset()
        
        # Should be zero after reset
        assert callback.get_total_tool_latency_ms() == 0
        assert len(callback.get_tool_latencies()) == 0
    
    def test_callback_returns_latency_breakdown(self):
        """Test that callback provides per-tool latency breakdown."""
        callback = ToolLatencyCallback()
        
        # Track multiple tools
        callback.on_tool_start(
            serialized={"name": "tool_1"},
            input_str="input",
            run_id="run_1"
        )
        sleep(0.01)
        callback.on_tool_end(output="output", run_id="run_1")
        
        callback.on_tool_start(
            serialized={"name": "tool_2"},
            input_str="input",
            run_id="run_2"
        )
        sleep(0.02)
        callback.on_tool_end(output="output", run_id="run_2")
        
        # Get breakdown
        latencies = callback.get_tool_latencies()
        assert len(latencies) == 2
        assert "run_1" in latencies
        assert "run_2" in latencies
        # run_2 should have longer latency
        assert latencies["run_2"] > latencies["run_1"]

