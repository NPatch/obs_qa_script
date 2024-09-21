import obspython as obs
import math, time
#import os
import obsutil, gameutil

oldskies_scene_name = "Old Skies Scene"
oldskies_scene_source_name = "Old Skies"
oldskies_capture_window_name = "[OldSkies.exe]: Old Skies"
oldskies_capture_window_string = "Old Skies:SDL_app:OldSkies.exe"
oldskies_game_proc_name = "OldSkies.exe"
oldskies_proc_main_window_name = "Old Skies"
oldskies_proc_main_window_class = "SDL_app"
oldskies_proc_crash_window_name = "Adventure Game Studio"
oldskies_proc_crash_window_class = "#32770"
oldskies_steam_gameid = 1346360

proc = None
proc_result = None
last_app_status = None

qa_started = False
game_app_hooked = False

# Description displayed in the Scripts dialog window
def script_description():
  return """<center><h2>Old Skies QA Tools</h2></center>
            <p>Tools that automate and help in QA testing Old Skies</p>"""

# def script_defaults(settings):
#     print("script_defaults")

def script_load(settings):
    obs.script_log(obs.LOG_INFO, "script_load")
    obs.obs_frontend_add_event_callback(on_frontend_finished_loading)

# def script_update(settings):
#     print("script_update")

def script_properties():
    obs.script_log(obs.LOG_INFO, "script_properties")
    props = obs.obs_properties_create()

    obs.obs_properties_add_button(props, "button0", "Start QA",start_qa)
    obs.obs_properties_add_button(props, "button1", "Print Scene Info",print_scene_info)
    obs.obs_properties_add_button(props, "button2", "Enum Scene Items",enum_scene_items)
    obs.obs_properties_add_button(props, "button3", "Create Source",create_game_capture_source)
    #obs.obs_properties_add_button(props, "button1", "Start QA:",start_qa)
    return props

def print_scene_info(props, property):
    obsutil.print_scene_info(oldskies_scene_name)

def enum_scene_items(props, property):
    obsutil.enum_scene_items(oldskies_scene_name)

def create_game_capture_source(props, property):
    obs.script_log(obs.LOG_INFO, "create_game_capture_source")
    scene_ref = obsutil.find_scene(oldskies_scene_name)
    if not obsutil.game_capture_source_exists(scene_ref, oldskies_scene_source_name):
        source_ref = obsutil.create_game_capture_source(scene_ref, oldskies_scene_source_name, oldskies_capture_window_string)
        obs.obs_source_release(source_ref)

def setup_needs():
    obs.script_log(obs.LOG_INFO, "setup_needs")
    scene_ref = obsutil.find_scene(oldskies_scene_name)
    if scene_ref is None:
        obs.script_log(obs.LOG_INFO, "Scene does not exist. Will create.")
        scene_ref = obs.obs_scene_create(oldskies_scene_name)

    source_ref = None
    if not obsutil.game_capture_source_exists(scene_ref, oldskies_scene_source_name):
        obs.script_log(obs.LOG_INFO, "Source does not exist. Will create.")
        source_ref = obsutil.create_game_capture_source(scene_ref, oldskies_scene_source_name, oldskies_capture_window_string)
        obs.obs_frontend_set_current_scene(source_ref)
        obs.obs_source_release(source_ref)

def setup_signals():
    obs.script_log(obs.LOG_INFO, "setup_signals")
    scene_ref = obsutil.find_scene(oldskies_scene_name)
    scene_item_ref = obsutil.find_scene_item(scene_ref, oldskies_scene_source_name)
    source_ref = obs.obs_sceneitem_get_source(scene_item_ref)
    signal_handler = obs.obs_source_get_signal_handler(source_ref)
    #Signals to get
    #source_activate/deactivate
    obs.signal_handler_connect(signal_handler,"source_activated",source_activated_callback)
    obs.signal_handler_connect(signal_handler,"source_deactivated",source_activated_callback)
    #hooked/unhooked for game_capture
    obs.signal_handler_connect(signal_handler,"hooked",game_hooked_callback)
    obs.signal_handler_connect(signal_handler,"unhooked",game_unhooked_callback)
    #obs.obs_scene_release(scene_ref)

def unset_signals():
    obs.script_log(obs.LOG_INFO, "unset_signals")
    scene_ref = obsutil.find_scene(oldskies_scene_name)
    scene_item_ref = obsutil.find_scene_item(scene_ref, oldskies_scene_source_name)
    source_ref = obs.obs_sceneitem_get_source(scene_item_ref)
    signal_handler = obs.obs_source_get_signal_handler(source_ref)
    #Signals to get
    #source_activate/deactivate
    obs.signal_handler_disconnect(signal_handler,"source_activated",source_activated_callback)
    obs.signal_handler_disconnect(signal_handler,"source_deactivated",source_activated_callback)
    #hooked/unhooked for game_capture
    obs.signal_handler_disconnect(signal_handler,"hooked",game_hooked_callback)
    obs.signal_handler_disconnect(signal_handler,"unhooked",game_unhooked_callback)
    #obs.obs_scene_release(scene_ref)

def source_activated_callback(calldata):
    source = obs.calldata_source(calldata,"source")
    obs.script_log(obs.LOG_INFO, "activated: ", obs.obs_source_get_name(source))

def source_deactivated_callback(calldata):
    source = obs.calldata_source(calldata,"source")
    obs.script_log(obs.LOG_INFO, "deactivated: ", obs.obs_source_get_name(source))

def game_hooked_callback(calldata):
    source = obs.calldata_source(calldata,"source")
    game_title = obs.calldata_source(calldata,"title")
    game_class = obs.calldata_source(calldata,"class")
    game_executable = obs.calldata_source(calldata,"executable")
    msg = "hooked: {source_name}, game_title: {game_title}, game_class: {game_class}, game_executable: {game_executable}".format(source_name=obs.obs_source_get_name(source),game_title=
    game_title, game_class=game_class, game_executable=game_executable)
    obs.script_log(obs.LOG_INFO, msg)

    global game_app_hooked
    game_app_hooked = True

    global proc
    proc = gameutil.find_processid_by_name(oldskies_game_proc_name)

def game_unhooked_callback(calldata):
    source = obs.calldata_source(calldata,"source")
    print("unhooked: ", obs.obs_source_get_name(source))
    obs.script_log(obs.LOG_INFO, "unhooked: ", obs.obs_source_get_name(source))

    global game_app_hooked
    game_app_hooked = False

    unset_signals()

def script_tick(seconds):
    if qa_started and game_app_hooked:
        #start recording
        app_status = None
        global proc, last_app_status
        if proc is not None:
            while(True):
                app_status = gameutil.get_process_status(proc, oldskies_proc_main_window_name, oldskies_proc_main_window_class, oldskies_proc_crash_window_name, oldskies_proc_crash_window_class)
                if app_status != psutil.STATUS_RUNNING:
                    break
            print(str(last_app_status), " " + str(app_status))
            if last_app_status is not app_status:
                    if app_status == psutil.STATUS_STOPPED:
                        print("App Crashed")
                    last_app_status = app_status
            # elif app_status == psutil.STATUS_DEAD:
            #     print("App Exited")

def start_qa(props, property):
    obs.script_log(obs.LOG_INFO, "start_qa")
    scene_ref = obsutil.find_scene(oldskies_scene_name)
    scene_source_ref = obs.obs_scene_get_source(scene_ref)
    obs.obs_frontend_set_current_scene(scene_source_ref)
    scene_item_ref = obsutil.find_scene_item(scene_ref, oldskies_scene_source_name)
    obs.obs_sceneitem_select(scene_item_ref, True)
    #source_ref = obs.obs_sceneitem_get_source(scene_item_ref)
    #obs.obs_frontend_set_current_scene(source_ref)
    setup_signals()
    gameutil.run_steam_game(oldskies_proc_main_window_name, oldskies_steam_gameid)
    global qa_started
    qa_started = True
    last_app_status = None
    
def on_frontend_finished_loading(event):
    obs.script_log(obs.LOG_INFO, "on_frontend_finished_loading: ", str(event))
    if event == obs.OBS_FRONTEND_EVENT_FINISHED_LOADING:
        setup_needs()

#def script_unload():
#   obs.script_log(obs.LOG_INFO, "script_unload")
#    unset_signals()