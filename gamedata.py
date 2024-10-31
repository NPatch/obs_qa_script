import os
import json

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
