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

# For the audio feedback:
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

def trace(event):
    event.print_line()

def trace_rotation(event):
	# TODO
    event.print_line() 
    print("Rotation:", event.hand.rotation) 

def trace_index_finger_tip(event):
    event.print_line() 
    x, y = event.hand.landmarks[8,:2]
    print(f"Index finger tip : x={x}  y={y}") 

def select_area(area):
    """This is the function to select the area (e.g. kitchen, whole appartment, ...) 
    according to item_tree configuration."""
    selections['area'] = area
    audio_fb(f'You selected {area}, please select function.')
    print(f'area selected: {area}.')

def select_function(function):
    selections['function'] = function
    audio_fb(f'OK, which {function}?')
    print(f'function selected: {function}.')

def select_item(item_key):
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
    # GET current state:
    current_state = iface.get_state(selections['item'])
    print(f'current state: {current_state}.')
    new_state = 'OFF'
    if current_state == 'OFF':    	# toggle state ON/OFF
        new_state = 'ON'
    audio_fb(str(f'The {selections["function"]} is {current_state}. Do you like to switch it {new_state}?'))
    selections['state'] = new_state
    print(f'state selected: {selections["state"]}.')

def handle_percentagetype():
    # GET current state:
    current_state = iface.get_state(selections['item'])
    print(f'current state: {current_state}.')
    audio_fb(str(f'The {selections["function"]} is {current_state} percent. How much do you like?'))

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

def one(event):    								# Kitchen, Lighting, item 1
    global selections
    event.print_line
    if 'area' not in selections:
        area_list = list(item_tree)
        if len(area_list) > 0:
            area = area_list[0]
            select_area(area)
        else:
            audio_fb('Sorry, there is no area one, please select another area.')
    elif 'function' not in selections:
        function_list = list(item_tree[selections['area']])
        if len(function_list) > 0:
            function = function_list[0]
            select_function(function)
        else:
            audio_fb('Sorry, there is no function one, please select another function.')
    elif 'item' not in selections:
        item_list = list(item_tree[selections['area']][selections['function']])
        if len(item_list) > 0:
            item_key = item_list[0]
            select_item(item_key)
        else:
            audio_fb('Sorry, there is no item one, please select another item.')
    else:
        audio_fb('Please finish with OK.')
    print('selections: ') 
    for k, v in selections.items():
        print(f'    {k}: {v}')
    print('------------') 

def two(event):    # Living Room, Blinds, item 2
    global selections
    event.print_line
    if 'area' not in selections:
        area_list = list(item_tree)
        if len(area_list) > 1:
            area = area_list[1]
            select_area(area)
        else:
            audio_fb('Sorry, theres no area two, please select another area.')
    elif 'function' not in selections:
        function_list = list(item_tree[selections['area']])
        if len(function_list) > 1:
            function = function_list[1]
            select_function(function)
        else:
            audio_fb('Sorry, theres no function two, please select another function.')
    elif 'item' not in selections:
        item_list = list(item_tree[selections['area']][selections['function']])
        if len(item_list) > 1:
            item_key = item_list[1]
            select_item(item_key)
        else:
            audio_fb('Sorry, theres no item two, please select another item.')
    else:
        audio_fb('Please finish with OK.')
    print('selections: ') 
    for k, v in selections.items():
        print(f'    {k}: {v}')
    print('------------') 
    
def three(event):   # Bedroom, item 3, ...
    global selections
    event.print_line
    if 'area' not in selections:
        area_list = list(item_tree)
        if len(area_list) > 2:
            area = area_list[2]
            select_area(area)
        else:
            audio_fb('Sorry, theres no area three, please select another area.')
    elif 'function' not in selections:
        function_list = list(item_tree[selections['area']])
        if len(function_list) > 2:
            function = function_list[2]
            select_function(function)
        else:
            audio_fb('Sorry, theres no function three, please select another function.')
    elif 'item' not in selections:
        item_list = list(item_tree[selections['area']][selections['function']])
        if len(item_list) > 2:
            item_key = item_list[2]
            select_item(item_key)
        else:
            audio_fb('Sorry, theres no item three, please select another item.')
    else:
        audio_fb('Please finish with OK.')
    print('selections: ') 
    for k, v in selections.items():
        print(f'    {k}: {v}')
    print('------------') 
	
def four(event):   # Seminar Room, item 4, ...
    global selections
    event.print_line
    if 'area' not in selections:
        area_list = list(item_tree)
        if len(area_list) > 3:
            area = area_list[3]
            select_area(area)
        else:
            audio_fb('Sorry, theres no area four, please select another area.')
    elif 'function' not in selections:
        function_list = list(item_tree[selections['area']])
        if len(function_list) > 3:
            function = function_list[3]
            select_function(function)
        else:
            audio_fb('Sorry, theres no function four, please select another function.')
    elif 'item' not in selections:
        item_list = list(item_tree[selections['area']][selections['function']])
        if len(item_list) > 3:
            item_key = item_list[3]
            select_item(item_key)
        else:
            audio_fb('Sorry, theres no item four, please select another item.')
    else:
        audio_fb('Please finish with OK.')
    print('selections: ') 
    for k, v in selections.items():
        print(f'    {k}: {v}')
    print('------------') 
	
def five(event):   # IoT Lab, item 5, ...
    global selections
    event.print_line
    if 'area' not in selections:
        area_list = list(item_tree)
        if len(area_list) > 4:
            area = area_list[4]
            select_area(area)
        else:
            audio_fb('Sorry, theres no area five, please select another area.')
    elif 'function' not in selections:
        function_list = list(item_tree[selections['area']])
        if len(function_list) > 4:
            function = function_list[4]
            select_function(function)
        else:
            audio_fb('Sorry, theres no function five, please select another function.')
    elif 'item' not in selections:
        item_list = list(item_tree[selections['area']][selections['function']])
        if len(item_list) > 4:
            item_key = item_list[4]
            select_item(item_key)
        else:
            audio_fb('Sorry, theres no item five, please select another item.')
    else:
        audio_fb('Please finish with OK.')
    print('selections: ') 
    for k, v in selections.items():
        print(f'    {k}: {v}')
    print('------------') 
	
def six(event):   # Bathroom, item 6, ...
    global selections
    event.print_line
    if 'area' not in selections:
        area_list = list(item_tree)
        if len(area_list) > 5:
            area = area_list[5]
            select_area(area)
        else:
            audio_fb('Sorry, theres no area six, please select another area.')
    elif 'function' not in selections:
        function_list = list(item_tree[selections['area']])
        if len(function_list) > 5:
            function = function_list[5]
            select_function(function)
        else:
            audio_fb('Sorry, theres no function six, please select another function.')
    elif 'item' not in selections:
        item_list = list(item_tree[selections['area']][selections['function']])
        if len(item_list) > 5:
            item_key = item_list[5]
            select_item(item_key)
        else:
            audio_fb('Sorry, theres no item six, please select another item.')
    else:
        audio_fb('Please finish with OK.')
    print('selections: ') 
    for k, v in selections.items():
        print(f'    {k}: {v}')
    print('------------') 

def ten(event):   # Whole appartment central switches, item 10, ...
    global selections
    event.print_line
    if 'area' not in selections:
        area_list = list(item_tree)
        if len(area_list) > 9:
            area = area_list[9]
            select_area(area)
        else:
            audio_fb('Sorry, theres no area ten, please select another area.')
    elif 'function' not in selections:
        function_list = list(item_tree[selections['area']])
        if len(function_list) > 9:
            function = function_list[9]
            select_function(function)
        else:
            audio_fb('Sorry, theres no function ten, please select another function.')
    elif 'item' not in selections:
        item_list = list(item_tree[selections['area']][selections['function']])
        if len(item_list) > 9:
            item_key = item_list[9]
            select_item(item_key)
        else:
            audio_fb('Sorry, theres no item ten, please select another item.')
    else:
        audio_fb('Please finish with OK.')
    print('selections: ') 
    for k, v in selections.items():
        print(f'    {k}: {v}')
    print('------------') 
    
def back(event):
    """ Goes one step back """
    event.print_line() 
    
    try:
        rk, rv = selections.popitem()
        print(f'removed: {rk} {rv}')
    except KeyError:
        # Dictionary is empty
        print('Selections is empty.') 
        
    print('selections: ') 
    for k, v in selections.items():
        print(f'    {k}: {v}')
    print('------------') 

def quit_selections(event):
    """ Quits all selections and starts from the beginning """
    # Clear selections:
    selections = {}

def audio_fb(text):
    """ Gives auditive feedback """
    speech_controller.kill_proc()
    print(f'say: {text}')
    speech_controller.say(str(text))    # make sure text is a string for espeak

def ok(event):
    """ Completes the input """
    global selections
    event.print_line()
    print('selections: ') 
    for k, v in selections.items():
        print(f'    {k}: {v}')
    print('------------') 
    audio_fb("OK!")
    
    # Post state:
    if 'item' in selections and 'state' in selections:
        r = iface.post_state(selections['item'], selections['state'])
    else:
        print('ERROR: item or state missing.')
        r = 'Error: item or state missing.'
        # TODO handling if item or state missing, e.g. when false recognition of ok,...
    audio_fb(f'Request is {r}.')
    print(f'Request is {r}.')
    
    # Clear selections:
    selections = {}

def shut_down(event):
    """Shuts down the raspberry pi"""
    subprocess.Popen(['sudo','shutdown','-h','now'])


config = {
    'renderer' : {'enable': True},
    
    'pose_actions' : [
        {'name': '1_right_enter', 'pose':'ONE', 'hand':'right', 'callback': 'one',"trigger":"enter", "first_trigger_delay":0.3},
        {'name': '2_right_enter', 'pose':'TWO', 'hand':'right', 'callback': 'two',"trigger":"enter", "first_trigger_delay":0.3},
        {'name': '3_right_enter', 'pose':'THREE', 'hand':'right', 'callback': 'three',"trigger":"enter", "first_trigger_delay":0.3},
        {'name': '4_right_enter', 'pose':'FOUR', 'hand':'right', 'callback': 'four',"trigger":"enter", "first_trigger_delay":0.3},
        {'name': '5_right_enter', 'pose':'FIVE', 'hand':'right', 'callback': 'five',"trigger":"enter", "first_trigger_delay":0.3},
        {'name': '6_right_enter', 'pose':'SIX', 'hand':'right', 'callback': 'six',"trigger":"enter", "first_trigger_delay":0.3},
        {'name': '10_right_enter', 'pose':'ALOHA', 'hand':'right', 'callback': 'ten',"trigger":"enter", "first_trigger_delay":0.3},
        {'name': '12_right_enter', 'pose':'OK', 'hand':'right', 'callback': 'ok',"trigger":"enter", "first_trigger_delay":0.3},
        {'name': '11_right_enter', 'pose':'BACK', 'hand':'right', 'callback': 'back',"trigger":"enter", "first_trigger_delay":0.3},
        {'name': '13_right_enter', 'pose':'HORNS', 'hand':'right', 'callback': 'shut_down',"trigger":"enter", "first_trigger_delay":0.3},
        #{'name': 'trackbar_continuous', 'pose':'TRACK', 'hand':'right', 'callback': 'trackbar',"trigger":"continuous", "first_trigger_delay":0.5, "next_trigger_delay": 0.5},
        {'name': 'trackbar_periodic', 'pose':'TRACK', 'hand':'right', 'callback': 'trackbar',"trigger":"periodic", "first_trigger_delay":0.5, "next_trigger_delay": 0.3},
        {'name': '1_left_continuous_xy', 'pose':'ONE', 'hand':'left', 'callback': 'trace_index_finger_tip',"trigger":"continuous"},
        #{'name': '5_periodic_rotation', 'pose':'FIVE', 'callback': 'trace_rotation', "trigger":"periodic", "first_trigger_delay":0, "next_trigger_delay": 0.2},
    ]
}

HandController(config).loop()
