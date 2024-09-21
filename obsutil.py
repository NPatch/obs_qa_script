import obspython as obs
import math, time
from enum import Enum

source_property_types = [
    "OBS_PROPERTY_INVALID",
    "OBS_PROPERTY_BOOL",
    "OBS_PROPERTY_INT",
    "OBS_PROPERTY_FLOAT",
    "OBS_PROPERTY_TEXT",
    "OBS_PROPERTY_PATH",
    "OBS_PROPERTY_LIST",
    "OBS_PROPERTY_COLOR",
    "OBS_PROPERTY_BUTTON",
    "OBS_PROPERTY_FONT",
    "OBS_PROPERTY_EDITABLE_LIST",
    "OBS_PROPERTY_FRAME_RATE",
    "OBS_PROPERTY_GROUP",
]

def find_scene(scene_name : str):
    """
    finds and returns an obs_scene_t*

    Returns: obs_scene_t*, does **not require release**

    ##### obs API responsibilities
    * Uses [obs_frontend_get_scenes](https://docs.obsproject.com/reference-frontend-api#c.obs_frontend_get_scenes) which **requires release** through [source_list_release](https://docs.obsproject.com/scripting#source_list_release).

    * Uses [obs_source_get_name](https://docs.obsproject.com/reference-sources#c.obs_source_get_name) which doesn't increase the ref count.

    * Uses [obs_scene_from_source](https://docs.obsproject.com/reference-scenes#c.obs_scene_from_source) which doesn't increase ref count.
    """
    scene_ref = None
    scene = None
    scenes = obs.obs_frontend_get_scenes()
    for iscene in scenes:
        name = obs.obs_source_get_name(iscene)
        if name == scene_name:
            scene_ref = iscene
            break
    scene = obs.obs_scene_from_source(scene_ref)
    obs.source_list_release(scenes)
    return scene

def find_or_create_scene(scene_name: str):
    """
    Tries to find the scene with the same name, but if it doesn't, autocreates it.

    Returns: obs_scene_t*, does **not require release**

    ##### obs API responsibilities
    * Uses `find_scene`, doesn't require release.

    * Uses [obs_scene_create](https://docs.obsproject.com/reference-scenes#c.obs_scene_create), which doesn't require release.
    """
    scene_ref = find_scene(scene_name)
    if scene_ref is None:
        obs.script_log(obs.LOG_INFO, "Scene does not exist. Will create.")
        scene_ref = obs.obs_scene_create(scene_name)
    return scene_ref

def print_source_info(source_ref):
    settings = obs.obs_source_get_settings(source_ref)
    psettings = obs.obs_source_get_private_settings(source_ref)
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

def print_scene_info(scene_name: str):
    scene_ref = find_scene(scene_name)
    if scene_ref is None:
        print('Scene does not exist')
    scene_ref = obs.obs_scene_get_ref(scene_ref)
    source_ref = obs.obs_scene_get_source(scene_ref)
    print_source_info(source_ref)
    obs.obs_scene_release(scene_ref)

def walk_scene_items_in_current_source():
    current_scene_as_source = obs.obs_frontend_get_current_scene()
    if not current_scene_as_source:
        return

    current_scene = obs.obs_scene_from_source(current_scene_as_source)
    items = obs.obs_scene_enum_items(current_scene)
    for s, i in enumerate(items):
        source = obs.obs_sceneitem_get_source(i)
        if source is None:
            continue
        print("SourceItem:"+obs.obs_source_get_name(source))

    obs.sceneitem_list_release(items)
    obs.obs_source_release(current_scene_as_source)

def print_property_info(property, settings):
    if property is None:
        return
    
    source_property_name = obs.obs_property_name(property)
    print("\t\tSource Property Name: "+source_property_name)
    source_property_display_name = obs.obs_property_description(property)
    print("\t\tSource Property Display Name: "+source_property_display_name)
    source_property_type = obs.obs_property_get_type(property)
    print("\t\tSource Property Type: "+source_property_types[source_property_type])
    if source_property_type == obs.OBS_PROPERTY_LIST:
        list_type = obs.obs_property_list_type(property)
        print("\t\t\tProperty Type " + str(list_type))
        list_format = obs.obs_property_list_format(property)
        print("\t\t\tProperty Format " + str(list_format))
        list_count = obs.obs_property_list_item_count(property)
        for i in range(list_count):
            print("\t\t\tProperty Item " + str(i))
            list_item_name = obs.obs_property_list_item_name(property, i)
            print("\t\t\t\tName: " + list_item_name)
            list_item_string = obs.obs_property_list_item_string(property, i)
            print("\t\t\t\tString: " + list_item_string)
        
        setting_value = obs.obs_data_get_string(settings, source_property_name)
        print("\t\t\tSetting Value:" + str(setting_value))

def enum_scene_items(scene_name: str):
    #walk_scene_items_in_current_source()
    scene_ref = find_scene(scene_name)
    if(scene_ref is None):
        print('scene var is None')
        return
    scene_items = obs.obs_scene_enum_items(scene_ref)
    for s, i in enumerate(scene_items):
        source_ref = obs.obs_sceneitem_get_source(i)
        if source_ref is None:
            continue
        # print("SourceItem:"+obs.obs_source_get_name(source))
        source_name = obs.obs_source_get_name(source_ref)
        print("\tSource Name:" + source_name)
        # source_type = obs.obs_source_get_type(source_ref)
        # print("\tSource Type:" + str(source_type))
        # source_properties = obs.obs_source_properties(source_ref)
        source_settings = obs.obs_source_get_settings(source_ref)
        # source_property = obs.obs_properties_first(source_properties)
        # print_property_info(source_property, source_settings)
        # source_property = obs.obs_properties_get(source_properties, "mode")
        # print_property_info(source_property, source_settings)
        # source_property = obs.obs_properties_get(source_properties, "window")
        # print_property_info(source_property, source_settings)

        json = obs.obs_data_get_json_pretty_with_defaults(source_settings)
        print(json+"\n\n")

        # source_property_pp  = ffi.new("struct obs_property_t *[1]")
        # source_property_pp[0] = source_property
        # while(obs.obs_property_next(source_property_pp)):
        #     source_property = ffi.new("struct obs_property_t *", source_property_pp[0])
        #     print_property_info(source_property)
        #     source_property_pp  = ffi.new("struct obs_property_t *[1]")
        #     source_property_pp[0] = source_property

        #obs.obs_properties_destroy(source_properties)
        obs.obs_data_release(source_settings)

    obs.sceneitem_list_release(scene_items)
    obs.obs_scene_release(scene_ref)

def find_scene_item(scene_ref, source_name: str):
    """
    Tries to find the scene with the same name, but if it doesn't, autocreates it.

    Returns: obs_sceneitem_t*, does **not require release**.

    ##### obs API responsibilities
    * Uses [obs_scene_enum_items](https://docs.obsproject.com/scripting#obs_scene_enum_items), which **requires release** through [sceneitem_list_release](https://docs.obsproject.com/scripting#sceneitem_list_release).

    * Uses [obs_sceneitem_get_source](https://docs.obsproject.com/reference-scenes#c.obs_sceneitem_get_source, which does not increment ref count.

    * Uses [obs_source_get_name](https://docs.obsproject.com/reference-sources#c.obs_source_get_name) which doesn't increase the ref count.
    """
    scene_item = None
    scene_items = obs.obs_scene_enum_items(scene_ref)
    for s, i in enumerate(scene_items):
        source_ref = obs.obs_sceneitem_get_source(i)
        if source_ref is None:
            continue
        # print("SourceItem:"+obs.obs_source_get_name(source))
        scene_item_name = obs.obs_source_get_name(source_ref)
        if scene_item_name == source_name:
            scene_item = i
            break
    obs.sceneitem_list_release(scene_items)
    return scene_item

def find_scene_item(scene_name: str, source_name: str):
    """
    Finds the scene item within a scene, using names for both. A scene item is basically a source.

    Returns: obs_sceneitem_t*, does **not require release**

    ##### obs API responsibilities

    * Uses `find_scene`, which doesn't increment the ref count

    * Uses `find_scene_item(scene_ref, source_name: str)`, which doesn't increment the ref count
    """
    scene_ref = find_scene(scene_name)
    scene_item = find_scene_item(scene_ref, source_name)
    return scene_item

class HookRate(Enum):
    HOOK_RATE_SLOW = 0.5
    HOOK_RATE_NORMAL = 1.0
    HOOK_RATE_FAST = 2.0
    HOOK_RATE_FASTEST = 3.0
    def __str__(self):
        return f'{self.name}'

def create_game_capture_source(scene_ref, source_name: str, window_name: str):
    """
    Creates a game capture style source that targets a specific application through its window's name.

    Returns: obs_source_t*, does **require release**

    ##### obs API responsibilities

    * Uses [obs_source_create](https://docs.obsproject.com/reference-sources#c.obs_source_create), which **requires release**
    """
    settings = obs.obs_data_create()
    obs.obs_data_set_string(settings, "capture_mode", "window")
    obs.obs_data_set_string(settings, "window", window_name)
    obs.obs_data_set_double(settings, "hook_rate", HookRate.HOOK_RATE_FASTEST.value)

    #Size (w, h) of the window
    #Positional Alignment = Top Left
    # BB Size = 1,1
    new_source = obs.obs_source_create("game_capture", source_name, settings, None)
    obs.obs_scene_add(scene_ref, new_source)

    #source_properties = obs.obs_source_properties(new_source)
    #obs.obs_properties_apply_settings(source_properties, settings)
    #scene_item = find_scene_item(oldskies_scene_source_name)
    #if scene_item is None:
    #    new_source = obs.obs_source_create(None, oldskies_scene_source_name, #settings, None)
    #    obs.obs_save_sources()
    #obs.obs_properties_destroy(source_properties)
    obs.obs_save_sources()
    return new_source

def game_capture_source_exists(scene_ref, source_name: str) -> bool:
    """
    Returns whether a source of type game capture exists under the given scene reference.

    Returns: bool

    ##### obs API responsibilities

    * Uses `find_scene_item`, which doesn't require release.
    
    * Uses [obs_sceneitem_get_source](https://docs.obsproject.com/reference-scenes#c.obs_sceneitem_get_source), which does not increment the ref count.
    """
    scene_item_ref = find_scene_item(scene_ref, source_name)
    source_ref = obs.obs_sceneitem_get_source(scene_item_ref)
    return source_ref is not None