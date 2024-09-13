import obspython as obs
import math, time
import os, subprocess

import obsutil

oldskies_scene_name = "Old Skies Scene"
scene = None
proc = None
proc_result = None
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

def on_frontend_finished_loading(event):
    global scene
    if event == obs.OBS_FRONTEND_EVENT_FINISHED_LOADING:
        scene = find_or_create_scene(oldskies_scene_name)


def script_unload():
