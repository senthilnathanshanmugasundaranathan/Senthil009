# debug_debugger.py
# Now live at: https://github.com/senthilnathanshanmugasundaranathan/Senthil009/

import time
import traceback
import psutil
import threading
from datetime import datetime
from typing import Dict, List, Any, Callable
import json
import hashlib


class DebugDebugger:
    """
    When your debugging tools need debugging.
    The last line of defense before print('here') everywhere.
    """

    def __init__(self, paranoid_mode=True):
        self.paranoid_mode = paranoid_mode
        self.debug_tools_registry = {}
        self.tool_failures = []
        self.tool_performance = {}
        self.recursive_depth = 0
        self.MAX_RECURSION = 3  # Prevent debug inception

        # Track what's tracking the trackers
        self.watcher_thread = None
        self.emergency_fallback = print  # When all else fails

    def register_debug_tool(self, tool_name: str, tool_instance: Any):
        """Register a debugging tool to be monitored"""
        self.debug_tools_registry[tool_name] = {
            "instance": tool_instance,
            "failures": 0,
            "successes": 0,
            "total_time": 0,
            "status": "healthy",
            "last_heartbeat": time.time(),
        }

        # Wrap all methods of the tool
        self._instrument_tool(tool_name, tool_instance)

    def _instrument_tool(self, tool_name: str, tool_instance: Any):
        """Wrap every method of a debug tool to monitor it"""
        for attr_name in dir(tool_instance):
            if not attr_name.startswith("_"):
                attr = getattr(tool_instance, attr_name)
                if callable(attr):
                    wrapped = self._create_wrapper(tool_name, attr_name, attr)
                    setattr(tool_instance, attr_name, wrapped)

    def _create_wrapper(
        self, tool_name: str, method_name: str, original_method: Callable
    ):
        """Create a monitoring wrapper for debug tool methods"""

        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            method_id = f"{tool_name}.{method_name}"

            # Check if we're in a recursive debug loop
            if self.recursive_depth > self.MAX_RECURSION:
                self.emergency_fallback(
                    f"🚨 DEBUG INCEPTION DETECTED: {method_id} at depth {self.recursive_depth}"
                )
                return None

            self.recursive_depth += 1

            try:
                # Monitor memory before
                memory_before = psutil.Process().memory_info().rss / 1024 / 1024

                # Execute the actual debug tool method
                result = original_method(*args, **kwargs)

                # Monitor memory after
                memory_after = psutil.Process().memory_info().rss / 1024 / 1024
                memory_delta = memory_after - memory_before

                # Track performance
                elapsed = time.perf_counter() - start_time
                self._record_success(tool_name, method_name, elapsed, memory_delta)

                # Alert if debug tool is too slow
                if elapsed > 1.0:
                    self._alert(
                        f"🐌 Slow debugger: {method_id} took {elapsed:.2f}s",
                        level="warning",
                    )

                # Alert if debug tool is leaking memory
                if memory_delta > 100:  # MB
                    self._alert(
                        f"💾 Memory leak in debugger: {method_id} consumed {memory_delta:.2f}MB",
                        level="warning",
                    )

                return result

            except Exception as e:
                # The debugger failed!
                self._record_failure(tool_name, method_name, e)

                # Try to self-heal
                healing_result = self._attempt_self_heal(
                    tool_name, method_name, e, args, kwargs
                )
                if healing_result is not None:
                    return healing_result

                # If we can't heal, document the failure
                self._document_debugger_failure(tool_name, method_name, e, args, kwargs)

                # Use fallback debugging
                return self._fallback_debug(method_id, args, kwargs)

            finally:
                self.recursive_depth -= 1

        return wrapper

    def _record_success(
        self, tool_name: str, method_name: str, elapsed: float, memory_delta: float
    ):
        """Track successful debug tool execution"""
        tool_stats = self.debug_tools_registry[tool_name]
        tool_stats["successes"] += 1
        tool_stats["total_time"] += elapsed
        tool_stats["last_heartbeat"] = time.time()

        # Track performance patterns
        if tool_name not in self.tool_performance:
            self.tool_performance[tool_name] = []

        self.tool_performance[tool_name].append(
            {
                "method": method_name,
                "elapsed": elapsed,
                "memory_delta": memory_delta,
                "timestamp": time.time(),
            }
        )

        # Keep only last 100 entries per tool
        if len(self.tool_performance[tool_name]) > 100:
            self.tool_performance[tool_name] = self.tool_performance[tool_name][-100:]

    def _record_failure(self, tool_name: str, method_name: str, exception: Exception):
        """Track debug tool failures"""
        tool_stats = self.debug_tools_registry[tool_name]
        tool_stats["failures"] += 1

        failure_record = {
            "tool": tool_name,
            "method": method_name,
            "exception": str(exception),
            "traceback": traceback.format_exc(),
            "timestamp": time.time(),
        }

        self.tool_failures.append(failure_record)

        # Mark tool as unhealthy if too many failures
        failure_rate = tool_stats["failures"] / max(
            tool_stats["successes"] + tool_stats["failures"], 1
        )
        if failure_rate > 0.3:  # 30% failure rate
            tool_stats["status"] = "unhealthy"
            self._alert(
                f"🏥 Debug tool unhealthy: {tool_name} ({failure_rate:.1%} failure rate)"
            )

    def _attempt_self_heal(
        self, tool_name: str, method_name: str, exception: Exception, args, kwargs
    ):
        """Try to self-heal a broken debugger"""

        # Strategy 1: Retry with exponential backoff
        if "timeout" in str(exception).lower():
            time.sleep(0.1)
            try:
                tool = self.debug_tools_registry[tool_name]["instance"]
                method = getattr(tool, method_name.replace(f"{tool_name}.", ""))
                return method(*args, **kwargs)
            except:
                pass

        # Strategy 2: Clear any caches
        if hasattr(self.debug_tools_registry[tool_name]["instance"], "clear_cache"):
            try:
                self.debug_tools_registry[tool_name]["instance"].clear_cache()
            except:
                pass

        # Strategy 3: Reduce data size if possible
        if "memory" in str(exception).lower() and args:
            try:
                # Try with first 10 items if it's a collection
                if hasattr(args[0], "__len__") and len(args[0]) > 10:
                    reduced_args = (args[0][:10],) + args[1:]
                    tool = self.debug_tools_registry[tool_name]["instance"]
                    method = getattr(tool, method_name.replace(f"{tool_name}.", ""))
                    return method(*reduced_args, **kwargs)
            except:
                pass

        return None

    def _fallback_debug(self, method_id: str, args, kwargs):
        """When a debugger fails, fall back to primitive but reliable methods"""
        self.emergency_fallback(f"💀 DEBUGGER FAILED: {method_id}")
        self.emergency_fallback(
            f"📥 Args: {args[:3] if len(args) > 3 else args}"
        )  # Limit output
        self.emergency_fallback(f"📦 Kwargs: {list(kwargs.keys())}")

        # Return a safe default that won't crash the system
        return None

    def _document_debugger_failure(
        self, tool_name: str, method_name: str, exception: Exception, args, kwargs
    ):
        """Create detailed forensics when a debugger fails"""

        # Create unique filename for this failure
        failure_hash = hashlib.md5(
            f"{tool_name}{method_name}{time.time()}".encode()
        ).hexdigest()[:8]
        filename = f"/tmp/debugger_failure_{failure_hash}.json"

        forensics = {
            "tool_name": tool_name,
            "method_name": method_name,
            "exception": str(exception),
            "exception_type": type(exception).__name__,
            "timestamp": datetime.now().isoformat(),
            "traceback": traceback.format_exc(),
            "system_state": {
                "memory_percent": psutil.virtual_memory().percent,
                "cpu_percent": psutil.cpu_percent(),
                "thread_count": threading.active_count(),
                "disk_usage": psutil.disk_usage("/").percent,
            },
            "tool_history": self.debug_tools_registry.get(tool_name, {}),
            "recent_failures": self.tool_failures[-5:] if self.tool_failures else [],
        }

        try:
            # Save forensics for post-mortem
            with open(filename, "w") as f:
                json.dump(forensics, f, indent=2, default=str)
            self.emergency_fallback(f"📝 Debugger forensics saved to {filename}")
        except:
            # If we can't even write files, we're in deep trouble
            self.emergency_fallback(f"🔥 CRITICAL: Can't even save debugger forensics")

    def _alert(self, message: str, level="info"):
        """Send alerts about debugger health"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        if level == "warning":
            self.emergency_fallback(f"⚠️  [{timestamp}] {message}")
        elif level == "error":
            self.emergency_fallback(f"❌ [{timestamp}] {message}")
        else:
            self.emergency_fallback(f"ℹ️  [{timestamp}] {message}")

    def health_check(self) -> Dict[str, Any]:
        """Check health of all registered debug tools"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "tools": {},
            "overall_health": "healthy",
            "recommendations": [],
        }

        unhealthy_count = 0

        for tool_name, stats in self.debug_tools_registry.items():
            # Check if tool is responsive
            time_since_heartbeat = time.time() - stats["last_heartbeat"]
            if time_since_heartbeat > 300:  # 5 minutes
                stats["status"] = "unresponsive"

            # Calculate metrics
            total_calls = stats["successes"] + stats["failures"]
            failure_rate = stats["failures"] / max(total_calls, 1)
            avg_time = stats["total_time"] / max(stats["successes"], 1)

            report["tools"][tool_name] = {
                "status": stats["status"],
                "failure_rate": f"{failure_rate:.1%}",
                "average_time": f"{avg_time:.3f}s",
                "total_calls": total_calls,
                "last_seen": f"{time_since_heartbeat:.0f}s ago",
            }

            if stats["status"] != "healthy":
                unhealthy_count += 1

                # Generate recommendations
                if failure_rate > 0.5:
                    report["recommendations"].append(
                        f"Consider replacing {tool_name} - failure rate too high"
                    )
                elif time_since_heartbeat > 300:
                    report["recommendations"].append(
                        f"Restart {tool_name} - appears to be hung"
                    )
                elif avg_time > 5:
                    report["recommendations"].append(
                        f"Optimize {tool_name} - taking {avg_time:.1f}s per call"
                    )

        # Overall health assessment
        if unhealthy_count == 0:
            report["overall_health"] = "healthy"
        elif unhealthy_count < len(self.debug_tools_registry) / 2:
            report["overall_health"] = "degraded"
        else:
            report["overall_health"] = "critical"
            report["recommendations"].insert(
                0, "🚨 CRITICAL: Majority of debug tools failing. Use manual debugging."
            )

        return report

    def get_best_debugger_for(self, problem_type: str) -> str:
        """Recommend which debugger to use based on problem and tool health"""

        # Problem-to-debugger mapping based on 20 years of pain
        problem_map = {
            "race_condition": "quantum_logger",
            "memory_leak": "memory_archaeologist",
            "heisenbug": "heisenberg_trap",
            "performance": "production_profiler",
            "distributed": "distributed_tombstone",
            "random": "probability_collapser",
            "unknown": "print_statements",  # When in doubt...
        }

        recommended_tool = problem_map.get(problem_type, "print_statements")

        # Check if recommended tool is healthy
        if recommended_tool in self.debug_tools_registry:
            tool_stats = self.debug_tools_registry[recommended_tool]
            if tool_stats["status"] != "healthy":
                # Find best alternative
                for tool_name, stats in self.debug_tools_registry.items():
                    if stats["status"] == "healthy":
                        self._alert(
                            f"Recommended {recommended_tool} is unhealthy. Using {tool_name} instead."
                        )
                        return tool_name

        # If no healthy debuggers, admit defeat
        if recommended_tool not in self.debug_tools_registry:
            return "print_statements"

        return recommended_tool

    def emergency_diagnostic(self):
        """When everything is broken, run this"""
        self.emergency_fallback("=" * 50)
        self.emergency_fallback("EMERGENCY DIAGNOSTIC RUNNING")
        self.emergency_fallback("=" * 50)

        # Check system resources
        self.emergency_fallback(f"Memory: {psutil.virtual_memory().percent}%")
        self.emergency_fallback(f"CPU: {psutil.cpu_percent()}%")
        self.emergency_fallback(f"Threads: {threading.active_count()}")

        # Check each debugger
        for tool_name, stats in self.debug_tools_registry.items():
            status_icon = "✅" if stats["status"] == "healthy" else "❌"
            self.emergency_fallback(
                f"{status_icon} {tool_name}: {stats['failures']} failures, {stats['successes']} successes"
            )

        # Recent failures
        if self.tool_failures:
            self.emergency_fallback("\nRecent Debugger Failures:")
            for failure in self.tool_failures[-3:]:
                self.emergency_fallback(
                    f"  - {failure['tool']}: {failure['exception']}"
                )

        # Final recommendation
        healthy_tools = [
            name
            for name, stats in self.debug_tools_registry.items()
            if stats["status"] == "healthy"
        ]

        if healthy_tools:
            self.emergency_fallback(
                f"\n✅ Healthy tools available: {', '.join(healthy_tools)}"
            )
        else:
            self.emergency_fallback("\n🔥 ALL DEBUGGERS FAILED. Use print() and pray.")

        self.emergency_fallback("=" * 50)


# Production usage that saved the day
if __name__ == "__main__":
    # Initialize the meta-debugger
    meta_debug = DebugDebugger(paranoid_mode=True)

    # Register all your debugging tools
    from quantum_logger import QuantumLogger
    from heisenberg_trap import HeisenbergTrap
    from memory_archaeologist import MemoryArchaeologist

    quantum = QuantumLogger()
    heisenberg = HeisenbergTrap()
    archaeologist = MemoryArchaeologist()

    meta_debug.register_debug_tool("quantum_logger", quantum)
    meta_debug.register_debug_tool("heisenberg_trap", heisenberg)
    meta_debug.register_debug_tool("memory_archaeologist", archaeologist)

    # Now use your debuggers normally - they're being watched
    try:
        # Your normal debugging code
        quantum.log_async("Starting investigation")
        heisenberg.monitor("critical_section")
        archaeologist.track_birth(some_object)
    except:
        # When debuggers fail, the meta-debugger takes over
        meta_debug.emergency_diagnostic()

    # Check debugger health
    health_report = meta_debug.health_check()
    print(json.dumps(health_report, indent=2))

    # Get best debugger for current problem
    best_tool = meta_debug.get_best_debugger_for("race_condition")
    print(f"Recommended debugger: {best_tool}")
