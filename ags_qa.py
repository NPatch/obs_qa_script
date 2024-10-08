import obspython as obs
import math, time
from enum import Enum
import os
import json
import psutil
import subprocess
import win32gui, win32process

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
        scene_ref = obsutil.find_scene(scene_name)
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
        scene_ref = obsutil.find_scene(scene_name)
        if scene_ref is None:
            print('Scene does not exist')
        scene_ref = obs.obs_scene_get_ref(scene_ref)
        source_ref = obs.obs_scene_get_source(scene_ref)
        obsutil.print_source_info(source_ref)
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
        print("\t\tSource Property Type: "+obsutil.source_property_types[source_property_type])
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
        scene_ref = obsutil.find_scene(scene_name)
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
        scene_ref = obsutil.find_scene(scene_name)
        scene_item = obsutil.find_scene_item(scene_ref, source_name)
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
    def config_get_base_resolution() -> obs.vec2:
        '''
        Gets base resolution.

        ---
        
        ##### obs API responsibilities

        * Uses [obs_frontend_get_profile_config](https://docs.obsproject.com/reference-sources#c.obs_frontend_get_profile_config), which **does not require release**
        '''
        config = obs.obs_frontend_get_profile_config()
        res = obs.vec2()
        res.x = obs.config_get_uint(config, "Video", "BaseCX")
        res.y = obs.config_get_uint(config, "Video", "BaseCY")
        return res

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

        ---

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
    def run_steam_game(game_name: str, game_steam_gameid: str):
        """
        Runs a steam game, given its steam gameid.
        """
        obs.script_log(obs.LOG_INFO, "Running "+game_name)
        steamCommand = "steam"
        steamGameParameter = "steam://rungameid/"+game_steam_gameid
        subprocess.call([steamCommand, steamGameParameter])

    @staticmethod
    def run_game(game_executable: str):
        obs.script_log(obs.LOG_INFO, "Running" + game_executable)
        subprocess.call([game_executable])

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
                if proc.name().lower() in processName.lower() :
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
    
    def get_game_capture_window_string(self, process): 
        return "{winname}:{winclass}:{exename}".format(winname=self.window_name,winclass=self.window_class, exename=process.name())

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