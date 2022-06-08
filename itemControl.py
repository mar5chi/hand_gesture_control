#!/usr/bin/env python3

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

class ItemController():
    """
    This is the class where all pose actions are configured and the callback functions for 
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
    def __init__(self):
        # Load Item Tree (= Smart Home configuration):
        try:
            self.item_tree = itemTree.itemTree
        except AttributeError:
            sys.exit("Item tree configuration not found")

        # For audio feedback:
        self.speech_controller = SpeechController()

        # Stores the sequence of user selections:
        self.selections = {}

        # Trackbar state:
        self.trackbar_state = 0

        # Awake (when True: ready to recognize gestures other than the wakeup gesture)
        self.awake = False

        # Stores what to show on the display:
        self.to_display = 'I am sleeping, please wake me up ...'

        # Config:
        self.config = {
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
                {'name': '14_any_enter', 'pose':'WAKEUP', 'hand':'any', 'callback': 'wake_up',"trigger":"enter", "first_trigger_delay":1},
                {'name': 'trackbar_periodic', 'pose':'TRACK', 'hand':'any', 'callback': 'trackbar',"trigger":"periodic", "first_trigger_delay":0.5, "next_trigger_delay": 0.3},
            ]
        }

    def wake_up(self, event):
        if self.awake:
            self.awake = False
            fb = "I am sleeping, please wake me up ..."
            self.feedback(fb)
            self.selections = {}
        else:
            fb = "Hi, please select area..."
            self.feedback(fb)
            self.awake = True

    def select(self, index):
        """ Handles the sequence of user selections. """
        if 'area' not in self.selections:
            area_list = list(self.item_tree)
            if len(area_list) > index:
                area = area_list[index]
                self.select_area(area)
            else:
                fb = f'Sorry, there is no area {index + 1}, please select another area.'
                self.feedback(fb)
        elif 'function' not in self.selections:
            function_list = list(self.item_tree[self.selections['area']])
            if len(function_list) > index:
                function = function_list[index]
                self.select_function(function)
            else:
                fb = f'Sorry, there is no function {index + 1}, please select another function.'
                self.feedback(fb)
        elif 'item' not in self.selections:
            item_list = list(self.item_tree[self.selections['area']][self.selections['function']])
            if len(item_list) > index:
                item_key = item_list[index]
                self.select_item(item_key)
            else:
                fb = f'Sorry, there is no item {index + 1}, please select another item.'
                self.feedback(fb)
        else:
            fb = 'Please finish with OK.'
            self.feedback(fb)
        print('selections: ') 
        for k, v in self.selections.items():
            print(f'    {k}: {v}')
        print('------------') 

    def select_area(self, area):
        """ This is the function to select the area (e.g. kitchen, whole appartment, ...) 
        according to item_tree configuration. """
        self.selections['area'] = area
        fb = f'You selected {area}, please select function.'
        self.feedback(fb)
        print(f'area selected: {area}.')

    def select_function(self, function):
        """ This is the function to select the function (e.g. light, blind, temperature, ...) 
        according to item_tree configuration. """
        self.selections['function'] = function
        fb = f'OK, which {function}?'
        self.feedback(fb)
        print(f'function selected: {function}.')

    def select_item(self, item_key):
        """ This is the function to select the item (e.g. dinner table light, ...) 
        according to item_tree configuration. """
        print(f'item selected: {item_key}.')
        item = self.item_tree[self.selections['area']][self.selections['function']][item_key] # dict
        if isinstance(item, dict):
            item_name = item.get('name')    # if 'name' is not in the dicts keys, item_name is None
            item_type = item.get('type')
            item_label = item.get('label')
            if item_name:
                self.selections['item'] = item_name
                if item_label:
                    fb = f'You selected {item_label}.'
                    self.feedback(fb)
                else:
                    fb = f'You selected {item_name}.'
                    self.feedback(fb)
                if item_type:
                    if item_type == 'bool':
                        self.handle_booltype()
                    elif item_type == 'percentage':
                        self.handle_percentagetype()
                else:
                    fb = 'Sorry, item type not found. Please check configuration file or make another selection.'
                    self.feedback(fb)
                    del self.selections['item']
            else:
                fb = 'Sorry, item name not found. Please check configuration file or make another selection.'
                self.feedback(fb)
        else:
            fb = 'Sorry, wrong item format. Please check configuration file or make another selection.'
            self.feedback(fb)

    def handle_booltype(self):
        # GET current state:
        try:
            current_state = iface.get_state(self.selections['item'])
            self.selections['current state'] = current_state
            print(f'current state: {current_state}.')
            new_state = 'OFF'
            if current_state == 'OFF':    	# toggle state ON/OFF
                new_state = 'ON'
            fb = str(f'The {self.selections["function"]} is {current_state.lower()}. Do you like to switch it {new_state.lower()}?')
            self.feedback(fb)
            self.selections['state'] = new_state
            print(f'state selected: {self.selections["state"]}.')
        except HgcException as he:
            fb = f'Sorry, could not get current state. {he.args[0]} Please check connection to rest API.'
            self.feedback(fb)
            # Clear selections:
            self.selections = {}
            # TODO: maybe sys.exit(he.args[0]) after this?

    def handle_percentagetype(self):
        # GET current state:
        try:
            current_state = iface.get_state(self.selections['item'])
            self.selections['current state'] = current_state
            print(f'current state: {current_state}.')
            fb = str(f'The {self.selections["function"]} is {current_state} percent. How much do you like?')
            self.feedback(fb)
        except HgcException as he:
            fb = f'Sorry, could not get current state. {he.args[0]} Please check connection to rest API.'
            self.feedback(fb)
            # Clear selections:
            self.selections = {}
            # TODO: maybe sys.exit(he.args[0]) after this?

    def trackbar(self, event):
        """ Sets numbers dynamically between 0 and 100, e.g. state for dimmer, blinds, temperature """
        if 'item' in self.selections:
            dist = event.hand.distance_4_8
            percent = np.interp(dist, [0.2, 0.7], [0, 100])  # percentage
            smoothness = 10

            value = smoothness * round(percent / smoothness)
            if value > self.trackbar_state or value < self.trackbar_state:
                print(f"trackbar: value = {value}") 
                self.trackbar_state = value
                if value == 0:
                    self.to_display = '0'
                    self.audio_fb('zero')
                else:
                    self.feedback(str(value))
            self.selections['state'] = str(value)

    def back(self, event):
        """ Goes one step back. """
        event.print_line() 

        try:
            rk, rv = self.selections.popitem()
            print(f'removed: {rk} {rv}')
            self.feedback("Going back.")
            if 'area' not in self.selections:
                self.feedback("Please select area ...")
            elif 'function' not in self.selections:
                self.feedback("Please select function ...")
            elif 'item' not in self.selections:
                self.feedback("Please select item ...")
        except KeyError:
            # Dictionary is empty
            print('Selections is empty.') 
            self.feedback("Please select area ...")

        print('selections: ') 
        for k, v in self.selections.items():
            print(f'    {k}: {v}')
        print('------------') 

    #def quit_selections(self, event):
    #    """ Quits all selections and starts from the beginning. """
    #    # Clear selections:
    #    self.selections = {}

    def audio_fb(self, text):
        """ Gives auditive feedback. """
        self.speech_controller.kill_proc()
        print(f'say: {text}')
        self.speech_controller.say(str(text))    # make sure text is a string for espeak

    def ok(self, event):
        """ Completes the input, posts state. """
        event.print_line()
        print('selections: ') 
        for k, v in self.selections.items():
            print(f'    {k}: {v}')
        print('------------') 
        self.feedback("OK!")

        # Post state:
        if 'item' in self.selections and 'state' in self.selections:
            try:
                r = iface.post_state(self.selections['item'], self.selections['state'])
            except HgcException as he:
                r = f'Sorry, could not set state. {he.args[0]} Please check connection to rest API.'
                # TODO: maybe sys.exit(he.args[0]) after this?
        else:
            print('ERROR: item or state missing.')
            r = 'Error: item or state missing.'
        fb = f'Request is {r}.'
        self.feedback(fb)
        print(f'Request is {r}.')

        # Clear selections:
        self.selections = {}
        self.awake = False

    #def shut_down(self, event):
    #    """ Shuts down the raspberry pi """
    #    # subprocess.Popen(['sudo','shutdown','-h','now'])
    #    self.awake = False
    #    self.selections = {}
    #    fb = 'I am sleeping, please wake me up ...'
    #    self.feedback(fb)
    #    print(fb)
    
    def handle_event(self, event):
        print('handle_event(self, event):')
        event.print_line
        #print(f'event.callback: {event.callback}')
        #print(f'locals: {locals()}')
        #print(f'globalss: {globals()}')
        cb = event.callback
        if cb == 'wake_up':
            self.wake_up(event)
        elif cb == 'one':
            self.select(0)
        elif cb == 'two':
            self.select(1)
        elif cb == 'three':
            self.select(2)
        elif cb == 'four':
            self.select(3)
        elif cb == 'five':
            self.select(4)
        elif cb == 'six':
            self.select(5)
        elif cb == 'ten':
            self.select(9)
        elif cb == 'trackbar':
            self.trackbar(event)
        elif cb == 'back':
            self.back(event)
        elif cb == 'ok':
            self.ok(event)
        elif cb == 'shut_down':
            self.shut_down(event)
    
    def feedback(self, feedback):
        self.to_display = str(feedback)
        self.audio_fb(feedback)
    
    def start(self):
        #HandController(self.config).loop()
        HandController(self).loop()



def main():
    itemControl = ItemController()
    #print(itemControl.config)
    itemControl.start()

if __name__ == '__main__':
    main()
