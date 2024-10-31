import win32gui, win32process
import psutil, subprocess
import time
import os

class ProcessStateMachine:
    @staticmethod
    def get_window_count(pid):
        hwnds = 0

        def callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                if found_pid == pid:
                    nonlocal hwnds
                    hwnds = hwnds+1
            return True

        win32gui.EnumWindows(callback, None)
        return hwnds

    @staticmethod
    def get_main_window(pid, process_name):
        def callback(hwnd, hwnds):
            if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                if found_pid == pid:
                    hwnds.append(hwnd)
            return True

        hwnds = []
        win32gui.EnumWindows(callback, hwnds)

        for hwnd in hwnds:
            window_name = win32gui.GetWindowText(hwnd)
            print(window_name)
            norm_window_name = window_name.lower().replace(" ","")
            norm_proc_name = process_name.lower().replace(" ","")
            if norm_window_name in norm_proc_name:
                return hwnd

        return None
    
    def __init__(self, filepath, callback = None):
        self.target = filepath
        self.process = None
        self.process_name = ""
        self.main_win_hwnd = None
        self.state = 'INITIALIZING'
        self.callback = callback

    def run(self):
        while True:
            if self.process and self.process.poll() is not None:
                self.state = 'TERMINATED'
            if (self.state == 'TERMINATED'
            or self.state == 'ABORTED'
            or self.state == 'CRASHED'):
                break
            self.state_machine()
            time.sleep(0.2)
        if self.callback:
            self.callback(self.state)

    def state_machine(self):
        if self.state == 'INITIALIZING':
            self.initializing()
        elif self.state == 'STARTING':
            self.starting()
        elif self.state == 'RUNNING':
            self.running()
        elif self.state == 'TERMINATED':
            self.terminated()
        elif self.state == 'CRASHED':
            self.crashed()
        elif self.state == 'ABORTED':
            self.aborted()

    def initializing(self):
        if self.target is None:
            self.state = 'ABORTED'
            return
        if(os.name == "nt"):
            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            self.process = subprocess.Popen([self.target]
                                        , creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
                                        , close_fds=True)
        else:
            self.process = subprocess.Popen([self.target], preexec_fn=os.setsid)
        self.process_name = psutil.Process(self.process.pid).name()
        self.state = 'STARTING'

    def starting(self):
        self.main_win_hwnd = ProcessStateMachine.get_main_window(self.process.pid, self.process_name)
        if self.main_win_hwnd is not None:
            self.state = 'RUNNING'

    def running(self):
        if not win32gui.IsWindow(self.main_win_hwnd) and psutil.pid_exists(self.process.pid):
            time.sleep(0.5)
            window_count = ProcessStateMachine.get_window_count(self.process.pid)
            if psutil.pid_exists(self.process.pid) and window_count > 0:
                self.state = 'CRASHED'
            else:
                self.state = 'TERMINATED'

    def terminated(self):
        print("Process exited normally.")
        self.state = 'FINISHED'
    
    def crashed(self):
        print("Process crashed.")
        self.state = 'FINISHED'
    
    def aborted(self):
        print("Process aborted.")
        self.state = 'FINISHED'