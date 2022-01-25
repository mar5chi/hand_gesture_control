#!/usr/bin/env python3

README = """
This is the script where all pose actions are configured and the callback functions for 
the HandController are implemented. 

This control is defined with the following parameters of a pose-action:
- trigger : possible values: 
    - enter (default): an event is triggered once, when the pose begins,
    - enter_leave : two events are triggered, one when the pose begins and one when the pose ends,
    - periodic : events are triggered periodically as long as the pose stands.
                 The period is given by the parameter 'next_trigger_delay' in s.
    - continuous : events are triggered on every frame.

- first_trigger_delay: because false positive happen in pose recognition, 
you don't necessarily want to trigger an event on the first frame where the pose is recognized.
The 'first_trigger_delay' in seconds specifies how long the pose has to stand before triggering
an initial event.

"""

print(README)

from HandController import HandController
from SpeechController import SpeechController
import time
import iface
import mediapipe_utils as mpu
import numpy as np
import itemTree
import sys
import subprocess
from HgcException import HgcException

# For audio feedback:
speech_controller = SpeechController()

# Stores the sequence of user selections:
selections = {}

# Trackbar state:
trackbar_state = 0

# Item Tree
try:
    item_tree = itemTree.itemTree
except AttributeError:
    sys.exit("Item tree configuration not found")

def select(index):
    """ Handles the sequence of user selections. """
    global selections
    if 'area' not in selections:
        area_list = list(item_tree)
        if len(area_list) > index:
            area = area_list[index]
            select_area(area)
        else:
            audio_fb(f'Sorry, there is no area {index + 1}, please select another area.')
    elif 'function' not in selections:
        function_list = list(item_tree[selections['area']])
        if len(function_list) > index:
            function = function_list[index]
            select_function(function)
        else:
            audio_fb(f'Sorry, there is no function {index + 1}, please select another function.')
    elif 'item' not in selections:
        item_list = list(item_tree[selections['area']][selections['function']])
        if len(item_list) > index:
            item_key = item_list[index]
            select_item(item_key)
        else:
            audio_fb(f'Sorry, there is no item {index + 1}, please select another item.')
    else:
        audio_fb('Please finish with OK.')
    print('selections: ') 
    for k, v in selections.items():
        print(f'    {k}: {v}')
    print('------------') 

def select_area(area):
    """ This is the function to select the area (e.g. kitchen, whole appartment, ...) 
    according to item_tree configuration. """
    selections['area'] = area
    audio_fb(f'You selected {area}, please select function.')
    print(f'area selected: {area}.')

def select_function(function):
    """ This is the function to select the function (e.g. light, blind, temperature, ...) 
    according to item_tree configuration. """
    selections['function'] = function
    audio_fb(f'OK, which {function}?')
    print(f'function selected: {function}.')

def select_item(item_key):
    """ This is the function to select the item (e.g. dinner table light, ...) 
    according to item_tree configuration. """
    global selections
    print(f'item selected: {item_key}.')
    item = item_tree[selections['area']][selections['function']][item_key] # dict
    if isinstance(item, dict):
        item_name = item.get('name')    # if 'name' is not in the dicts keys, item_name is None
        item_type = item.get('type')
        item_label = item.get('label')
        if item_name:
            selections['item'] = item_name
            if item_label:
                audio_fb(f'You selected {item_label}.')
            else:
                audio_fb(f'You selected {item_name}.')
            if item_type:
                if item_type == 'bool':
                    handle_booltype()
                elif item_type == 'percentage':
                    handle_percentagetype()
            else:
                audio_fb('Sorry, item type not found. Please check configuration file or make another selection.')
                del selections['item']
        else:
            audio_fb('Sorry, item name not found. Please check configuration file or make another selection.')
    else:
        audio_fb('Sorry, wrong item format. Please check configuration file or make another selection.')

def handle_booltype():
    global selections
    # GET current state:
    try:
        current_state = iface.get_state(selections['item'])
        print(f'current state: {current_state}.')
        new_state = 'OFF'
        if current_state == 'OFF':    	# toggle state ON/OFF
            new_state = 'ON'
        audio_fb(str(f'The {selections["function"]} is {current_state.lower()}. Do you like to switch it {new_state.lower()}?'))
        selections['state'] = new_state
        print(f'state selected: {selections["state"]}.')
    except HgcException as he:
        audio_fb(f'Sorry, could not get current state. {he.args[0]} Please check connection to rest API.')
        # Clear selections:
        selections = {}
        # TODO: maybe sys.exit(he.args[0]) after this?

def handle_percentagetype():
    global selections
    # GET current state:
    try:
        current_state = iface.get_state(selections['item'])
        print(f'current state: {current_state}.')
        audio_fb(str(f'The {selections["function"]} is {current_state} percent. How much do you like?'))
    except HgcException as he:
        audio_fb(f'Sorry, could not get current state. {he.args[0]} Please check connection to rest API.')
        # Clear selections:
        selections = {}
        # TODO: maybe sys.exit(he.args[0]) after this?

def trackbar(event):
    """ Sets numbers dynamically between 0 and 100, e.g. state for dimmer, blinds, temperature """
    global trackbar_state
    
    dist = event.hand.distance_4_8
    percent = np.interp(dist, [0.2, 0.7], [0, 100])  # percentage
    smoothness = 10
    
    value = smoothness * round(percent / smoothness)
    if value > trackbar_state or value < trackbar_state:
        print(f"trackbar: value = {value}") 
        trackbar_state = value
        if value == 0:
            audio_fb('zero')
        else:
            audio_fb(value)
    selections['state'] = str(value)

def one(event):     # Kitchen, Lighting, item 1
    """ Callback for pose ONE. """
    select(0)

def two(event):     # Living Room, Blinds, item 2
    """ Callback for pose TWO. """
    select(1)
    
def three(event):   # Bedroom, item 3, ...
    """ Callback for pose THREE. """
    select(2)
	
def four(event):    # Seminar Room, item 4, ...
    """ Callback for pose FOUR. """
    select(3)
	
def five(event):    # IoT Lab, item 5, ...
    """ Callback for pose FIVE. """
    select(4)
	
def six(event):     # Bathroom, item 6, ...
    """ Callback for pose SIX. """
    select(5)

def ten(event):     # Whole appartment central switches, item 10, ...
    """ Callback for pose TEN. """
    select(9)
    
def back(event):
    """ Goes one step back. """
    event.print_line() 
    
    try:
        rk, rv = selections.popitem()
        print(f'removed: {rk} {rv}')
        audio_fb("Going back.")
        if 'area' not in selections:
            audio_fb("Please select area.")
        elif 'function' not in selections:
            audio_fb("Please select function.")
        elif 'item' not in selections:
            audio_fb("Please select item.")
    except KeyError:
        # Dictionary is empty
        print('Selections is empty.') 
        audio_fb("Please select area.")
        
    print('selections: ') 
    for k, v in selections.items():
        print(f'    {k}: {v}')
    print('------------') 

def quit_selections(event):
    """ Quits all selections and starts from the beginning. """
    # Clear selections:
    selections = {}

def audio_fb(text):
    """ Gives auditive feedback. """
    speech_controller.kill_proc()
    print(f'say: {text}')
    speech_controller.say(str(text))    # make sure text is a string for espeak

def ok(event):
    """ Completes the input, posts state. """
    global selections
    event.print_line()
    print('selections: ') 
    for k, v in selections.items():
        print(f'    {k}: {v}')
    print('------------') 
    audio_fb("OK!")
    
    # Post state:
    if 'item' in selections and 'state' in selections:
        try:
            r = iface.post_state(selections['item'], selections['state'])
        except HgcException as he:
            r = f'Sorry, could not set state. {he.args[0]} Please check connection to rest API.'
            # TODO: maybe sys.exit(he.args[0]) after this?
    else:
        print('ERROR: item or state missing.')
        r = 'Error: item or state missing.'
    audio_fb(f'Request is {r}.')
    print(f'Request is {r}.')
    
    # Clear selections:
    selections = {}

def shut_down(event):
    """ Shuts down the raspberry pi """
    subprocess.Popen(['sudo','shutdown','-h','now'])


config = {
    'renderer' : {'enable': True},
    
    'pose_actions' : [
        {'name': '1_any_enter', 'pose':'ONE', 'hand':'any', 'callback': 'one',"trigger":"enter", "first_trigger_delay":0.3},
        {'name': '2_any_enter', 'pose':'TWO', 'hand':'any', 'callback': 'two',"trigger":"enter", "first_trigger_delay":0.3},
        {'name': '3_any_enter', 'pose':'THREE', 'hand':'any', 'callback': 'three',"trigger":"enter", "first_trigger_delay":0.3},
        {'name': '4_any_enter', 'pose':'FOUR', 'hand':'any', 'callback': 'four',"trigger":"enter", "first_trigger_delay":0.3},
        {'name': '5_any_enter', 'pose':'FIVE', 'hand':'any', 'callback': 'five',"trigger":"enter", "first_trigger_delay":0.3},
        {'name': '6_any_enter', 'pose':'SIX', 'hand':'any', 'callback': 'six',"trigger":"enter", "first_trigger_delay":0.3},
        {'name': '10_any_enter', 'pose':'ALOHA', 'hand':'any', 'callback': 'ten',"trigger":"enter", "first_trigger_delay":0.3},
        {'name': '11_any_enter', 'pose':'BACK', 'hand':'any', 'callback': 'back',"trigger":"enter", "first_trigger_delay":0.3},
        {'name': '12_any_enter', 'pose':'OK', 'hand':'any', 'callback': 'ok',"trigger":"enter", "first_trigger_delay":0.3},
        {'name': '13_any_enter', 'pose':'HORNS', 'hand':'any', 'callback': 'shut_down',"trigger":"enter", "first_trigger_delay":1},
        {'name': 'trackbar_periodic', 'pose':'TRACK', 'hand':'any', 'callback': 'trackbar',"trigger":"periodic", "first_trigger_delay":0.5, "next_trigger_delay": 0.3},
    ]
}

HandController(config).loop()
