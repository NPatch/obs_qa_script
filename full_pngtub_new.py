# -*- coding: utf-8 -*-
# pylint: disable=C0301, R0902, R0903
"""
    Copyright (C) 2023 by Penwywern <gaspard.larrouturou@protonmail.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import obspython as obs
import math as mt
import time as t

import sys
import platform
import traceback

import ctypes as ct
import ctypes.util

minf    = float("-inf")
nan     = float("nan")



if platform.system() == "Linux":
    libobs = ct.CDLL(ct.util.find_library("obs"))
else:
    libobs = ct.CDLL("obs")


def wrap(lib, funcname, restype, argtypes):
    """Wraps a C function from the given lib into python
    """
    func = getattr(lib, funcname)
    func.restype = restype
    func.argtypes = argtypes
    return func



############################################################################

class ctSource(ct.Structure):
    pass


class ctVolmeter(ct.Structure):
    pass


volmeter_callback_t = ct.CFUNCTYPE(None, ct.c_void_p, ct.POINTER(ct.c_float),
                                   ct.POINTER(ct.c_float), ct.POINTER(ct.c_float))




obs.obs_volmeter_create             = wrap(libobs,
                                           "obs_volmeter_create",
                                           restype=ct.POINTER(ctVolmeter),
                                           argtypes=[ct.c_int])

obs.obs_volmeter_destroy            = wrap(libobs,
                                           "obs_volmeter_destroy",
                                           restype=None,
                                           argtypes=[ct.POINTER(ctVolmeter)])

obs.obs_volmeter_add_callback       = wrap(libobs,
                                           "obs_volmeter_add_callback",
                                           restype=None,
                                           argtypes=[ct.POINTER(ctVolmeter), volmeter_callback_t, ct.c_void_p])

obs.obs_volmeter_remove_callback    = wrap(libobs,
                                           "obs_volmeter_remove_callback",
                                           restype=None,
                                           argtypes=[ct.POINTER(ctVolmeter), volmeter_callback_t, ct.c_void_p])



_obs_volmeter_attach_source         = wrap(libobs,
                                           "obs_volmeter_attach_source",
                                           restype=ct.c_bool,
                                           argtypes=[ct.POINTER(ctVolmeter), ct.POINTER(ctSource)])

obs.obs_volmeter_attach_source = lambda volmeter, source : _obs_volmeter_attach_source(volmeter,
                                                                                       ct.cast(int(source), ct.POINTER(ctSource)))

##########################################################################################



class Parameters():
    # sound gate parameters
    gate_open_threshold     = nan
    gate_close_threshold    = nan
    gate_open               = False
    gate_opened_time        = nan

    # image source parameters
    img_source_name     = ""
    img_idle            = ""
    img_active          = ""
    item_list           = []

    # bounce parameters
    amplitude           = nan
    speed               = nan
    pos                 = (0, 0)

    def bounce_func(self, time):
        return 0, -mt.sin(time*mt.pi/1)

    def decay_func(self, time):
        return 0, 1.6*mt.exp(-mt.sqrt(time**3))

    # volmeter parameters
    noise           = {}
    data            = {}
    vol_lock        = {}
    audio_sources   = []
    volmeter        = {}

params = Parameters()

###########################################################################################

@volmeter_callback_t
def volmeter_callback(dat, mag, peak, input):
    try:
        _noise = float(peak[0])
        if mt.isnan(_noise):
            params.noise[ct.c_char_p(dat).value.decode()] = minf
        else:
            params.noise[ct.c_char_p(dat).value.decode()] = _noise
    except:
        destroy_volmeter(ct.c_char_p(dat).value.decode())
        raise


def create_volmeter():

    try:
        for audio_name in list(params.volmeter.keys()):
            if audio_name not in params.audio_sources:
                destroy_volmeter(audio_name)

        for audio_name in list(params.vol_lock.keys()):
            if audio_name not in params.audio_sources:
                del params.vol_lock[audio_name]

        for audio_name in params.audio_sources:
            if not audio_name in params.vol_lock:
                params.vol_lock[audio_name] = False

        for audio_name in params.audio_sources:
            if not params.vol_lock[audio_name]:

                source = obs.obs_get_source_by_name(audio_name)
                if source:
                    if not audio_name in params.volmeter:
                        params.noise[audio_name] = minf
                        params.volmeter[audio_name] = obs.obs_volmeter_create(2)
                        params.data[audio_name] = ct.c_char_p(audio_name.encode())
                        obs.obs_volmeter_add_callback(params.volmeter[audio_name], volmeter_callback, params.data[audio_name])
                    if obs.obs_volmeter_attach_source(params.volmeter[audio_name], source):
                        params.vol_lock[audio_name] = True
                        print(f"Attached to source {audio_name}")
                obs.obs_source_release(source)

        if all(params.vol_lock.values()):
            print(f"Attached to all sources {params.audio_sources}")
            obs.remove_current_callback()
    except:
        traceback.print_exc()
        print("exception in create_volmeter, removing callback, restart script to restore")
        obs.remove_current_callback()


def destroy_volmeters():
    if params.volmeter:
        for audio_name in list(params.volmeter.keys()):                        # NOT for audio_name in volmeter to avoid runtime error
            destroy_volmeter(audio_name)



def destroy_volmeter(source_name):
    obs.obs_volmeter_remove_callback(params.volmeter[source_name], volmeter_callback, params.data[source_name])
    obs.obs_volmeter_destroy(params.volmeter[source_name])
    params.volmeter.pop(source_name)
    print(f"Removed volmeter & volmeter_callback on {source_name}")
    params.vol_lock.pop(source_name)
    params.noise.pop(source_name)
    params.data.pop(source_name)


######################################################################################################################################################

class S_item():
    def __init__(self, item):
        self.item       = item
        pos = obs.vec2()
        obs.obs_sceneitem_get_pos(self.item, pos)
        self.startpos   = (pos.x, pos.y)
        self.currpos    = (0,0)
        self.velocity   = (0,0)

    def movelock(self):
        return obs.obs_sceneitem_locked(self.item)

    def id(self):
        return obs.obs_sceneitem_get_id(self.item)

    def scene(self):
        return obs.obs_sceneitem_get_scene(self.item)

    def lock(self, locked):
        if locked:
            pos = obs.vec2()
            obs.obs_sceneitem_get_pos(self.item, pos)
            self.startpos   = (pos.x, pos.y)
        else:
            self.reset()

    def changepos(self, x, y):
        pos = obs.vec2()
        try:
            pos.x = self.startpos[0] + int((x+90000)%180000 - 90000)
            pos.y = self.startpos[1] + int((y+90000)%180000 - 90000)
        except (OverflowError, ValueError):
            pos.x = self.startpos[0]
            pos.y = self.startpos[1]

        obs.obs_sceneitem_set_pos(self.item, pos)

    def reset(self):
        pos = obs.vec2()
        pos.x = self.startpos[0]
        pos.y = self.startpos[1]
        obs.obs_sceneitem_set_pos(self.item, pos)





def refresh_items(source_name):
    params.item_list = []
    for scene_a_s in obs.obs_frontend_get_scenes():
        scene = obs.obs_scene_from_source(scene_a_s)
        items = obs.obs_scene_enum_items(scene)

        for item in items:
            if obs.obs_source_get_name(obs.obs_sceneitem_get_source(item)) == source_name:
                params.item_list.append(S_item(item))

        obs.sceneitem_list_release(items)
        obs.obs_source_release(scene_a_s)



def script_tick(seconds):
    try :
        if not params.gate_open:
            return

        time = t.time() - params.gate_opened_time
        newpos = [int( bounce * decay * params.amplitude)
                  for bounce, decay in zip(params.bounce_func(time * params.speed),
                                           params.decay_func( time * params.speed))]    # TODO arbitrary array of funcs?

        if newpos != params.pos:
            params.pos = newpos
            for item in params.item_list:
                if item.movelock():
                    item.changepos(params.pos[0], params.pos[1])
    except:
        traceback.print_exc()
        print("exception in sctipt_tick")


######################################################################################################################################################

def noise_check():

    try:
        if params.noise:
            if (not params.gate_open) and (max(params.noise.values()) >= params.gate_open_threshold):
                params.gate_open = True

                img_source = obs.obs_get_source_by_name(params.img_source_name)
                if img_source:
                    img_settings = obs.obs_source_get_settings(img_source)
                    obs.obs_data_set_string(img_settings, "file", params.img_active)
                    obs.obs_source_update(img_source, img_settings)
                    obs.obs_data_release(img_settings)
                obs.obs_source_release(img_source)
                params.gate_opened_time = t.time()


            elif params.gate_open and (max(params.noise.values())  <= params.gate_close_threshold):
                params.gate_open = False

                img_source = obs.obs_get_source_by_name(params.img_source_name)
                if img_source:
                    img_settings = obs.obs_source_get_settings(img_source)
                    obs.obs_data_set_string(img_settings, "file", params.img_idle)
                    obs.obs_source_update(img_source, img_settings)
                    obs.obs_data_release(img_settings)
                obs.obs_source_release(img_source)

                for item in params.item_list:
                    if item.movelock():
                        item.reset()
    except:
        traceback.print_exc()
        print("exception in noise_check, removing callback, restart script to restore")
        obs.remove_current_callback()



def on_source_create(calldata):
    source = obs.calldata_source(calldata, "source")

    if obs.obs_source_get_name(source) == params.img_source_name:
        refresh_items(params.img_source_name)

    if obs.obs_source_get_type(source) == obs.OBS_SOURCE_TYPE_SCENE:
        sh = obs.obs_source_get_signal_handler(source)
        obs.signal_handler_connect(sh, "item_add", on_sceneitem_add)
        obs.signal_handler_connect(sh, "item_remove", on_sceneitem_remove)
        obs.signal_handler_connect(sh, "item_locked", on_sceneitem_locked)



def on_source_destroy(calldata):
    source = obs.calldata_source(calldata, "source")

    if obs.obs_source_get_name(source) in params.audio_sources:
        destroy_volmeter(obs.obs_source_get_name(source))
        if all(params.vol_lock.values()):
            obs.timer_add(create_volmeter, 500)

    if obs.obs_source_get_name(source) == params.img_source_name:
        params.item_list = []

    if obs.obs_source_get_type(source) == obs.OBS_SOURCE_TYPE_SCENE:
        sh = obs.obs_source_get_signal_handler(source)
        obs.signal_handler_disconnect(sh, "item_add", on_sceneitem_add)
        obs.signal_handler_disconnect(sh, "item_remove", on_sceneitem_remove)
        obs.signal_handler_disconnect(sh, "item_locked", on_sceneitem_locked)



def on_source_rename(calldata):
    source = obs.calldata_source(calldata, "source")
    prev_name = obs.calldata_string(calldata, "prev_name")
    new_name = obs.calldata_string(calldata, "new_name")

    if prev_name in params.audio_sources:
        destroy_volmeter(prev_name)
        if all(params.vol_lock.values()):
            obs.timer_add(create_volmeter, 500)

    if prev_name == params.img_source_name:
        params.item_list = []

    if new_name == params.img_source_name:
        refresh_items(params.img_source_name)



def on_sceneitem_add(calldata):
    item = obs.calldata_sceneitem(calldata, "item")
    if obs.obs_source_get_name(obs.obs_sceneitem_get_source(item)) == params.img_source_name:
        params.item_list.append(S_item(item))


def on_sceneitem_remove(calldata):
    item = obs.calldata_sceneitem(calldata, "item")
    item_id = obs.obs_sceneitem_get_id(item)
    scene = obs.obs_sceneitem_get_scene(item)
    for index, item in [*enumerate(params.item_list)][::-1]:
        print(f"{index}, {item}")
        if item.id() == item_id and item.scene() == scene:
            params.item_list.pop(index)
            item.reset()



def on_sceneitem_locked(calldata):
    item = obs.calldata_sceneitem(calldata, "item")
    item_id = obs.obs_sceneitem_get_id(item)
    scene = obs.obs_sceneitem_get_scene(item)
    locked = obs.calldata_bool(calldata, "locked")
    for item in params.item_list:
        if item.id() == item_id and item.scene() == scene:
            item.lock(locked)


######################################################################################################################################################

def script_load(settings):

    gsh = obs.obs_get_signal_handler()
    obs.signal_handler_connect(gsh, "source_create", on_source_create)
    obs.signal_handler_connect(gsh, "source_destroy", on_source_destroy)
    obs.signal_handler_connect(gsh, "source_rename", on_source_rename)

    for scene_a_s in obs.obs_frontend_get_scenes():
        sh = obs.obs_source_get_signal_handler(scene_a_s)
        obs.signal_handler_connect(sh, "item_add", on_sceneitem_add)
        obs.signal_handler_connect(sh, "item_remove", on_sceneitem_remove)
        obs.signal_handler_connect(sh, "item_locked", on_sceneitem_locked)
        obs.obs_source_release(scene_a_s)

def script_unload():

    obs.timer_remove(create_volmeter)
    obs.timer_remove(noise_check)
    destroy_volmeters()

    gsh = obs.obs_get_signal_handler()
    obs.signal_handler_disconnect(gsh, "source_create", on_source_create)
    obs.signal_handler_disconnect(gsh, "source_destroy", on_source_destroy)
    obs.signal_handler_disconnect(gsh, "source_rename", on_source_rename)

    for scene_a_s in obs.obs_frontend_get_scenes():
        sh = obs.obs_source_get_signal_handler(scene_a_s)
        obs.signal_handler_disconnect(sh, "item_add", on_sceneitem_add)
        obs.signal_handler_disconnect(sh, "item_remove", on_sceneitem_remove)
        obs.signal_handler_disconnect(sh, "item_locked", on_sceneitem_locked)
        obs.obs_source_release(scene_a_s)


    if params.gate_open:
        params.gate_open = False

        img_source = obs.obs_get_source_by_name(params.img_source_name)
        if img_source:
            img_settings = obs.obs_source_get_settings(img_source)
            obs.obs_data_set_string(img_settings, "file", params.img_idle)
            obs.obs_source_update(img_source, img_settings)
            obs.obs_data_release(img_settings)
        obs.obs_source_release(img_source)

        for item in params.item_list:
            if item.movelock():
                item.reset()


def script_description():
    return "Makes a given source bounce when a gate on a given audio source opens"

def script_properties():
    props = obs.obs_properties_create()
    obs.obs_properties_add_text(props, "audio", "Audio source", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "source", "PngTube Source", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_path(props, "img_idle", "Idle image path", obs.OBS_PATH_FILE, "", None)
    obs.obs_properties_add_path(props, "img_active", "Active image path", obs.OBS_PATH_FILE, "", None)
    obs.obs_properties_add_float_slider(props, "gate_close", "Audio gate closing level\n(Db)", -90, 0, 0.5)
    obs.obs_properties_add_float_slider(props, "gate_open", "Audio gate opening level\n(Db)", -90, 0, 0.5)
    obs.obs_properties_add_float_slider(props, "decay_time", "Decay time\n(seconds)", 0.02, 5, 0.01)
    obs.obs_properties_add_int_slider(props, "amplitude", "Bounce amplitude\n(pixels)", 1, 500, 1)
    return props

def script_update(settings):

    obs.timer_remove(create_volmeter)
    obs.timer_remove(noise_check)


    if params.gate_open:
        params.gate_open = False

        img_source = obs.obs_get_source_by_name(params.img_source_name)
        if img_source:
            img_settings = obs.obs_source_get_settings(img_source)
            obs.obs_data_set_string(img_settings, "file", params.img_idle)
            obs.obs_source_update(img_source, img_settings)
            obs.obs_data_release(img_settings)
        obs.obs_source_release(img_source)

        for item in params.item_list:
            if item.movelock():
                item.reset()


    params.gate_open_threshold = obs.obs_data_get_double(settings, "gate_open")
    params.gate_close_threshold = obs.obs_data_get_double(settings, "gate_close")
    params.img_idle = obs.obs_data_get_string(settings, "img_idle").strip()
    params.img_active = obs.obs_data_get_string(settings, "img_active").strip()
    params.amplitude = obs.obs_data_get_int(settings, "amplitude")
    params.speed = 3/obs.obs_data_get_double(settings, "decay_time")
    params.img_source_name = obs.obs_data_get_string(settings, "source").strip()

    audio_sources = [_.strip() for _ in obs.obs_data_get_string(settings, "audio").split(",")]
    if params.audio_sources != audio_sources:
        params.audio_sources = audio_sources
        obs.timer_add(create_volmeter, 500)

    refresh_items(params.img_source_name)
    obs.timer_add(noise_check, 50)


def script_defaults(settings):
    obs.obs_data_set_default_string(settings, "audio", "Mic/Aux")
    obs.obs_data_set_default_double(settings, "gate_open", -35.)
    obs.obs_data_set_default_double(settings, "gate_close", -75.)
    obs.obs_data_set_default_double(settings, "decay_time", 0.5)
    obs.obs_data_set_default_int(settings, "amplitude", 20)

def script_save(settings):

    if params.gate_open:
        params.gate_open = False

        img_source = obs.obs_get_source_by_name(params.img_source_name)
        if img_source:
            img_settings = obs.obs_source_get_settings(img_source)
            obs.obs_data_set_string(img_settings, "file", params.img_idle)
            obs.obs_source_update(img_source, img_settings)
            obs.obs_data_release(img_settings)
        obs.obs_source_release(img_source)

        for item in params.item_list:
            if item.movelock():
                item.reset()
