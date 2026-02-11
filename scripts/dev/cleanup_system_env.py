import subprocess
import sys

def cleanup():
    print("Gathering installed packages...")
    try:
        # Get list directly from pip
        output = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
        packages = output.splitlines()
    except subprocess.CalledProcessError as e:
        print(f"Failed to list packages: {e}")
        return

    # Filter out essentials
    essentials = {"pip", "setuptools", "wheel", "distribute", "cx-freeze", "cx_Freeze"}
    to_remove = []
    
    for p in packages:
        # pip freeze format: name==version
        if "==" in p:
            name = p.split("==")[0]
        elif "@" in p:
             name = p.split("@")[0]
        else:
            name = p
            
        name = name.strip().lower()
        
        if name and name not in essentials and not name.startswith("-e"):
             to_remove.append(name)
    
    if not to_remove:
        print("No packages to remove!")
        return

    print(f"Removing {len(to_remove)} packages: {', '.join(to_remove[:5])}...")
    
    # Write filtered list to temp file for batch uninstall
    with open("temp_uninstall_list.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(to_remove))
        
    # Run uninstall
    cmd = [sys.executable, "-m", "pip", "uninstall", "-r", "temp_uninstall_list.txt", "-y"]
    subprocess.run(cmd, check=False)
    print("Cleanup complete.")

if __name__ == "__main__":
    cleanup()
