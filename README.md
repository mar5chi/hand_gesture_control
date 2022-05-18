# hand_gesture_control
A computer vision based hand gesture control for Smart Home appliances using OAK-D, depthai, Raspberry Pi. It also gives an audio feedback if you connect speakers to your Pi.

For information on depthai and OAK-D please visit https://docs.luxonis.com/en/latest/#.

This project uses partially modified https://github.com/geaxgx/depthai_hand_tracker.git.

## Raspberry Pi setup
This project is tested on a Raspberry Pi 3B with \
Raspberry Pi OS with desktop (64 bit) \
Release date: April 4th 2022 \
Kernel version: 5.15 \
downloaded from https://www.raspberrypi.com/software/operating-systems/ \
Python3.9.2 (comes with Raspberry Pi OS) \

### 1. Install dependencies needed by depthai
See also https://docs.luxonis.com/projects/api/en/latest/install/ for more information
```console
sudo curl -fL https://docs.luxonis.com/install_dependencies.sh | bash
```

### 2. Install espeak 
```console
sudo apt-get install espeak
```

### 3. Clone this repository
In a folder of your choice open a terminal and enter: 
```console
git clone https://github.com/mar5chi/hand_gesture_control.git
```

### 4. Create virtual environment
```console
cd hand_gesture_control/
```
Create a virtual environment with name myvenv: 
```console
python3 -m venv myvenv 
```
Activate the virtual environment: 
```console
source myvenv/bin/activate 
```
Update pip, setuptools, wheel: 
```console
pip install -U pip 
pip install -U setuptools 
pip install -U wheel 
```
Install requirements:
```console
python3 -m pip install -r requirements.txt
```

### 5. Run hand gesture control
(cd controls/) \
Optional - To check if your virtual environment is activated enter in the terminal: 
```console
which python
```
this should show the \<path to your install folder\>/myvenv/bin/python 

#### In your activated environment run:
```console
python itemControl.py
```

###  Optional - autostart hand gesture control on reboot: 
In a terminal enter: 
```console
sudo nano /etc/xdg/lxsession/LXDE-pi/autostart
```
  
  Add following line at the end of the autostart file: \
  \<path to your install folder\>/myvenv/bin/python \<path to your install folder\>/itemControl.py \
  Press CTRL+S to save and CTRL+X to exit nano 

```console
sudo reboot
```
