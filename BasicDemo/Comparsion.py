# -- coding: utf-8 --
import os.path
import time
import tkinter.messagebox
from functools import partial
from math import fabs, sin, radians, cos
from tkinter import messagebox

from opcua.ua import UaError

from CamOperation_class import *
from PIL import Image, ImageTk
import serial
import csv
from cnocr import CnOcr
import threading
import pickle
import win32event
import win32api
import winerror
import pandas as pd
from loguru import logger
import serial.tools.list_ports
import matplotlib
import cv2
import numpy as np
matplotlib.use('TkAgg')
from matplotlib import pyplot as plt
from opcua import Client,ua


class SubHandler(object):

    """
    Subscription Handler. To receive events from server for a subscription
    data_change and event methods are called directly from receiving thread.
    Do not do expensive, slow or network operation there. Create another
    thread if you need to do such a thing
    """
    def datachange_notification(self, node, val, data):
        if(val==1):
            # print(val)
            sendSerialOrder()


    def event_notification(self, event):
        print("Python: New event", event)

def custom_filter(record):
    # 如果消息与上一条消息相同，返回False，表示丢弃该消息
    if hasattr(custom_filter, "last_message") and custom_filter.last_message == record["message"]:
        return False
    custom_filter.last_message = record["message"]
    return True


logger.add('log\\runtime_{time}.log', rotation='00:00', retention='2 days', backtrace=True, diagnose=True,
           filter=custom_filter)


# 获取选取设备信息的索引，通过[]之间的字符去解析
def TxtWrapBy(start_str, end, all):
    start = all.find(start_str)
    if start >= 0:
        start += len(start_str)
        end = all.find(end, start)
        if end >= 0:
            return all[start:end].strip()


# 将返回的错误码转换为十六进制显示
def ToHexStr(num):
    chaDic = {10: 'a', 11: 'b', 12: 'c', 13: 'd', 14: 'e', 15: 'f'}
    hexStr = ""
    if num < 0:
        num = num + 2 ** 32
    while num >= 16:
        digit = num % 16
        hexStr = chaDic.get(digit, str(digit)) + hexStr
        num //= 16
    hexStr = chaDic.get(num, str(num)) + hexStr
    return hexStr


@logger.catch
def show_frame(frame):
    frame.tkraise()


@logger.catch
def show_mianframe(frame):
    global loginflag
    loginflag = False
    # 需要解开
    stop_grabbing()
    show_frame(frame)
    start_grabbing1()


# 返回登陆结果信息

loginflag = False


@logger.catch
def do_login(login_win, account_va, password_va, frame2):
    global loginflag
    username = account_va.get()
    password = password_va.get()
    if (username or password):
        if (username == 'admin' and password == '12345678'):
            tk.messagebox.showinfo("登陆成功", "欢迎您，管理员！")
            login_win.destroy()
            loginflag = True
            # 需要解开
            stop_grabbing()
            show_frame(frame2)
            start_grabbing()
        else:
            tk.messagebox.showerror("登录失败", "用户名或密码错误！")
            login_win.destroy()
            loginflag = False
            show_frame(frame1)
    else:
        tk.messagebox.showerror("登录失败", "请填写用户名和密码！")
        login_win.destroy()
        loginflag = False
        show_frame(frame1)


# 登陆取消

@logger.catch
def do_cancel(login_win):
    global loginflag
    login_win.destroy()
    loginflag = False


@logger.catch
def on_exit(login_win):
    global loginflag
    loginflag = False
    login_win.destroy()


# 显示登陆页面
@logger.catch
def show_login_page(frame2):
    global loginflag
    if loginflag==False:
        login_win = tk.Toplevel()
        login_win.title('登陆')
        login_win.iconbitmap(current_file + 'logo.ico')
        login_win.geometry('300x200')
        login_win.protocol("WM_DELETE_WINDOW", lambda: on_exit(login_win))
        # 用户登陆
        tk.Label(login_win, text='用户登陆', font=('微软雅黑', 20)).grid(row=0, column=0, columnspan=10)
        # 登陆账号
        tk.Label(login_win, text='登陆账号:', font=('微软雅黑', 15)).grid(row=1, column=0, padx=10)
        # 账号输入框
        account_va = tk.StringVar()
        tk.Entry(login_win, textvariable=account_va).grid(row=1, column=1, padx=5)

        # 登陆密码
        tk.Label(login_win, text='登陆密码:', font=('微软雅黑', 15)).grid(row=2, column=0, padx=10)
        # 密码输入框
        password_va = tk.StringVar()
        tk.Entry(login_win, textvariable=password_va, show='*').grid(row=2, column=1, padx=5)
        # 登陆按钮
        tk.Button(login_win, text='登陆', font='微软雅黑', bg='red', fg='white', width=10, relief="flat",
                  command=lambda: do_login(login_win, account_va, password_va, frame2)).grid(row=3, column=0,
                                                                                             columnspan=5)
        tk.Button(login_win, text='取消', font='微软雅黑', bg='green', fg='white', width=10, relief="flat",
                  command=lambda: do_cancel(login_win)).grid(row=5, column=0, columnspan=5)
        loginflag = True
    else:
        pass


@logger.catch
def show_label(show):
    if show:
        labelORIGIN.grid(row=6, column=0, columnspan=2, sticky='wens', padx=30, pady=10)
        time.sleep(0.1)
        labelORIGIN.grid_forget()
        labelNG.grid_forget()
        labelOK.grid(row=6, column=0, columnspan=2, sticky='wens', padx=30, pady=10)
    else:
        labelORIGIN.grid(row=6, column=0, columnspan=2, sticky='wens', padx=30, pady=10)
        time.sleep(0.1)
        labelORIGIN.grid_forget()
        labelOK.grid_forget()
        labelNG.grid(row=6, column=0, columnspan=2, sticky='wens', padx=30, pady=10)


@logger.catch
def handle_space(event):
    labelORIGIN.grid_forget()
    labelOK.grid_forget()
    labelNG.grid_forget()
    labelORIGIN.grid(row=6, column=0, columnspan=2, sticky='wens', padx=30, pady=10)


@logger.catch
def base_path(path):
    if getattr(sys, 'frozen', None):
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(__file__)
    return os.path.join(basedir, path)


if __name__ == "__main__":
    mutex = win32event.CreateMutex(None, False, 'MyMutexName')
    if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
        mutex = None
    else:
        global deviceList
        deviceList = MV_CC_DEVICE_INFO_LIST()
        global tlayerType
        tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE
        global cam
        cam = MvCamera()
        global nSelCamIndex
        nSelCamIndex = 0
        global obj_cam_operation
        obj_cam_operation = 0
        global b_is_run
        ser1=None
        b_is_run = False
        last_result = None
        threadflag = None
        COMGUNNUM = ""
        matche_point=0
        COMSIGNALNUM = ""
        previous_COMGUNNUM = ""
        previous_COMSIGNALNUM = ""
        contour_info_list = []
        signalbuttonup = ''
        signalbuttondown = ''
        left_left_NUM = 0
        left_upper_NUM = 0
        right_left_NUM = 0
        right_lower_NUM = 0
        process_threshold_NUM = 0
        compare_threshold_NUM = 0
        process_kernel_x_threshold_NUM = 0
        process_kernel_y_threshold_NUM = 0
        process_area_low_threshold_NUM = 0
        process_area_threshold_high_NUM = 0
        weight_threshold_NUM = 0
        pattern_compare_threshold_NUM = 0
        image_threading_NUM=0
        opcua_address_NUM=None
        subscribe_node_NUM=None
        takephoto_NUM=None
        xintiao_NUM=None
        finalresult_NUM=None
        client=None
        opc_connect=False
        # different_threshold_NUM=0
        COM_sharedata = {'sedata': None}
        current_file = base_path('')
        parentdir = current_file + 'image\\test.jpg'
        parentdirsign = current_file + 'image\\sign.jpg'
        parentdirdemo = current_file + 'image\\demo.jpg'
        folder_path = current_file + 'cuts'
        folder_path1 = current_file + 'cut1'
        imagepath = current_file + 'image'
        csvpath = current_file + 'csv'
        # 界面设计代码
        window = tk.Tk()
        window.title('条码比对系统')
        window.iconbitmap(current_file + 'logo.ico')
        window.geometry('1400x800')
        main_menu = tk.Menu(window)
        picklename = 'settings.dat'
        picklename1 = 'parameter.dat'
        compickle = 'comport.dat'
        screenshot = 'screenshot.dat'
        saveImg = 'saveImg.dat'
        thresholdpickle = 'thresholdpickle.dat'
        comparea = 'comparea.dat'
        # 创建一个空列表以存储所有图片
        image_list = []
        image_rectangle = False
        cut_Pos = np.zeros((2, 2), int)
        global screenshotNum
        screenshotNum = 0

        global screen_img
        event = threading.Event()

        try:
            with open(thresholdpickle, "rb") as f:
                loaded_params = pickle.load(f)
                param1_loaded, param2_loaded, param3_loaded, param4_loaded, param5_loaded, param6_loaded, param7_loaded,param8_loaded,param9_loaded,param10_loaded,param11_loaded ,param12_loaded,param13_loaded,param14_loaded= loaded_params
                process_threshold_NUM = int(param1_loaded)
                compare_threshold_NUM = int(param2_loaded)
                process_kernel_x_threshold_NUM = int(param3_loaded)
                process_kernel_y_threshold_NUM = int(param4_loaded)
                process_area_low_threshold_NUM = int(param5_loaded)
                process_area_threshold_high_NUM = int(param6_loaded)
                weight_threshold_NUM = int(param7_loaded)
                pattern_compare_threshold_NUM=int(param8_loaded)
                image_threading_NUM = int(param9_loaded)
                opcua_address_NUM = str(param10_loaded).strip()
                subscribe_node_NUM = str(param11_loaded).strip()
                takephoto_NUM = str(param12_loaded).strip()
                xintiao_NUM = str(param13_loaded).strip()
                finalresult_NUM = str(param14_loaded).strip()
                # different_threshold_NUM = int(param10_loaded)

        except:
            process_threshold_NUM = 200
            compare_threshold_NUM = 100
            process_kernel_x_threshold_NUM = 75
            process_kernel_y_threshold_NUM = 1
            process_area_low_threshold_NUM = 4000
            process_area_threshold_high_NUM = 250000
            weight_threshold_NUM = 5
            pattern_compare_threshold_NUM=20
            image_threading_NUM = 8
            opcua_address_NUM = ''
            subscribe_node_NUM = ''
            takephoto_NUM = ''
            xintiao_NUM = ''
            finalresult_NUM = ''
            # different_threshold_NUM = 200
        # thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=image_threading_NUM)
        try:
            with open(comparea, 'rb') as f:
                left_left_NUM = int(pickle.load(f))
                left_upper_NUM = int(pickle.load(f))
                right_left_NUM = int(pickle.load(f))
                right_lower_NUM = int(pickle.load(f))
        except:
            left_left_NUM = 100
            left_upper_NUM = 100
            right_left_NUM = 200
            right_lower_NUM = 200
        try:
            with open(picklename, 'rb') as f:
                checked = pickle.load(f)
                # print(checked,'withwith')
        except:
            checked = False
        try:
            with open(saveImg, 'rb') as f:
                img_checked = pickle.load(f)
        except:
            img_checked = False
        try:
            with open(compickle, 'rb') as f:
                COMGUNNUM = pickle.load(f)
                matche_point = float(pickle.load(f))
                # COMSIGNALNUM=pickle.load(f)
        except:
            COMGUNNUM = ""
            matche_point = 0
        try:
            with open(screenshot, 'rb') as f:
                screenshotNum = int(pickle.load(f))
        except:
            screenshotNum = 0

        if not os.path.exists(imagepath):
            # 如果不存在，创建文件夹
            os.makedirs(imagepath, exist_ok=True)
        if not os.path.exists(csvpath):
            # 如果不存在，创建文件夹xua
            os.makedirs(csvpath, exist_ok=True)
        # 创建目录以保存图像
        if not os.path.exists(folder_path):
            # 如果不存在，创建文件夹
            os.makedirs(folder_path, exist_ok=True)
        if not os.path.exists(folder_path1):
            # 如果不存在，创建文件夹
            os.makedirs(folder_path1, exist_ok=True)
        global frame1
        try:
            ser1 = serial.Serial(COMGUNNUM, 9600, timeout=1)
        except serial.SerialException as e:
            tkinter.messagebox.showinfo('show info', '串口打开失败，请选择端口后重试！')
        except Exception as e:
            tkinter.messagebox.showinfo('show info', '有异常，请检查设备！')


        frame1 = tk.Frame(window)
        frame2 = tk.Frame(window)
        main_menu.add_command(label="比对界面", command=lambda: show_mianframe(frame1))
        main_menu.add_command(label="管理员界面", command=lambda: show_login_page(frame2))
        window.config(menu=main_menu)
        window.grid_rowconfigure(0, weight=1)
        window.grid_columnconfigure(0, weight=1)
        frame1.grid(row=0, column=0, sticky="nsew")
        frame2.grid(row=0, column=0, sticky="nsew")
        frame1.grid_columnconfigure(0, weight=0)
        frame1.grid_columnconfigure(1, weight=0)
        frame1.grid_columnconfigure(2, weight=0)
        frame1.grid_columnconfigure(3, weight=0)
        frame1.grid_columnconfigure(4, weight=0)
        frame1.grid_rowconfigure(0, weight=1)
        frame1.grid_rowconfigure(1, weight=1)
        frame1.grid_rowconfigure(2, weight=1)
        frame1.grid_rowconfigure(3, weight=1)
        frame1.grid_rowconfigure(4, weight=1)
        frame1.grid_rowconfigure(5, weight=1)
        frame1.grid_rowconfigure(6, weight=1)
        frame1.grid_rowconfigure(7, weight=1)
        frame1.grid_rowconfigure(7, weight=1)
        frame1.grid_rowconfigure(8, weight=1)
        frame1.grid_rowconfigure(9, weight=1)
        frame1.grid_rowconfigure(10, weight=1)
        frame1.grid_rowconfigure(11, weight=1)
        frame1.grid_rowconfigure(12, weight=1)
        frame1.grid_rowconfigure(13, weight=1)
        frame1.grid_rowconfigure(14, weight=1)
        frame1.grid_rowconfigure(15, weight=1)
        frame1.grid_rowconfigure(16, weight=1)

        frame2.grid_columnconfigure(0, weight=0)
        frame2.grid_columnconfigure(1, weight=0)
        frame2.grid_columnconfigure(2, weight=0)
        frame2.grid_columnconfigure(3, weight=0)
        frame2.grid_columnconfigure(4, weight=0)
        frame2.grid_columnconfigure(5, weight=0)
        frame2.grid_columnconfigure(6, weight=0)
        frame2.grid_rowconfigure(0, weight=1)
        frame2.grid_rowconfigure(1, weight=1)
        frame2.grid_rowconfigure(2, weight=1)
        frame2.grid_rowconfigure(3, weight=1)
        frame2.grid_rowconfigure(4, weight=1)
        frame2.grid_rowconfigure(5, weight=1)
        frame2.grid_rowconfigure(6, weight=1)
        frame2.grid_rowconfigure(7, weight=1)
        frame2.grid_rowconfigure(7, weight=1)
        frame2.grid_rowconfigure(8, weight=1)
        frame2.grid_rowconfigure(9, weight=1)
        frame2.grid_rowconfigure(10, weight=1)
        frame2.grid_rowconfigure(11, weight=1)
        frame2.grid_rowconfigure(12, weight=1)
        frame2.grid_rowconfigure(13, weight=1)
        frame2.grid_rowconfigure(14, weight=1)
        frame2.grid_rowconfigure(15, weight=1)
        frame2.grid_rowconfigure(16, weight=1)
        frame1.tkraise()
        checked_val = tk.BooleanVar()
        checked_val.set(checked)
        on_save_img_val = tk.BooleanVar()
        on_save_img_val.set(img_checked)
        model_val = tk.StringVar()
        global triggercheck_val
        triggercheck_val = tk.IntVar()
        # page2 = Frame(frame2, height=384, width=512, relief=GROOVE, borderwidth=2)
        # page1 = Frame(frame1, height=384, width=512, relief=GROOVE, borderwidth=2)
        # page2.grid(row=0, column=0, sticky="nsew")
        # page1.grid(row=0, column=0, sticky="nsew")
        panel2 = Label(frame2)
        panel1 = Label(frame1, height=384, width=512)
        panel2.grid(row=1, column=6, rowspan=10,columnspan=4,padx=10, pady=10)
        panel1.grid(row=2, column=3, rowspan=10, padx=10, pady=10)
        global labelOK
        global labelNG
        global labelORIGIN
        labelOK = tk.Label(frame1, text="OK", background="green", font=('黑体', 40, 'bold'), padx=80, pady=80)
        labelNG = tk.Label(frame1, text="NG", background="red", font=('黑体', 40, 'bold'), padx=80, pady=80)
        labelORIGIN = tk.Label(frame1, text="AB", font=('黑体', 40, 'bold'), background="white", padx=80, pady=80)
        # labelOK.grid(row=6, column=0, columnspan=2, sticky='wens', padx=30, pady=10)

        try:
            image = Image.open(parentdirsign)
        except:
            image = Image.open(current_file + 'logo.ico')
        resized_image = image.resize((512, 384), Image.LANCZOS)
        photo = ImageTk.PhotoImage(resized_image)
        canvas = tk.Canvas(frame1, width=photo.width(), height=photo.height())
        image_item = canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        canvas.grid(row=2, column=2, rowspan=10, padx=10, pady=10)
        # print(parentdir)
        ocr = CnOcr(rec_model_name='densenet_lite_136-gru', det_model_name='en_PP-OCRv3_det',
                    det_more_configs={'use_angle_clf': True})
        now = datetime.datetime.now()
        year = now.year
        month = now.month


        @logger.catch
        def Opcua_Connect():
            global client,opcua_address_NUM,opc_connect
            client = Client(opcua_address_NUM)
            # print("开始链结")
            try:
                client.connect()
                subscribe_nodes()
                opc_connect=True

            except Exception as e:
                opc_connect=False
                # print("链结失败")
                pass




        # 绑定下拉列表至设备信息索引
        def xFunc(event):
            global nSelCamIndex
            nSelCamIndex = TxtWrapBy("[", "]", device_list.get())


        # ch:枚举相机 | en:enum devices
        @logger.catch()
        def enum_devices():
            global deviceList
            global obj_cam_operation
            deviceList = MV_CC_DEVICE_INFO_LIST()
            tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE
            ret = MvCamera.MV_CC_EnumDevices(tlayerType, deviceList)
            if ret != 0:
                tkinter.messagebox.showerror('show error', 'enum devices fail! ret = ' + ToHexStr(ret))

            if deviceList.nDeviceNum == 0:
                tkinter.messagebox.showinfo('show info', 'find no device!')
            # print ("Find %d devices!" % deviceList.nDeviceNum)

            devList = []
            for i in range(0, deviceList.nDeviceNum):
                mvcc_dev_info = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
                if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE:
                    # print ("\ngige device: [%d]" % i)
                    chUserDefinedName = ""
                    for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chUserDefinedName:
                        if 0 == per:
                            break
                        chUserDefinedName = chUserDefinedName + chr(per)
                    # print ("device model name: %s" % chUserDefinedName)

                    nip1 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
                    nip2 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
                    nip3 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
                    nip4 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
                    # print ("current ip: %d.%d.%d.%d\n" % (nip1, nip2, nip3, nip4))
                    devList.append(
                        "[" + str(i) + "]GigE: " + chUserDefinedName + "(" + str(nip1) + "." + str(nip2) + "." + str(
                            nip3) + "." + str(nip4) + ")")
                elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
                    # print ("\nu3v device: [%d]" % i)
                    chUserDefinedName = ""
                    for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chUserDefinedName:
                        if per == 0:
                            break
                        chUserDefinedName = chUserDefinedName + chr(per)
                    # print ("device model name: %s" % chUserDefinedName)

                    strSerialNumber = ""
                    for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber:
                        if per == 0:
                            break
                        strSerialNumber = strSerialNumber + chr(per)
                    # print ("user serial number: %s" % strSerialNumber)
                    devList.append("[" + str(i) + "]USB: " + chUserDefinedName + "(" + str(strSerialNumber) + ")")
            device_list["value"] = devList
            device_list.current(0)

            # ch:打开相机 | en:open device


        @logger.catch
        def open_device():
            global deviceList
            global nSelCamIndex
            global obj_cam_operation
            global b_is_run
            if True == b_is_run:
                tkinter.messagebox.showinfo('show info', 'Camera is Running!')
                return
            obj_cam_operation = CameraOperation(cam, deviceList, nSelCamIndex)
            ret = obj_cam_operation.Open_device()
            if 0 != ret:
                b_is_run = False
            else:
                model_val.set('continuous')
                b_is_run = True
            devicestatuclose.grid_forget()
            devicestatucl.grid_forget()
            devicestatuop.grid(row=1, column=1, padx=10, pady=10, sticky="w")
            devicestatuopen.grid(row=0, column=2, columnspan=2, padx=10, pady=10, sticky="w")


        # ch:开始取流 | en:Start grab image

        @logger.catch
        def start_grabbing():
            global obj_cam_operation
            obj_cam_operation.Start_grabbing(frame2, panel2)


        @logger.catch
        def start_grabbing1():
            global obj_cam_operation
            obj_cam_operation.Start_grabbing(frame1, panel1)


        # ch:停止取流 | en:Stop grab image
        @logger.catch
        def stop_grabbing():
            global obj_cam_operation
            obj_cam_operation.Stop_grabbing()


        @logger.catch
        def stop_grabbing1():
            global obj_cam_operation
            obj_cam_operation.Stop_grabbing()



        def process_and_display_difference_images(partial_image, matched_region, threshold=compare_threshold_NUM):
            global image_rectangle
            try:
                # 确保partial_image与matched_region具有相同的尺寸
                partial_image = cv2.resize(partial_image, (matched_region.shape[1], matched_region.shape[0]))
                gray_matched_region = cv2.cvtColor(matched_region, cv2.COLOR_BGR2GRAY)
                _, binary_matched_region = cv2.threshold(gray_matched_region, process_threshold_NUM, 255,
                                                         cv2.THRESH_BINARY_INV)
                # cv2.imshow('binary_matched_region', binary_matched_region)
                # cv2.waitKey(0)
                all_pixel_count = np.sum(binary_matched_region == 255)
                # 计算两图像的差异
                difference = cv2.absdiff(matched_region, partial_image)
                # 转换差异图像为灰度
                gray_difference = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)
                # cv2.imshow('gray_difference', gray_difference)
                # cv2.waitKey(0)
                # 二值化差异图像
                _, binary_difference = cv2.threshold(gray_difference, threshold, 255, cv2.THRESH_BINARY)
                # cv2.imshow('binary_difference', binary_difference)
                # cv2.waitKey(0)
                white_pixel_count = np.sum(binary_difference == 255)
                percent = (white_pixel_count * weight_threshold_NUM) / all_pixel_count
                # print(white_pixel_count, 'white_pixel_count',compare_threshold_NUM,all_pixel_count,'all_pixel_count',percent)
                # 寻找差异区域的轮廓
                contours, _ = cv2.findContours(binary_difference, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                # 合并相邻的轮廓
                merged_contours = []
                current_contour = None
                for contour in contours:
                    area = cv2.contourArea(contour)
                    # print(area, 'area')
                    if area > 10:
                        x1, y1, w1, h1 = cv2.boundingRect(current_contour)
                        x2, y2, w2, h2 = cv2.boundingRect(contour)
                        if current_contour is None:
                            current_contour = contour
                        elif x2 - (x1 + w1) < 100:
                            # 如果相邻，则合并两个轮廓
                            current_contour = np.concatenate((current_contour, contour))
                        else:
                            # 如果不相邻，则将当前轮廓添加到合并列表中，并更新当前轮廓为下一个轮廓
                            merged_contours.append(current_contour)
                            current_contour = contour
                    else:
                        pass

                # 将最后一个轮廓添加到合并列表中
                if current_contour is not None:
                    merged_contours.append(current_contour)
                try:
                    for contour in merged_contours:
                        area = cv2.contourArea(contour)
                        # print(area, 'area') #and percent > 0.15
                        if area > pattern_compare_threshold_NUM:
                            image_rectangle = True
                            x, y, w, h = cv2.boundingRect(contour)
                            # 绘制方框
                            cv2.rectangle(matched_region, (x, y), (x + w, y + h), (0, 0, 255), 6)
                except:
                    image_rectangle = True
                    matched_region = matched_region
                return matched_region

            except Exception as e:
                image_rectangle = False
                # print(f"An exception occurred: {str(e)}")
                # return None
                pass



        def process_and_insert_cropped_region(image1, image2):
            def extract_rotated_rect(image):
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                blurred_image = cv2.GaussianBlur(gray, (5, 5), 0)
                _, binary_image = cv2.threshold(blurred_image, process_threshold_NUM, 255, cv2.THRESH_BINARY_INV)
                # kernel = np.ones((3, 3), np.uint8)
                # opening = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, kernel)
                contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                merged_contour = np.concatenate(contours)
                rect = cv2.minAreaRect(merged_contour)
                angle = rect[2]
                return rect, merged_contour

            def rotate_image(image, angle, rect2):
                center_x, center_y = image.shape[1] // 2, image.shape[0] // 2
                h, w = image.shape[:2]
                rotation_matrix = cv2.getRotationMatrix2D(rect2, angle, 1)
                new_H = int(w * fabs(sin(radians(angle))) + h * fabs(cos(radians(angle))))
                new_W = int(h * fabs(sin(radians(angle))) + w * fabs(cos(radians(angle))))
                # 2.3 平移
                rotation_matrix[0, 2] += (new_W - w) / 2
                rotation_matrix[1, 2] += (new_H - h) / 2
                rotated_image = cv2.warpAffine(image, rotation_matrix, (new_W, new_H),
                                               borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))

                return rotated_image

            rect1, merged_contour1 = extract_rotated_rect(image1)
            rect2, merged_contour2 = extract_rotated_rect(image2)

            box1 = cv2.boxPoints(cv2.minAreaRect(merged_contour1))
            box2 = cv2.boxPoints(cv2.minAreaRect(merged_contour2))

            mask1 = np.ones_like(image1) * 255
            mask2 = np.ones_like(image2) * 255

            cv2.fillPoly(mask1, [np.int0(box1)], (255, 255, 255))
            cv2.fillPoly(mask2, [np.int0(box2)], (255, 255, 255))

            result1 = cv2.bitwise_and(image1, mask1)
            result2 = cv2.bitwise_and(image2, mask2)

            image3 = result1
            image4 = result2
            # cv2.imshow('image3', image3)
            # cv2.imshow('image4', image4)
            angle1 = rect1[2]
            angle2 = rect2[2]
            # print(angle1, angle2)
            if (angle1 > 45):
                angle1 = angle1 - 90
            if (angle2 > 45):
                angle2 = angle2 - 90
            # print(angle1, angle2)
            if abs(angle1 - angle2) < 25:
                # print(angle1 - angle2)
                # print('1111')
                image3 = rotate_image(image3, angle1 - angle2, rect1[0])
            else:
                # print(angle1 - angle2)
                # print('2222')
                x1, y1, w1, h1 = cv2.boundingRect(merged_contour1)
                image3 = image3[y1:y1 + h1, x1:x1 + w1]
            # time.sleep(0.2)
            gray3 = cv2.cvtColor(image3, cv2.COLOR_BGR2GRAY)
            gray4 = cv2.cvtColor(image4, cv2.COLOR_BGR2GRAY)
            _, binary_image3 = cv2.threshold(gray3, process_threshold_NUM, 255, cv2.THRESH_BINARY_INV)
            _, binary_image4 = cv2.threshold(gray4, process_threshold_NUM, 255, cv2.THRESH_BINARY_INV)

            contours3, _ = cv2.findContours(binary_image3, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contours4, _ = cv2.findContours(binary_image4, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            merged_contour3 = np.concatenate(contours3)
            merged_contour4 = np.concatenate(contours4)

            x3, y3, w3, h3 = cv2.boundingRect(merged_contour3)
            x4, y4, w4, h4 = cv2.boundingRect(merged_contour4)

            # cv2.rectangle(image5, (x3, y3), (x3 + w3, y3 + h3), (0, 255, 0), 1)
            # cv2.rectangle(image6, (x4, y4), (x4 + w4, y4 + h4), (0, 255, 0), 1)
            roi1 = image3[y3:y3 + h3, x3:x3 + w3]
            roi2 = image2[y4:y4 + h4, x4:x4 + w4]
            roi1 = cv2.resize(roi1, (roi2.shape[1], roi2.shape[0]))
            return roi1, roi2, image2, x4, y4, w4, h4



        def match_and_extract_region(partial_image, full_image):
            # partial_image = cv2.imread(partial_image)
            # image = cv2.imread(input_image_path)
            # 转换图像为灰度
            gray_full_image = cv2.cvtColor(full_image, cv2.COLOR_BGR2GRAY)
            gray_partial_image = cv2.cvtColor(partial_image, cv2.COLOR_BGR2GRAY)

            # 使用SIFT特征检测和匹配
            sift = cv2.SIFT_create()
            kp1, des1 = sift.detectAndCompute(gray_partial_image, None)
            kp2, des2 = sift.detectAndCompute(gray_full_image, None)
            # 使用FLANN匹配器进行特征匹配
            FLANN_INDEX_KDTREE = 0
            index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
            search_params = dict(checks=50)
            flann = cv2.FlannBasedMatcher(index_params, search_params)
            matches = flann.knnMatch(des1, des2, k=2)
            # 创建BFMatcher（暴力匹配器）对象
            # bf = cv2.BFMatcher()
            #
            # # 使用KNN匹配
            # matches = bf.knnMatch(des1, des2, k=2)
            # 选择良好的匹配项

            good_matches = [m for m, n in matches if m.distance < float(matche_point) * n.distance]
            # 绘制匹配结果
            # matched_image = cv2.drawMatches(full_image, kp1, partial_image, kp2, good_matches, None,
            #                                 flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)

            # 获取局部图片和完整图片中的对应点
            partial_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            full_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

            # 计算单映射变换矩阵H
            H, _ = cv2.findHomography(partial_pts, full_pts, cv2.RANSAC, 5.0)

            # 使用透视变换来截取匹配区域
            h, w = partial_image.shape[:2]
            corners = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
            transformed_corners = cv2.perspectiveTransform(corners, H)

            # 计算匹配区域的尺寸
            min_x = np.min(transformed_corners[:, :, 0])
            max_x = np.max(transformed_corners[:, :, 0])
            min_y = np.min(transformed_corners[:, :, 1])
            max_y = np.max(transformed_corners[:, :, 1])
            # 裁剪匹配区域
            matched_region = full_image[int(min_y):int(max_y), int(min_x):int(max_x)]
            return matched_region, int(min_y), int(max_y), int(min_x), int(max_x)
        # 多线程处理图片
        def process_all_image(image, template_image, results_to_match):
            # for image in images_to_match:
            # image, template_image, index, template_images_list = args
            try:
                matched_region, min_y, max_y, min_x, max_x = match_and_extract_region(image, template_image)
                matched_region_array=np.array(matched_region)
                if matched_region_array.size!=0:
                    try:
                        roi1, roi2, image4, x4, y4, w4, h4 = process_and_insert_cropped_region(image, matched_region)
                        result = process_and_display_difference_images(roi1, roi2)
                        image4[y4:y4 + h4, x4:x4 + w4] = result
                        # 将image4粘贴到template_image的指定位置
                        # 将image4和坐标信息封装到一个元组
                        image_info = (image4, min_y, max_y, min_x, max_x)
                        results_to_match.append(image_info)
                    except (TypeError, ValueError) as e:
                        # print(f"An error occurred: {e}")
                        pass
                else:
                    cv2.imwrite('image/not_match.jpg',image)
                    logger.info('有未识别到的图片！')
            except:
                logger.info('有未识别到的图片！')
        def contour_sort_key(contour):
            x, y, w, h = cv2.boundingRect(contour)
            # print(x, y, w, h ,'x, y, w, h ')
            # print(y, x, 'xyyyy')
            y_group = y // 40  # 除以10用于忽略10像素范围内的误差
            return (y_group, x, y)

        @logger.catch()
        def process_image1(input_image_path, outputdir, threshold, kernel_threshold_x, kernel_threshold_y,
                          process_area_low_threshold,
                          process_area_threshold_high):
            # print(threshold, kernel_threshold_x, kernel_threshold_y, process_area_low_threshold,
            #       process_area_threshold_high)
            # print(process_threshold_NUM, compare_threshold_NUM)
            # 读取图像
            image = cv2.imread(input_image_path)

            # 转换为灰度图像
            gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

            # 对灰度图像进行二值化处理
            _, binary_image = cv2.threshold(gray_image, threshold, 255, cv2.THRESH_BINARY)
            cv2.namedWindow("binary_image", cv2.WINDOW_NORMAL)
            cv2.imshow("binary_image", binary_image)
            cv2.waitKey(0)
            # 执行边缘检测，例如使用Canny算法
            edges = cv2.Canny(binary_image, 30, 255)
            cv2.namedWindow("edges", cv2.WINDOW_NORMAL)
            cv2.imshow("edges", edges)
            cv2.waitKey(0)
            # 使用形态学操作来连接相邻的轮廓
            kernel = np.ones((kernel_threshold_y, kernel_threshold_x), np.uint8)
            closed_image = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
            cv2.namedWindow("closed_image", cv2.WINDOW_NORMAL)
            cv2.imshow("closed_image", closed_image)
            cv2.waitKey(0)
            # 寻找轮廓
            contours, _ = cv2.findContours(closed_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # 创建一个副本以绘制方框
            image_with_boxes = image.copy()

            # 创建一个列表来存储满足面积阈值条件的轮廓
            filtered_contours = []

            # 遍历轮廓
            for contour in contours:
                # 计算轮廓的面积
                area = cv2.contourArea(contour)
                # print(area)

                # 如果面积在阈值范围内，则添加到列表中
                if process_area_low_threshold < area < process_area_threshold_high:
                    filtered_contours.append(contour)
                    x, y, w, h = cv2.boundingRect(contour)
                    # 绘制方框
                    cv2.rectangle(image_with_boxes, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # 保存带有方框的图像
            output_image_path = os.path.join(imagepath, 'image_with_boxes.jpg')
            cv2.imwrite(output_image_path, image_with_boxes)
            # 列出文件夹中的所有文件
            file_list = os.listdir(outputdir)
            # 遍历文件列表并删除图片文件
            for filename in file_list:
                file_path = os.path.join(folder_path, filename)
                if filename.endswith((".jpg", ".jpeg", ".png", ".gif")):  # 指定图片文件扩展名
                    os.remove(file_path)
            # 保存满足条件的轮廓图像
            sorted_contours = sorted(filtered_contours, key=contour_sort_key)
            # print(sorted_contours,'sorted_contours = sorted(filtered_contours, key=contour_sort_key)')
            for i, contour in enumerate(sorted_contours):
                x, y, w, h = cv2.boundingRect(contour)
                # print(y, x, 'yxxxxx')
                try:
                    roi = image[y - 5:y + h + 5, x - 5:x + w + 5]
                    filename = os.path.join(outputdir, f'cut_{i}.jpg')
                    cv2.imwrite(filename, roi)
                    contour_info_list.append({
                        'x': x - 5,
                        'y': y - 5,
                        'w': w + 5,
                        'h': h + 5,
                        'filename': f'cut_{i}.jpg'
                    })
                except:
                    roi = image[y:y + h, x:x + w]
                    filename = os.path.join(outputdir, f'cut_{i}.jpg')
                    cv2.imwrite(filename, roi)
                    contour_info_list.append({
                        'x': x,
                        'y': y,
                        'w': w,
                        'h': h,
                        'filename': f'cut_{i}.jpg'
                    })

            if outputdir == folder_path1:
                return True
            else:
                return False

        @logger.catch()
        def read_all_img():
            global image_list
            for filename1 in os.listdir(folder_path):
                if filename1.endswith(('.jpg', '.jpeg', '.png')):  # 确保文件是图片文件
                    filepath1 = os.path.join(folder_path, filename1)
                    image = cv2.imread(filepath1)
                    image_list.append(image)

        @logger.catch()
        def read_files():
            # global image_list
            # imagedemo=cv2.imread(parentdirdemo)
            full_image = cv2.imread(parentdirdemo)
            # 创建线程
            threads = []
            results_to_match = []
            num_threads = len(image_list)
            max_threads = 8
            # num_cores = multiprocessing.cpu_count()
            # print("可用的CPU核心数：", num_cores)
            # partial_func = functools.partial(process_all_image, full_image)
            # print('开始了')
            # pool = multiprocessing.Pool(processes=num_cores)
            # for result in pool.map(partial_func, image_list):
            #     result_list.append(result)  # 将处理结果添加到共享列表中
            # pool.close()
            # pool.join()
            # print('thread time: %s Seconds' % (end - start))
            for image in image_list:
                thread = threading.Thread(target=process_all_image, args=(image,full_image, results_to_match))
                threads.append(thread)
                thread.start()
            # with ThreadPoolExecutor(max_workers=max_threads) as executor:
            #     for i in range(num_threads):
            #         executor.submit(process_all_image, image_list[i], full_image, results_to_match)
            #     executor.shutdown(wait=True)  # 这将阻塞主线程直到所有任务完成
            # for i in range(num_threads):
            #     thread = threading.Thread(target=process_image,
            #                               args=(image_list[i], full_image, results_to_match, lock))
            #     threads.append(thread)
            #     thread.start()

            # 等待所有线程完成
            for thread in threads:
                thread.join()
            for image_info in results_to_match:
                image4, min_y, max_y, min_x, max_x = image_info
                full_image[min_y:max_y, min_x:max_x] = image4
            # cv2.imwrite('full_image.jpg', full_image)
            return full_image
        # ch:关闭设备 | Close device
        @logger.catch
        def close_device():
            global b_is_run
            global obj_cam_operation
            obj_cam_operation.Close_device()
            b_is_run = False
            # 清除文本框的数值
            text_frame_rate.delete(1.0, tk.END)
            text_exposure_time.delete(1.0, tk.END)
            text_gain.delete(1.0, tk.END)
            devicestatuopen.grid_forget()
            devicestatuop.grid_forget()
            devicestatucl.grid(row=1, column=1, padx=10, pady=10, sticky="w")
            devicestatuclose.grid(row=0, column=2, columnspan=2, padx=10, pady=10, sticky="w")


        # ch:设置触发模式 | en:set trigger mode
        @logger.catch
        def set_triggermode():
            global obj_cam_operation
            strMode = model_val.get()
            obj_cam_operation.Set_trigger_mode(strMode)


        # ch:设置触发命令 | en:set trigger software
        @logger.catch
        def trigger_once():
            global triggercheck_val
            global obj_cam_operation
            nCommand = triggercheck_val.get()
            obj_cam_operation.Trigger_once(nCommand)


        # ch:保存bmp图片 | en:save bmp image
        @logger.catch
        def bmp_save():
            global obj_cam_operation
            obj_cam_operation.b_save_bmp = True


        # ch:保存jpg图片 | en:save jpg image
        @logger.catch
        def jpg_save():
            global obj_cam_operation
            obj_cam_operation.b_save_jpg = True


        @logger.catch
        def getSerialdata():
            global ser1
            try:
                # print(COMGUNNUM)
                if ser1.is_open:
                    data = ser1.readline()
                    serialdata = data.decode().strip()
                    if (serialdata != ''):
                        serialdata = data.decode().strip()
                        # print(serialdata,'serialdata')
                        return serialdata
                    else:
                        time.sleep(0.1)
                else:
                    tkinter.messagebox.showinfo('show info', '串口未开启，将尝试为你打开串口')
                    ser1.open()
            except:
                pass


        @logger.catch  # 发送扫描命令
        def sendSerialOrder():
            global ser1
            if ser1:
                try:
                    if ser1.is_open:
                        hexStr = "16 54 0D"
                        # hexStr = "16 54 0D"
                        bytes_hex = bytes.fromhex(hexStr)
                        ser1.write(bytes_hex)
                    else:
                        tkinter.messagebox.showinfo('show info', '串口未开启，将尝试为你打开串口')
                        ser1.open()
                except:
                    ser1.close()
                    tkinter.messagebox.showinfo('show info', '获取串口信息失败，串口已关闭！')
            else:
                pass


        # 获得图片OCR识别结果
        @logger.catch
        def get_sn_code():
            keywords = ['SN', 'PN']
            search_prefix = 'N:'
            sn_code = ''
            position = np.zeros((4, 2))
            res = ocr.ocr(parentdirdemo)
            if res:
                for i in res:
                    text = i.get('text', '')
                    if any(keyword in text for keyword in keywords) and len(text) >= 17:
                        text = ''.join(text.split())
                        sn_code = text.replace(" ", "")[-17:]
                        position = i.get('position', position)
                        break
                #需改进
                if not sn_code:
                    for i in res:
                        if 'text' in i and len(i['text']) == 17:
                            sn_code = i['text']
                            position = i['position']
                            break

                if sn_code:
                    sn_code = sn_code[0] + str(sn_code[1:]).replace('O', '0')
                else:
                    sn_code = '未识别到合适数据'
            else:
                sn_code = '没找到数据'

            return sn_code, position

        @logger.catch
        def jpg_save1(event=None):
            global obj_cam_operation
            obj_cam_operation.b_save_jpg1 = True



        @logger.catch
        def on_save_img(event=None):
            with open(saveImg, 'wb') as f:
                pickle.dump(on_save_img_val.get(), f)
            flag = on_save_img_val.get()
            global obj_cam_operation
            obj_cam_operation.flag = flag


        @logger.catch
        def file_not_exist(file_path):
            return not os.path.exists(file_path)


        @logger.catch
        def CountRows(file_name):
            try:
                df = pd.read_csv(file_name)
                ok_rows = df[df['result'] == 'OK']
                ok_count = len(ok_rows)
                ng_rows = df[df['result'] == 'NG']
                ng_count = len(ng_rows)
                all_count = len(df)
                return ok_count, ng_count, all_count
            except:
                ok_count = 0
                ng_count = 0
                all_count = 0
                return ok_count, ng_count, all_count


        @logger.catch
        def CountProducts():
            current_dir = os.path.dirname(__file__)
            file_path = os.path.abspath(os.path.join(current_dir, 'csv'))
            filenames = os.listdir(file_path)
            ok_result = 0
            ng_result = 0
            all_result = 0
            for file_name in filenames:
                file_name_path = file_path + '\\' + file_name
                ok_count, ng_count, all_count = CountRows(file_name_path)
                ok_result += ok_count
                ng_result += ng_count
                all_result += all_count
            try:
                Reliability_rate = ok_result / all_result
            except:
                Reliability_rate = 0
            percentage = "{:.2%}".format(Reliability_rate)
            return (all_result, ng_result, percentage)


        @logger.catch
        def write_to_csv(serial_data, sn_code, result):
            open_flag = file_not_exist(base_path('csv\{year}.{mon}.csv').format(year=year, mon=month).strip())
            with open(base_path('csv\{year}.{mon}.csv').format(year=year, mon=month), mode='a', encoding='utf-8',
                      newline='') as file:
                writer = csv.writer(file)
                column_names = ['serial_data', 'SnCode', 'result', 'costrat_time']
                if open_flag:
                    writer.writerow(column_names)
                costrat_time = datetime.datetime.now()
                data = [serial_data, sn_code, result, costrat_time]
                if result != 'continue':
                    writer.writerow(data)


        @logger.catch
        def save_counts_to_pickle(ok_count, ng_count, all_count):
            with open(picklename1, 'wb') as f:
                pickle.dump(ok_count, f)
                pickle.dump(ng_count, f)
                pickle.dump(all_count, f)


        @logger.catch
        def subscribe_nodes():
            global client
            handler = SubHandler()
            myvar = client.get_node(subscribe_node_NUM)
            sub = client.create_subscription(500, handler)
            handle = sub.subscribe_data_change(myvar)
            time.sleep(0.1)

        @logger.catch
        def send_order_to_zero():
            global client
            try:
                write_value_zero = ua.DataValue(ua.Variant(0, ua.VariantType.Int16))
                take_photo_NUM_flag = client.get_node(takephoto_NUM)
                final_result_NUM_flag = client.get_node(finalresult_NUM)
                temp_take_photo_NUM = take_photo_NUM_flag.get_value()
                temp_final_result_NUM = final_result_NUM_flag.get_value()
                if temp_take_photo_NUM != 0:
                    take_photo_NUM_flag.set_value(write_value_zero)
                if temp_final_result_NUM != 0:
                    final_result_NUM_flag.set_value(write_value_zero)
            except:
                messagebox.showinfo('show info', '清线连接opcua服务器！')

        @logger.catch
        def wait_for_response1():
            global image_rectangle,client
            write_value_OK = ua.DataValue(ua.Variant(1, ua.VariantType.Int16))
            write_value_NG = ua.DataValue(ua.Variant(2, ua.VariantType.Int16))
            write_value_ERROR = ua.DataValue(ua.Variant(3, ua.VariantType.Int16))
            while True:
                serial_data = getSerialdata()
                if serial_data:
                    flag = False
                    global last_result
                    result = ''
                    start_jpg_save1()
                    time.sleep(0.3)
                    img_flag = get_pardemo(parentdir, left_left_NUM, left_upper_NUM, right_left_NUM,
                                               right_lower_NUM,
                                               parentdirdemo)
                    img_opcua_flag = client.get_node(takephoto_NUM)
                    temp_opc=img_opcua_flag.get_value()
                    if(temp_opc==0):
                        img_opcua_flag.set_value(write_value_OK)
                    if img_flag:
                        SnCode, position = get_sn_code()
                        rect = canvas.create_rectangle(0, 0, canvas.winfo_width(), canvas.winfo_height(), fill='white',
                                                       outline='white')
                        canvas.update()
                        start_update_img_task(position)
                        result_node = client.get_node(finalresult_NUM)
                        if SnCode == serial_data:
                            if serial_data != last_result:
                                label_frame_rate5.config(text=serial_data, bg='green')
                                label_frame_rate6.config(text=SnCode, bg='green')
                                label_frame_rate4.config(text=last_result)
                                if not image_rectangle:
                                    flag = True
                                    result_node.set_value(write_value_OK)
                                else:
                                    flag = False
                                    result_node.set_value(write_value_NG)
                            else:
                                label_frame_rate4.config(text=last_result, bg='red')
                                label_frame_rate5.config(text=serial_data, bg='red')
                                label_frame_rate6.config(text=SnCode, bg='red')
                                flag = False
                                result_node.set_value(write_value_NG)
                        else:
                            label_frame_rate4.config(text=last_result)
                            label_frame_rate5.config(text=serial_data, bg='green')
                            label_frame_rate6.config(text=SnCode, bg='red')
                            flag = False
                            result_node.set_value(write_value_NG)
                        show_label(flag)
                        canvas.delete(rect)
                        try:
                            image1 = Image.open(parentdirsign)
                        except:
                            image1 =Image.open(parentdirdemo)
                        photo1 = ImageTk.PhotoImage(image1.resize((512, 384), Image.LANCZOS))
                        canvas.itemconfig(image_item, image=photo1)
                        canvas.update()
                        if checked_val.get():
                            write_to_csv(serial_data, SnCode, result)
                        else:
                            pass
                    else:
                        pass
                    last_result = serial_data
                    result_list = CountProducts()
                    ok_count = result_list[0]
                    ng_count = result_list[1]
                    all_count = result_list[2]
                    save_counts_to_pickle(ok_count, ng_count, all_count)
                    text_frame1_rate4.config(text=ok_count)
                    text_frame1_rate5.config(text=ng_count)
                    text_frame1_rate6.config(text=all_count)
                    image_rectangle=False
                else:
                    pass


        @logger.catch
        def send_heartbeat():
            global client, xintiao_NUM,opc_connect
            # print("send_heartbeat")
            timeout = 10  # 设置超时时间为10秒
            last_heartbeat_time = time.time()  # 记录上次接收到心跳信号的时间
            heartbeat = client.get_node(xintiao_NUM)
            while client is not None:
                current_time = time.time()  # 获取当前时间
                elapsed_time = current_time - last_heartbeat_time  # 计算与上次心跳信号的时间间隔

                # 如果超过了设定的超时时间，则触发报错操作
                if elapsed_time >= timeout:
                    messagebox.showinfo('show info', '心跳超时，请检查设备！')

                try:
                    heartbeat_value = heartbeat.get_value()
                    if heartbeat_value is None:  # 如果没有拿到心跳值，判断为与 OPC UA 断开连接
                        messagebox.showinfo('show info', '与 OPC UA 断开连接！')
                        break  # 跳出循环

                    if heartbeat_value == 100:
                        write_value = ua.DataValue(ua.Variant(200, ua.VariantType.Int16))
                    elif heartbeat_value == 200:
                        write_value = ua.DataValue(ua.Variant(100, ua.VariantType.Int16))
                    else:
                        # 处理其他情况的代码可以放在这里
                        pass
                    heartbeat.set_value(write_value)
                    opc_connect=True
                except Exception as e:
                    opc_connect=False
                    opcuabutton1.config(state="normal")
                    opcuabutton.config(state="normal")
                    logger.info(f"Error: {e}")
                    break


                last_heartbeat_time = current_time  # 更新上次接收到心跳信号的时间
                time.sleep(1)  # 等待1秒钟，避免频繁发送心跳


        @logger.catch
        def start_long_task():
            tkinter.messagebox.showinfo('show info', '已开始！')
            t = threading.Thread(target=wait_for_response1)
            t.daemon = True
            t.start()
            showimg()
            btn_start_jpg.config(state="disabled")

        @logger.catch
        def heartbeat_thread_task():
            heartbeat_thread = threading.Thread(target=send_heartbeat)
            heartbeat_thread.daemon = True
            heartbeat_thread.start()

        @logger.catch
        def opcua_connect_thread_task():
            opcua_connect_thread = threading.Thread(target=Opcua_Connect)
            opcua_connect_thread.daemon = True
            opcua_connect_thread.start()
            opcua_connect_thread.join()

        @logger.catch
        def start_update_img_task(position):
            t = threading.Thread(target=updateimg, args=(position,))
            t.daemon = True
            t.start()
            t.join()

        @logger.catch()
        def get_cut_params():
            left_left_text.delete("1.0", "end")
            left_left_text.insert('1.0', left_left_NUM)
            left_upper_text.delete("1.0", "end")
            left_upper_text.insert('1.0', left_upper_NUM)
            right_left_text.delete("1.0", "end")
            right_left_text.insert('1.0', right_left_NUM)
            right_lower_text.delete("1.0", "end")
            right_lower_text.insert('1.0', right_lower_NUM)


        @logger.catch
        def start_jpg_save1():
            t = threading.Thread(target=jpg_save1())
            t.daemon = True
            t.start()
            t.join()
        # @logger.catch
        # def start_reset_task():
        #     t=threading.Thread(target=reset_result)
        #     t.daemon=True
        #     t.start()

        @logger.catch
        def updateimg(position):
            # start=time.time()
            imagetest = cv2.imread(parentdir)
            full_image=read_files()
            if full_image is not None and np.all(position != 0):
                color = (0, 255, 0)
                x, y, w, h = cv2.boundingRect(position)
                cv2.rectangle(full_image, (x, y), (x + w, y + h), color, 6)
                result_image = imagetest.copy()
                result_image[left_upper_NUM:right_lower_NUM, left_left_NUM:right_left_NUM] = full_image
                cv2.imwrite(parentdirsign, result_image)
            else:
                pass

        @logger.catch
        def showimg():
            canvas.grid(row=2, column=2, rowspan=10, padx=10, pady=10)


        @logger.catch
        def on_checked():
            with open(picklename, 'wb') as f:
                pickle.dump(checked_val.get(), f)


        @logger.catch
        def get_parameter():
            global obj_cam_operation
            obj_cam_operation.Get_parameter()
            text_frame_rate.delete(1.0, tk.END)
            text_frame_rate.insert(1.0, obj_cam_operation.frame_rate)
            text_exposure_time.delete(1.0, tk.END)
            text_exposure_time.insert(1.0, obj_cam_operation.exposure_time)
            text_gain.delete(1.0, tk.END)
            text_gain.insert(1.0, obj_cam_operation.gain)


        @logger.catch
        def set_parameter():
            global obj_cam_operation
            obj_cam_operation.exposure_time = text_exposure_time.get(1.0, tk.END)
            obj_cam_operation.exposure_time = obj_cam_operation.exposure_time.rstrip("\n")
            obj_cam_operation.gain = text_gain.get(1.0, tk.END)
            obj_cam_operation.gain = obj_cam_operation.gain.rstrip("\n")
            obj_cam_operation.frame_rate = text_frame_rate.get(1.0, tk.END)
            obj_cam_operation.frame_rate = obj_cam_operation.frame_rate.rstrip("\n")
            obj_cam_operation.Set_parameter(obj_cam_operation.frame_rate, obj_cam_operation.exposure_time,
                                            obj_cam_operation.gain)


        xVariable = tkinter.StringVar()
        device_list = ttk.Combobox(frame2, textvariable=xVariable)
        device_list.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="we")
        # device_list.bind("<<ComboboxSelected>>", xFunc)
        devicestatuopen = tk.Label(frame2, text='设备处于打开状态,请直接点击开始抓取', bg='skyblue', width=30, height=1)
        devicestatuclose = tk.Label(frame2, text='设备处于关闭状态,请点击打开设备再点击开始抓取', bg='skyblue',
                                    width=40, height=1)
        devicestatucl = tk.Label(frame1, text='设备已关闭', bg='skyblue', width=10, height=1)
        devicestatuop = tk.Label(frame1, text='设备已开启', bg='skyblue', width=10, height=1)


        # commonuser
        device_list1 = ttk.Combobox(frame1, textvariable=xVariable)
        device_list1.grid(column=0, row=0, columnspan=2, padx=10, pady=10, sticky="we")
        # device_list1.bind("<<ComboboxSelected>>", xFunc)

        label_exposure_time = tk.Label(frame2, text='曝光时间', width=15, height=1)
        label_exposure_time.grid(row=7, column=0, padx=10, pady=10, sticky="we")
        text_exposure_time = tk.Text(frame2, width=15, height=1)
        text_exposure_time.grid(row=7, column=1, padx=10, pady=10, sticky="we")

        label_gain = tk.Label(frame2, text='增益', width=15, height=1)
        label_gain.grid(row=8, column=0, padx=10, pady=10, sticky="we")
        text_gain = tk.Text(frame2, width=15, height=1)
        text_gain.grid(row=8, column=1, padx=10, pady=10, sticky="we")

        label_frame_rate = tk.Label(frame2, text='帧速率', width=15, height=1)
        label_frame_rate.grid(row=9, column=0, padx=10, pady=10, sticky="we")
        text_frame_rate = tk.Text(frame2, width=15, height=1)
        text_frame_rate.grid(row=9, column=1, padx=10, pady=10, sticky="we")

        btn_enum_devices = tk.Button(frame2, text='发现设备', width=35, height=1,
                                     command=enum_devices)  # , command=enum_devices
        btn_enum_devices.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="we")

        # commonuser
        btn_open_device = tk.Button(frame2, text='打开设备', width=15, height=1,
                                    command=open_device)  # , command=open_device
        btn_open_device.grid(row=2, column=0, padx=10, pady=10, sticky="we")

        btn_close_device = tk.Button(frame2, text='关闭设备', width=15, height=1,
                                     command=close_device)  # , command=close_device
        btn_close_device.grid(row=2, column=1, padx=10, pady=10, sticky="we")

        radio_continuous = tk.Radiobutton(frame2, text='持续性抓取', variable=model_val, value='continuous', width=15,
                                          height=1, command=set_triggermode)  # , command=set_triggermode
        radio_continuous.grid(row=3, column=0, padx=10, pady=10, sticky="we")

        radio_trigger = tk.Radiobutton(frame2, text='触发模式', variable=model_val, value='triggermode', width=15,
                                       height=1, command=set_triggermode)  # , command=set_triggermode
        radio_trigger.grid(row=3, column=1, padx=10, pady=10, sticky="we")
        model_val.set(1)

        btn_start_grabbing = tk.Button(frame2, text='开始抓取', width=15, height=1,
                                       command=start_grabbing)  # , command=start_grabbing
        btn_start_grabbing.grid(row=4, column=0, padx=10, pady=10, sticky="we")

        btn_stop_grabbing = tk.Button(frame2, text='停止抓取', width=15, height=1,
                                      command=stop_grabbing)  # , command=stop_grabbing
        btn_stop_grabbing.grid(row=4, column=1, padx=10, pady=10, sticky="we")

        checkbtn_trigger_software = tk.Checkbutton(frame2, text='Tigger by Software', variable=triggercheck_val,
                                                   onvalue=1, offvalue=0)
        checkbtn_trigger_software.grid(row=5, column=0, padx=10, pady=10, sticky="we")
        btn_trigger_once = tk.Button(frame2, text='触发一次', width=15, height=1,
                                     command=trigger_once)  # , command=trigger_once
        btn_trigger_once.grid(row=5, column=1, padx=10, pady=10, sticky="we")

        btn_save_bmp = tk.Button(frame2, text='Save as BMP', width=15, height=1, command=bmp_save)  # , command=bmp_save
        btn_save_bmp.grid(row=6, column=0, padx=10, pady=10, sticky="we")
        btn_save_jpg = tk.Button(frame2, text='Save as JPG', width=15, height=1, command=jpg_save)  # , command=jpg_save
        btn_save_jpg.grid(row=6, column=1, padx=10, pady=10, sticky="we")
        label_frame1_all = tk.Label(frame1, text='总数量：', bg='skyblue', width=8, height=1, anchor='e')
        label_frame1_ng = tk.Label(frame1, text='不良数量：', bg='skyblue', width=8, height=1, anchor='e')
        label_frame1_per = tk.Label(frame1, text='可靠率：', bg='skyblue', width=8, height=1, anchor='e')
        text_frame1_rate4 = tk.Label(frame1, text='', width=20, height=1, anchor='w')
        text_frame1_rate4.grid(row=13, column=1, padx=10, pady=10, sticky="w")
        text_frame1_rate5 = tk.Label(frame1, text='', width=16, height=1, anchor='w')
        text_frame1_rate6 = tk.Label(frame1, text='', width=8, height=1, anchor='w')
        label_frame1_all.grid(row=13, column=0, padx=10, pady=10, sticky="e")
        label_frame1_ng.grid(row=14, column=0, padx=10, pady=10, sticky="e")
        label_frame1_per.grid(row=15, column=0, padx=10, pady=10, sticky="e")
        text_frame1_rate5.grid(row=14, column=1, padx=10, pady=10, sticky="nsew")
        text_frame1_rate6.grid(row=15, column=1, padx=10, pady=10, sticky="nsew")

        opcuabutton_0 = tk.Button(frame1, text='opcua参数清0', bg='skyblue', width=15, height=1,
                                  command=send_order_to_zero)  # , command=comportfunction
        opcuabutton_0.grid(row=14, column=2, padx=10, pady=10, sticky="w")
        try:
            with open(picklename1, 'rb') as f:
                ok_count = pickle.load(f)
                ng_count = pickle.load(f)
                all_count = pickle.load(f)
                text_frame1_rate4.config(text=ok_count)
                text_frame1_rate4.grid(row=13, column=1, padx=10, pady=10, sticky="nsew")
                text_frame1_rate5.config(text=ng_count)
                text_frame1_rate5.grid(row=14, column=1, padx=10, pady=10, sticky="nsew")
                text_frame1_rate6.config(text=all_count)
                text_frame1_rate6.grid(row=15, column=1, padx=10, pady=10, sticky="nsew")
        except:
            result_list = ['0', '0', '0%']
            text_frame1_rate4.config(text=result_list[0])
            text_frame1_rate4.grid(row=13, column=1, padx=10, pady=10, sticky="nsew")
            text_frame1_rate5.config(text=result_list[1])
            text_frame1_rate5.grid(row=14, column=1, padx=10, pady=10, sticky="nsew")
            text_frame1_rate6.config(text=result_list[2])
            text_frame1_rate6.grid(row=15, column=1, padx=10, pady=10, sticky="nsew")

        label_frame_rate1 = tk.Label(frame1, text='上一个SN：', font=('黑体', 12, "bold"), bg='skyblue', height=1)
        label_frame_rate2 = tk.Label(frame1, text='  本次SN：', font=('黑体', 12, "bold"), bg='skyblue', height=1)
        label_frame_rate3 = tk.Label(frame1, text=' OCR结果：', font=('黑体', 12, "bold"), bg='skyblue', height=1)
        label_frame_rate4 = tk.Label(frame1, text='', font=('Arial', 12), width=18, height=1)
        label_frame_rate5 = tk.Label(frame1, text='', font=('Arial', 12), width=18, height=1)
        label_frame_rate6 = tk.Label(frame1, text='', font=('Arial', 12), width=18, height=1)
        # label_frame_rate4.config(text='A2001021448325486')
        # label_frame_rate4.grid(row=3, column=1, pady=10, sticky="nsew")
        label_frame_rate1.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        label_frame_rate2.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")
        label_frame_rate3.grid(row=5, column=0, padx=10, pady=10, sticky="nsew")
        label_frame_rate4.grid(row=3, column=1, padx=10, pady=10, sticky="w")
        label_frame_rate5.grid(row=4, column=1, padx=10, pady=10, sticky="w")
        label_frame_rate6.grid(row=5, column=1, padx=10, pady=10, sticky="w")
        text_frame1_tips = tk.Label(frame1,
                                    text='如果点击开始后扫码枪为一天内的第一次开机，请等待扫码枪开机声音结束后再次点击开始比对按钮',
                                    font=(12), width=90, height=1, anchor='w')
        text_frame1_tips.grid(row=13, column=2, columnspan=2, sticky="w", padx=10, pady=10)

        checkbutton = tk.Checkbutton(frame1, text="保存比对数据信息", variable=checked_val, state=DISABLED)
        checkbutton.grid(row=2, column=0, padx=10, pady=10, sticky="we")
        checkbutton = tk.Checkbutton(frame2, text="保存比对数据信息", variable=checked_val,
                                     command=on_checked)  # , command=on_checked
        checkbutton.grid(row=11, column=0, padx=10, pady=10, sticky="we")

        # leidiaobutton = tk.Checkbutton(frame1, text="镭雕机模式", state=DISABLED)
        # leidiaobutton.grid(row=2, column=1, padx=10, pady=10, sticky="we")
        #

        leidiaobutton = tk.Checkbutton(frame2, text="镭雕机模式")  # , command=on_checked
        leidiaobutton.grid(row=11, column=1, padx=10, pady=10, sticky="we")


        @logger.catch
        def getCOMS():
            all_comports = serial.tools.list_ports.comports()
            available_ports = []
            for comport in all_comports:
                available_ports.append(comport.device)
            return available_ports


        COMGUN = tk.Label(frame2, text='扫码枪端口', width=8, height=1)
        COMGUN.grid(row=12, column=0, padx=10, pady=10, sticky="we")
        xVariableCOM = tkinter.StringVar(value=COMGUNNUM)

        COMGUN_list = ttk.Combobox(frame2, textvariable=xVariableCOM, width=8)


        @logger.catch
        def changeCOMS(event):
            global COMGUNNUM
            global previous_COMGUNNUM
            previous_COMGUNNUM = COMGUNNUM
            COMGUNNUM = xVariableCOM.get()



        @logger.catch
        def on_combobox_selected(event):
            global matche_point
            matche_point = float(xVariableMATCH.get())

        COMLIST = getCOMS()
        COMGUN_list['value'] = COMLIST
        COMGUN_list.grid(row=12, column=1, padx=10, pady=10, sticky="we")
        COMGUN_list.bind("<<ComboboxSelected>>", changeCOMS)

        values = list(map(lambda x: f"{x:.2f}", [i * 0.05 for i in range(21)]))  # 将浮点数转换为字符串
        xVariableMATCH = tkinter.StringVar(value=matche_point)
        combobox = ttk.Combobox(frame2, textvariable=xVariableMATCH,width=8, state="readonly")
        combobox['value']=values
        combobox.grid(row=11, column=3, padx=10, pady=10, sticky="w")
        combobox.bind("<<ComboboxSelected>>", on_combobox_selected)  # 绑定选中事件


        def opcuaconnect():
            global opc_connect
            try:
                opcua_connect_thread_task()
                # print("开启心跳线程")
                heartbeat_thread_task()
                if opc_connect:
                    tkinter.messagebox.showinfo('show info', '连接成功！')
                    opcuabutton1.config(state="disabled")
                    opcuabutton.config(state="disabled")
                else:
                    tkinter.messagebox.showinfo('show info', '连接失败！')
                    opcuabutton1.config(state="normal")
                    opcuabutton.config(state="normal")
            except Exception as e:
                tkinter.messagebox.showerror('show error', f"连接失败！\n错误信息: {str(e)}")
                # 在这里添加适当的错误处理代码，如果需要的话

        @logger.catch
        def comportfunction():
            global COMGUNNUM,matche_point,ser1,opcua_address_NUM,client
            COMGUNNUM = xVariableCOM.get()
            matche_point = xVariableMATCH.get()
            if COMGUNNUM:  # and COMSIGNAL
                with open(compickle, 'wb') as f:
                    pickle.dump(COMGUNNUM, f)
                    pickle.dump(float(matche_point), f)
                    # pickle.dump(COMSIGNALNUM,f)
            else:
                tk.messagebox.showerror('show error', "请选择端口！")
            threshold_confirm()
            try:
                if ser1:
                    ser1.close()
                ser1 = serial.Serial(COMGUNNUM, 9600, timeout=0.5)
            except serial.SerialException as e:
                tkinter.messagebox.showinfo('show error', '串口打开失败，请选择端口后重试！')
            except Exception as e:
                pass


        combutton = tk.Button(frame2, text='提交', bg='skyblue', width=10, height=1,
                              command=comportfunction)  # , command=comportfunction
        combutton.grid(row=12, column=2, padx=10, pady=10, sticky="we")
        opcuabutton = tk.Button(frame2, text='opcua连接', bg='skyblue', width=10, height=1,
                              command=opcuaconnect)  # , command=comportfunction
        opcuabutton.grid(row=12, column=3, padx=10, pady=10, sticky="w")

        opcuabutton1 = tk.Button(frame1, text='opcua连接', bg='skyblue', width=10, height=1,
                                 command=opcuaconnect)  # , command=comportfunction
        opcuabutton1.grid(row=2, column=1, padx=10, pady=10, sticky="we")


        btn_start_jpg = tk.Button(frame1, text='开始比对', width=15, height=1,
                                  command=start_long_task)  # , command=start_long_task
        btn_start_jpg.grid(row=1, column=0, padx=10, pady=10, sticky="we")
        videostream = tk.Label(frame1, text='实时视频流', font=('黑体', 12, "bold"), width=20, height=1)
        videostream.grid(row=1, column=3, padx=10, pady=10)
        picturescreen = tk.Label(frame1, text='本次样本', font=('黑体', 12, "bold"), width=20, height=1)
        picturescreen.grid(row=1, column=2, padx=10, pady=10)
        btn_get_parameter = tk.Button(frame2, text='获取参数', width=15, height=1,
                                      command=get_parameter)  # , command=get_parameter
        btn_get_parameter.grid(row=10, column=0, padx=10, pady=10, sticky="we")
        btn_set_parameter = tk.Button(frame2, text='设置参数', width=15, height=1,
                                      command=set_parameter)  # , command=set_parameter
        btn_set_parameter.grid(row=10, column=1, padx=10, pady=10, sticky="we")


        @logger.catch
        def look_picture():
            img = cv2.imread(parentdir)
            plt.subplot(111), plt.imshow(img),
            plt.title('Detected Point'), plt.axis('off')
            plt.show()


        @logger.catch
        def add_cuts_picture():
            global process_threshold_NUM, process_kernel_x_threshold_NUM,process_kernel_y_threshold_NUM, process_area_low_threshold_NUM,process_area_threshold_high_NUM
            get_pardemo(parentdir, left_left_NUM, left_upper_NUM, right_left_NUM, right_lower_NUM, parentdirdemo)
            flag = process_image1(parentdirdemo, folder_path, process_threshold_NUM, process_kernel_x_threshold_NUM,
                                 process_kernel_y_threshold_NUM, process_area_low_threshold_NUM,
                                 process_area_threshold_high_NUM)
            # print(parentdirdemo, folder_path, process_threshold_NUM, process_kernel_x_threshold_NUM,
            #       process_kernel_y_threshold_NUM, process_area_low_threshold_NUM, process_area_threshold_high_NUM)
            read_all_img()

        # 需要解开
        enum_devices()
        time.sleep(1)
        open_device()
        start_grabbing1()

        @logger.catch
        def show_cut(path, left, upper, right, lower):
            """
                原图与所截区域相比较
            :param path: 图片路径
            :param left: 区块左上角位置的像素点离图片左边界的距离
            :param upper：区块左上角位置的像素点离图片上边界的距离
            :param right：区块右下角位置的像素点离图片左边界的距离
            :param lower：区块右下角位置的像素点离图片上边界的距离
             故需满足：lower > upper、right > left
            """

            img = cv2.imread(path)

            plt.figure("Image Contrast")
            plt.subplot(1, 2, 1)
            plt.title('origin')
            plt.imshow(img)  # 展示图片的颜色会改变
            plt.axis('off')

            cropped = img[upper:lower, left:right]

            plt.subplot(1, 2, 2)
            plt.title('roi')
            plt.imshow(cropped)
            plt.axis('off')
            plt.show()


        @logger.catch
        def get_pardemo(path, left, upper, right, lower, save_path):
            """
                所截区域图片保存
            :param path: 图片路径
            :param left: 区块左上角位置的像素点离图片左边界的距离
            :param upper：区块左上角位置的像素点离图片上边界的距离
            :param right：区块右下角位置的像素点离图片左边界的距离
            :param lower：区块右下角位置的像素点离图片上边界的距离
             故需满足：lower > upper、right > left
            :param save_path: 所截图片保存位置
            """
            # print(path, left, upper, right, lower, save_path)
            img = cv2.imread(path)  # 打开图像
            cropped = img[upper:lower, left:right]
            # 保存截取的图片
            # cv2.namedWindow("cropped", cv2.WINDOW_NORMAL)
            # cv2.imshow("cropped", cropped)
            # cv2.waitKey(0)
            flag = cv2.imwrite(save_path, cropped)
            return flag


        @logger.catch
        def image_cut_save(path, left, upper, right, lower, save_path):
            """
                所截区域图片保存
            :param path: 图片路径
            :param left: 区块左上角位置的像素点离图片左边界的距离
            :param upper：区块左上角位置的像素点离图片上边界的距离
            :param right：区块右下角位置的像素点离图片左边界的距离
            :param lower：区块右下角位置的像素点离图片上边界的距离
             故需满足：lower > upper、right > left
            :param save_path: 所截图片保存位置
            """
            img = cv2.imread(path)  # 打开图像
            cropped = img[upper:lower, left:right]
            # 保存截取的图片
            cv2.imwrite(save_path, cropped)


        @logger.catch
        def add_Template_picture():
            pic_save_dir_path = parentdirdemo
            left_left_NUM = int(left_left_text.get("1.0", "end-1c"))
            left_upper_NUM = int(left_upper_text.get("1.0", "end-1c"))
            right_left_NUM = int(right_left_text.get("1.0", "end-1c"))
            right_lower_NUM = int(right_lower_text.get("1.0", "end-1c"))
            if left_left_NUM == '' or left_upper_NUM == '' or right_left_NUM == '' or right_lower_NUM == '':
                messagebox.showinfo(title='提示', message='请输入模板图片位置')
            else:
                with open(comparea, 'wb') as f:
                    pickle.dump(left_left_NUM, f)
                    pickle.dump(left_upper_NUM, f)
                    pickle.dump(right_left_NUM, f)
                    pickle.dump(right_lower_NUM, f)
                show_cut(parentdir, left_left_NUM, left_upper_NUM, right_left_NUM, right_lower_NUM)
                image_cut_save(parentdir, left_left_NUM, left_upper_NUM, right_left_NUM, right_lower_NUM,
                               pic_save_dir_path)


        @logger.catch
        def diff_this_picture():
            img = cv2.imread(parentdirsign)
            plt.subplot(111), plt.imshow(img),
            plt.title('Detected Point'), plt.axis('off')
            plt.show()

        @logger.catch
        def look_this_picture():
            try:
                selected_item = listbox.get(listbox.curselection())
                if selected_item:
                    file_path = os.path.join(folder_path, selected_item)
                    img = cv2.imread(file_path)
                    image_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    plt.subplot(111), plt.imshow(image_rgb),
                    plt.title(selected_item), plt.axis('off')
                    plt.show()
            except:
                messagebox.showinfo(title='提示', message='请选择图片!')


        @logger.catch
        def delete_this_picture():
            try:
                selected_indices = listbox.curselection()
                if selected_indices:
                    selected_item = listbox.get(selected_indices[0])  # 获取第一个选定的项目
                    file_path = os.path.join(folder_path, selected_item)
                    try:
                        os.remove(file_path)
                        listbox.delete(selected_indices)  # 从列表框中删除选定的项目
                        messagebox.showinfo("删除成功", f"文件 {selected_item} 已删除")
                    except Exception as e:
                        messagebox.showerror("删除失败", f"无法删除文件 {selected_item}: {str(e)}")
            except:
                messagebox.showinfo(title='提示', message='请选择图片!')


        @logger.catch
        def refresh():
            listbox.delete(0, tk.END)
            image_files = [f for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            # 将图片文件名添加到列表框中
            for file in image_files:
                listbox.insert(tk.END, file)


        @logger.catch
        def on_mouse(event, x, y, flags, param, file_name):
            global screen_img, point1, point2, screenshotNum, left_left_NUM, left_upper_NUM, right_left_NUM, right_lower_NUM
            img2 = screen_img.copy()
            if event == cv2.EVENT_LBUTTONDOWN:
                point1 = (x, y)
                cv2.circle(img2, point1, 10, (0, 255, 0), 2)  # 点击左键，显示绿色圆圈
                cv2.imshow('image', img2)
            elif event == cv2.EVENT_MOUSEMOVE and (flags & cv2.EVENT_FLAG_LBUTTON):
                cv2.rectangle(img2, point1, (x, y), (255, 0, 0), 2)  # 移动点击下的左键，画出蓝色截图框
                cv2.imshow('image', img2)
            elif event == cv2.EVENT_LBUTTONUP:
                point2 = (x, y)
                cv2.rectangle(img2, point1, point2, (0, 0, 255), 2)  # 松开左键，显示最终的红色截图框
                cv2.imshow('image', img2)

                cut_Pos[0][0] = min(point1[0], point2[0])
                cut_Pos[0][1] = max(point1[0], point2[0])
                cut_Pos[1][0] = min(point1[1], point2[1])
                cut_Pos[1][1] = max(point1[1], point2[1])
                    # left_left_NUM = cut_Pos[0][0]
                    # left_upper_NUM = cut_Pos[1][0]
                    # right_left_NUM = cut_Pos[0][1]
                    # right_lower_NUM = cut_Pos[1][1]
                    # print(left_left_NUM, left_upper_NUM, right_left_NUM, right_lower_NUM)
                    # with open(comparea, 'wb') as f:
                    #     pickle.dump(left_left_NUM, f)
                    #     pickle.dump(left_upper_NUM, f)
                    #     pickle.dump(right_left_NUM, f)
                    #     pickle.dump(right_lower_NUM, f)
                cv2.namedWindow('image', cv2.WINDOW_NORMAL)
                cv2.imshow('image', screen_img[cut_Pos[1][0]:cut_Pos[1][1], cut_Pos[0][0]:cut_Pos[0][1]])
                folder_name = file_name + f"\\screen_img_{screenshotNum + 1}.jpg"
                screenshotNum += 1
                cv2.imwrite(folder_name, screen_img[cut_Pos[1][0]:cut_Pos[1][1], cut_Pos[0][0]:cut_Pos[0][1]])


        @logger.catch
        def on_mouse1(event, x, y, flags, param, file_name):
            global screen_img, point1, point2, screenshotNum, left_left_NUM, left_upper_NUM, right_left_NUM, right_lower_NUM
            img2 = screen_img.copy()
            if event == cv2.EVENT_LBUTTONDOWN:
                point1 = (x, y)
                cv2.circle(img2, point1, 10, (0, 255, 0), 2)  # 点击左键，显示绿色圆圈
                cv2.imshow('image', img2)
            elif event == cv2.EVENT_MOUSEMOVE and (flags & cv2.EVENT_FLAG_LBUTTON):
                cv2.rectangle(img2, point1, (x, y), (255, 0, 0), 2)  # 移动点击下的左键，画出蓝色截图框
                cv2.imshow('image', img2)
            elif event == cv2.EVENT_LBUTTONUP:
                point2 = (x, y)
                cv2.rectangle(img2, point1, point2, (0, 0, 255), 2)  # 松开左键，显示最终的红色截图框
                cv2.imshow('image', img2)

                cut_Pos[0][0] = min(point1[0], point2[0])
                cut_Pos[0][1] = max(point1[0], point2[0])
                cut_Pos[1][0] = min(point1[1], point2[1])
                cut_Pos[1][1] = max(point1[1], point2[1])
                left_left_NUM = cut_Pos[0][0]
                left_upper_NUM = cut_Pos[1][0]
                right_left_NUM = cut_Pos[0][1]
                right_lower_NUM = cut_Pos[1][1]
                # print(left_left_NUM, left_upper_NUM, right_left_NUM, right_lower_NUM)
                with open(comparea, 'wb') as f:
                    pickle.dump(left_left_NUM, f)
                    pickle.dump(left_upper_NUM, f)
                    pickle.dump(right_left_NUM, f)
                    pickle.dump(right_lower_NUM, f)
                cv2.namedWindow('image', cv2.WINDOW_NORMAL)
                cv2.imshow('image', screen_img[cut_Pos[1][0]:cut_Pos[1][1], cut_Pos[0][0]:cut_Pos[0][1]])

                cv2.imwrite(parentdirdemo, screen_img[cut_Pos[1][0]:cut_Pos[1][1], cut_Pos[0][0]:cut_Pos[0][1]])
        @logger.catch
        def screen_shot(file):
            global screenshotNum
            global screen_img
            screen_img = cv2.imread(parentdir)
            cv2.namedWindow('image', cv2.WINDOW_NORMAL)
            on_mouse_callback = partial(on_mouse, file_name=file)
            cv2.setMouseCallback('image', on_mouse_callback)
            cv2.imshow('image', screen_img)
            cv2.waitKey(0)


        @logger.catch
        def screen_shot1(file):
            global screenshotNum
            global screen_img
            screen_img = cv2.imread(parentdir)
            cv2.namedWindow('image', cv2.WINDOW_NORMAL)
            on_mouse_callback = partial(on_mouse1, file_name=file)
            cv2.setMouseCallback('image', on_mouse_callback)
            cv2.imshow('image', screen_img)
            cv2.waitKey(0)


        @logger.catch
        def threshold_confirm():
            global process_threshold_NUM, compare_threshold_NUM, process_kernel_x_threshold_NUM,\
                process_kernel_y_threshold_NUM, process_area_low_threshold_NUM, process_area_threshold_high_NUM,\
                weight_threshold_NUM,pattern_compare_threshold_NUM, image_threading_NUM,opcua_address_NUM,subscribe_node_NUM,takephoto_NUM,xintiao_NUM,finalresult_NUM,client

            param1 = process_binary_threshold_text.get(1.0, tk.END)
            param2 = compare_binary_threshold_text.get(1.0, tk.END)
            param3 = process_kernel_x_threshold_text.get(1.0, tk.END)
            param4 = process_kernel_y_threshold_text.get(1.0, tk.END)
            param5 = process_area_low_threshold_text.get(1.0, tk.END)
            param6 = process_area_threshold_high_text.get(1.0, tk.END)
            param7 = weight_threshold_text.get(1.0, tk.END)
            param8 = pattern_compar_threshold_text.get(1.0, tk.END)
            param9 = image_threading_text.get(1.0, tk.END)
            param10 = opcua_address_text.get(1.0, tk.END)
            param11 = subscribe_node_text.get(1.0, tk.END)
            param12 = takephoto_text.get(1.0, tk.END)
            param13 = xintiao_text.get(1.0, tk.END)
            param14 = finalresult_text.get(1.0, tk.END)
            # param10 = different_threshold_text.get(1.0, tk.END)
            params = (param1, param2, param3, param4, param5, param6, param7,param8,param9,param10,param11,param12,param13,param14)  # 将三个参数打包成元组
            if params:
                with open(thresholdpickle, "wb") as f:
                    pickle.dump(params, f)
                process_threshold_NUM = int(param1)
                compare_threshold_NUM = int(param2)
                process_kernel_x_threshold_NUM = int(param3)
                process_kernel_y_threshold_NUM = int(param4)
                process_area_low_threshold_NUM = int(param5)
                process_area_threshold_high_NUM = int(param6)
                weight_threshold_NUM = int(param7)
                pattern_compare_threshold_NUM = int(param8)
                image_threading_NUM = int(param9)
                opcua_address_NUM = str(param10).strip()
                subscribe_node_NUM = str(param11).strip()
                takephoto_NUM = str(param12).strip()
                xintiao_NUM = str(param13).strip()
                finalresult_NUM = str(param14).strip()
                # different_threshold_NUM = int(param10)
                tkinter.messagebox.showinfo('show info', '提交成功！')
            else:
                tk.messagebox.showerror('show error', "填写数据！")


        btn_look_picture = tk.Button(frame2, text='查看目标图片', width=10, height=1, command=look_picture)  #
        btn_look_picture.grid(row=2, column=4, padx=10, pady=10, sticky="w")
        btn_add_picture = tk.Button(frame2, text='生成比对模板', width=12, height=1, command=add_cuts_picture)  #
        btn_add_picture.grid(row=2, column=5, padx=10, pady=10, sticky="w")
        btn_add_template = tk.Button(frame2, text='添加模板图片', width=12, height=1, command=add_Template_picture)  #
        btn_add_template.grid(row=6, column=2, padx=10, pady=10, sticky="wens")
        btn_screenshot = tk.Button(frame2, text='目标位置截图', width=12, height=1,
                                   command=lambda: screen_shot(folder_path))  #
        btn_screenshot.grid(row=6, column=3, padx=10, pady=10, sticky="wens")
        btn_refresh = tk.Button(frame2, text='刷新', width=12, height=1, command=refresh)  #
        btn_refresh.grid(row=6, column=4, padx=10, pady=10, sticky="wens")
        # 图片截取功能
        left_left = tk.Label(frame2, text='左上距左', width=8, height=1)
        left_left.grid(row=2, column=2, padx=10, pady=10, sticky="e")
        left_left_text = tk.Text(frame2, width=10, height=1)
        left_left_text.grid(row=2, column=3, padx=10, pady=10, sticky="w")
        # 图片截取功能
        left_upper = tk.Label(frame2, text='左上距上', width=8, height=1)
        left_upper.grid(row=3, column=2, padx=10, pady=10, sticky="e")
        left_upper_text = tk.Text(frame2, width=10, height=1)
        left_upper_text.grid(row=3, column=3, padx=10, pady=10, sticky="w")

        # 图片截取功能
        right_left = tk.Label(frame2, text='右下距左', width=8, height=1)
        right_left.grid(row=4, column=2, padx=10, pady=10, sticky="e")
        right_left_text = tk.Text(frame2, width=10, height=1)
        right_left_text.grid(row=4, column=3, padx=10, pady=10, sticky="w")

        # 图片截取功能
        right_lower = tk.Label(frame2, text='右下距上', width=8, height=1)
        right_lower.grid(row=5, column=2, padx=10, pady=10, sticky="e")
        right_lower_text = tk.Text(frame2, width=10, height=1)
        right_lower_text.grid(row=5, column=3, padx=10, pady=10, sticky="w")

        # 阈值
        process_binary_threshold = tk.Label(frame2, text='图片二值化阈值', width=10, height=1)
        process_binary_threshold.grid(row=8, column=2, padx=10, pady=10, sticky="we")
        process_binary_threshold_text = tk.Text(frame2, width=10, height=1)
        process_binary_threshold_text.grid(row=8, column=3, padx=10, pady=10, sticky="w")

        process_kernel_x_threshold = tk.Label(frame2, text='图片处理卷积核横向', width=15, height=1)
        process_kernel_x_threshold.grid(row=9, column=2, padx=10, pady=10, sticky="we")
        process_kernel_x_threshold_text = tk.Text(frame2, width=10, height=1)
        process_kernel_x_threshold_text.grid(row=9, column=3, padx=10, pady=10, sticky="w")

        process_kernel_y_threshold = tk.Label(frame2, text='图片处理卷积核纵向', width=15, height=1)
        process_kernel_y_threshold.grid(row=10, column=2, padx=10, pady=10, sticky="we")
        process_kernel_y_threshold_text = tk.Text(frame2, width=10, height=1)
        process_kernel_y_threshold_text.grid(row=10, column=3, padx=10, pady=10, sticky="w")

        pattern_compar_threshold = tk.Label(frame2, text='最小缺漏像素数量', width=10, height=1)
        pattern_compar_threshold.grid(row=7, column=4, padx=10, pady=10, sticky="we")
        pattern_compar_threshold_text = tk.Text(frame2, width=10, height=1)
        pattern_compar_threshold_text.grid(row=7, column=5, padx=10, pady=10, sticky="w")

        process_area_low_threshold = tk.Label(frame2, text='图片最小保留面积', width=10, height=1)
        process_area_low_threshold.grid(row=8, column=4, padx=10, pady=10, sticky="we")
        process_area_low_threshold_text = tk.Text(frame2, width=10, height=1)
        process_area_low_threshold_text.grid(row=8, column=5, padx=10, pady=10, sticky="w")

        process_area_threshold_high = tk.Label(frame2, text='图片最大保留面积', width=10, height=1)
        process_area_threshold_high.grid(row=9, column=4, padx=10, pady=10, sticky="we")
        process_area_threshold_high_text = tk.Text(frame2, width=10, height=1)
        process_area_threshold_high_text.grid(row=9, column=5, padx=10, pady=10, sticky="w")

        compare_binary_threshold = tk.Label(frame2, text='不同像素二值化阈值', width=10, height=1)
        compare_binary_threshold.grid(row=10, column=4, padx=10, pady=10, sticky="we")
        compare_binary_threshold_text = tk.Text(frame2, width=10, height=1)
        compare_binary_threshold_text.grid(row=10, column=5, padx=10, pady=10, sticky="w")

        weight_threshold = tk.Label(frame2, text='白色像素权值', width=10, height=1)
        weight_threshold.grid(row=11, column=4, padx=10, pady=10, sticky="we")
        weight_threshold_text = tk.Text(frame2, width=10, height=1)
        weight_threshold_text.grid(row=11, column=5, padx=10, pady=10, sticky="w")

        image_threading = tk.Label(frame2, text='线程数', width=10, height=1)
        image_threading.grid(row=12, column=4, padx=10, pady=10, sticky="we")
        image_threading_text = tk.Text(frame2, width=10, height=1)
        image_threading_text.grid(row=12, column=5, padx=10, pady=10, sticky="w")



        opcua_address = tk.Label(frame2, text='OPCUA地址', width=20, height=1)
        opcua_address.grid(row=10, column=6, padx=10,columnspan=2, pady=10, sticky="e")
        opcua_address_text = tk.Text(frame2, width=30, height=1)
        opcua_address_text.grid(row=10, column=8, padx=10,columnspan=2, pady=10, sticky="w")

        subscribe_node = tk.Label(frame2, text='订阅节点', width=10, height=1)
        subscribe_node.grid(row=11, column=6, padx=10, pady=10, sticky="we")
        subscribe_node_text = tk.Text(frame2, width=25, height=1)
        subscribe_node_text.grid(row=11, column=7, padx=10, pady=10, sticky="w")

        xintiao = tk.Label(frame2, text='心跳节点', width=10, height=1)
        xintiao.grid(row=11, column=8, padx=10, pady=10, sticky="we")
        xintiao_text = tk.Text(frame2, width=25, height=1)
        xintiao_text.grid(row=11, column=9, padx=10, pady=10, sticky="w")

        takephoto = tk.Label(frame2, text='拍照节点', width=10, height=1)
        takephoto.grid(row=12, column=6, padx=10, pady=10, sticky="we")
        takephoto_text = tk.Text(frame2, width=25, height=1)
        takephoto_text.grid(row=12, column=7, padx=10, pady=10, sticky="w")

        finalresult = tk.Label(frame2, text='结果节点', width=10, height=1)
        finalresult.grid(row=12, column=8, padx=10, pady=10, sticky="we")
        finalresult_text = tk.Text(frame2, width=25, height=1)
        finalresult_text.grid(row=12, column=9, padx=10, pady=10, sticky="w")

        # different_threshold = tk.Label(frame2, text='最小缺漏像素数量', width=10, height=1)
        # different_threshold.grid(row=13, column=4, padx=10, pady=10, sticky="we")
        # different_threshold_text = tk.Text(frame2, width=10, height=1)
        # different_threshold_text.grid(row=13, column=5, padx=10, pady=10, sticky="w")
        # thresholdbutton = tk.Button(frame2, text='提交', bg='skyblue', width=10, height=1,
        #                             command=threshold_confirm)  #
        # thresholdbutton.grid(row=8, column=4, padx=10, pady=10, sticky="w")
        get_cut_params()
        try:
            read_all_img()
        except:
            pass

        try:
            with open(thresholdpickle, "rb") as f:
                loaded_params = pickle.load(f)
                param1_loaded, param2_loaded, param3_loaded, param4_loaded, param5_loaded, param6_loaded, param7_loaded,param8_loaded,param9_loaded,param10_loaded,param11_loaded ,param12_loaded,param13_loaded,param14_loaded = loaded_params
                process_binary_threshold_text.delete("1.0", "end")  # 清空Text组件
                process_binary_threshold_text.insert("1.0", param1_loaded)
                process_kernel_x_threshold_text.delete("1.0", "end")
                process_kernel_x_threshold_text.insert("1.0", param3_loaded)
                process_kernel_y_threshold_text.delete("1.0", "end")
                process_kernel_y_threshold_text.insert("1.0", param4_loaded)
                process_area_low_threshold_text.delete("1.0", "end")  # 清空Text组件
                process_area_low_threshold_text.insert("1.0", param5_loaded)
                process_area_threshold_high_text.delete("1.0", "end")
                process_area_threshold_high_text.insert("1.0", param6_loaded)
                compare_binary_threshold_text.delete("1.0", "end")
                compare_binary_threshold_text.insert("1.0", param2_loaded)
                weight_threshold_text.delete("1.0", "end")
                weight_threshold_text.insert("1.0", param7_loaded)
                pattern_compar_threshold_text.delete("1.0", "end")
                pattern_compar_threshold_text.insert("1.0", param8_loaded)
                image_threading_text.delete("1.0", "end")
                image_threading_text.insert("1.0", param9_loaded)
                opcua_address_text.delete("1.0", "end")
                opcua_address_text.insert("1.0", param10_loaded)
                subscribe_node_text.delete("1.0", "end")
                subscribe_node_text.insert("1.0", param11_loaded)
                takephoto_text.delete("1.0", "end")
                takephoto_text.insert("1.0", param12_loaded)
                xintiao_text.delete("1.0", "end")
                xintiao_text.insert("1.0", param13_loaded)
                finalresult_text.delete("1.0", "end")
                finalresult_text.insert("1.0", param14_loaded)
                # different_threshold_text.delete("1.0", "end")
                # different_threshold_text.insert("1.0", param10_loaded)
        except FileNotFoundError:
            process_threshold_NUM = 200
            compare_threshold_NUM = 100
            process_kernel_x_threshold_NUM = 75
            process_kernel_y_threshold_NUM = 1
            process_area_low_threshold_NUM = 4000
            process_area_threshold_high_NUM = 250000
            weight_threshold_NUM = 5
            pattern_compare_threshold_NUM=20
            image_threading_NUM = 8
            opcua_address_NUM = ''
            subscribe_node_NUM = ''
            takephoto_NUM = ''
            xintiao_NUM = ''
            finalresult_NUM = ''
            # different_threshold_NUM = 200
            process_binary_threshold_text.delete("1.0", "end")  # 清空Text组件
            process_binary_threshold_text.insert("1.0", process_threshold_NUM)
            process_kernel_x_threshold_text.delete("1.0", "end")
            process_kernel_x_threshold_text.insert("1.0", process_kernel_x_threshold_NUM)
            process_kernel_y_threshold_text.delete("1.0", "end")
            process_kernel_y_threshold_text.insert("1.0", process_kernel_y_threshold_NUM)
            process_area_low_threshold_text.delete("1.0", "end")  # 清空Text组件
            process_area_low_threshold_text.insert("1.0", process_area_low_threshold_NUM)
            process_area_threshold_high_text.delete("1.0", "end")
            process_area_threshold_high_text.insert("1.0", process_area_threshold_high_NUM)
            compare_binary_threshold_text.delete("1.0", "end")
            compare_binary_threshold_text.insert("1.0", compare_threshold_NUM)
            weight_threshold_text.delete("1.0", "end")
            weight_threshold_text.insert("1.0", weight_threshold_NUM)
            pattern_compar_threshold_text.delete("1.0", "end")
            pattern_compar_threshold_text.insert("1.0", pattern_compare_threshold_NUM)
            image_threading_text.delete("1.0", "end")
            image_threading_text.insert("1.0", image_threading_NUM)
            opcua_address_text.delete("1.0", "end")
            opcua_address_text.insert("1.0", opcua_address_NUM)
            subscribe_node_text.delete("1.0", "end")
            subscribe_node_text.insert("1.0", subscribe_node_NUM)
            takephoto_text.delete("1.0", "end")
            takephoto_text.insert("1.0", takephoto_NUM)
            xintiao_text.delete("1.0", "end")
            xintiao_text.insert("1.0", xintiao_NUM)
            finalresult_text.delete("1.0", "end")
            finalresult_text.insert("1.0", finalresult_NUM)
            # different_threshold_text.delete("1.0", "end")
            # different_threshold_text.insert("1.0", different_threshold_NUM)

        img_save_button = tk.Checkbutton(frame2, text="保存比对图片", variable=on_save_img_val,
                                         command=on_save_img)  # , command=on_save_img
        img_save_button.grid(row=11, column=2, padx=10, pady=10, sticky="we")

        listbox = Listbox(frame2, width=20, height=10)
        listbox.grid(row=3, rowspan=3, column=4, padx=10, pady=10, sticky="e")
        scrollbar = Scrollbar(frame2, command=listbox.yview)
        scrollbar.grid(row=4, column=5, sticky="w", padx=10, pady=20)
        listbox.config(yscrollcommand=scrollbar.set)
        image_files = [f for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
        # 将图片文件名添加到列表框中
        for file in image_files:
            listbox.insert(tk.END, file)
        btn_look_this = tk.Button(frame2, text='查看选中图片', width=12, height=1, command=look_this_picture)  #
        btn_look_this.grid(row=3, column=5, padx=10, pady=10, sticky="w")
        btn_delete_this = tk.Button(frame2, text='删除选中图片', width=12, height=1, command=delete_this_picture)  #
        btn_delete_this.grid(row=5, column=5, padx=10, pady=10, sticky="w")
        btn_diff_this = tk.Button(frame2, text='查看不同图片', width=12, height=1, command=diff_this_picture)  #
        btn_diff_this.grid(row=6, column=5, padx=10, pady=10, sticky="w")

        @logger.catch()
        def on_closing():
            if messagebox.askokcancel("关闭窗口", "你确定要关闭窗口吗？"):
                # 执行其他关闭窗口前需要进行的操作
                with open(screenshot, 'wb') as f:
                    pickle.dump(screenshotNum, f)
                window.destroy()



        IMAGEMatch = tk.Button(frame2, text='刷新截图参数', width=12, height=1, command=get_cut_params)
        IMAGEMatch.grid(row=7, column=2, padx=10, pady=10, sticky="wens")
        btn_cut_area = tk.Button(frame2, text='选择比对区域', width=12, height=1,
                                 command=lambda: screen_shot1(imagepath))  #
        btn_cut_area.grid(row=7, column=3, padx=10, pady=10, sticky="wens")


        window.bind("<space>", handle_space)
        window.protocol("WM_DELETE_WINDOW", on_closing)
        window.mainloop()
        try:
            win32event.ReleaseMutex(mutex)
            win32api.CloseHandle(mutex)
        except:
            pass