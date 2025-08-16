
import datetime

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import  QLabel, QVBoxLayout, QSpinBox, QSlider, QHBoxLayout, QWidget, QCheckBox, QLineEdit, QPushButton
from PyQt5.QtGui import QPixmap, QFont

from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread

import cv2
import numpy as np
import box_detection as bd
import kuka_com
from py_openshowvar import openshowvar
import program_data as pdata
import camera

block_capture = False

class VideoCaptureThread(QThread):

    update_frame_signal = pyqtSignal(np.ndarray, bool)
    handle_camera_fault = pyqtSignal()

    def __init__(self, camera_name):
        super(VideoCaptureThread, self).__init__()
        self.camera_name = camera_name

    def run(self):
        cap = camera.connect_camera(self.camera_name)
        cap.set(3, 320)
        cap.set(4, 240)
        while True:

            camera_detected = cap is not None
            if camera_detected:
                camera_detected, frame = cap.read()
            if block_capture:
                continue

            if not camera_detected:
                fault_frame = np.zeros((1, 1, 3), np.uint8)
                self.update_frame_signal.emit(fault_frame, camera_detected)
                cap = camera.connect_camera(self.camera_name)

            else:
                self.update_frame_signal.emit(frame, camera_detected)



class VisionSystemWindow(QtWidgets.QMainWindow):
    def __init__(self, enable_robot_connection:bool):
        super(VisionSystemWindow, self).__init__()

        self.enable_robot_connection = enable_robot_connection

        uic.loadUi('ui/gui_reforged.ui', self)
        self.setWindowTitle("Zamykarka: System Wizyjny")

        self.a = datetime.datetime.now()
        self.b = datetime.datetime.now() 

        camera_name = "Integrated Camera"

        vid = camera.connect_camera(camera_name)
        camera_detected, frame = vid.read()

        self.kuka_client = None



        if self.enable_robot_connection:
            self.kuka_client = openshowvar(kuka_com.kuka_ip, kuka_com.kukavarproxy_port)

        self.vsdata = pdata.VisionSystemData(frame)
        self.bdata = pdata.BoxParameters()

        if not camera_detected:
            self.draw_camera_fault()

    
        self.setup_sliders()
        self.setup_control_buttons_panel() 
        self.setup_results_panel()

        self.vidcap_thread = VideoCaptureThread(camera_name)
        self.vidcap_thread.update_frame_signal.connect(self.update_images)
        self.vidcap_thread.start()
        self.show()


    @pyqtSlot(np.ndarray, bool)
    def update_images(self, cv_frame, camera_detected:bool):



        global block_capture
        block_capture = True
        self.measure_fps()

        if not camera_detected:
            self.vsdata.camera_fault = True
            self.draw_camera_fault()
            block_capture = False
            return

        else:
            self.vsdata.camera_fault = False

        edges = cv2.Canny(cv_frame, self.vsdata.t1, self.vsdata.t2)
        output_frame = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)

        chd = None
        cvd = None

        horizontal_is_valid = True

        # scanning from mid x origin
        if self.checkbox_detect_horizontal.isChecked():
            if self.checkbox_display_rays.isChecked():
                chd = bd.detectCornersHorizontal(edges, output_frame, self.vsdata.detection_step)
            else:
                chd = bd.detectCornersHorizontal(edges, None, self.vsdata.detection_step)
            for c in chd:
                for p in c:
                    if p is None:
                        horizontal_is_valid = False
            #cv_frame = cv2.circle(cv_frame, (box_x, box_y), radius = 6, color = (0, 0, 255), thickness=2)
            


        #scanning from mid y origin

        vertical_is_valid = True

        if self.checkbox_detect_vertical.isChecked():
            if self.checkbox_display_rays.isChecked():
                cvd = bd.detectCornersVertical(edges, output_frame, self.vsdata.detection_step)
            else:
                cvd = bd.detectCornersVertical(edges, None, self.vsdata.detection_step)

            for c in cvd:
                for p in c:
                    if p is None:
                        vertical_is_valid = False

        corners = []
        box_angle = None
        box_x, box_y = None, None

        if self.vsdata.v_detect_enabled and self.vsdata.h_detect_enabled and vertical_is_valid and horizontal_is_valid:
            top_a, top_b = bd.calculate_ab_line(chd[bd.TOP_LEFT][1], chd[bd.TOP_LEFT][2], chd[bd.TOP_RIGHT][1], chd[bd.TOP_RIGHT][2])
            cv_frame = cv2.line(cv_frame, (0, int(bd.ab_value(0, top_a, top_b))), (self.vsdata.frame_width - 1, int(bd.ab_value(self.vsdata.frame_width - 1, top_a, top_b))), color=(0,150,0), thickness=1)

            bot_a, bot_b = bd.calculate_ab_line(chd[bd.BOT_LEFT][1], chd[bd.BOT_LEFT][2], chd[bd.BOT_RIGHT][1], chd[bd.BOT_RIGHT][2])
            cv_frame = cv2.line(cv_frame, (0, int(bd.ab_value(0, bot_a, bot_b))), (self.vsdata.frame_width - 1, int(bd.ab_value(self.vsdata.frame_width - 1, bot_a, bot_b))), color=(0,150,0), thickness=1)

            right_a, right_b = bd.calculate_ab_line(cvd[bd.TOP_RIGHT][1], cvd[bd.TOP_RIGHT][2], cvd[bd.BOT_RIGHT][1], cvd[bd.BOT_RIGHT][2])
            cv_frame = cv2.line(cv_frame, (0, int(bd.ab_value(0, right_a, right_b))), (self.vsdata.frame_width - 1, int(bd.ab_value(self.vsdata.frame_width - 1, right_a, right_b))), color=(0,150,0), thickness=1)

            left_a, left_b = bd.calculate_ab_line(cvd[bd.TOP_LEFT][1], cvd[bd.TOP_LEFT][2], cvd[bd.BOT_LEFT][1], cvd[bd.BOT_LEFT][2])
            cv_frame = cv2.line(cv_frame, (0, int(bd.ab_value(0, left_a, left_b))), (self.vsdata.frame_width - 1, int(bd.ab_value(self.vsdata.frame_width - 1, left_a, left_b))), color=(0,150,0), thickness=1)

            top_left_x, top_left_y = bd.find_intersection_from_ab(top_a, top_b, left_a, left_b)
            top_right_x, top_right_y = bd.find_intersection_from_ab(top_a, top_b, right_a, right_b)
            bot_right_x, bot_right_y = bd.find_intersection_from_ab(right_a, right_b, bot_a, bot_b)
            bot_left_x, bot_left_y = bd.find_intersection_from_ab(bot_a, bot_b, left_a, left_b)

            corners.append(["top-left", top_left_x, top_left_y])
            corners.append(["top-right", top_right_x, top_right_y])
            corners.append(["bot-right", bot_right_x, bot_right_y])
            corners.append(["bot-left", bot_left_x, bot_left_y])
            box_x, box_y = bd.find_intersection_from_corners(corners)

            T1 = bd.calculate_tilt(top_left_x, top_left_y, top_right_x, top_right_y)
            T2 = bd.calculate_tilt(bot_left_x, bot_left_y, bot_right_x, bot_right_y)
            T3 = bd.calculate_tilt(top_right_x, top_right_y, bot_right_x, bot_right_y) - 90
            T4 = bd.calculate_tilt(top_left_x, top_left_y, bot_left_x, bot_left_y) - 90
            AVG = (T1 + T2 + T3 + T4) / 4
            box_angle = AVG
            box_angle_str = f'{box_angle:.2f}'
            self.boxpos_angle_lineedit.setText(box_angle_str)
            self.boxpos_x_lineedit.setText(str(box_x))
            self.boxpos_y_lineedit.setText(str(box_y))

        if self.vsdata.h_detect_enabled:
            for c in chd:
                #cv_frame = cv2.circle(cv_frame, (c[1], c[2]), radius = 10, color = (0, 0, 255), thickness=2)
                cv_frame = cv2.line(cv_frame, (chd[0][1],chd[0][2]), (chd[1][1], chd[1][2]), color = (0,0,255), thickness=1)
                cv_frame = cv2.line(cv_frame, (chd[3][1], chd[3][2]), (chd[2][1], chd[2][2]), color = (0,0,255), thickness=1)

        if self.vsdata.v_detect_enabled:
            for c in cvd:
                #cv_frame = cv2.circle(cv_frame, (box_x, box_y), radius = 6, color = (0, 0, 255), thickness=2)
                cv_frame = cv2.line(cv_frame, (cvd[0][1],cvd[0][2]), (cvd[2][1], cvd[2][2]), color = (0,0,255), thickness=1)
                cv_frame = cv2.line(cv_frame, (cvd[1][1], cvd[1][2]), (cvd[3][1], cvd[3][2]), color = (0,0,255), thickness=1)


        if self.enable_robot_connection:
            update_required = kuka_com.check_vision_update_request(self.kuka_client)
            print("?:" + str(update_required))
            if update_required == b'TRUE':
                #print("UPDATE REQUIRED")
                if box_angle is None or box_x is None or box_y is None:
                    print("BOX:", box_angle, box_x, box_y)
                else:
                    if self.vsdata.capture_repeater_counter < self.vsdata.capture_repeater_max:
                        self.vsdata.capture_repeater_counter += 1
                        block_capture = False
                        return
                    else:
                        self.vsdata.capture_repeater_counter = 0
                    print("UPDATE")
                    kuka_com.kuka_send_box_angle(self.kuka_client, -box_angle)
                    box_x_mm = (box_x - self.vsdata.frame_width / 2) * self.vsdata.test_mm_px_ratio
                    box_y_mm = (box_y - self.vsdata.frame_height / 2) * self.vsdata.test_mm_px_ratio
                    print(box_x_mm, box_y_mm, box_angle)
                    kuka_com.kuka_send_box_place_pos(self.kuka_client, box_x_mm, box_y_mm)
                    kuka_com.ack_vision_update_completion(self.kuka_client)

                    if self.vsdata.capture_mode:
                        print("update")
                        box_angle_str = f'{box_angle:.2f}'
                        self.boxpos_angle_lineedit.setText(box_angle_str)
                        self.draw_input_image(cv_frame)
                        self.draw_output_image(output_frame)
                        self.boxpos_x_lineedit.setText(str(box_x))
                        self.boxpos_y_lineedit.setText(str(box_y))
            else:
                print("NO UPDATE REQUIRED")  
        

        if not self.vsdata.capture_mode:
            self.draw_input_image(cv_frame)
            self.draw_output_image(output_frame)

        block_capture = False



    def setup_sliders(self):
        self.t1_slider.valueChanged[int].connect(self.t1_slider_valuechange)
        self.t1_slider.setValue(self.vsdata.t1)
        self.t2_slider.valueChanged[int].connect(self.t2_slider_valuechange)
        self.t2_slider.setValue(self.vsdata.t2)

        self.step_slider.valueChanged[int].connect(self.step_slider_valuechange)    
        self.step_slider.setValue(self.vsdata.detection_step)

        self.slider_calibration_size.valueChanged[int].connect(self.slider_calibration_size_valuechange)    
        self.slider_calibration_size.setValue(self.vsdata.calibration_size)

        self.slider_calibration_x_shift.valueChanged[int].connect(self.slider_calibration_x_shift_valuechange)    
        self.slider_calibration_x_shift.setValue(self.vsdata.calibration_x_shift)

        self.slider_calibration_y_shift.valueChanged[int].connect(self.slider_calibration_y_shift_valuechange)    
        self.slider_calibration_y_shift.setValue(self.vsdata.calibration_y_shift)


    def setup_control_buttons_panel(self):
        
        self.checkbox_capture_enabled.toggle()

        #self.checkbox_display_corners.toggle()

        self.checkbox_detect_horizontal.setChecked(self.vsdata.h_detect_enabled)
        self.checkbox_detect_horizontal.stateChanged.connect(self.checkbox_detect_horizontal_changed)

        self.checkbox_detect_vertical.setChecked(self.vsdata.v_detect_enabled)
        self.checkbox_detect_vertical.stateChanged.connect(self.checkbox_detect_vertical_changed)
        self.checkbox_capture_mode.stateChanged.connect(self.checkbox_capture_mode_changed)
        self.button_set_box_size.clicked.connect(self.button_set_box_size_onclick)

    def checkbox_detect_horizontal_changed(self):
        self.vsdata.h_detect_enabled = self.checkbox_detect_horizontal.isChecked()

    def checkbox_detect_vertical_changed(self):
        self.vsdata.v_detect_enabled = self.checkbox_detect_vertical.isChecked()

    def checkbox_capture_mode_changed(self):
        self.vsdata.capture_mode = self.checkbox_capture_mode.isChecked()
        print(self.vsdata.capture_mode)

    def setup_results_panel(self):

        return



    def t1_slider_valuechange(self, value):
        self.vsdata.t1 = value
        self.t1_label.setText("T1:" + str(value))

    def t2_slider_valuechange(self, value):
        self.vsdata.t2 = value
        self.t2_label.setText("T2:" + str(value))

    def step_slider_valuechange(self, value):
        self.vsdata.detection_step = value
        self.step_label.setText("STEP:" + str(value))

    def slider_calibration_size_valuechange(self, value):
        self.vsdata.calibration_size = value
        self.spinbox_calibration_size.setValue(value)

    def slider_calibration_x_shift_valuechange(self, value):
        self.vsdata.calibration_x_shift = value
        self.label_calibration_x.setText("x:" + str(value))
        #self.spinbox_calibration_x.setValue(value)

    def slider_calibration_y_shift_valuechange(self, value):
        self.vsdata.calibration_y_shift = value
        self.label_calibration_y.setText("y:" + str(value))
        #self.spinbox_calibration_x.setValue(value)

    def button_set_box_size_onclick(self):
        print("siusiak")
        self.bdata.box_height_mm = self.spinbox_box_height.value()
        self.bdata.box_width_mm = self.spinbox_box_width.value()
        self.bdata.box_lenght_mm = self.spinbox_box_lenght.value()
        kuka_com.kuka_send_box_size(self.kuka_client, self.bdata.box_width_mm, self.bdata.box_lenght_mm, self.bdata.box_height_mm)
        print(type(self.bdata.box_lenght_mm))
        print(self.bdata.box_lenght_mm)
        

    def draw_input_image(self, cv_frame):

        if self.checkbox_draw_axis.isChecked():
            self.draw_calibration_axes(cv_frame)
            self.draw_calibration_box(cv_frame)

        input_frame_qt_format = QtGui.QImage(cv_frame.data, self.vsdata.frame_width, self.vsdata.frame_height, self.vsdata.bytes_per_line, QtGui.QImage.Format_BGR888)
        input_frame_pixmap = QPixmap.fromImage(input_frame_qt_format)
        self.input_image_label.setPixmap(input_frame_pixmap)


    def draw_output_image(self, cv_frame):
        output_frame_qt_format = QtGui.QImage(cv_frame.data, self.vsdata.frame_width, self.vsdata.frame_height, self.vsdata.bytes_per_line, QtGui.QImage.Format_BGR888)
        output_frame_pixmap = QPixmap.fromImage(output_frame_qt_format)
        self.output_image_label.setPixmap(output_frame_pixmap)


    def draw_camera_fault(self):
        fault_image = np.zeros((self.vsdata.frame_height, self.vsdata.frame_width, 3), np.uint8)
        fault_text = "CAMERA ERROR"
        font = cv2.FONT_HERSHEY_SIMPLEX
        color = (0, 0, 255)
        org = (00, 185)
        fault_image = cv2.putText(fault_image, fault_text, org, font, 1,color, 2, cv2.LINE_AA, False)
        self.draw_input_image(fault_image)
        self.draw_output_image(fault_image)


    def draw_calibration_axes(self, cv_frame):
        x1 = int(self.vsdata.frame_width / 2)
        y1 = 0
        x2 = int(self.vsdata.frame_width / 2)
        y2 = int(self.vsdata.frame_height - 1)
        cv_frame = cv2.line(cv_frame, (x1, y1), (x2, y2), color=(0, 255, 0), thickness=1)

        x1 = 0
        y1 = int(self.vsdata.frame_height / 2)
        x2 = int(self.vsdata.frame_width - 1)
        y2 = int(self.vsdata.frame_height / 2)
        cv_frame = cv2.line(cv_frame, (x1, y1), (x2, y2), color=(0, 255, 0), thickness=1)


    def draw_calibration_box(self, cv_frame):
        cx = int(self.vsdata.frame_width / 2) + self.vsdata.calibration_x_shift
        cy = int(self.vsdata.frame_height / 2) + self.vsdata.calibration_y_shift

        x1 = int(cx - (self.vsdata.calibration_size / 2))
        y1 = int(cy + (self.vsdata.calibration_size / 2))
        x2 = int(cx + (self.vsdata.calibration_size / 2))
        y2 = int(cy - (self.vsdata.calibration_size / 2))
        cv_frame = cv2.rectangle(cv_frame, (x1, y1), (x2, y2), color=(0,255,0), thickness=1, lineType=cv2.LINE_8)


    def measure_fps(self):
        self.a = datetime.datetime.now()
        delta = self.a - self.b 
        delta_ms = int(delta.total_seconds() * 1000)
        if delta_ms != 0:
            fps = int(1000 / delta_ms)
            self.fps_counter_label.setText("FPS:" + str(fps))
        self.b = datetime.datetime.now() 