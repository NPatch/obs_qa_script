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
sh = None
source_name = ""
scene_name = "Old Skies Scene"


def script_update(settings):
    global sh
    global source_name
    if sh:
         obs.signal_handler_disconnect_global(sh, on_source_signal)
         sh = None
    source_name = obs.obs_data_get_string(settings, "source")
    source = obs.obs_get_source_by_name(source_name)
    if source:
        sh = obs.obs_source_get_signal_handler(source)
        obs.signal_handler_connect_global(sh, on_source_signal)
    obs.obs_source_release(source)
    pass

def script_unload():
    global sh
    if sh:
         obs.signal_handler_disconnect_global(sh, on_source_signal)
         sh = None

def script_load(settings):
    gsh = obs.obs_get_signal_handler()
    obs.signal_handler_connect_global(gsh, on_global_signal)
    obs.obs_frontend_add_event_callback(on_fe_event_change)
    source = obs.obs_frontend_get_current_transition()
    if source:
        sh = obs.obs_source_get_signal_handler(source)
        obs.signal_handler_connect_global(sh, on_source_signal)
        scene = obs.obs_scene_from_source(source)
        ssh = obs.obs_scene_get_signal_handler(scene)
        obs.signal_handler_connect_global(ssh, on_scene_signal)
    obs.obs_source_release(source)


def script_defaults(settings):
    pass

def script_properties():

    props = obs.obs_properties_create()
    obs.obs_properties_add_text(props, "source", "Source Name", obs.OBS_TEXT_DEFAULT)
    return props



def script_save(settings):
    pass

def on_fe_event_change(event):
    global sh
    print(f"recieved event : {event}, {fe_events[event]}")
    if event == obs.OBS_FRONTEND_EVENT_FINISHED_LOADING or event == obs.OBS_FRONTEND_EVENT_TRANSITION_CHANGED:
        if sh:
             obs.signal_handler_disconnect_global(sh, on_source_signal)
             sh = None
        source = obs.obs_frontend_get_current_transition()
        if source:
            sh = obs.obs_source_get_signal_handler(source)
            obs.signal_handler_connect_global(sh, on_source_signal)
        obs.obs_source_release(source)

def on_global_signal(signal, calldata):
    print(f"recieved signal : {signal}")
    source = obs.calldata_source(calldata, "source")
    if source:
        print(f"source : {obs.obs_source_get_name(source)}")

def on_source_signal(signal, calldata):
    source = obs.calldata_source(calldata, "source")
    print(f"source {obs.obs_source_get_name(source)} recieved signal : {signal}")

def on_scene_signal(signal, calldata):
    source = obs.calldata_source(calldata, "source")
    print(f"source {obs.obs_source_get_name(source)} recieved signal : {signal}")



fe_events = [
    "OBS_FRONTEND_EVENT_STREAMING_STARTING",
    "OBS_FRONTEND_EVENT_STREAMING_STARTED",
    "OBS_FRONTEND_EVENT_STREAMING_STOPPING",
    "OBS_FRONTEND_EVENT_STREAMING_STOPPED",
    "OBS_FRONTEND_EVENT_RECORDING_STARTING",
    "OBS_FRONTEND_EVENT_RECORDING_STARTED",
    "OBS_FRONTEND_EVENT_RECORDING_STOPPING",
    "OBS_FRONTEND_EVENT_RECORDING_STOPPED",
    "OBS_FRONTEND_EVENT_SCENE_CHANGED",
    "OBS_FRONTEND_EVENT_SCENE_LIST_CHANGED",
    "OBS_FRONTEND_EVENT_TRANSITION_CHANGED",
    "OBS_FRONTEND_EVENT_TRANSITION_STOPPED",
    "OBS_FRONTEND_EVENT_TRANSITION_LIST_CHANGED",
    "OBS_FRONTEND_EVENT_SCENE_COLLECTION_CHANGED",
    "OBS_FRONTEND_EVENT_SCENE_COLLECTION_LIST_CHANGED",
    "OBS_FRONTEND_EVENT_PROFILE_CHANGED",
    "OBS_FRONTEND_EVENT_PROFILE_LIST_CHANGED",
    "OBS_FRONTEND_EVENT_EXIT",
    "OBS_FRONTEND_EVENT_REPLAY_BUFFER_STARTING",
    "OBS_FRONTEND_EVENT_REPLAY_BUFFER_STARTED",
    "OBS_FRONTEND_EVENT_REPLAY_BUFFER_STOPPING",
    "OBS_FRONTEND_EVENT_REPLAY_BUFFER_STOPPED",
    "OBS_FRONTEND_EVENT_STUDIO_MODE_ENABLED",
    "OBS_FRONTEND_EVENT_STUDIO_MODE_DISABLED",
    "OBS_FRONTEND_EVENT_PREVIEW_SCENE_CHANGED",
    "OBS_FRONTEND_EVENT_SCENE_COLLECTION_CLEANUP",
    "OBS_FRONTEND_EVENT_FINISHED_LOADING",
    "OBS_FRONTEND_EVENT_RECORDING_PAUSED",
    "OBS_FRONTEND_EVENT_RECORDING_UNPAUSED",
    "OBS_FRONTEND_EVENT_TRANSITION_DURATION_CHANGED",
    "OBS_FRONTEND_EVENT_REPLAY_BUFFER_SAVED",
    "OBS_FRONTEND_EVENT_VIRTUALCAM_STARTED",
    "OBS_FRONTEND_EVENT_VIRTUALCAM_STOPPED",
    "OBS_FRONTEND_EVENT_TBAR_VALUE_CHANGED",
    "OBS_FRONTEND_EVENT_SCENE_COLLECTION_CHANGING",
    "OBS_FRONTEND_EVENT_PROFILE_CHANGING",
    "OBS_FRONTEND_EVENT_SCRIPTING_SHUTDOWN",
    "OBS_FRONTEND_EVENT_PROFILE_RENAMED",
    "OBS_FRONTEND_EVENT_SCENE_COLLECTION_RENAMED",
    "OBS_FRONTEND_EVENT_THEME_CHANGED",
    "OBS_FRONTEND_EVENT_SCREENSHOT_TAKEN",
    "NOT FOUND",
    "NOT FOUND",
    "NOT FOUND",
    "NOT FOUND",
    "NOT FOUND",
    "NOT FOUND",
    "NOT FOUND",
    "NOT FOUND",
    "NOT FOUND",
    "NOT FOUND",
    "NOT FOUND",
    "NOT FOUND",
    "NOT FOUND",
    "NOT FOUND",
    "NOT FOUND",
    "NOT FOUND",
    "NOT FOUND",
    "NOT FOUND",
    "NOT FOUND",
    "NOT FOUND",
    "NOT FOUND",
    "NOT FOUND",
    "NOT FOUND",
]