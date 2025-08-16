

class VisionSystemData():
    def __init__(self, frame=None):

        # indicate wheter camera is detected and can capture image
        self.camera_fault:bool = False

        # canny filter tresholds
        self.t1:int = 250
        self.t2:int = 200

        self.detection_step = 20

        self.set_frame_size(frame)

        self.h_detect_enabled:bool = True
        self.h_detect_inversion:bool = True

        self.v_detect_enabled:bool = False
        self.v_detect_inversion:bool = False
        self.capture_mode:bool = False
        self.capture_repeater_max:int = 15
        self.capture_repeater_counter:int = 0

        # check wheter detected points from horizontal mode and vertical mode match within match radius
        # and discard results outside this radius
        self.double_check_mode:bool = False
        self.double_check_match_radius:int = 5

        self.calibration_size = 10
        self.calibration_x_shift = 0
        self.calibration_y_shift = 0

        self.test_mm_px_ratio = 200 / 330



    # setup frame size based on captured frame parameters
    def set_frame_size(self, frame):
        if frame is not None:
            self.frame_height, self.frame_width, self.frame_ch = frame.shape
            self.bytes_per_line = self.frame_ch * self.frame_width
        else:
            self.frame_height = 480
            self.frame_width = 640
            self.frame_ch = 3
            self.bytes_per_line = self.frame_ch * self.frame_width




class BoxParameters():
    def __init__(self):
        self.box_width_mm = None
        self.box_height_mm = None
        self.box_lenght_mm = None

    def set_box_size(self, w, h, l):
        self.box_width_mm = w
        self.box_height_mm = h
        self.box_lenght_mm = l

    def get_box_size(self):
        return self.box_width_mm, self.box_height_mm, self.box_lenght_mm
