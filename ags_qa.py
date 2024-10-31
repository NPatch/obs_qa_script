import obspython as obs
from enum import Enum
import psutil
import win32gui, win32process
from obsutil import obsutil
from gameutil import gameutil
from gamedata import AGSGameData

class obs_frontend_event(Enum):
    OBS_FRONTEND_EVENT_STREAMING_STARTING = 0
    OBS_FRONTEND_EVENT_STREAMING_STARTED = 1
    OBS_FRONTEND_EVENT_STREAMING_STOPPING = 2
    OBS_FRONTEND_EVENT_STREAMING_STOPPED = 3
    OBS_FRONTEND_EVENT_RECORDING_STARTING = 4
    OBS_FRONTEND_EVENT_RECORDING_STARTED = 5
    OBS_FRONTEND_EVENT_RECORDING_STOPPING = 6
    OBS_FRONTEND_EVENT_RECORDING_STOPPED = 7
    OBS_FRONTEND_EVENT_SCENE_CHANGED = 8
    OBS_FRONTEND_EVENT_SCENE_LIST_CHANGED = 9
    OBS_FRONTEND_EVENT_TRANSITION_CHANGED = 10
    OBS_FRONTEND_EVENT_TRANSITION_STOPPED = 11
    OBS_FRONTEND_EVENT_TRANSITION_LIST_CHANGED = 12
    OBS_FRONTEND_EVENT_SCENE_COLLECTION_CHANGED = 13
    OBS_FRONTEND_EVENT_SCENE_COLLECTION_LIST_CHANGED = 14
    OBS_FRONTEND_EVENT_PROFILE_CHANGED = 15
    OBS_FRONTEND_EVENT_PROFILE_LIST_CHANGED = 16
    OBS_FRONTEND_EVENT_EXIT = 17
    OBS_FRONTEND_EVENT_REPLAY_BUFFER_STARTING = 18
    OBS_FRONTEND_EVENT_REPLAY_BUFFER_STARTED = 19
    OBS_FRONTEND_EVENT_REPLAY_BUFFER_STOPPING = 20
    OBS_FRONTEND_EVENT_REPLAY_BUFFER_STOPPED = 21
    OBS_FRONTEND_EVENT_STUDIO_MODE_ENABLED = 22
    OBS_FRONTEND_EVENT_STUDIO_MODE_DISABLED = 23
    OBS_FRONTEND_EVENT_PREVIEW_SCENE_CHANGED = 24
    OBS_FRONTEND_EVENT_SCENE_COLLECTION_CLEANUP = 25
    OBS_FRONTEND_EVENT_FINISHED_LOADING = 26
    OBS_FRONTEND_EVENT_RECORDING_PAUSED = 27
    OBS_FRONTEND_EVENT_RECORDING_UNPAUSED = 28
    OBS_FRONTEND_EVENT_TRANSITION_DURATION_CHANGED = 29
    OBS_FRONTEND_EVENT_REPLAY_BUFFER_SAVED = 30
    OBS_FRONTEND_EVENT_VIRTUALCAM_STARTED = 31
    OBS_FRONTEND_EVENT_VIRTUALCAM_STOPPED = 32
    OBS_FRONTEND_EVENT_TBAR_VALUE_CHANGED = 33
    OBS_FRONTEND_EVENT_SCENE_COLLECTION_CHANGING = 34
    OBS_FRONTEND_EVENT_PROFILE_CHANGING = 35
    OBS_FRONTEND_EVENT_SCRIPTING_SHUTDOWN = 36
    OBS_FRONTEND_EVENT_PROFILE_RENAMED = 37
    OBS_FRONTEND_EVENT_SCENE_COLLECTION_RENAMED = 38
    OBS_FRONTEND_EVENT_THEME_CHANGED = 39
    OBS_FRONTEND_EVENT_SCREENSHOT_TAKEN = 40

ags_data = AGSGameData()

proc = None
proc_result = None
last_app_status = None

# Description displayed in the Scripts dialog window
def script_description():
  return """<center><h2>Old Skies QA Tools</h2></center>
            <p>Tools that automate and help in QA testing AGS games</p>"""

def script_defaults(settings):
    obs.script_log(obs.LOG_DEBUG, "script_defaults")
    obs.obs_data_set_default_string(settings, "scene_name", "")
    obs.obs_data_set_default_string(settings, "source_name", "")
    obs.obs_data_set_default_string(settings, "steam_gameid", "0")
    obs.obs_data_set_default_string(settings, "exe_name", "")
    obs.obs_data_set_default_string(settings, "win_name", "")
    obs.obs_data_set_default_string(settings, "win_class", "")
    obs.obs_data_set_default_string(settings, "crash_win_name", "")
    obs.obs_data_set_default_string(settings, "crash_win_class", "")

    obs.obs_data_set_default_string(settings, "scene_name", "Old Skies Scene")
    obs.obs_data_set_default_string(settings, "source_name", "Old Skies")
    obs.obs_data_set_default_string(settings, "steam_gameid", "1346360")
    obs.obs_data_set_default_string(settings, "exe_name", "OldSkies.exe")
    obs.obs_data_set_default_string(settings, "win_name", "Old Skies")
    obs.obs_data_set_default_string(settings, "win_class", "SDL_app")
    obs.obs_data_set_default_string(settings, "crash_win_name", "Adventure Game Studio")
    obs.obs_data_set_default_string(settings, "crash_win_class", "#32770")

def script_load(settings):
    obs.script_log(obs.LOG_DEBUG, "script_load")
    #we only initialize the scene name because we'll be running the setup_signals
    #next and we need scene_name to correctly compare against
    ags_data.scene_name = obs.obs_data_get_string(settings, "scene_name")
    ags_data.source_name = obs.obs_data_get_string(settings, "source_name")
    setup_signals()
    obs.obs_frontend_add_event_callback(on_frontend_finished_loading)

def script_properties():
    obs.script_log(obs.LOG_DEBUG, "script_properties")
    props = obs.obs_properties_create()

    obs.obs_properties_add_text(props, "scene_name", "Scene name", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "source_name", "Source name", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "steam_gameid", "Steam GameID", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "exe_name", "Executable Name", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "win_name", "Window Name", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "win_class", "Window Class", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "crash_win_name", "Crash Window Name", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "crash_win_class", "Crash Window Class", obs.OBS_TEXT_DEFAULT)

    obs.obs_properties_add_button(props, "button0", "Start QA",start_qa)

    return props

def script_update(settings):
    obs.script_log(obs.LOG_DEBUG, "script_update")
    ags_data.scene_name = obs.obs_data_get_string(settings, "scene_name")
    ags_data.source_name = obs.obs_data_get_string(settings, "source_name")
    ags_data.steam_gameid = obs.obs_data_get_string(settings, "steam_gameid")
    ags_data.exe_name = obs.obs_data_get_string(settings, "exe_name")
    ags_data.window_name = obs.obs_data_get_string(settings, "win_name")
    ags_data.window_class = obs.obs_data_get_string(settings, "win_class")
    ags_data.crash_window_name = obs.obs_data_get_string(settings, "crash_win_name")
    ags_data.crash_window_class = obs.obs_data_get_string(settings, "crash_win_class")

def create_game_capture_source(props, property):
    obs.script_log(obs.LOG_DEBUG, "create_game_capture_source")
    scene_ref = obsutil.find_scene(ags_data.scene_name)
    if not obsutil.game_capture_source_exists(scene_ref, ags_data.source_name):
        source_ref = obsutil.create_game_capture_source(scene_ref, ags_data.source_name, ags_data.game_capture_window_string)
        obs.obs_source_release(source_ref)

def setup_needs():
    obs.script_log(obs.LOG_DEBUG, "setup_needs")
    scene_ref = obsutil.find_scene(ags_data.scene_name)
    if scene_ref is None:
        obs.script_log(obs.LOG_INFO, "Scene does not exist. Will create.")
        scene_ref = obs.obs_scene_create(ags_data.scene_name)

    source_ref = None
    if not obsutil.game_capture_source_exists(scene_ref, ags_data.source_name):
        obs.script_log(obs.LOG_INFO, "Source does not exist. Will create.")
        source_ref = obsutil.create_game_capture_source(scene_ref, ags_data.source_name, ags_data.game_capture_window_string)
        obs.obs_frontend_set_current_scene(source_ref)

        scene_item_ref = obs.obs_scene_sceneitem_from_source(scene_ref, source_ref)
        if scene_item_ref:
            obsutil.reset_transform_and_crop(scene_item_ref)
            obs.obs_sceneitem_release(scene_item_ref)
        obs.obs_source_release(source_ref)

def on_scene_item_created(calldata):
    scene_item_ref = obs.calldata_sceneitem(calldata, "item")
    scene_src_ref = obs.calldata_source(calldata, "scene")
    msg = "scene item created: {item_name}".format(item_name=obs.obs.obs_source_get_name(obs.obs_sceneitem_get_source(scene_item_ref)))
    obs.script_log(obs.LOG_INFO, msg)

def on_scene_item_removed(calldata):
    scene_item_ref = obs.calldata_sceneitem(calldata, "item")
    scene_src_ref = obs.calldata_source(calldata, "scene")
    source_ref = obs.obs_sceneitem_get_source(scene_item_ref)
    msg = "scene item removed: {item_name}".format(item_name=obs.obs_source_get_name(source_ref))
    obs.script_log(obs.LOG_INFO, msg)
    sh = obs.obs_source_get_signal_handler(source_ref)
    #Signals to get
    #hooked/unhooked for game_capture
    obs.signal_handler_disconnect(sh, "item_add", on_scene_item_created)
    obs.signal_handler_disconnect(sh, "item_remove", on_scene_item_removed)
    obs.signal_handler_disconnect(sh, "item_visible", on_source_renamed)
    obs.signal_handler_disconnect(sh, "hooked", game_hooked_callback)
    obs.signal_handler_disconnect(sh, "unhooked", game_unhooked_callback)

def on_scene_item_visible(calldata):
    scene_src_ref = obs.calldata_source(calldata, "scene")
    scene_item_ref = obs.calldata_sceneitem(calldata, "item")
    visible = obs.calldata_bool(calldata, "visible")
    msg = "scene item: {item_name} state: {visibility}".format(item_name=obs.obs_source_get_name(obs.obs_sceneitem_get_source(scene_item_ref)), visibility=visible)
    obs.script_log(obs.LOG_INFO, msg)

def on_source_created(calldata):
    source_ref = obs.calldata_source(calldata, "source")
    source_name = obs.obs_source_get_name(source_ref)
    msg = "source created: {source_name}".format(source_name=source_name)
    obs.script_log(obs.LOG_INFO, msg)

    if (obs.obs_source_get_type(source_ref) == obs.OBS_SOURCE_TYPE_SCENE and
        source_name == ags_data.source_name):
        print("Hooking signals for {source_name} source".format(source_name=source_name))
        sh = obs.obs_source_get_signal_handler(source_ref)
        obs.signal_handler_connect(sh, "item_add", on_scene_item_created)
        obs.signal_handler_connect(sh, "item_remove", on_scene_item_removed)
        obs.signal_handler_connect(sh, "item_visible", on_scene_item_visible)
        obs.signal_handler_connect(sh, "hooked", game_hooked_callback)
        obs.signal_handler_connect(sh, "unhooked", game_unhooked_callback)

def on_source_destroyed(calldata):
    source_ref = obs.calldata_source(calldata,"source")
    source_name = obs.obs_source_get_name(source_ref)
    msg = "source destroyed: {source_name}".format(source_name=source_name)
    obs.script_log(obs.LOG_INFO, msg)

    if (obs.obs_source_get_type(source_ref) == obs.OBS_SOURCE_TYPE_SCENE and
        source_name == ags_data.source_name):
        sh = obs.obs_source_get_signal_handler(source_ref)
        obs.signal_handler_disconnect(sh, "item_add", on_scene_item_created)
        obs.signal_handler_disconnect(sh, "item_remove", on_scene_item_removed)
        obs.signal_handler_disconnect(sh, "item_visible", on_scene_item_visible)
        obs.signal_handler_disconnect(sh, "hooked", game_hooked_callback)
        obs.signal_handler_disconnect(sh, "unhooked", game_unhooked_callback)

def on_source_removed(calldata):
    # source_ref = obs.calldata_source(calldata,"source")
    # msg = "deactivated: {source_name}".format(source_name=obs.obs_source_get_name(source_ref))
    # obs.script_log(obs.LOG_INFO, msg)
    pass

def on_source_renamed(calldata):
    source_ref = obs.calldata_source(calldata,"source")
    prev_name = obs.calldata_get_string(calldata, "prev_name")
    new_name = obs.calldata_get_string(calldata, "new_name")
    msg = "source renamed: {source_name} from {old} to {new}".format(source_name=obs.obs_source_get_name(source_ref), old=prev_name, new=new_name)
    obs.script_log(obs.LOG_INFO, msg)

def source_show_callback(calldata):
    source_ref = obs.calldata_source(calldata,"source")
    msg = "shown: {source_name}".format(source_name=obs.obs_source_get_name(source_ref))
    obs.script_log(obs.LOG_INFO, msg)

def source_hide_callback(calldata):
    source_ref = obs.calldata_source(calldata,"source")
    msg = "hidden: {source_name}".format(source_name=obs.obs_source_get_name(source_ref))
    obs.script_log(obs.LOG_INFO, msg)

def game_hooked_callback(calldata):
    source_ref = obs.calldata_source(calldata,"source")
    game_title = obs.calldata_string(calldata,"title")
    game_class = obs.calldata_string(calldata,"class")
    game_executable = obs.calldata_string(calldata,"executable")
    msg = "hooked: {source_name}, game_title: {game_title}, game_class: {game_class}, game_executable: {game_executable}".format(source_name=obs.obs_source_get_name(source_ref),game_title=
    game_title, game_class=game_class, game_executable=game_executable)
    obs.script_log(obs.LOG_INFO, msg)

    source_width = obs.obs_source_get_width(source_ref)
    source_height = obs.obs_source_get_height(source_ref)

    print("Window Res: ", source_width, "x", source_height)

    #obsutil.config_set_base_resolution(source_width, source_height)
    #obsutil.config_set_output_resolution(source_width, source_height)
    obsutil.set_rescale_resolution(source_width, source_height, obsutil.ScaleType.LANCZOS)

    output = obs.obs_frontend_get_recording_output()
    obs.obs_output_set_preferred_size(output, source_width, source_height)
    obs.obs_output_release(output)
    
    scene_ref = obsutil.find_scene(ags_data.scene_name)
    scene_item_ref = obsutil.find_scene_item(scene_ref, ags_data.source_name)
    base_resolution = obsutil.config_get_base_resolution()
    obsutil.reset_transform_and_crop(scene_item_ref, base_resolution.x, base_resolution.y)

    global proc
    if proc is None:
        proc = gameutil.find_processid_by_name(ags_data.exe_name)

def game_unhooked_callback(calldata):
    source = obs.calldata_source(calldata,"source")
    obs.script_log(obs.LOG_INFO, "unhooked: "+ obs.obs_source_get_name(source))

    global proc
    if proc is not None and proc.is_running():
        proc_state = did_qa_crash(proc)
        if proc_state:
            obs.script_log(obs.LOG_ERROR, "Application Crashed")
            proc = None
    else: #hopefully when the process has exited normally
        proc = None

def setup_signals():
    obs.script_log(obs.LOG_DEBUG, "setup_signals")
    
    gsh = obs.obs_get_signal_handler()
    obs.signal_handler_connect(gsh, "source_create", on_source_created)
    obs.signal_handler_connect(gsh, "source_destroy", on_source_destroyed)
    # obs.signal_handler_connect(gsh, "source_remove", on_source_removed)
    obs.signal_handler_connect(gsh, "source_rename", on_source_renamed)

    for scene_a_s in obs.obs_frontend_get_scenes():
        scene_name = obs.obs_source_get_name(scene_a_s)
        print("setup signals, scene name:" +scene_name)
        print("ags_data.scene_name:"+ags_data.scene_name)
        if(scene_name == ags_data.scene_name):
            obs.script_log(obs.LOG_DEBUG, "Hooking Signals for {source_name}".format(source_name = scene_name))
            sh = obs.obs_source_get_signal_handler(scene_a_s)
            obs.signal_handler_connect(sh, "item_add", on_scene_item_created)
            obs.signal_handler_connect(sh, "item_remove", on_scene_item_removed)
            obs.signal_handler_connect(sh, "item_visible", on_scene_item_visible)
            
            scene_item_ref = obsutil.find_scene_item(obs.obs_scene_from_source(scene_a_s), ags_data.source_name)
            source_ref = obs.obs_sceneitem_get_source(scene_item_ref)
            source_name = obs.obs_source_get_name(source_ref)
            print("source_name: "+source_name+" ags_data.source_name:"+ags_data.source_name)
            if(source_name == ags_data.source_name):
                ssh = obs.obs_source_get_signal_handler(source_ref)
                obs.signal_handler_connect(ssh, "hooked", game_hooked_callback)
                obs.signal_handler_connect(ssh, "unhooked", game_unhooked_callback)

        obs.obs_source_release(scene_a_s)

def unset_signals():
    obs.script_log(obs.LOG_DEBUG, "unset_signals")

    gsh = obs.obs_get_signal_handler()
    obs.signal_handler_disconnect(gsh, "source_create", on_source_created)
    obs.signal_handler_disconnect(gsh, "source_destroy", on_source_destroyed)
    # obs.signal_handler_disconnect(gsh, "source_remove", on_source_removed)
    obs.signal_handler_disconnect(gsh, "source_rename", on_source_renamed)

    for scene_a_s in obs.obs_frontend_get_scenes():
        scene_name = obs.obs_source_get_name(scene_a_s)
        if(scene_name == ags_data.scene_name):
            obs.script_log(obs.LOG_DEBUG, "Unhooking Signals for {source_name}".format(source_name = scene_name))
            sh = obs.obs_source_get_signal_handler(scene_a_s)
            obs.signal_handler_disconnect(sh, "item_add", on_scene_item_created)
            obs.signal_handler_disconnect(sh, "item_remove", on_scene_item_removed)
            obs.signal_handler_disconnect(sh, "item_visible", on_scene_item_visible)
            
            scene_item_ref = obsutil.find_scene_item(obs.obs_scene_from_source(scene_a_s), ags_data.source_name)
            source_ref = obs.obs_sceneitem_get_source(scene_item_ref)
            source_name = obs.obs_source_get_name(source_ref)
            print("source_name: "+source_name+" ags_data.source_name:"+ags_data.source_name)
            if(source_name == ags_data.source_name):
                ssh = obs.obs_source_get_signal_handler(source_ref)
                obs.signal_handler_disconnect(ssh, "hooked", game_hooked_callback)
                obs.signal_handler_disconnect(ssh, "unhooked", game_unhooked_callback)

        obs.obs_source_release(scene_a_s)

def did_qa_crash(proc: psutil.Process) -> bool:
    app_status = None
    if proc is not None:
        # while(True):
        app_status = gameutil.get_process_status(proc, ags_data.window_name, ags_data.window_class, ags_data.crash_window_name, ags_data.crash_window_class)
            # if app_status != psutil.STATUS_RUNNING:
            #     break
        if app_status == psutil.STATUS_STOPPED:
            #obs.script_log(obs.LOG_INFO, "App Crashed")
            return True
        elif app_status == psutil.STATUS_DEAD:
            #obs.script_log(obs.LOG_INFO, "App Exited")
            return False
    return False

def findWindow(pid):
    found_hwnd = None
    def enumHandler(hwnd, lParam):
        if win32gui.IsWindowVisible(hwnd):
            thread_id, process_id = win32process.GetWindowThreadProcessId(hwnd)
            if(process_id == pid):
                nonlocal found_hwnd
                found_hwnd = hwnd

    win32gui.EnumWindows(enumHandler, None)
    return found_hwnd

def find_proc():
    global proc
    global ags_data
    proc = gameutil.find_processid_by_name(ags_data.exe_name)
    if proc is not None:
        #print("process found: "+ str(proc.pid))
        game_hwnd = findWindow(proc.pid)

        ags_data.window_name = win32gui.GetWindowText(game_hwnd)
        ags_data.window_class = win32gui.GetClassName(game_hwnd)
        window_string = ags_data.get_game_capture_window_string(proc)
        #print("Discovered window name: "+ags_data.window_name)

        scene_ref = obsutil.find_scene(ags_data.scene_name)
        scene_item_ref = obsutil.find_scene_item(scene_ref, ags_data.source_name)
        source_ref = obs.obs_sceneitem_get_source(scene_item_ref)
        settings = obs.obs_source_get_settings(source_ref)

        obs.obs_data_set_string(settings, "window", window_string)
        obs.obs_source_update(source_ref, settings)
        obs.obs_data_release(settings)
    obs.remove_current_callback()

def start_qa(props, property):
    obs.script_log(obs.LOG_DEBUG, "start_qa")
    scene_ref = obsutil.find_scene(ags_data.scene_name)
    scene_source_ref = obs.obs_scene_get_source(scene_ref)
    obs.obs_frontend_set_current_scene(scene_source_ref)
    scene_item_ref = obsutil.find_scene_item(scene_ref, ags_data.source_name)
    obs.obs_sceneitem_select(scene_item_ref, True)
   
    gameutil.run_steam_game(ags_data.window_name, ags_data.steam_gameid)

    obs.timer_add(find_proc, 4000)
    
def on_frontend_finished_loading(event):
    msg = "on_frontend_finished_loading: "+ obs_frontend_event(event).name
    obs.script_log(obs.LOG_DEBUG, msg)
    if event == obs.OBS_FRONTEND_EVENT_FINISHED_LOADING:
        setup_needs()
    elif event == obs.OBS_FRONTEND_EVENT_RECORDING_STARTING:
        obs.script_log(obs.LOG_DEBUG, "Recording Starting")
    elif event == obs.OBS_FRONTEND_EVENT_RECORDING_STARTED:
        obs.script_log(obs.LOG_DEBUG, "Recording Started")
    elif event == obs.OBS_FRONTEND_EVENT_RECORDING_STOPPING:
        obs.script_log(obs.LOG_DEBUG, "Recording Stopping")
    elif event == obs.OBS_FRONTEND_EVENT_RECORDING_STOPPED:
        obs.script_log(obs.LOG_DEBUG, "Recording Stopped")
    elif event == obs.OBS_FRONTEND_EVENT_RECORDING_PAUSED:
        obs.script_log(obs.LOG_DEBUG, "Recording Paused")
    elif event == obs.OBS_FRONTEND_EVENT_RECORDING_UNPAUSED:
        obs.script_log(obs.LOG_DEBUG, "Recording Unpaused")

def print_video_settings(props, property):
    print("print_video_settings")
    vid_settings = obs.obs_video_info()
    obs.obs_get_video_info(vid_settings)
    print("FPS numenator: ", str(vid_settings.fps_num))
    print("FPS denominator: ", str(vid_settings.fps_den))
    print("Base Res Width: ", str(vid_settings.base_width))
    print("Base Res Height: ", str(vid_settings.base_height))
    print("Output Res Width: ", str(vid_settings.output_width))
    print("Output Res Height: ", str(vid_settings.output_height))
    print("Output Format: ", str(vid_settings.output_format))
    print("Adapter: ", str(vid_settings.adapter))
    print("Gpu Conversion: ", str(vid_settings.gpu_conversion))
    print("Colorspace Type: ", str(vid_settings.colorspace))
    print("Video Range Type: ", str(vid_settings.range))
    print("Scale Type: ", str(vid_settings.scale_type))

def script_unload():
    obs.script_log(obs.LOG_DEBUG, "script_unload")
    unset_signals()
    obs.obs_frontend_remove_event_callback(on_frontend_finished_loading)
    global proc
    if proc is not None and proc.is_running():
        proc.kill()