import obspython as obs
import math, time
import os, subprocess

oldskies_scene_name = "Old Skies Scene"
scene = None
proc = None
proc_result = None

# Description displayed in the Scripts dialog window
def script_description():
  return """<center><h2>Old Skies QA Tools</h2></center>
            <p>Tools that automate and help in QA testing Old Skies</p>"""



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

def find_scene(scene_name):
    local_scene = None
    scenes = obs.obs_frontend_get_scenes()
    if scenes is None:
        print("Scenes Collection is None")
    for iscene in scenes:
        name = obs.obs_source_get_name(iscene)
        print("SceneName:"+name)
        if name == scene_name:
            print("Old Skies Scene exists. Will reference.")
            local_scene = iscene
            break
    obs.source_list_release(scenes)
    return local_scene

def find_or_create_scene(scene_name):
    scene = find_scene(oldskies_scene_name)
    if scene is None:
        print("Old Skies scene does not exist. Will create.")
        scene = obs.obs_scene_create(oldskies_scene_name)


def PrintSceneInfo(scene):
    source = obs.obs_get_source_by_name(scene)
    settings = obs.obs_source_get_settings(source)
    psettings = obs.obs_source_get_private_settings(source)
    dsettings = obs.obs_data_get_defaults(settings)
    pdsettings = obs.obs_data_get_defaults(psettings)
    print("[---------- settings ----------")
    print(obs.obs_data_get_json(settings))
    print("---------- private_settings ----------")
    print(obs.obs_data_get_json(psettings))
    print("---------- default settings for this source type ----------")
    print(obs.obs_data_get_json(dsettings))
    print("---------- default private settings for this source type ----------")
    print(obs.obs_data_get_json(pdsettings))
    print("[--------- filter names --------")
    for i in range(filter_count):
        settings = obs.obs_data_array_item(filters, i)
        filter_name = obs.obs_data_get_string(settings, "name")
        obs.obs_data_release(settings)
        print(filter_name)
    print(" filter names of %s --------" % scene)

def script_defaults(settings):
    print("script_defaults")

def script_load(settings):
    print("script_load")
    obs.obs_frontend_add_event_callback(on_frontend_finished_loading)

def script_update(settings):
    print("script_update")

def script_properties():
    props = obs.obs_properties_create()

    obs.obs_properties_add_button(props, "button1", "Start QA:",start_qa)
    return props

#def script_tick(seconds):

def start_qa(props, property):
    RunGame()
    print("HAHA")

def on_frontend_finished_loading(event):
    global scene
    if event == obs.OBS_FRONTEND_EVENT_FINISHED_LOADING:
        scene = find_or_create_scene(oldskies_scene_name)


def script_unload():
    if scene is not None:
        obs.obs_scene_release(scene)