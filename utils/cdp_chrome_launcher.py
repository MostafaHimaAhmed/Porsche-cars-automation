import subprocess 
from pathlib import Path 
from urllib.request import urlopen
import time 
from utils.logger import log 

class CdpChromeLauncher:

    def __init__(self, chrome_path, profile_dir, port) -> None:
        self.chrome_path = chrome_path
        self.profile_dir = profile_dir
        self.port = port
        self._process  = None
        self.startup_timeout = 20.0

    @property
    def _version_url(self):
        return f"http://127.0.0.1:{self.port}/json/version"

    
    def start_chrome(self):
        self._process = subprocess.Popen(
            [
                self.chrome_path,
                f'--remote-debugging-port={self.port}',
                f'--user-data-dir={self.profile_dir}'
            ]
        )

        if self._wait_until_ready():
            log('Chrome Launcher', 'chrome is ready successfuly', 'green')

    def _wait_until_ready(self):

        deadline = time.monotonic() + self.startup_timeout

        while time.monotonic() < deadline :
            if self._process and self._process.poll() is not None:
                break # That means chrome exited by itself no point to wait 

            try:
                with urlopen(self._version_url, timeout=1) as f:
                    return True
            except OSError:
                time.sleep(1)

        self.stop_chrome()
        log('Chrome Launcher', f'chrome did not open on debugging port {self.port}', 'red')
        log('Chrome Launcher', f'check chrome path and that {self.profile_dir} not in use', 'red')
        return False

    
    def stop_chrome(self):
        if self._process is None:
            return # safe to call even if chrome never started

        self._process.terminate()

        try:
            self._process.wait(10.0)
        except subprocess.TimeoutExpired:
            self._process.kill()

        self._process = None
        log('Chrome Launcher', 'chrome stopped successfuly', 'yellow')


        
