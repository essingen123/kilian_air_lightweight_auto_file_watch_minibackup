# firimport303a.py
import subprocess

try:
    subprocess.check_call(['pip', 'install', '--upgrade', '--quiet', 'watchdog'])
except subprocess.CalledProcessError:
    pass

try:
    subprocess.check_call(['pip', 'install', '--upgrade', '--quiet', 'psutil'])
except subprocess.CalledProcessError:
    pass
