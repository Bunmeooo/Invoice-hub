import os
import subprocess
import tempfile
import rarfile

# Configure rarfile tool path
unrar_paths = [
    r"C:\Program Files\WinRAR\UnRAR.exe",
    r"C:\Program Files\7-Zip\7z.exe",
    r"C:\Program Files (x86)\WinRAR\UnRAR.exe"
]
for p in unrar_paths:
    if os.path.exists(p):
        rarfile.UNRAR_TOOL = p
        print("Set rarfile.UNRAR_TOOL to:", p)
        break

# Test 7z command
cmd_7z = r"C:\Program Files\7-Zip\7z.exe"
print("7z version test:")
res = subprocess.run([cmd_7z], capture_output=True, text=True)
print(res.stdout.splitlines()[1] if res.stdout else "No output")
