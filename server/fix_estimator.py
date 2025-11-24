"""Fix estimator examples to handle scalar evs/stds."""
import re

def fix_file(filename):
    with open(filename, 'r') as f:
        content = f.read()

    # Replace complex expressions with simpler numpy-compatible ones
    # Pattern 1: evs access
    pattern1 = r'pub_result\.data\.evs\.item\(\) if hasattr\(pub_result\.data\.evs, "item"\) and pub_result\.data\.evs\.ndim == 0 else pub_result\.data\.evs\[0\]'
    replacement1 = 'float(pub_result.data.evs.flat[0])'

    # Pattern 2: stds access
    pattern2 = r'pub_result\.data\.stds if isinstance\(pub_result\.data\.stds, \(int, float\)\) else \(pub_result\.data\.stds\.item\(\) if hasattr\(pub_result\.data\.stds, "item"\) and pub_result\.data\.stds\.ndim == 0 else pub_result\.data\.stds\[0\]\)'
    replacement2 = 'float(pub_result.data.stds) if isinstance(pub_result.data.stds, (int, float)) else float(pub_result.data.stds.flat[0])'

    content = re.sub(pattern1, replacement1, content)
    content = re.sub(pattern2, replacement2, content)

    with open(filename, 'w') as f:
        f.write(content)

    print(f"Fixed {filename}")

if __name__ == "__main__":
    fix_file("examples/09_estimator_basic.py")
