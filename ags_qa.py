import obspython as obs
import math, time
from enum import Enum
import os
import json
import psutil
import subprocess
import win32gui

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

class obsutil:
    '''
    obsutil is basically a namespace for helper functions on top of the obspython module
    '''

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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def print_scene_info(scene_name: str):
        scene_ref = find_scene(scene_name)
        if scene_ref is None:
            print('Scene does not exist')
        scene_ref = obs.obs_scene_get_ref(scene_ref)
        source_ref = obs.obs_scene_get_source(scene_ref)
        print_source_info(source_ref)
        obs.obs_scene_release(scene_ref)

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def find_scene_item_by_names(scene_name: str, source_name: str):
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
        
    class Alignment(Enum):
        ALIGN_CENTER = 0
        ALIGN_LEFT = 1
        ALIGN_RIGHT = 2
        ALIGN_TOP = 4
        ALIGN_BOTTOM = 6
        def __str__(self):
            return f'{self.name}'
        def __int__(self):
            return self.value
        def __or__(self, other):
            return self.value | other.value
        
    class BoundsType(Enum):
        NONE = 0            #no bounds
        STRETCH = 1         #stretch (ignores base scale)
        SCALE_INNER = 2     #scales to inner rectangle
        SCALE_OUTER = 3     #scales to outer rectangle
        SCALE_TO_WIDTH = 4  #scales to the width
        SCALE_TO_HEIGHT = 5 #scales to the height
        MAX_ONLY = 6        #no scaling, maximum size only
        def __str__(self):
            return f'{self.name}'
        def __int__(self):
            return self.value
    
    @staticmethod
    def strvec2(vec : obs.vec2) -> str:
        return "{{{posx},{posy}}}".format(posx=vec.x, posy=vec.y)
    
    @staticmethod
    def reset_transform_and_crop(scene_item_ref, width = -1, height = -1):
        '''
        Resets both the transform and the crop to required levels
        
        ---
        
        Alignment is handled as a bitwise or of the literals. These literals in the repo are handled as\n
        #define OBS_ALIGN_CENTER (0)\n
        #define OBS_ALIGN_LEFT (1 << 0)\n
        #define OBS_ALIGN_RIGHT (1 << 1)\n
        #define OBS_ALIGN_TOP (1 << 2)\n
        #define OBS_ALIGN_BOTTOM (1 << 3)\n

        Bitwise ORs:\n
        LEFT | TOP = 5\n
        TOP | CENTER = 4
        '''
        obs.script_log(obs.LOG_DEBUG, "reset_transform_and_crop")
        transform_info = obs.obs_transform_info()
        obs.obs_sceneitem_get_info(scene_item_ref, transform_info)
        obs.vec2_set(transform_info.pos, 0.0, 0.0)
        transform_info.rot = 0.0
        transform_info.alignment = obsutil.Alignment.ALIGN_LEFT | obsutil.Alignment.ALIGN_TOP
        if width > -1 and height > -1:
            transform_info.scale.x  = 1.0
            transform_info.scale.y  = 1.0

        #bounds_type
        transform_info.bounds_type = obs.OBS_BOUNDS_SCALE_INNER
        #print("bounds type: ", str(int(transform_info.bounds_type)))
        #bounds_alignment
        #print("bounds alignment: ", str(transform_info.bounds_alignment))
        transform_info.bounds_alignment = obsutil.Alignment.ALIGN_CENTER.value
        #bounds
        if width > -1 and height > -1:
            transform_info.bounds.x = width
            transform_info.bounds.y = height
        print("bounds: ", obsutil.strvec2(transform_info.bounds))
            

        obs.obs_sceneitem_set_info(scene_item_ref, transform_info)
        #print("transform.pos: ", strvec2(transform_info.pos))
        #print("transform.rot: ", str(transform_info.rot))
        #print("transform.alignment: ", str(transform_info.alignment))
        print("transform_info set")

        crop_info = obs.obs_sceneitem_crop()
        obs.obs_sceneitem_get_crop(scene_item_ref, crop_info)
        crop_info.left = 0
        crop_info.right = 0
        crop_info.top = 0
        crop_info.bottom = 0
        obs.obs_sceneitem_set_crop(scene_item_ref, crop_info)
        print("crop_info set")

        #print("crop.left: ", str(crop_info.left))
        #print("crop.right: ", str(crop_info.right))
        #print("crop.top: ", str(crop_info.top))
        #print("crop.bottom: ", str(crop_info.bottom))

    @staticmethod
    def config_set_base_resolution(width: int = 0, height: int = 0):
        '''
        Sets base resolution.

        ---
        
        ##### obs API responsibilities

        * Uses [obs_frontend_get_profile_config](https://docs.obsproject.com/reference-sources#c.obs_frontend_get_profile_config), which **does not require release**
        '''
        config = obs.obs_frontend_get_profile_config()

        disable = (width == 0 or height == 0)
        if(disable):
            return

        obs.config_set_uint(config, "Video", "BaseCX", width)
        obs.config_set_uint(config, "Video", "BaseCY", height)

    @staticmethod
    def config_set_output_resolution(width: int = 0, height: int = 0):
        '''
        Sets output resolution.

        ---
        
        ##### obs API responsibilities

        * Uses [obs_frontend_get_profile_config](https://docs.obsproject.com/reference-sources#c.obs_frontend_get_profile_config), which **does not require release**
        '''
        config = obs.obs_frontend_get_profile_config()

        disable = (width == 0 or height == 0)
        if(disable):
            return

        obs.config_set_uint(config, "Video", "OutputCX", width)
        obs.config_set_uint(config, "Video", "OutputCY", height)

    class ScaleType(Enum):
        DISABLE = 0
        POINT = 1
        BICUBIC = 2
        BILINEAR = 3
        LANCZOS = 4
        AREA = 5
        
        def __str__(self):
            return f'{self.name}'
        def __int__(self):
            return self.value

    @staticmethod
    def set_rescale_resolution(width: int = 0, height: int = 0, scale_type: ScaleType = ScaleType.BILINEAR):
        '''
        Sets the Rescale resolution and type for the output.

        ---
        
        ##### obs API responsibilities

        * Uses [obs_frontend_get_profile_config](https://docs.obsproject.com/reference-sources#c.obs_frontend_get_profile_config), which **does not require release**
        '''
        config = obs.obs_frontend_get_profile_config()

        disable = (width == 0 or height == 0)
        if(disable):
            scale_type = obsutil.ScaleType.DISABLE
            width = height = 0

        obs.config_set_int(config, "AdvOut", "RecRescaleFilter", scale_type.value)
        resolution = str(width)+"x"+str(height)
        obs.config_set_string(config, "AdvOut", "RecRescaleRes", resolution)

    @staticmethod
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
        obs.obs_data_set_double(settings, "hook_rate", obsutil.HookRate.HOOK_RATE_FASTEST.value)

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

    @staticmethod
    def game_capture_source_exists(scene_ref, source_name: str) -> bool:
        """
        Returns whether a source of type game capture exists under the given scene reference.

        Returns: bool

        ##### obs API responsibilities

        * Uses `find_scene_item`, which doesn't require release.
        
        * Uses [obs_sceneitem_get_source](https://docs.obsproject.com/reference-scenes#c.obs_sceneitem_get_source), which does not increment the ref count.
        """
        scene_item_ref = obsutil.find_scene_item(scene_ref, source_name)
        source_ref = obs.obs_sceneitem_get_source(scene_item_ref)
        return source_ref is not None

class gameutil:
    '''
    gameutil provides helper functions for process tracking and running applications (steam or otherwise)
    '''

    @staticmethod
    def run_steam_game(game_name: str, game_steam_gameid: int):
        """
        Runs a steam game, given its steam gameid.
        """
        obs.script_log(obs.LOG_INFO, "Running "+game_name)
        steamCommand = "steam"
        steamGameParameter = "steam://rungameid/"+str(game_steam_gameid)
        subprocess.call([steamCommand, steamGameParameter])

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
                if processName.lower() == proc.name().lower() :
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

class GameData:
    '''
    GameData is used to hold various settings that we also allow the user to modify, regarding the target application for the testing
    '''
    scene_name :str = ""
    source_name :str = ""
    steam_gameid : str = ""
    exe_name :str = ""
    window_name :str = ""
    window_class :str = ""

    @property
    def game_capture_window_string(self): 
        return "{winname}:{winclass}:{exename}".format(winname=self.window_name,winclass=self.window_class, exename=self.exe_name)

    def __init__(self):
        self.scene_name = ""
        self.scene_name = ""

        self.steam_gameid = ""
        self.exe_name = ""
        self.window_name = ""
        self.window_class = ""

    def settings_json_filename(self, script_path : str):
        name = self.exe_name.lower()
        name = name.replace(".exe", ".json")
        name = "testing_config.json"
        return os.path.join(script_path, name).__str__()
    
    def settings_load_from_disk(self, script_path : str):
        name = "testing_config.json"
        filepath = os.path.join(script_path, name).__str__()
        with open(filepath, "r") as file:
            data = json.load(file)
            self.scene_name = data["scene_name"]
            self.source_name = data["source_name"]
            self.steam_gameid = data["steam_gameid"]
            self.exe_name = data["exe_name"]
            self.window_name = data["window_name"]
            self.window_class = data["window_class"]
    
    def __json__(self):
        return json.dumps(self.__dict__, indent=4)
    
class AGSGameData(GameData):
    crash_window_name :str = ""
    crash_window_class :str = ""

    def __init__(self):
        super().__init__()
        self.crash_window_name = ""
        self.crash_window_class = ""

    def __json__(self):
        return json.dumps(self.__dict__, indent=4)
    
    def settings_load_from_disk(self, script_path : str):
        name = "testing_config.json"
        filepath = os.path.join(script_path, name).__str__()
        with open(filepath, "r") as file:
            data = json.load(file)
            self.scene_name = data["scene_name"]
            self.source_name = data["source_name"]
            self.steam_gameid = data["steam_gameid"]
            self.exe_name = data["exe_name"]
            self.window_name = data["window_name"]
            self.window_class = data["window_class"]
            self.crash_window_name = data["crash_window_name"]
            self.crash_window_class = data["crash_window_class"]

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
    obs.obs_data_set_default_int(settings, "steam_gameid", 0)
    obs.obs_data_set_default_string(settings, "exe_name", "")
    obs.obs_data_set_default_string(settings, "win_name", "")
    obs.obs_data_set_default_string(settings, "win_class", "")
    obs.obs_data_set_default_string(settings, "crash_win_name", "")
    obs.obs_data_set_default_string(settings, "crash_win_name", "")

def script_load(settings):
    obs.script_log(obs.LOG_DEBUG, "script_load")
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
    obs.obs_properties_add_button(props, "button1", "Check Video Settings",print_video_settings)

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

# def setup_persistent_signals():
#     obs.script_log(obs.LOG_DEBUG, "setup_persistent_signals")
#     scene_ref = obsutil.find_scene(ags_data.scene_name)
#     scene_item_ref = obsutil.find_scene_item(scene_ref, ags_data.source_name)
#     source_ref = obs.obs_sceneitem_get_source(scene_item_ref)
#     signal_handler = obs.obs_source_get_signal_handler(source_ref)
    #Signals to get
    #source_activate/deactivate
    # obs.signal_handler_connect(signal_handler,"source_activated",source_activated_callback)
    # obs.signal_handler_connect(signal_handler,"source_deactivated",source_deactivated_callback)
    # obs.signal_handler_connect(signal_handler,"enable",source_enabled_callback)
    
    # obs.signal_handler_connect(signal_handler,"show",source_show_callback)
    # obs.signal_handler_connect(signal_handler,"hide",source_hide_callback)

def setup_signals():
    obs.script_log(obs.LOG_DEBUG, "setup_signals")
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

# def unset_persistent_signals():
#     obs.script_log(obs.LOG_DEBUG, "unset_persistent_signals")
#     scene_ref = obsutil.find_scene(ags_data.scene_name)
#     scene_item_ref = obsutil.find_scene_item(scene_ref, ags_data.source_name)
#     source_ref = obs.obs_sceneitem_get_source(scene_item_ref)
#     signal_handler = obs.obs_source_get_signal_handler(source_ref)
    #Signals to get
    #source_activate/deactivate
    # obs.signal_handler_disconnect(signal_handler,"source_activated",source_activated_callback)
    # obs.signal_handler_disconnect(signal_handler,"source_deactivated",source_deactivated_callback)
    # obs.signal_handler_disconnect(signal_handler,"enable",source_enabled_callback)

    # obs.signal_handler_disconnect(signal_handler,"show",source_show_callback)
    # obs.signal_handler_disconnect(signal_handler,"hide",source_hide_callback)

def unset_signals():
    obs.script_log(obs.LOG_DEBUG, "unset_signals")
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
    obs.script_log(obs.LOG_DEBUG, "start_qa")
    scene_ref = obsutil.find_scene(ags_data.scene_name)
    scene_source_ref = obs.obs_scene_get_source(scene_ref)
    obs.obs_frontend_set_current_scene(scene_source_ref)
    scene_item_ref = obsutil.find_scene_item(scene_ref, ags_data.source_name)
    obs.obs_sceneitem_select(scene_item_ref, True)
    setup_signals()
    
    gameutil.run_steam_game(ags_data.window_name, ags_data.steam_gameid)

def on_frontend_finished_loading(event):
    obs.script_log(obs.LOG_DEBUG, "on_frontend_finished_loading: ")
    if event == obs.OBS_FRONTEND_EVENT_FINISHED_LOADING:
        setup_needs()

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
    #unset_signals()