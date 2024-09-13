import obspython as obs
import math, time
import os, subprocess

import obsutil

oldskies_scene_name = "Old Skies Scene"
oldskies_scene_source_name = "Old Skies"
oldskies_capture_window_name = "[OldSkies.exe]: Old Skies"
oldskies_capture_window_string = "Old Skies:SDL_app:OldSkies.exe"

# Description displayed in the Scripts dialog window
def script_description():
  return """<center><h2>Old Skies QA Tools</h2></center>
            <p>Tools that automate and help in QA testing Old Skies</p>"""

# def script_defaults(settings):
#     print("script_defaults")

def script_load(settings):
    print("script_load")
    obs.obs_frontend_add_event_callback(on_frontend_finished_loading)

# def script_update(settings):
#     print("script_update")

def script_properties():
    props = obs.obs_properties_create()

    obs.obs_properties_add_button(props, "button0", "Start QA",start_qa)
    obs.obs_properties_add_button(props, "button1", "Print Scene Info",print_scene_info)
    obs.obs_properties_add_button(props, "button2", "Enum Scene Items",enum_scene_items)
    obs.obs_properties_add_button(props, "button3", "Create Source",create_game_capture_source)
    #obs.obs_properties_add_button(props, "button1", "Start QA:",start_qa)
    return props

#def script_tick(seconds):

def print_scene_info(props, property):
    obsutil.print_scene_info(oldskies_scene_name)

def enum_scene_items(props, property):
    obsutil.enum_scene_items(oldskies_scene_name)

def create_game_capture_source(props, property):
    scene_ref = obsutil.find_scene(oldskies_scene_name)
    if not obsutil.game_capture_source_exists(scene_ref, oldskies_scene_source_name):
        source_ref = obsutil.create_game_capture_source(scene_ref, oldskies_scene_source_name, oldskies_capture_window_string)
        obs.obs_source_release(source_ref)

def setup_needs():
    scene_ref = obsutil.find_scene(oldskies_scene_name)
    if scene_ref is None:
        print("Scene does not exist. Will create.")
        scene_ref = obs.obs_scene_create(oldskies_scene_name)

    source_ref = None
    if not obsutil.game_capture_source_exists(scene_ref, oldskies_scene_source_name):
        print("Source does not exist. Will create.")
        source_ref = obsutil.create_game_capture_source(scene_ref, oldskies_scene_source_name, oldskies_capture_window_string)
        obs.obs_source_release(source_ref)

def setup_signals():
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


def source_activated_callback(calldata):
    source = obs.calldata_source(calldata,"source")
    print("activated: ", obs.obs_source_get_name(source))

def source_deactivated_callback(calldata):
    source = obs.calldata_source(calldata,"source")
    print("deactivated: ", obs.obs_source_get_name(source))

def game_hooked_callback(calldata):
    source = obs.calldata_source(calldata,"source")
    game_title = obs.calldata_source(calldata,"title")
    game_class = obs.calldata_source(calldata,"class")
    game_executable = obs.calldata_source(calldata,"executable")
    print("hooked: ", obs.obs_source_get_name(source),
    ",", game_title, ",", game_class, ",", game_executable)

def game_unhooked_callback(calldata):
    source = obs.calldata_source(calldata,"source")
    print("unhooked: ", obs.obs_source_get_name(source))


def RunGame():
    print("Running Old Skies")
    steamCommand = "steam"
    steamOldSkiesParameter = "steam://rungameid/1346360"
    #subprocess.call([steamCommand, steamOldSkiesParameter])
    global proc
    proc = subprocess.run(
        executable = steamCommand,
        args = steamOldSkiesParameter,
        capture_output=True,
        # avoid having to explicitly encode
        text=True)
    data = proc.stdout
    global proc_result
    proc_result = proc.returncode

def start_qa(props, property):
    scene_ref = obsutil.find_scene(oldskies_scene_name)
    source_ref = obs.obs_scene_get_source(scene_ref)
    obs.obs_frontend_set_current_scene(source_ref)
    
    #RunGame()
    
def on_frontend_finished_loading(event):
    if event == obs.OBS_FRONTEND_EVENT_FINISHED_LOADING:
        setup_needs()
        setup_signals()

def script_unload():
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