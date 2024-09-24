import obspython as obs
import math, time
#import os
import psutil
import obsutil, gameutil
import gamedata as gd

# oldskies_scene_name = "Old Skies Scene"
# oldskies_scene_source_name = "Old Skies"

# #oldskies_capture_window_name = "[OldSkies.exe]: Old Skies"
# oldskies_steam_gameid = 1346360
# oldskies_game_proc_name = "OldSkies.exe"
# oldskies_proc_main_window_name = "Old Skies"
# oldskies_proc_main_window_class = "SDL_app"

# oldskies_capture_window_string = "{winname}:{winclass}:{exename}".format(winname=oldskies_proc_main_window_name,winclass=oldskies_proc_main_window_class, exename=oldskies_game_proc_name)

# oldskies_proc_crash_window_name = "Adventure Game Studio"
# oldskies_proc_crash_window_class = "#32770"

ags_data = gd.AGSGameData()

proc = None
proc_result = None
last_app_status = None

# Description displayed in the Scripts dialog window
def script_description():
  return """<center><h2>Old Skies QA Tools</h2></center>
            <p>Tools that automate and help in QA testing AGS games</p>"""

def script_defaults(settings):
    obs.script_log(obs.LOG_INFO, "script_defaults")
    obs.obs_data_set_default_string(settings, "scene_name", "")
    obs.obs_data_set_default_string(settings, "source_name", "")
    obs.obs_data_set_default_int(settings, "steam_gameid", 0)
    obs.obs_data_set_default_string(settings, "exe_name", "")
    obs.obs_data_set_default_string(settings, "win_name", "")
    obs.obs_data_set_default_string(settings, "win_class", "")
    obs.obs_data_set_default_string(settings, "crash_win_name", "")
    obs.obs_data_set_default_string(settings, "crash_win_name", "")

def script_load(settings):
    obs.script_log(obs.LOG_INFO, "script_load")
    obs.obs_frontend_add_event_callback(on_frontend_finished_loading)

def script_properties():
    obs.script_log(obs.LOG_INFO, "script_properties")
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
    obs.script_log(obs.LOG_INFO, "script_update")
    ags_data.scene_name = obs.obs_data_get_string(settings, "scene_name")
    ags_data.source_name = obs.obs_data_get_string(settings, "source_name")
    ags_data.steam_gameid = obs.obs_data_get_string(settings, "steam_gameid")
    ags_data.exe_name = obs.obs_data_get_string(settings, "exe_name")
    ags_data.window_name = obs.obs_data_get_string(settings, "win_name")
    ags_data.window_class = obs.obs_data_get_string(settings, "win_class")
    ags_data.crash_window_name = obs.obs_data_get_string(settings, "crash_win_name")
    ags_data.crash_window_class = obs.obs_data_get_string(settings, "crash_win_class")

def create_game_capture_source(props, property):
    obs.script_log(obs.LOG_INFO, "create_game_capture_source")
    scene_ref = obsutil.find_scene(ags_data.scene_name)
    if not obsutil.game_capture_source_exists(scene_ref, ags_data.source_name):
        source_ref = obsutil.create_game_capture_source(scene_ref, ags_data.source_name, ags_data.game_capture_window_string)
        obs.obs_source_release(source_ref)

def setup_needs():
    obs.script_log(obs.LOG_INFO, "setup_needs")
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

def setup_signals():
    obs.script_log(obs.LOG_INFO, "setup_signals")
    scene_ref = obsutil.find_scene(ags_data.scene_name)
    scene_item_ref = obsutil.find_scene_item(scene_ref, ags_data.source_name)
    source_ref = obs.obs_sceneitem_get_source(scene_item_ref)
    signal_handler = obs.obs_source_get_signal_handler(source_ref)
    #Signals to get
    #source_activate/deactivate
    # obs.signal_handler_connect(signal_handler,"source_activated",source_activated_callback)
    # obs.signal_handler_connect(signal_handler,"source_deactivated",source_activated_callback)
    #hooked/unhooked for game_capture
    obs.signal_handler_connect(signal_handler,"hooked",game_hooked_callback)
    obs.signal_handler_connect(signal_handler,"unhooked",game_unhooked_callback)

def unset_signals():
    obs.script_log(obs.LOG_INFO, "unset_signals")
    scene_ref = obsutil.find_scene(ags_data.scene_name)
    scene_item_ref = obsutil.find_scene_item(scene_ref, ags_data.source_name)
    source_ref = obs.obs_sceneitem_get_source(scene_item_ref)
    signal_handler = obs.obs_source_get_signal_handler(source_ref)
    #Signals to get
    #source_activate/deactivate
    # obs.signal_handler_disconnect(signal_handler,"source_activated",source_activated_callback)
    # obs.signal_handler_disconnect(signal_handler,"source_deactivated",source_activated_callback)
    # #hooked/unhooked for game_capture
    obs.signal_handler_disconnect(signal_handler,"hooked",game_hooked_callback)
    obs.signal_handler_disconnect(signal_handler,"unhooked",game_unhooked_callback)

def source_activated_callback(calldata):
    source = obs.calldata_source(calldata,"source")
    obs.script_log(obs.LOG_INFO, "activated: ", obs.obs_source_get_name(source))

def source_deactivated_callback(calldata):
    source = obs.calldata_source(calldata,"source")
    obs.script_log(obs.LOG_INFO, "deactivated: ", obs.obs_source_get_name(source))

def game_hooked_callback(calldata):
    source = obs.calldata_source(calldata,"source")
    game_title = obs.calldata_string(calldata,"title")
    game_class = obs.calldata_string(calldata,"class")
    game_executable = obs.calldata_string(calldata,"executable")
    msg = "hooked: {source_name}, game_title: {game_title}, game_class: {game_class}, game_executable: {game_executable}".format(source_name=obs.obs_source_get_name(source),game_title=
    game_title, game_class=game_class, game_executable=game_executable)
    obs.script_log(obs.LOG_INFO, msg)

    # scene_ref = obsutil.find_scene(oldskies_scene_name)
    # scene_item_ref = obsutil.find_scene_item(scene_ref, oldskies_scene_source_name)
    # source_ref = obs.obs_sceneitem_get_source(scene_item_ref)
    # signal_handler = obs.obs_source_get_signal_handler(source_ref)
    # obs.signal_handler_disconnect(signal_handler,"hooked",game_hooked_callback)
    # obs.signal_handler_connect(signal_handler,"unhooked",game_unhooked_callback)
    global proc
    proc = gameutil.find_processid_by_name(ags_data.exe_name)

def game_unhooked_callback(calldata):
    source = obs.calldata_source(calldata,"source")
    obs.script_log(obs.LOG_INFO, "unhooked: "+ obs.obs_source_get_name(source))

    global proc
    proc_state = did_qa_crash(proc)
    if proc_state:
        obs.script_log(obs.LOG_ERROR, "Application Crashed")
    proc = None

    # scene_ref = obsutil.find_scene(oldskies_scene_name)
    # scene_item_ref = obsutil.find_scene_item(scene_ref, oldskies_scene_source_name)
    # source_ref = obs.obs_sceneitem_get_source(scene_item_ref)
    # signal_handler = obs.obs_source_get_signal_handler(source_ref)
    # obs.signal_handler_disconnect(signal_handler,"unhooked",game_unhooked_callback)
    unset_signals()

def did_qa_crash(proc: psutil.Process) -> bool:
    app_status = None
    if proc is not None:
        while(True):
            app_status = gameutil.get_process_status(proc, ags_data.window_name, ags_data.window_class, ags_data.crash_window_name, ags_data.crash_window_class)
            if app_status != psutil.STATUS_RUNNING:
                break
        if app_status == psutil.STATUS_STOPPED:
            #obs.script_log(obs.LOG_INFO, "App Crashed")
            return True
        elif app_status == psutil.STATUS_DEAD:
            #obs.script_log(obs.LOG_INFO, "App Exited")
            return False

def start_qa(props, property):
    obs.script_log(obs.LOG_INFO, "start_qa")
    scene_ref = obsutil.find_scene(ags_data.scene_name)
    scene_source_ref = obs.obs_scene_get_source(scene_ref)
    obs.obs_frontend_set_current_scene(scene_source_ref)
    scene_item_ref = obsutil.find_scene_item(scene_ref, ags_data.source_name)
    obs.obs_sceneitem_select(scene_item_ref, True)
    setup_signals()
    gameutil.run_steam_game(ags_data.window_name, ags_data.steam_gameid)
    
def on_frontend_finished_loading(event):
    obs.script_log(obs.LOG_INFO, "on_frontend_finished_loading: ")
    if event == obs.OBS_FRONTEND_EVENT_FINISHED_LOADING:
        setup_needs()

def script_unload():
    obs.script_log(obs.LOG_INFO, "script_unload")
    #unset_signals()