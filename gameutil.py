import obspython as obs
import psutil
import win32gui
import subprocess

class gameutil:
    '''
    gameutil provides helper functions for process tracking and running applications (steam or otherwise)
    '''

    @staticmethod
    def run_steam_game(game_name: str, game_steam_gameid: str):
        """
        Runs a steam game, given its steam gameid.
        """
        obs.script_log(obs.LOG_INFO, "Running "+game_name)
        steamCommand = "steam"
        steamGameParameter = "steam://rungameid/"+game_steam_gameid
        subprocess.call([steamCommand, steamGameParameter])

    @staticmethod
    def run_game(game_executable: str):
        obs.script_log(obs.LOG_INFO, "Running" + game_executable)
        subprocess.call([game_executable])

    @staticmethod
    def check_if_process_running(processName: str) -> bool:
        '''
        Check if there is any running process that contains the given name processName.

        Returns: bool
        '''
        #Iterate over the all the running process
        for proc in psutil.process_iter():
            try:
                # Check if process name contains the given name string.
                if processName.lower() in proc.name().lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False
    
    @staticmethod
    def find_processid_by_name(processName: str) -> psutil.Process | None:
        '''
        Iterate through running processes and return the one with the given proces name, otherwise None

        Returns: Process | None
        '''
        listOfProcessObjects = []
    
        #Iterate over the all the running process
        for proc in psutil.process_iter():
            try:
                # Check if process name contains the given name string.
                if proc.name().lower() in processName.lower() :
                    listOfProcessObjects.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied , psutil.ZombieProcess) :
                pass

        if len(listOfProcessObjects) == 0:
            return None
        else:
            return listOfProcessObjects[0]

    @staticmethod
    def print_parent_proc(process: psutil.Process):
        if process is None:
            return
        parent = process.parent()
        if parent is not None:
            msg = "Parent {proc_name} [PID = {proc_id}]".format(proc_name=parent.name(), proc_id=parent.pid)
            obs.script_log(obs.LOG_INFO, msg)

    @staticmethod
    def print_current_proc(process: psutil.Process):
        if process is None:
            return
        msg = "   - Process {proc_name} [PID = {proc_id}]".format(proc_name=process.name(), proc_id=process.pid)
        obs.script_log(obs.LOG_INFO, msg)

    @staticmethod
    def print_child_procs(process: psutil.Process):
        if process is None:
            return
        for child in process.children(recursive=True):
            if child.pid != process.pid:
                msg = "        - Child {proc_name} [PID = {proc_id}]".format(proc_name=child.name(), proc_id=child.pid)
                obs.script_log(obs.LOG_INFO, msg)
            else:
                msg = "        - Child {proc_name} [PID = {proc_id}]".format(proc_name=process.name(), proc_id=process.pid)
                obs.script_log(obs.LOG_INFO, msg)

    @staticmethod
    def get_process_status(process: psutil.Process, window_name: str, window_class: str, crash_window_name: str, crash_window_class: str) -> str:
        '''
        Finds the window handle for the application's main window, as well as, for the crash window. Returns the process' status based on combination of Process.status() and which window of the two is currently in use.

        Returns: string
        '''
        try:
            main_hwnd = win32gui.FindWindow(window_class, window_name)
            crash_hwnd = win32gui.FindWindow(crash_window_class, crash_window_name)
            app_status = process.status()
            #obs.script_log(obs.LOG_INFO, str(main_hwnd)+","+str(crash_hwnd))
            if main_hwnd == 0 and crash_hwnd != 0:
                app_status = psutil.STATUS_STOPPED
            
            return app_status
        except (psutil.NoSuchProcess, psutil.AccessDenied , psutil.ZombieProcess) :
            return psutil.STATUS_DEAD
