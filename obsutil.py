import obspython as obs
import math, time
from cffi import FFI as ffi

def find_scene(scene_name):
    scene_ref = None
    scene = None
    scenes = obs.obs_frontend_get_scenes()
    for iscene in scenes:
        name = obs.obs_source_get_name(iscene)
        #print("Frontend SceneName:"+name)
        if name == scene_name:
            scene_ref = iscene
            break
    scene = obs.obs_scene_from_source(scene_ref)
    obs.source_list_release(scenes)
    return scene

def find_or_create_scene(scene_name):
    scene_ref = find_scene(scene_name)
    if scene_ref is None:
        print("Scene does not exist. Will create.")
        scene_ref = obs.obs_scene_create(scene_name)
    return scene_ref

def PrintSceneInfo(source_ref):
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

def print_scene_info(scene_name):
    scene_ref = find_scene(scene_name)
    if scene_ref is None:
        print('Scene does not exist')
    scene_ref = obs.obs_scene_get_ref(scene_ref)
    source_ref = obs.obs_scene_get_source(scene_ref)
    PrintSceneInfo(source_ref)
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

def enum_scene_items(scene_name):
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


def find_scene_item(scene_name, source_name):
    scene_item = None
    scene_ref = find_scene(scene_name)
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
    obs.obs_scene_release(scene_ref)
    return scene_item

def create_source(props, property):
    scene_ref = find_scene(oldskies_scene_name)
    settings = obs.obs_data_create()
    obs.obs_data_set_string(settings, "capture_mode", "window")
    obs.obs_data_set_string(settings, "window", window_name)

    new_source = obs.obs_source_create("game_capture", source_name, settings, None)
    obs.obs_scene_add(scene_ref, new_source)
    
    source_properties = obs.obs_source_properties(new_source)
    obs.obs_properties_apply_settings(source_properties, settings)
    #scene_item = find_scene_item(oldskies_scene_source_name)
    #if scene_item is None:
    #    new_source = obs.obs_source_create(None, oldskies_scene_source_name, #settings, None)
    #    obs.obs_save_sources()
    obs.obs_properties_destroy(source_properties)
    obs.obs_save_sources()


