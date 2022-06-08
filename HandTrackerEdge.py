import numpy as np
from collections import namedtuple
import mediapipe_utils as mpu
import depthai as dai
import cv2
from pathlib import Path
from FPS import FPS, now
import time
import sys
from string import Template
import marshal


SCRIPT_DIR = Path(__file__).resolve().parent
PALM_DETECTION_MODEL = str(SCRIPT_DIR / "models/palm_detection_sh4.blob")
LANDMARK_MODEL = str(SCRIPT_DIR / "models/hand_landmark_sh4.blob")
DETECTION_POSTPROCESSING_MODEL = str(SCRIPT_DIR / "custom_models/DetectionBestCandidate_sh1.blob")
TEMPLATE_MANAGER_SCRIPT = str(SCRIPT_DIR / "template_manager_script.py")

def to_planar(arr: np.ndarray, shape: tuple) -> np.ndarray:
    return cv2.resize(arr, shape).transpose(2,0,1).flatten()



class HandTracker:
    """
    Mediapipe Hand Tracker for depthai
    Arguments:
    - input_src: frame source, 
                    - "rgb" or None: OAK* internal color camera,
                    - "rgb_laconic": same as "rgb" but without sending the frames to the host (Edge mode only),
                    - a file path of an image or a video,
                    - an integer (eg 0) for a webcam id,
                    In edge mode, only "rgb" and "rgb_laconic" are possible
    - pd_model: palm detection model blob file (if None, takes the default value PALM_DETECTION_MODEL),
    - pd_score: confidence score to determine whether a detection is reliable (a float between 0 and 1).
    - pd_nms_thresh: NMS threshold.
    - use_lm: boolean. When True, run landmark model. Otherwise, only palm detection model is run
    - lm_model: landmark model blob file
                    - None : the default blob file LANDMARK_MODEL,
                    - a path of a blob file. 
    - lm_score_thresh : confidence score to determine whether landmarks prediction is reliable (a float between 0 and 1).
    - pp_model: path to the detection post processing model,
    - solo: boolean, when True detect one hand max (much faster since we run the pose detection model only if no hand was detected in the previous frame)
                    On edge mode, always True
    - internal_fps : when using the internal color camera as input source, set its FPS to this value (calling setFps()).
    - resolution : sensor resolution "full" (1920x1080) or "ultra" (3840x2160),
    - internal_frame_height : when using the internal color camera, set the frame height (calling setIspScale()).
                    The width is calculated accordingly to height and depends on value of 'crop'
    - use_gesture : boolean, when True, recognize hand poses froma predefined set of poses
                    (ONE, TWO, THREE, FOUR, FIVE, OK, PEACE, FIST)
    - body_model : Movenet single pose model: "lightning", "thunder"
    - body_score_thresh : Movenet score thresh
    - hands_up_only: boolean. When using body_pre_focusing, if hands_up_only is True, consider only hands for which the wrist keypoint
                    is above the elbow keypoint.
    - stats : boolean, when True, display some statistics when exiting.   
    - trace: boolean, when True print some debug messages or show output of ImageManip nodes
                    (used only in Edge mode)   
    """
    def __init__(self, input_src=None,
                pd_model=None, 
                pd_score_thresh=0.5, pd_nms_thresh=0.3,
                use_lm=True,
                lm_model=None,
                lm_score_thresh=0.5,
                pp_model = DETECTION_POSTPROCESSING_MODEL,
                solo=True,
                internal_fps=None,
                resolution="full",
                internal_frame_height=640,  # see HandController DEFAULT Config
                use_gesture=False,
                stats=False,
                trace=False
                #trace=True
                ):

        self.use_lm = use_lm
        if not use_lm:
            print("use_lm=False is not supported in Edge mode.")
            sys.exit()
        self.pd_model = pd_model if pd_model else PALM_DETECTION_MODEL
        print(f"Palm detection blob : {self.pd_model}")
        self.lm_model = lm_model if lm_model else LANDMARK_MODEL
        print(f"Landmark blob       : {self.lm_model}")

        self.pd_score_thresh = pd_score_thresh
        self.pd_nms_thresh = pd_nms_thresh
        self.lm_score_thresh = lm_score_thresh
        self.pp_model = pp_model
        if not solo:
            print("Warning: non solo mode is not implemented in edge mode. Continuing in solo mode.")
        self.solo = True
           
        self.stats = stats
        self.trace = trace
        self.use_gesture = use_gesture

        self.device = dai.Device()

        if input_src == None or input_src == "rgb" or input_src == "rgb_laconic":
            # Note that here (in Host mode), specifying "rgb_laconic" has no effect
            # Color camera frames are systematically transferred to the host
            self.input_type = "rgb" # OAK* internal color camera
            self.laconic = input_src == "rgb_laconic" # Camera frames are not sent to the host
            if resolution == "full":
                self.resolution = (1920, 1080)
            elif resolution == "ultra":
                self.resolution = (3840, 2160)
            else:
                print(f"Error: {resolution} is not a valid resolution !")
                sys.exit()
            print("Sensor resolution:", self.resolution)

            if internal_fps is None:
                self.internal_fps = 30
            else:
                self.internal_fps = internal_fps 
            print(f"Internal camera FPS set to: {self.internal_fps}") 

            self.video_fps = self.internal_fps # Used when saving the output in a video file. Should be close to the real fps

            width, self.scale_nd = mpu.find_isp_scale_params(internal_frame_height * self.resolution[0] / self.resolution[1], self.resolution, is_height=False)
            # --------------------------------------------------------------------------------------------
            print(f'HandTrackerEdge __init__: width={width}, scale_nd={self.scale_nd}, internal_frame_height={internal_frame_height}, self.resolution={self.resolution}')
            # -> output: HandTrackerEdge __init__: width=800, scale_nd=(5, 12), internal_frame_height=450, self.resolution=(1920, 1080)
            # --------------------------------------------------------------------------------------------
            self.img_h = int(round(self.resolution[1] * self.scale_nd[0] / self.scale_nd[1]))
            self.img_w = int(round(self.resolution[0] * self.scale_nd[0] / self.scale_nd[1]))
            self.pad_h = (self.img_w - self.img_h) // 2
            self.pad_w = 0
            self.frame_size = self.img_w
            self.crop_w = 0
        
            print(f"Internal camera image size: {self.img_w} x {self.img_h} - pad_h: {self.pad_h}")

        else:
            print("Invalid input source:", input_src)
            sys.exit()

        # Define and start pipeline
        usb_speed = self.device.getUsbSpeed()
        self.device.startPipeline(self.create_pipeline())
        print(f"Pipeline started - USB speed: {str(usb_speed).split('.')[-1]}")

        # Define data queues 
        if not self.laconic:
            self.q_video = self.device.getOutputQueue(name="cam_out", maxSize=1, blocking=False)
        self.q_manager_out = self.device.getOutputQueue(name="manager_out", maxSize=1, blocking=False)
        # For showing outputs of ImageManip nodes (debugging)
        if self.trace:
            self.q_pre_pd_manip_out = self.device.getOutputQueue(name="pre_pd_manip_out", maxSize=1, blocking=False)
            self.q_pre_lm_manip_out = self.device.getOutputQueue(name="pre_lm_manip_out", maxSize=1, blocking=False)    

        self.fps = FPS()

        self.nb_pd_inferences = 0
        self.nb_lm_inferences = 0
        self.nb_lm_inferences_after_landmarks_ROI = 0
        self.nb_frames_no_hand = 0
        self.nb_spatial_requests = 0
        self.glob_pd_rtrip_time = 0
        self.glob_lm_rtrip_time = 0
        self.glob_spatial_rtrip_time = 0
        

    def create_pipeline(self):
        print("Creating pipeline...")
        # Start defining a pipeline
        pipeline = dai.Pipeline()
        pipeline.setOpenVINOVersion(version = dai.OpenVINO.Version.VERSION_2021_4)
        self.pd_input_length = 128

        # ColorCamera
        print("Creating Color Camera...")
        cam = pipeline.createColorCamera()
        if self.resolution[0] == 1920:
            cam.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        else:
            cam.setResolution(dai.ColorCameraProperties.SensorResolution.THE_4_K)
        cam.setBoardSocket(dai.CameraBoardSocket.RGB)
        cam.setInterleaved(False)
        cam.setIspScale(self.scale_nd[0], self.scale_nd[1])
        cam.setFps(self.internal_fps)

        cam.setVideoSize(self.img_w, self.img_h)
        cam.setPreviewSize(self.img_w, self.img_h)

        if not self.laconic:
            cam_out = pipeline.createXLinkOut()
            cam_out.setStreamName("cam_out")
            cam_out.input.setQueueSize(1)
            cam_out.input.setBlocking(False)
            cam.video.link(cam_out.input)

        # Define manager script node
        manager_script = pipeline.create(dai.node.Script)
        manager_script.setScript(self.build_manager_script())

        # Define palm detection pre processing: resize preview to (self.pd_input_length, self.pd_input_length)
        print("Creating Palm Detection pre processing image manip...")
        pre_pd_manip = pipeline.create(dai.node.ImageManip)
        pre_pd_manip.setMaxOutputFrameSize(self.pd_input_length*self.pd_input_length*3)
        pre_pd_manip.setWaitForConfigInput(True)
        pre_pd_manip.inputImage.setQueueSize(1)
        pre_pd_manip.inputImage.setBlocking(False)
        cam.preview.link(pre_pd_manip.inputImage)
        manager_script.outputs['pre_pd_manip_cfg'].link(pre_pd_manip.inputConfig)

        # For debugging
        if self.trace:
            pre_pd_manip_out = pipeline.createXLinkOut()
            pre_pd_manip_out.setStreamName("pre_pd_manip_out")
            pre_pd_manip.out.link(pre_pd_manip_out.input)

        # Define palm detection model
        print("Creating Palm Detection Neural Network...")
        pd_nn = pipeline.create(dai.node.NeuralNetwork)
        pd_nn.setBlobPath(self.pd_model)
        # Increase threads for detection
        # pd_nn.setNumInferenceThreads(2)
        pre_pd_manip.out.link(pd_nn.input)

        # Define pose detection post processing "model"
        print("Creating Palm Detection post processing Neural Network...")
        post_pd_nn = pipeline.create(dai.node.NeuralNetwork)
        post_pd_nn.setBlobPath(self.pp_model)
        pd_nn.out.link(post_pd_nn.input)
        post_pd_nn.out.link(manager_script.inputs['from_post_pd_nn'])
        
        # Define link to send result to host 
        manager_out = pipeline.create(dai.node.XLinkOut)
        manager_out.setStreamName("manager_out")
        manager_script.outputs['host'].link(manager_out.input)

        # Define landmark pre processing image manip
        print("Creating Landmark pre processing image manip...") 
        self.lm_input_length = 224
        pre_lm_manip = pipeline.create(dai.node.ImageManip)
        pre_lm_manip.setMaxOutputFrameSize(self.lm_input_length*self.lm_input_length*3)
        pre_lm_manip.setWaitForConfigInput(True)
        pre_lm_manip.inputImage.setQueueSize(1)
        pre_lm_manip.inputImage.setBlocking(False)
        cam.preview.link(pre_lm_manip.inputImage)

        # For debugging
        if self.trace:
            pre_lm_manip_out = pipeline.createXLinkOut()
            pre_lm_manip_out.setStreamName("pre_lm_manip_out")
            pre_lm_manip.out.link(pre_lm_manip_out.input)

        manager_script.outputs['pre_lm_manip_cfg'].link(pre_lm_manip.inputConfig)

        # Define landmark model
        print("Creating Hand Landmark Neural Network...")          
        lm_nn = pipeline.create(dai.node.NeuralNetwork)
        lm_nn.setBlobPath(self.lm_model)
        # lm_nn.setNumInferenceThreads(1)
        pre_lm_manip.out.link(lm_nn.input)
        lm_nn.out.link(manager_script.inputs['from_lm_nn'])
            
        print("Pipeline created.")
        return pipeline        
    
    def build_manager_script(self):
        '''
        The code of the scripting node 'manager_script' depends on :
            - the score threshold,
            - the video frame shape
        So we build this code from the content of the file template_manager_script.py which is a python template
        '''
        # Read the template
        with open(TEMPLATE_MANAGER_SCRIPT, 'r') as file:  # template_manager_script.py
            template = Template(file.read())
        
        # Perform the substitution
        code = template.substitute(
                    _TRACE = "node.warn" if self.trace else "#",
                    _pd_score_thresh = self.pd_score_thresh,
                    _lm_score_thresh = self.lm_score_thresh,
                    _pad_h = self.pad_h,
                    _img_h = self.img_h,
                    _img_w = self.img_w,
                    _frame_size = self.frame_size,
                    _crop_w = self.crop_w,
                    _buffer_size = 1138,  # _buffer_size = 1185 if self.xyz else 1138,
                    _first_branch = 1     # _first_branch = 0 if self.body_pre_focusing else 1,
        )
        # Remove comments and empty lines
        import re                                                  # regular expression
        code = re.sub(r'"{3}.*?"{3}', '', code, flags=re.DOTALL)   # "{3} - 3 times """, match any character 0 or more occurences, 3 times """
        code = re.sub(r'#.*', '', code)
        code = re.sub('\n\s*\n', '\n', code)
        # {m} -- occurs “m” times	sd{3} = sddd
        # . (a period) -- matches any single character except newline '\n' 
        # + -- 1 or more occurrences of the pattern to its left, e.g. 'i+' = one or more i's
        # * -- 0 or more occurrences of the pattern to its left
        # ? -- match 0 or 1 occurrences of the pattern to its left 
        #  re.DOTALL
            # Make the '.' special character match any character at all, including a newline; 
            # without this flag, '.' will match anything except a newline. Corresponds to the inline flag (?s).

        # For debugging
        if self.trace:
            with open("tmp_code.py", "w") as file:
                file.write(code)

        return code

    # --------------------------------------------------------------------
    def print_norm_landmarks(self, r):
        for i, l in enumerate(r.norm_landmarks):
            print(f'landmark [{i}]: {r.norm_landmarks[i]}')
            for j, lm in enumerate(l):
                print(f'[{i}][{j}]: {r.norm_landmarks[i][j]}', end=' - ')
            print() # line break
        time.sleep(1)
    # --------------------------------------------------------------------
    
    def recognize_gesture(self, r):           
        #-----------------------------------------------------------------
        #self.print_norm_landmarks(r)
        #-----------------------------------------------------------------
        # Finger states
        # state: -1=unknown, 0=close, 1=open
        d_3_5 = mpu.distance(r.norm_landmarks[3], r.norm_landmarks[5])
        d_2_3 = mpu.distance(r.norm_landmarks[2], r.norm_landmarks[3])
        # ---------------------------------------------------------------
        d_4_8 = mpu.distance(r.norm_landmarks[4], r.norm_landmarks[8])      # thumb - index tip, for tracker
        d_8_12 = mpu.distance(r.norm_landmarks[8], r.norm_landmarks[12])    # index - middle tip for back and wake_up
        d_12_16 = mpu.distance(r.norm_landmarks[12], r.norm_landmarks[16])  # middle - ring tip, for back and wake_up
        d_15_20 = mpu.distance(r.norm_landmarks[15], r.norm_landmarks[20])  # ring - pinky tip,  for back and wake_up
        #print(f'HandTrackerEdge norm_landmarks[4]: {r.norm_landmarks[4]}')
        #print(f'HandTrackerEdge norm_landmarks[8]: {r.norm_landmarks[8]}')
        #print(f'HandTrackerEdge d_4_8: {d_4_8}')
        #print(f'HandTrackerEdge d_8_12: {d_8_12}')
        #print(f'HandTrackerEdge d_12_16: {d_12_16}')
        # ---------------------------------------------------------------
        angle0 = mpu.angle(r.norm_landmarks[0], r.norm_landmarks[1], r.norm_landmarks[2])
        angle1 = mpu.angle(r.norm_landmarks[1], r.norm_landmarks[2], r.norm_landmarks[3])
        angle2 = mpu.angle(r.norm_landmarks[2], r.norm_landmarks[3], r.norm_landmarks[4])
        r.thumb_angle = angle0+angle1+angle2
        if angle0+angle1+angle2 > 460 and d_3_5 / d_2_3 > 1.2: 
            r.thumb_state = 1
        else:
            r.thumb_state = 0

        if r.norm_landmarks[8][1] < r.norm_landmarks[7][1] < r.norm_landmarks[6][1]:
            r.index_state = 1
        elif r.norm_landmarks[6][1] < r.norm_landmarks[8][1]:
            r.index_state = 0
        else:
            r.index_state = -1

        if r.norm_landmarks[12][1] < r.norm_landmarks[11][1] < r.norm_landmarks[10][1]:
            r.middle_state = 1
        elif r.norm_landmarks[10][1] < r.norm_landmarks[12][1]:
            r.middle_state = 0
        else:
            r.middle_state = -1

        if r.norm_landmarks[16][1] < r.norm_landmarks[15][1] < r.norm_landmarks[14][1]:
            r.ring_state = 1
        elif r.norm_landmarks[14][1] < r.norm_landmarks[16][1]:
            r.ring_state = 0
        else:
            r.ring_state = -1

        if r.norm_landmarks[20][1] < r.norm_landmarks[19][1] < r.norm_landmarks[18][1]:
            r.little_state = 1
        elif r.norm_landmarks[18][1] < r.norm_landmarks[20][1]:
            r.little_state = 0
        else:
            r.little_state = -1

        # Gesture
        if r.thumb_state == 0 and r.index_state == 0 and r.middle_state == 0 and r.ring_state == 0 and r.little_state == 0:
            r.gesture = "FIST"
        elif r.thumb_state == 1 and r.index_state == 0 and r.middle_state == 0 and r.ring_state == 0 and r.little_state == 0:
            r.gesture = "OK" 
        elif r.thumb_state == 1 and r.index_state == 1 and r.middle_state == 0 and r.ring_state == 0 and r.little_state == 0:
            r.gesture = "TRACK"
        elif r.thumb_state == 0 and r.index_state == 1 and r.middle_state == 0 and r.ring_state == 0 and r.little_state == 0:
            r.gesture = "ONE"
        elif r.thumb_state == 0 and r.index_state == 1 and r.middle_state == 1 and r.ring_state == 0 and r.little_state == 0:
            r.gesture = "TWO"
        elif r.thumb_state == 1 and r.index_state == 1 and r.middle_state == 1 and r.ring_state == 0 and r.little_state == 0:
            r.gesture = "THREE"
        elif r.thumb_state == 0 and r.index_state == 1 and r.middle_state == 1 and r.ring_state == 1 and r.little_state == 1:
            r.gesture = "FOUR"
        elif r.thumb_state == 1 and r.index_state == 1 and r.middle_state == 1 and r.ring_state == 1 and r.little_state == 1:
            r.gesture = "FIVE"
        #----------------------------------------------------------------------------------------------------------------------
        elif r.thumb_state == 0 and r.index_state == 1 and r.middle_state == 1 and r.ring_state == 1 and r.little_state == 0:
            r.gesture = "SIX"
        elif r.thumb_state == 1 and r.index_state == 0 and r.middle_state == 0 and r.ring_state == 0 and r.little_state == 1:
            r.gesture = "ALOHA"
        elif r.thumb_state == 0 and r.index_state == 1 and r.middle_state == 0 and r.ring_state == 0 and r.little_state == 1:
            r.gesture = "WAKEUP"
        #----------------------------------------------------------------------------------------------------------------------
        else:
            r.gesture = None
        # ---------------------------------------------------------------
        #print(f'HandTrackerEdge recognize_gesture: {r.gesture}')
        if r.gesture is not None:
            r.distance_4_8 = d_4_8
        if r.gesture == 'FOUR':
            if d_8_12 < 0.1 and d_12_16 < 0.15 and d_15_20 < 0.1:
                r.gesture = 'BACK'
            #elif d_8_12 < 0.1 and d_12_16 >= 0.15 and d_15_20 < 0.1:
            #    r.gesture = 'WAKEUP'  # Vulcan greeting
                #print("WAKEUP")
        # ---------------------------------------------------------------
            

    def next_frame(self):

        self.fps.update()

        if self.laconic:
            video_frame = np.zeros((self.img_h, self.img_w, 3), dtype=np.uint8)
        else:
            in_video = self.q_video.get()
            video_frame = in_video.getCvFrame()       

        # For debugging
        if self.trace:
            pre_pd_manip = self.q_pre_pd_manip_out.tryGet()
            if pre_pd_manip:
                pre_pd_manip = pre_pd_manip.getCvFrame()
                cv2.imshow("pre_pd_manip", pre_pd_manip)
            pre_lm_manip = self.q_pre_lm_manip_out.tryGet()
            if pre_lm_manip:
                pre_lm_manip = pre_lm_manip.getCvFrame()
                cv2.imshow("pre_lm_manip", pre_lm_manip)

        # Get result from device
        res = marshal.loads(self.q_manager_out.get().getData())
        #---------------------------------------------
        #print(f'HandTrackerEdge next_frame res["type"]: {res["type"]}, res["lm_score"]: {res["lm_score"]}')
        #---------------------------------------------

        if res["type"] != 0 and res["lm_score"] > self.lm_score_thresh:
            hand = mpu.HandRegion()
            hand.rect_x_center_a = res["rect_center_x"] * self.frame_size
            hand.rect_y_center_a = res["rect_center_y"] * self.frame_size
            hand.rect_w_a = hand.rect_h_a = res["rect_size"] * self.frame_size
            hand.rotation = res["rotation"] 
            hand.rect_points = mpu.rotated_rect_to_points(hand.rect_x_center_a, hand.rect_y_center_a, hand.rect_w_a, hand.rect_h_a, hand.rotation)
            hand.lm_score = res["lm_score"]
            hand.handedness = res["handedness"]
            hand.label = "right" if hand.handedness > 0.5 else "left"
            # hand.norm_landmarks contains the normalized ([0:1]) 3D coordinates of landmarks in the square rotated body bounding box
            hand.norm_landmarks = np.array(res['rrn_lms']).reshape(-1,3)
            # hand.landmarks = the landmarks in the image coordinate system (in pixel)
            hand.landmarks = (np.array(res["sqn_lms"]) * self.frame_size).reshape(-1,2).astype(np.int)
            if self.pad_h > 0:
                hand.landmarks[:,1] -= self.pad_h
                for i in range(len(hand.rect_points)):
                    hand.rect_points[i][1] -= self.pad_h
            if self.pad_w > 0:
                hand.landmarks[:,0] -= self.pad_w
                for i in range(len(hand.rect_points)):
                    hand.rect_points[i][0] -= self.pad_w
            if self.use_gesture: 
                self.recognize_gesture(hand)
            hands = [hand]
            #---------------------------------------------------
            #print('hand: ')
            #hand.print()
            #print('hand end')
            #---------------------------------------------------

        else:
            hands = []
        
        # Statistics
        if self.stats:
            if res["type"] == 0:
                self.nb_pd_inferences += 1
                self.nb_frames_no_hand += 1
            else:  
                self.nb_lm_inferences += 1
                if res["type"] == 1:
                    self.nb_pd_inferences += 1
                else: # res["type"] == 2
                    self.nb_lm_inferences_after_landmarks_ROI += 1
                if res["lm_score"] < self.lm_score_thresh: self.nb_frames_no_hand += 1

        return video_frame, hands, None


    def exit(self):
        self.device.close()
        # Print some stats
        if self.stats:
            print(f"FPS : {self.fps.get_global():.1f} f/s (# frames = {self.fps.nb_frames()})")
            print(f"# frames without hand       : {self.nb_frames_no_hand}")
            print(f"# pose detection inferences : {self.nb_pd_inferences}")
            print(f"# landmark inferences       : {self.nb_lm_inferences} - # after pose detection: {self.nb_lm_inferences - self.nb_lm_inferences_after_landmarks_ROI} - # after landmarks ROI prediction: {self.nb_lm_inferences_after_landmarks_ROI}")
        
