# hand_gesture_control
A computer vision based hand gesture control for Smart Home appliances using OAK-D, depthai, Raspberry Pi. It also gives an audio feedback if you connect speakers to your Pi.

For information on depthai and OAK-D please visit https://docs.luxonis.com/en/latest/#.

This project uses partially modified https://github.com/geaxgx/depthai_hand_tracker.git.

## Raspberry Pi setup
This project is tested on a Raspberry Pi 3B with \
Raspberry Pi OS with desktop (32 bit) \
Release date: October 30th 2021 \
Kernel version: 5.10 \
downloaded from https://www.raspberrypi.com/software/operating-systems/ \
Python3.9.2 (comes with Raspberry Pi OS) \

### 1. Install dependencies needed by depthai
See also: https://docs.luxonis.com/projects/api/en/latest/install/ \
sudo curl -fL https://docs.luxonis.com/install_dependencies.sh | bash

### 2. Install espeak 
sudo apt-get install espeak

### 3. Clone this repository
in a folder of your choice open a terminal and enter: \
git clone https://github.com/mar5chi/hand_gesture_control.git

### 4. Create virtual environment
cd hand_gesture_control/ 
#### Create virtual environment with name myvenv: 
python3 -m venv myvenv 
#### Activate the virtual environment: 
source myvenv/bin/activate 
#### Update pip, setuptools, wheel: 
pip install -U pip \
pip install -U setuptools \
pip install -U wheel 
#### Install requirements:
python3 -m pip install -r requirements.txt

### 5. Run hand gesture control
(cd controls/) \
To make sure your virtual environment is activated enter in the terminal: \
which python \
this should show the <path to your virtual environment>/bin/python 

#### In your activated environment run:
python itemControl.py

###  Optional - autostart hand gesture control on reboot: 
In a terminal enter: \
sudo nano /etc/xdg/lxsession/LXDE-pi/autostart
  
  Add following line at the end of the autostart file: \
  \<path to your install folder\>/myvenv/bin/python \<path to your install folder\>/itemControl.py \
  Press CTRL+S to save then CTRL+X to exit nano \
    
sudo reboot
