from py_openshowvar import openshowvar
import time

kuka_ip = '172.31.1.147'

kukavarproxy_port = 7000


def kuka_send_box_angle(kuka_client, angle:float):
    #if kuka_client.can_connect:
    #    msg = kuka_client.write("BOX_ANGLE", "{:.2f}".format(angle), debug=True)
    #else:
    msg = kuka_client.write("BOX_ANGLE", "{:.2f}".format(angle), debug=False)


def kuka_set_camera_fault(kuka_client, fault:bool):
    #if kuka_client.can_connect:
    #    msg = kuka_client.write("CAMERA_FAULT", fault, debug=True)
    #else:
    msg = kuka_client.write("CAMERA_FAULT", fault, debug=True)

def kuka_send_box_size(kuka_client, box_width:float, box_lenght:float, box_height:float):
    msg = kuka_client.write("BOX_WIDTH", "{:.2f}".format(box_width))
    msg = kuka_client.write("BOX_HEIGHT", "{:.2f}".format(box_height))
    msg = kuka_client.write("BOX_LENGHT", "{:.2f}".format(box_lenght))

def kuka_send_box_place_pos(kuka_client, box_x_mm:float, box_y_mm:float):
    msg = kuka_client.write("BOX_PLACE_X_MM", "{:.2f}".format(box_x_mm), False)
    msg = kuka_client.write("BOX_PLACE_Y_MM", "{:.2f}".format(box_y_mm), False)

def check_vision_update_request(kuka_client:openshowvar):
    msg = kuka_client.read("REQUEST_VISION_UPDATE", debug=False)
    return msg

def ack_vision_update_completion(kuka_client:openshowvar):
    msg = kuka_client.write("REQUEST_VISION_UPDATE", "FALSE", False)
    msg = kuka_client.write("VISION_UPDATE_DONE", "TRUE", False)
    