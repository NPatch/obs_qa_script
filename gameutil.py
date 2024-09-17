import math, time
import os, subprocess
import keyboard
import psutil
import win32gui
import win32process

def RunSteamGame(game_name, game_steam_gameid):
    print("Running ", game_name)
    steamCommand = "steam"
    steamGameParameter = "steam://rungameid/"+str(game_steam_gameid)
    subprocess.call([steamCommand, steamGameParameter])
    # global proc
    # proc = subprocess.Popen(
    #     executable = steamCommand,
    #     args = steamOldSkiesParameter,
    #     # avoid having to explicitly encode
    #     shell = True,
    #     text=True)
    # global proc_result
    # proc_result = proc.returncode

def checkIfProcessRunning(processName):
    '''
    Check if there is any running process that contains the given name processName.
    '''
    #Iterate over the all the running process
    for proc in psutil.process_iter():
        try:
            # Check if process name contains the given name string.
            if processName.lower() in proc.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False;
 
def findProcessIdByName(processName):
    '''
    Get a list of all the PIDs of a all the running process whose name contains
    the given string processName
    '''
    listOfProcessObjects = []
 
    #Iterate over the all the running process
    for proc in psutil.process_iter():
       try:
           # Check if process name contains the given name string.
           if processName.lower() == proc.name().lower() :
               listOfProcessObjects.append(proc)
       except (psutil.NoSuchProcess, psutil.AccessDenied , psutil.ZombieProcess) :
           pass

    if len(listOfProcessObjects) == 0:
        return None
    else:
        return listOfProcessObjects[0]

def print_parent_proc(process):
    if process is None:
        return
    parent = process.parent()
    if parent is not None:
        print('Parent %s [PID = %d]' % (parent.name(), parent.pid))
            
def print_current_proc(process):
    if process is None:
        return
    print ('   - Process %s [PID = %d]' % (process.name(), process.pid))

def print_child_procs(process):
    if process is None:
        return
    for child in process.children(recursive=True):
        if child.pid != process.pid:
            print ('        - Child %s [PID = %d]' % (child.name(), child.pid))
        else:
            print('        - Child %s [PID = %d] (Self)' % (child.name(), child.pid))

def get_process_status(process, window_name, window_class, crash_window_name, crash_window_class):
    try:
        main_hwnd = win32gui.FindWindow(window_class, window_name)
        crash_hwnd = win32gui.FindWindow(crash_window_class, crash_window_name)
        app_status = process.status()
        
        if main_hwnd == 0 and crash_hwnd != 0:
            app_status = psutil.STATUS_STOPPED
        
        return app_status
    except (psutil.NoSuchProcess, psutil.AccessDenied , psutil.ZombieProcess) :
        return psutil.STATUS_DEAD