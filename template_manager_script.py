"""
This file is the template of the scripting node source code in edge mode
Substitution is made in HandTrackerEdge.py

In the following:
rrn_ : normalized [0:1] coordinates in rotated rectangle coordinate systems 
sqn_ : normalized [0:1] coordinates in squared input image
"""
import marshal
from math import sin, cos, atan2, pi, degrees, floor, dist


pad_h = ${_pad_h}
img_h = ${_img_h}
img_w = ${_img_w}
frame_size = ${_frame_size}
crop_w = ${_crop_w}

${_TRACE} ("Starting manager script node")

def send_result(buf, type, lm_score=0, handedness=0, rect_center_x=0, rect_center_y=0, rect_size=0, rotation=0, rrn_lms=0, sqn_lms=0, xyz=0, xyz_zone=0):
    # type : 0, 1 or 2
    #   0 : pose detection only (detection score < threshold)
    #   1 : pose detection + landmark regression
    #   2 : landmark regression only (ROI computed from previous landmarks)   
    result = dict([("type", type), ("lm_score", lm_score), ("handedness", handedness), ("rotation", rotation),
            ("rect_center_x", rect_center_x), ("rect_center_y", rect_center_y), ("rect_size", rect_size), ("rrn_lms", rrn_lms), ('sqn_lms', sqn_lms),
            ("xyz", xyz), ("xyz_zone", xyz_zone)])
    result_serial = marshal.dumps(result)
    ${_TRACE} ("len result:"+str(len(result_serial)))   
    buf.getData()[:] = result_serial  
    node.io['host'].send(buf)
    ${_TRACE} ("Manager sent result to host")

def rr2img(rrn_x, rrn_y):
    # Convert a point (rrn_x, rrn_y) expressed in normalized rotated rectangle (rrn)
    # into (X, Y) expressed in normalized image (sqn)
    X = sqn_rr_center_x + sqn_rr_size * ((rrn_x - 0.5) * cos_rot + (0.5 - rrn_y) * sin_rot)
    Y = sqn_rr_center_y + sqn_rr_size * ((rrn_y - 0.5) * cos_rot + (rrn_x - 0.5) * sin_rot)
    return X, Y

def normalize_radians(angle):
    return angle - 2 * pi * floor((angle + pi) / (2 * pi))

# send_new_frame_to_branch defines on which branch new incoming frames are sent
# 0 = body detection branch
# 1 = palm detection branch 
# 2 = hand landmark branch
send_new_frame_to_branch = ${_first_branch}

# Predefined buffer variables used for sending result to host
buf1 = Buffer(169)
buf2 = Buffer(${_buffer_size})
buf3 = Buffer(173)

cfg_pre_pd = ImageManipConfig()
cfg_pre_pd.setResizeThumbnail(128, 128, 0, 0, 0)

id_wrist = 0
id_index_mcp = 5
id_middle_mcp = 9
id_ring_mcp =13
ids_for_bounding_box = [0, 1, 2, 3, 5, 6, 9, 10, 13, 14, 17, 18]

lm_input_size = 224

while True: 
    if send_new_frame_to_branch == 1: # Routing frame to pd branch
        node.io['pre_pd_manip_cfg'].send(cfg_pre_pd)
        ${_TRACE} ("Manager sent thumbnail config to pre_pd manip")
        # Wait for pd post processing's result 
        detection = node.io['from_post_pd_nn'].get().getLayerFp16("result")
        ${_TRACE} ("Manager received pd result: "+str(detection))
        pd_score, box_x, box_y, box_size, kp0_x, kp0_y, kp2_x, kp2_y = detection
        
        if pd_score < ${_pd_score_thresh}:
            send_result(buf1, 0)
            # _first_branch = 0 if using Body Pre Focusing, 1 otherwise
            send_new_frame_to_branch = ${_first_branch}
            continue

        # scale_center_x = sqn_scale_x - sqn_rr_center_x
        # scale_center_y = sqn_scale_y - sqn_rr_center_y
        kp02_x = kp2_x - kp0_x
        kp02_y = kp2_y - kp0_y
        sqn_rr_size = 2.9 * box_size
        rotation = 0.5 * pi - atan2(-kp02_y, kp02_x)
        rotation = normalize_radians(rotation)
        sqn_rr_center_x = box_x + 0.5*box_size*sin(rotation)
        sqn_rr_center_y = box_y - 0.5*box_size*cos(rotation)

    # Tell pre_lm_manip how to crop hand region 
    rr = RotatedRect()
    rr.center.x    = sqn_rr_center_x
    rr.center.y    = (sqn_rr_center_y * frame_size - pad_h) / img_h
    rr.size.width  = sqn_rr_size
    rr.size.height = sqn_rr_size * frame_size / img_h
    rr.angle       = degrees(rotation)
    cfg = ImageManipConfig()
    cfg.setCropRotatedRect(rr, True)
    cfg.setResize(lm_input_size, lm_input_size)
    node.io['pre_lm_manip_cfg'].send(cfg)
    ${_TRACE} ("Manager sent config to pre_lm manip")

    # Wait for lm's result
    lm_result = node.io['from_lm_nn'].get()
    ${_TRACE} ("Manager received result from lm nn")
    lm_score = lm_result.getLayerFp16("Identity_1")[0]
    if lm_score > ${_lm_score_thresh}:
        handedness = lm_result.getLayerFp16("Identity_2")[0]

        rrn_lms = lm_result.getLayerFp16("Identity_dense/BiasAdd/Add")
        # Retroproject landmarks into the original squared image 
        sqn_lms = []
        cos_rot = cos(rotation)
        sin_rot = sin(rotation)
        for i in range(21):
            rrn_lms[3*i] /= lm_input_size
            rrn_lms[3*i+1] /= lm_input_size
            rrn_lms[3*i+2] /= lm_input_size  #* 0.4
            sqn_x, sqn_y = rr2img(rrn_lms[3*i], rrn_lms[3*i+1])
            sqn_lms += [sqn_x, sqn_y]
        xyz = 0
        xyz_zone = 0

        # Send result to host
        send_result(buf2, send_new_frame_to_branch, lm_score, handedness, sqn_rr_center_x, sqn_rr_center_y, sqn_rr_size, rotation, rrn_lms, sqn_lms, xyz, xyz_zone)
        send_new_frame_to_branch = 2 

        # Calculate the ROI for next frame
        # Compute rotation
        x0 = sqn_lms[0]
        y0 = sqn_lms[1]
        x1 = 0.25 * (sqn_lms[2*id_index_mcp] + sqn_lms[2*id_ring_mcp]) + 0.5 * sqn_lms[2*id_middle_mcp]
        y1 = 0.25 * (sqn_lms[2*id_index_mcp+1] + sqn_lms[2*id_ring_mcp+1]) + 0.5 * sqn_lms[2*id_middle_mcp+1]
        rotation = 0.5 * pi - atan2(y0 - y1, x1 - x0)
        rotation = normalize_radians(rotation)
        # Find boundaries of landmarks
        min_x = min_y = 1
        max_x = max_y = 0
        for id in ids_for_bounding_box:
            min_x = min(min_x, sqn_lms[2*id])
            max_x = max(max_x, sqn_lms[2*id])
            min_y = min(min_y, sqn_lms[2*id+1])
            max_y = max(max_y, sqn_lms[2*id+1])
        axis_aligned_center_x = 0.5 * (max_x + min_x)
        axis_aligned_center_y = 0.5 * (max_y + min_y)
        cos_rot = cos(rotation)
        sin_rot = sin(rotation)
        # Find boundaries of rotated landmarks
        min_x = min_y = 1
        max_x = max_y = -1
        for id in ids_for_bounding_box:
            original_x = sqn_lms[2*id] - axis_aligned_center_x
            original_y = sqn_lms[2*id+1] - axis_aligned_center_y
            projected_x = original_x * cos_rot + original_y * sin_rot
            projected_y = -original_x * sin_rot + original_y * cos_rot
            min_x = min(min_x, projected_x)
            max_x = max(max_x, projected_x)
            min_y = min(min_y, projected_y)
            max_y = max(max_y, projected_y)
        projected_center_x = 0.5 * (max_x + min_x)
        projected_center_y = 0.5 * (max_y + min_y)
        center_x = (projected_center_x * cos_rot - projected_center_y * sin_rot + axis_aligned_center_x)
        center_y = (projected_center_x * sin_rot + projected_center_y * cos_rot + axis_aligned_center_y)
        width = (max_x - min_x)
        height = (max_y - min_y)
        #
        sqn_rr_size = 2 * max(width, height) 
        sqn_rr_center_x = (center_x + 0.1 * height * sin_rot) 
        sqn_rr_center_y = (center_y - 0.1 * height * cos_rot) 
        
    else:
        send_result(buf3, send_new_frame_to_branch, lm_score)
        send_new_frame_to_branch = ${_first_branch}
