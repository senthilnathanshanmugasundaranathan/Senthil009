import copy
import time

class MemoryArchaeologist:
    def __init__(self):
        self.snapshots = []

    def excavate(self, obj, note=""):
        # Store a deep copy of the object plus metadata
        snapshot = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'note': note,
            'state': copy.deepcopy(obj)
        }
        self.snapshots.append(snapshot)
        print(f"Excavated memory at {snapshot['timestamp']}: {note}")

    def show_excavations(self):
        print("\n=== Memory Excavations ===")
        for idx, snap in enumerate(self.snapshots):
            print(f"{idx+1}. {snap['timestamp']} | Note: {snap['note']} | State: {snap['state']}")

# Example usage
if __name__ == "__main__":
    archaeologist = MemoryArchaeologist()
    my_dict = {'counter': 0}

    for i in range(3):
        my_dict['counter'] += 1
        archaeologist.excavate(my_dict, note=f"After increment {i+1}")

    archaeologist.show_excavations()
