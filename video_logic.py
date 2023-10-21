import cv2
import sys
import pathlib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import albumentations as A
from albumentations.pytorch import ToTensorV2
from tqdm import tqdm
from tqdm.contrib import tzip
import config as cf


def get_tracker(tracker_type_):
    if tracker_type_ == 'BOOSTING':
        return cv2.TrackerBoosting_create()
    if tracker_type_ == 'MIL':
        return cv2.TrackerMIL_create()
    if tracker_type_ == 'TLD':
        return cv2.TrackerTLD_create()
    if tracker_type_ == 'MEDIANFLOW':
        return cv2.TrackerMedianFlow_create()
    if tracker_type_ == 'GOTURN':
        return cv2.TrackerGOTURN_create()
    if tracker_type_ == 'MOSSE':
        return cv2.TrackerMOSSE_create()
    if tracker_type_ == "CSRT":
        return cv2.TrackerCSRT_create()
    return None


def read_video(path, img_size, transform=None, frames_freq=10):
    frames = []
    cap = cv2.VideoCapture(path)

    if not cap.isOpened():
        print("Could not open video")
        return []

    fps = int(cap.get(cv2.CAP_PROP_FPS))

    length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print("Initial frames num", length)
    # N = length // (frames_num)
    N = length // frames_freq
    print("Step N", N)

    current_frame = 1
    for i in range(length):
        ret, frame = cap.read(current_frame)

        if ret and i == current_frame and len(frames) < N:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, img_size)

            frames.append(frame)
            current_frame += frames_freq
    cap.release()

    return frames


def get_slice(frame, thickness=4):
    slice = frame.copy()
    slice.resize((thickness, frame.shape[0] * 2 + frame.shape[1] * 2, 3))
    # up - left
    xc = 0
    for x in range(frame.shape[1] // 2, -1, -1):
        xc += 1
        yc = 0
        for y in range(thickness):
            slice[yc, xc] = frame[y, x]
            yc += 1
    # left
    for y in range(frame.shape[0]):
        xc += 1
        yc = 0
        for x in range(thickness):
            slice[yc, xc] = frame[y, x]
            yc += 1
    # bottom
    for x in range(frame.shape[1]):
        xc += 1
        yc = 3
        for y in range(frame.shape[0] - 1, frame.shape[0] - thickness - 1, -1):
            slice[yc, xc] = frame[y, x]
            yc -= 1
    # right
    for y in range(frame.shape[0] - 1, -1, -1):
        xc += 1
        yc = 0
        for x in range(frame.shape[1] - 1, frame.shape[1] - thickness - 1, -1):
            slice[yc, xc] = frame[y, x]
            yc += 1
    # up - right
    for x in range(frame.shape[1] - 1, frame.shape[1] // 2, -1):
        xc += 1
        if xc >= slice.shape[1]:
            break
        yc = 0
        for y in range(thickness):
            slice[yc, xc] = frame[y, x]
            yc += 1
    return slice


def video_main(thickness=4):
    # (major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')
    tracker = get_tracker(cf.TRACKER_TYPES[1])

    video_list = []
    for video_path in pathlib.Path(cf.INPUT_DATA_PATH).glob('*.mp4'):
        video_list.append(str(video_path))
    for video_index in range(len(video_list)):
        frames = read_video(video_list[video_index], cf.IMG_SIZE, frames_freq=1)
        sizes = (thickness, frames[0].shape[0] * 2 + frames[0].shape[1] * 2, 3)
        img = frames[0].copy()
        img.resize((sizes[0] * len(frames), sizes[1], sizes[2]))
        for i in range(len(frames)):
            slice = get_slice(frames[i])
            # print(i)
            for x in range(sizes[1]):
                for y in range(sizes[0]):
                    img[y + i * thickness, x] = slice[y, x]

        plt.imshow(img)
        plt.savefig(cf.OUT_DATA_PATH + '/' + f'map {video_index}.png')
        # plt.show()
