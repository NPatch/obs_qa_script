import os, re, winreg

class steamutil:
    '''
    steamutil has helper functions that give us info for installed games, either based on name or steamGameID
    '''

    @staticmethod
    def get_steam_install_path()->str:
        """
        Queries the Steam install path from registry

        Returns:
            string: Steam's install path
        """
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam')
            steam_path, _ = winreg.QueryValueEx(key, 'SteamPath')
            winreg.CloseKey(key)
            return steam_path
        except Exception as e:
            print(f"Error accessing registry: {e}")
            return None
        
    @staticmethod
    def get_app_id_by_name(game_name):
        steam_apps_key = r'Software\Valve\Steam\Apps'
        
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, steam_apps_key) as key:
                subkey_count = winreg.QueryInfoKey(key)[0]
                index = 0
                for index in range(subkey_count):
                    try:
                        subkey_name = winreg.EnumKey(key, index)
                        subkey_path = f"{steam_apps_key}\\{subkey_name}"
                        
                        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey_path) as subkey:
                            value_name, _ = winreg.QueryValueEx(subkey, 'Name')
                            if value_name.lower() == game_name.lower():
                                return subkey_name  # The subkey name is the app_id
                            
                    except OSError:
                        continue
        except OSError as e:
            print(f"Error accessing registry: {e}")
            return None


    @staticmethod
    def get_all_game_install_prefix_dirs(steam_path: str)->list[str]:
        """
        Looks for the libraryfolders.vdf file within the Steam install dir. In there it looks for all install dirs for games.

        Returns:
            string[]: All prefix paths we might find steam games installed in.
        """

        if not steam_path:
            return []
        
        library_folders_file = os.path.join(steam_path, 'steamapps', 'libraryfolders.vdf')
        library_paths = [os.path.normpath(steam_path).lower()]

        if os.path.exists(library_folders_file):
            with open(library_folders_file, 'r') as file:
                content = file.read()
                matches = re.findall(r'^\s*"path"\s*"(.+)"', content, re.MULTILINE)
                for match in matches:
                    norm_path = os.path.normpath(match).lower()
                    if norm_path not in library_paths:
                        library_paths.append(norm_path)
        return library_paths

    @staticmethod
    def get_game_install_dir_by_appid(app_id: str)->str:
        """
        Searches for app_manifests in the paths Steam uses to install games in(`{install_prefixes}`) and looks for the one whose app_id matches the parameter.
        The manifest contains the name of its install folder within the `{install_prefix}/common/`

        Returns: 
            string: returns the path the game with the given app_id is installed in.
        """
        steam_path = steamutil.get_steam_install_path()
        install_prefixes = steamutil.get_all_game_install_prefix_dirs(steam_path)
        
        for lib_path in install_prefixes:
            lib_path = os.path.join(lib_path, 'steamapps')
            potential_app_manifest = os.path.join(lib_path, "appmanifest_{id}.acf".format(id=app_id))
            if os.path.exists(potential_app_manifest):
                content = ""
                with open(potential_app_manifest, 'r') as file:
                    content = file.read()
                if(content == ""):
                    return None
                installdir_match = re.search(r'"installdir"\s*"(.*?)"', content)
                if installdir_match:
                    game_sub_dir = installdir_match.group(1)
                    game_install_dir = os.path.join(lib_path, 'common', game_sub_dir)
                    return game_install_dir
        return None
    
    @staticmethod
    def get_install_dir(potential_app_manifest):
        try:
            game_name = ""
            install_dir = ""
            with open(potential_app_manifest, 'r') as file:
                for line in file:
                    if line.strip():  # Check if the line is not empty
                        if game_name is not None:
                            name_match = re.search(r'"name"\s*"(.*?)"', line)
                            if(name_match):
                                game_name = name_match.group(1)
                        installdir_match = re.search(r'"installdir"\s*"(.*?)"', line)
                        if installdir_match:
                            return [game_name, installdir_match.group(1)]
                return ["", ""]
        except FileNotFoundError:
            return ["", ""]
    
    @staticmethod
    def get_game_install_dir_by_name_fast(name: str)->str:
        """
        Searches the common folder in the paths Steam uses to install games in(`{install_prefixes}`) and looks for the one whose name matches the parameter.

        Returns: 
            string: returns the path the game with the given app_id is installed in.
        """
        steam_path = steamutil.get_steam_install_path()
        install_prefixes = steamutil.get_all_game_install_prefix_dirs(steam_path)
        
        for lib_path in install_prefixes:
            lib_path = os.path.join(lib_path, 'steamapps', 'common')

            for gdir in os.scandir(lib_path): #we know this is just folders, so no need to check if file or folder
                if(gdir.name.lower() == name.lower()):
                    return os.path.join(lib_path, gdir)
        return None

    @staticmethod
    def get_game_install_dir_by_name(name:str)->str:
        steam_path = steamutil.get_steam_install_path()
        install_prefixes = steamutil.get_all_game_install_prefix_dirs(steam_path)

        for lib_path in install_prefixes:
            lib_path = os.path.join(lib_path, 'steamapps')

            for dentry in os.listdir(lib_path):
                if dentry.endswith(".acf"): #listdir gives back filenames, not filepaths, so we can't use os.path.isfile
                    #app_id = dentry.replace("appmanifest_","").replace(".acf","")
                    inst_dir = steamutil.get_install_dir(os.path.join(lib_path, dentry))
                    if(inst_dir[0] == name):
                        inst_dir[1] = os.path.join(lib_path, 'common', inst_dir[1])
                        return inst_dir[1]
                        #return [app_id, inst_dir]
        return None

    @staticmethod
    def get_game_info_by_name(name:str)->str:
        steam_path = steamutil.get_steam_install_path()
        install_prefixes = steamutil.get_all_game_install_prefix_dirs(steam_path)

        for lib_path in install_prefixes:
            lib_path = os.path.join(lib_path, 'steamapps')

            for dentry in os.listdir(lib_path):
                if dentry.endswith(".acf"): #listdir gives back filenames, not filepaths, so we can't use os.path.isfile
                    app_id = dentry.replace("appmanifest_","").replace(".acf","")
                    inst_dir = steamutil.get_install_dir(os.path.join(lib_path, dentry))
                    if(inst_dir[0] == name):
                        inst_dir[1] = os.path.join(lib_path, 'common', inst_dir[1])
                        return {
                            "app_id" : app_id, 
                            "name" : inst_dir[0], 
                            "install_dir": inst_dir[1]
                        }
        return None
    
    @staticmethod
    def get_game_info_by_appid(app_id:str)->str:
        steam_path = steamutil.get_steam_install_path()
        install_prefixes = steamutil.get_all_game_install_prefix_dirs(steam_path)

        for lib_path in install_prefixes:
            lib_path = os.path.join(lib_path, 'steamapps')
            dentry = os.path.join(lib_path, "appmanifest_{}.acf".format(app_id))
            if(os.path.exists(dentry)):
                inst_dir = steamutil.get_install_dir(os.path.join(lib_path, dentry))
                inst_dir[1] = os.path.join(lib_path, 'common', inst_dir[1])
                return {
                    "app_id" : app_id, 
                    "name" : inst_dir[0], 
                    "install_dir": inst_dir[1]
                }
        return None
