from cv2_enumerate_cameras import enumerate_cameras
import cv2

def get_camera_index(camera_name):
    for camera_info in enumerate_cameras(cv2.CAP_MSMF):
            print(f'{camera_info.index}: {camera_info.name}')
            if camera_name == camera_info.name:
                return camera_info.index
    return None

def connect_camera(camera_name):
     camera_index = get_camera_index(camera_name)
     if camera_name is None:
          return None
     return cv2.VideoCapture(camera_index)

for camera_info in enumerate_cameras(cv2.CAP_MSMF):
            print(f'{camera_info.index}: {camera_info.name}')