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
import math as m


def read_video(path, img_size, frames_freq=10):
    frames = []
    cap = cv2.VideoCapture(path)

    if not cap.isOpened():
        print("Could not open video")
        return []

    fps = int(cap.get(cv2.CAP_PROP_FPS))

    length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print("Initial frames num", length)
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


def get_map(video_path, thickness=4, frame_freq=2):
    frames = read_video(video_path, cf.IMG_SIZE, frames_freq=frame_freq)
    sizes = (thickness, frames[0].shape[0] * 2 + frames[0].shape[1] * 2, 3)
    img = frames[0].copy()
    img.resize((sizes[0] * len(frames), sizes[1], sizes[2]))
    for i in range(len(frames)):
        slice = get_slice(frames[i], thickness)
        for x in range(sizes[1]):
            for y in range(sizes[0]):
                img[y + i * thickness, x] = slice[y, x]
    return img


def rotate_map(origin_map):
    # img = origin_map.copy()
    # return img
    return origin_map


def skew_map(origin_img, effect=20):
    img = origin_img.copy()
    coef = 8 * m.pi / origin_img.shape[1]
    img.resize((origin_img.shape[0] + 2 * effect, origin_img.shape[1], origin_img.shape[2]))
    new_y = [0] * origin_img.shape[1]
    for x in range(origin_img.shape[1]):
        new_y[x] = int((m.cos(coef * x) + 1) * effect)
    for y in range(origin_img.shape[0]):
        for x in range(origin_img.shape[1]):
            img[new_y[x] + y, x] = origin_img[y, x]
    return img


def crop_img(origin_img, x_=160, y_=70):
    img = origin_img.copy()
    img.resize((origin_img.shape[0] - 2*y_, origin_img.shape[1] - 2*x_,3))
    for x in range(img.shape[1]):
        for y in range(img.shape[0]):
            img[y, x] = origin_img[y + y_, x + x_]
    return img


def get_counters_list(image, dust_thresh_, dust_min_area_):
    img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    ret, thresh = cv2.threshold(img_gray, dust_thresh_, 255, cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(image=thresh, mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_NONE)

    filters = []
    for i in contours:
        area = np.abs(cv2.contourArea(i))
        if area > dust_min_area_:
            filters.append(i)
    return filters


def dust_selection(origin_img, dust_thresh_, dust_min_area_):
    origin_img_copy = origin_img.copy()
    image = origin_img[0:origin_img.shape[0],
            origin_img.shape[1] * 970 // 2240: origin_img.shape[1] * 1570 // 2240]

    filters = get_counters_list(image, dust_thresh_, dust_min_area_)
    cv2.drawContours(image=origin_img_copy, contours=filters, contourIdx=-1, color=(0, 0, 255), thickness=1,
                     lineType=cv2.LINE_AA, offset=(origin_img.shape[1] * 970 // 2240, 0))
    return origin_img_copy


def save_map(img, index) -> str:
    plt.imshow(img)
    save_path = cf.OUT_DATA_PATH + '/' + f'map {index}.png'
    plt.savefig(save_path)
    return save_path


def video_main():
    video_list = []
    for video_path in pathlib.Path(cf.INPUT_DATA_PATH).glob('*.mp4'):
        video_list.append(str(video_path))

    for video_index in range(len(video_list)):
        img = get_map(video_list[9], frame_freq=1)
        img = rotate_map(img)
        img = skew_map(img)
        save_map(img, video_index)
        break
