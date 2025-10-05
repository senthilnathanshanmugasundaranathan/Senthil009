import inspect
import time

class DebugDebugger:
    def __init__(self):
        self.debug_log = []

    def debug(self, message):
        # Get caller frame info
        caller = inspect.stack()[1]
        info = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'filename': caller.filename,
            'lineno': caller.lineno,
            'function': caller.function,
            'message': message
        }
        self.debug_log.append(info)
        print(f"[DEBUG] {info['timestamp']} {info['filename']}:{info['lineno']} in {info['function']}: {message}")

    def show_debug_history(self):
        print("\n=== Debug History ===")
        for entry in self.debug_log:
            print(f"{entry['timestamp']} | {entry['filename']}:{entry['lineno']} | {entry['function']} | {entry['message']}")

# Example usage
if __name__ == "__main__":
    debugger = DebugDebugger()
    
    def test_func():
        debugger.debug("Starting test_func")
        for i in range(3):
            debugger.debug(f"Loop iteration {i}")
        debugger.debug("Ending test_func")

    test_func()
    debugger.show_debug_history()