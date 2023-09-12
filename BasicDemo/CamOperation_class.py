# -- coding: utf-8 --
import datetime
import string
import sys
import threading
import msvcrt
import _tkinter
import tkinter.messagebox
from tkinter import *
from tkinter.messagebox import *
import tkinter as tk
import numpy as np
import cv2
import time
import sys, os
import inspect
import ctypes
import random
from PIL import Image, ImageTk
from ctypes import *
from tkinter import ttk
import cv2
from MvImport.MvCameraControl_class import *
from cnocr import CnOcr
import concurrent.futures

i = 0
k = 0
now = datetime.datetime.now()
year = now.year
month = now.month
day = now.day

randomfilename = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
ymdname = str(year) + '.' + str(month) + '.' + str(day)


def Async_raise(tid, exctype):
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def Stop_thread(thread):
    Async_raise(thread.ident, SystemExit)


def count_photos(folder_path):
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)
    extensions = ['jpg', 'png', 'jpeg', 'gif']
    photos = [file for file in os.listdir(folder_path) if file.lower().endswith(tuple(extensions))]
    return len(photos)


def mythread(test_path):
    file_test = open(str(test_path).encode('ascii'), 'ab+')
    return file_test


class CameraOperation():

    def __init__(self, obj_cam, st_device_list, n_connect_num=0, b_open_device=False, b_start_grabbing=False,
                 b_start_grabbing1=False, h_thread_handle=None, \
                 b_thread_closed=False, st_frame_info=None, b_exit=False, b_save_bmp=False, b_save_jpg=False,
                 b_save_jpg1=False, buf_save_image=None, \
                 n_save_image_size=0, n_win_gui_id=0, frame_rate=0, exposure_time=0, gain=0, comflag=False):

        self.obj_cam = obj_cam
        self.st_device_list = st_device_list
        self.n_connect_num = n_connect_num
        self.b_open_device = b_open_device
        self.b_start_grabbing = b_start_grabbing
        self.b_start_grabbing1 = b_start_grabbing1
        self.b_thread_closed = b_thread_closed
        self.st_frame_info = st_frame_info
        self.b_exit = b_exit
        self.b_save_bmp = b_save_bmp
        self.b_save_jpg = b_save_jpg
        self.b_save_jpg1 = b_save_jpg1  # Լ
        self.buf_save_image = buf_save_image
        self.h_thread_handle = h_thread_handle
        self.n_win_gui_id = n_win_gui_id
        self.n_save_image_size = n_save_image_size
        self.b_thread_closed
        self.frame_rate = frame_rate
        self.exposure_time = exposure_time
        self.gain = gain
        self.comflag = comflag

    def To_hex_str(self, num):
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

    def Open_device(self):
        if False == self.b_open_device:
            # ch:ѡ   豸          | en:Select device and create handle
            nConnectionNum = int(self.n_connect_num)
            stDeviceList = cast(self.st_device_list.pDeviceInfo[int(nConnectionNum)],
                                POINTER(MV_CC_DEVICE_INFO)).contents
            self.obj_cam = MvCamera()
            ret = self.obj_cam.MV_CC_CreateHandle(stDeviceList)
            if ret != 0:
                self.obj_cam.MV_CC_DestroyHandle()
                tkinter.messagebox.showerror('show error', 'create handle fail! ret = ' + self.To_hex_str(ret))
                return ret

            ret = self.obj_cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
            if ret != 0:
                tkinter.messagebox.showerror('show error', '   豸ʧ ܣ            ϵ    Ա ret = ' + self.To_hex_str(ret))
                return ret
            # print ("open device successfully!")
            self.b_open_device = True
            self.b_thread_closed = False

            # ch:̽        Ѱ   С(ֻ  GigE     Ч) | en:Detection network optimal package size(It only works for the GigE camera)
            if stDeviceList.nTLayerType == MV_GIGE_DEVICE:
                nPacketSize = self.obj_cam.MV_CC_GetOptimalPacketSize()
                if int(nPacketSize) > 0:
                    ret = self.obj_cam.MV_CC_SetIntValue("GevSCPSPacketSize", nPacketSize)
                #     if ret != 0:
                #         print ("warning: set packet size fail! ret[0x%x]" % ret)
                # else:
                #     print ("warning: set packet size fail! ret[0x%x]" % nPacketSize)

            stBool = c_bool(False)
            ret = self.obj_cam.MV_CC_GetBoolValue("AcquisitionFrameRateEnable", stBool)
            # if ret != 0:
            # print ("get acquisition frame rate enable fail! ret[0x%x]" % ret)

            # ch:   ô   ģʽΪoff | en:Set trigger mode as off
            ret = self.obj_cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
            # if ret != 0:
            #     print ("set trigger mode fail! ret[0x%x]" % ret)
            # return 0

    def Start_grabbing(self, root, panel):
        if False == self.b_start_grabbing and True == self.b_open_device:
            self.b_exit = False
            ret = self.obj_cam.MV_CC_StartGrabbing()
            if ret != 0:
                tkinter.messagebox.showerror('show error', 'start grabbing fail! ret = ' + self.To_hex_str(ret))
                return
            self.b_start_grabbing = True
            # print ("start grabbing successfully!")
            try:
                self.n_win_gui_id = random.randint(1, 10000)
                self.h_thread_handle = threading.Thread(target=CameraOperation.Work_thread, args=(self, root, panel))
                self.h_thread_handle.daemon = True
                self.h_thread_handle.start()
                self.b_thread_closed = True
            except:
                tkinter.messagebox.showerror('show error', 'error: unable to start thread')
                False == self.b_start_grabbing

    def Stop_grabbing(self):
        if True == self.b_start_grabbing and self.b_open_device == True:
            # ˳  ߳
            if True == self.b_thread_closed:
                Stop_thread(self.h_thread_handle)
                self.b_thread_closed = False
            ret = self.obj_cam.MV_CC_StopGrabbing()
            if ret != 0:
                tkinter.messagebox.showerror('show error', 'stop grabbing fail! ret = ' + self.To_hex_str(ret))
                return
            # print ("stop grabbing successfully!")
            self.b_start_grabbing = False
            self.b_exit = True

    def Close_device(self):
        if True == self.b_open_device:
            # ˳  ߳
            if True == self.b_thread_closed:
                Stop_thread(self.h_thread_handle)
                self.b_thread_closed = False
            ret = self.obj_cam.MV_CC_CloseDevice()
            if ret != 0:
                tkinter.messagebox.showerror('show error', 'close deivce fail! ret = ' + self.To_hex_str(ret))
                return

        # ch:   پ   | Destroy handle
        self.obj_cam.MV_CC_DestroyHandle()
        self.b_open_device = False
        self.b_start_grabbing = False
        self.b_exit = True
        # print ("close device successfully!")

    def Set_trigger_mode(self, strMode):
        if True == self.b_open_device:
            if "continuous" == strMode:
                ret = self.obj_cam.MV_CC_SetEnumValue("TriggerMode", 0)
                if ret != 0:
                    tkinter.messagebox.showerror('show error', 'set triggermode fail! ret = ' + self.To_hex_str(ret))
            if "triggermode" == strMode:
                ret = self.obj_cam.MV_CC_SetEnumValue("TriggerMode", 1)
                if ret != 0:
                    tkinter.messagebox.showerror('show error', 'set triggermode fail! ret = ' + self.To_hex_str(ret))
                ret = self.obj_cam.MV_CC_SetEnumValue("TriggerSource", 7)
                if ret != 0:
                    tkinter.messagebox.showerror('show error', 'set triggersource fail! ret = ' + self.To_hex_str(ret))

    def Trigger_once(self, nCommand):
        if True == self.b_open_device:
            if 1 == nCommand:
                ret = self.obj_cam.MV_CC_SetCommandValue("TriggerSoftware")
                if ret != 0:
                    tkinter.messagebox.showerror('show error',
                                                 'set triggersoftware fail! ret = ' + self.To_hex_str(ret))

    def Get_parameter(self):
        if True == self.b_open_device:
            stFloatParam_FrameRate = MVCC_FLOATVALUE()
            memset(byref(stFloatParam_FrameRate), 0, sizeof(MVCC_FLOATVALUE))
            stFloatParam_exposureTime = MVCC_FLOATVALUE()
            memset(byref(stFloatParam_exposureTime), 0, sizeof(MVCC_FLOATVALUE))
            stFloatParam_gain = MVCC_FLOATVALUE()
            memset(byref(stFloatParam_gain), 0, sizeof(MVCC_FLOATVALUE))
            ret = self.obj_cam.MV_CC_GetFloatValue("AcquisitionFrameRate", stFloatParam_FrameRate)
            if ret != 0:
                tkinter.messagebox.showerror('show error',
                                             'get acquistion frame rate fail! ret = ' + self.To_hex_str(ret))
            self.frame_rate = stFloatParam_FrameRate.fCurValue
            ret = self.obj_cam.MV_CC_GetFloatValue("ExposureTime", stFloatParam_exposureTime)
            if ret != 0:
                tkinter.messagebox.showerror('show error', 'get exposure time fail! ret = ' + self.To_hex_str(ret))
            self.exposure_time = stFloatParam_exposureTime.fCurValue
            ret = self.obj_cam.MV_CC_GetFloatValue("Gain", stFloatParam_gain)
            if ret != 0:
                tkinter.messagebox.showerror('show error', 'get gain fail! ret = ' + self.To_hex_str(ret))
            self.gain = stFloatParam_gain.fCurValue
            tkinter.messagebox.showinfo('show info', 'get parameter success!')

    def Set_parameter(self, frameRate, exposureTime, gain):
        if '' == frameRate or '' == exposureTime or '' == gain:
            tkinter.messagebox.showinfo('show info', 'please type in the text box !')
            return
        if True == self.b_open_device:
            ret = self.obj_cam.MV_CC_SetFloatValue("ExposureTime", float(exposureTime))
            if ret != 0:
                tkinter.messagebox.showerror('show error', 'set exposure time fail! ret = ' + self.To_hex_str(ret))

            ret = self.obj_cam.MV_CC_SetFloatValue("Gain", float(gain))
            if ret != 0:
                tkinter.messagebox.showerror('show error', 'set gain fail! ret = ' + self.To_hex_str(ret))

            ret = self.obj_cam.MV_CC_SetFloatValue("AcquisitionFrameRate", float(frameRate))
            if ret != 0:
                tkinter.messagebox.showerror('show error',
                                             'set acquistion frame rate fail! ret = ' + self.To_hex_str(ret))

            tkinter.messagebox.showinfo('show info', 'set parameter success!')

    def Work_thread(self, root, panel):
        stOutFrame = MV_FRAME_OUT()
        img_buff = None
        buf_cache = None
        numArray = None
        temp = ''
        while True:
            ret = self.obj_cam.MV_CC_GetImageBuffer(stOutFrame, 1000)
            if 0 == ret:
                if None == buf_cache:
                    buf_cache = (c_ubyte * stOutFrame.stFrameInfo.nFrameLen)()
                #  ȡ  ͼ   ʱ 俪ʼ ڵ  ȡ  ͼ   ʱ 俪ʼ ڵ
                self.st_frame_info = stOutFrame.stFrameInfo
                cdll.msvcrt.memcpy(byref(buf_cache), stOutFrame.pBufAddr, self.st_frame_info.nFrameLen)
                # print ("get one frame: Width[%d], Height[%d], nFrameNum[%d]"  % (self.st_frame_info.nWidth, self.st_frame_info.nHeight, self.st_frame_info.nFrameNum))
                self.n_save_image_size = self.st_frame_info.nWidth * self.st_frame_info.nHeight * 3 + 2048
                if img_buff is None:
                    img_buff = (c_ubyte * self.n_save_image_size)()

                if True == self.b_save_jpg:
                    self.Save_jpg(buf_cache)  # ch:    JpgͼƬ | en:Save Jpg
                if True == self.b_save_jpg1:
                    # self.comflag=self.Save_jpg1(buf_cache) #ch:    JpgͼƬ | en:Save Jpg
                    self.Save_jpg1(buf_cache)
                if True == self.b_save_bmp:
                    self.Save_Bmp(buf_cache)  # ch:    BmpͼƬ | en:Save Bmp
            else:
                # print("no data, nret = "+self.To_hex_str(ret))
                continue

            # ת     ؽṹ 帳ֵ
            stConvertParam = MV_CC_PIXEL_CONVERT_PARAM()
            memset(byref(stConvertParam), 0, sizeof(stConvertParam))
            stConvertParam.nWidth = self.st_frame_info.nWidth
            stConvertParam.nHeight = self.st_frame_info.nHeight
            stConvertParam.pSrcData = cast(buf_cache, POINTER(c_ubyte))
            stConvertParam.nSrcDataLen = self.st_frame_info.nFrameLen
            stConvertParam.enSrcPixelType = self.st_frame_info.enPixelType

            mode = None  # arrayתΪImageͼ   ת  ģʽ
            # RGB8ֱ    ʾ
            if PixelType_Gvsp_RGB8_Packed == self.st_frame_info.enPixelType:
                numArray = CameraOperation.Color_numpy(self, buf_cache, self.st_frame_info.nWidth,
                                                       self.st_frame_info.nHeight)
                mode = "RGB"

            # Mono8ֱ    ʾ
            elif PixelType_Gvsp_Mono8 == self.st_frame_info.enPixelType:
                numArray = CameraOperation.Mono_numpy(self, buf_cache, self.st_frame_info.nWidth,
                                                      self.st_frame_info.nHeight)
                mode = "L"

            #     ǲ ɫ ҷ RGB  תΪRGB    ʾ
            elif self.Is_color_data(self.st_frame_info.enPixelType):
                nConvertSize = self.st_frame_info.nWidth * self.st_frame_info.nHeight * 3
                stConvertParam.enDstPixelType = PixelType_Gvsp_RGB8_Packed
                stConvertParam.pDstBuffer = (c_ubyte * nConvertSize)()
                stConvertParam.nDstBufferSize = nConvertSize
                time_start = time.time()
                ret = self.obj_cam.MV_CC_ConvertPixelType(stConvertParam)
                time_end = time.time()
                # print('MV_CC_ConvertPixelType to RGB:',time_end - time_start)
                if ret != 0:
                    tkinter.messagebox.showerror('show error', 'convert pixel fail! ret = ' + self.To_hex_str(ret))
                    continue
                cdll.msvcrt.memcpy(byref(img_buff), stConvertParam.pDstBuffer, nConvertSize)
                numArray = CameraOperation.Color_numpy(self, img_buff, self.st_frame_info.nWidth,
                                                       self.st_frame_info.nHeight)
                mode = "RGB"

            #     Ǻڰ  ҷ Mono8  תΪMono8    ʾ
            elif self.Is_mono_data(self.st_frame_info.enPixelType):
                nConvertSize = self.st_frame_info.nWidth * self.st_frame_info.nHeight
                stConvertParam.enDstPixelType = PixelType_Gvsp_Mono8
                stConvertParam.pDstBuffer = (c_ubyte * nConvertSize)()
                stConvertParam.nDstBufferSize = nConvertSize
                time_start = time.time()
                ret = self.obj_cam.MV_CC_ConvertPixelType(stConvertParam)
                time_end = time.time()
                # print('MV_CC_ConvertPixelType to Mono8:',time_end - time_start)
                if ret != 0:
                    tkinter.messagebox.showerror('show error', 'convert pixel fail! ret = ' + self.To_hex_str(ret))
                    continue
                cdll.msvcrt.memcpy(byref(img_buff), stConvertParam.pDstBuffer, nConvertSize)
                numArray = CameraOperation.Mono_numpy(self, img_buff, self.st_frame_info.nWidth,
                                                      self.st_frame_info.nHeight)
                mode = "L"
            # ϲ OpenCV  Tkinter
            current_image = Image.frombuffer(mode, (self.st_frame_info.nWidth, self.st_frame_info.nHeight),
                                             numArray.astype('uint8')).resize((640, 480), Image.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=current_image.transpose(Image.ROTATE_270),
                                       master=root)  # .transpose(Image.ROTATE_180)
            panel.imgtk = imgtk
            panel.config(image=imgtk)
            root.obr = imgtk
            nRet = self.obj_cam.MV_CC_FreeImageBuffer(stOutFrame)
            if self.b_exit == True:
                if img_buff is not None:
                    del img_buff
                if buf_cache is not None:
                    del buf_cache
                break

    def Save_jpg(self, buf_cache):
        if (None == buf_cache):
            return
        self.buf_save_image = None
        file_path = str(self.st_frame_info.nFrameNum) + ".jpg"
        self.n_save_image_size = self.st_frame_info.nWidth * self.st_frame_info.nHeight * 3 + 2048
        if self.buf_save_image is None:
            self.buf_save_image = (c_ubyte * self.n_save_image_size)()

        stParam = MV_SAVE_IMAGE_PARAM_EX()
        stParam.enImageType = MV_Image_Jpeg;  # ch:  Ҫ     ͼ       | en:Image format to save
        stParam.enPixelType = self.st_frame_info.enPixelType  # ch:     Ӧ     ظ ʽ | en:Camera pixel type
        stParam.nWidth = self.st_frame_info.nWidth  # ch:     Ӧ Ŀ  | en:Width
        stParam.nHeight = self.st_frame_info.nHeight  # ch:     Ӧ ĸ  | en:Height
        stParam.nDataLen = self.st_frame_info.nFrameLen
        stParam.pData = cast(buf_cache, POINTER(c_ubyte))
        stParam.pImageBuffer = cast(byref(self.buf_save_image), POINTER(c_ubyte))
        stParam.nBufferSize = self.n_save_image_size  # ch: 洢 ڵ Ĵ С | en:Buffer node size
        stParam.nJpgQuality = 80;  # ch:jpg   룬   ڱ   Jpgͼ  ʱ  Ч      BMPʱSDK ں  Ըò
        return_code = self.obj_cam.MV_CC_SaveImageEx2(stParam)

        if return_code != 0:
            tkinter.messagebox.showerror('show error', 'save jpg fail! ret = ' + self.To_hex_str(return_code))
            self.b_save_jpg = False
            return
        file_open = open(file_path.encode('ascii'), 'wb+')
        img_buff = (c_ubyte * stParam.nImageLen)()
        try:
            cdll.msvcrt.memcpy(byref(img_buff), stParam.pImageBuffer, stParam.nImageLen)
            file_open.write(img_buff)
            self.b_save_jpg = False
            tkinter.messagebox.showinfo('show info', 'save jpg success!')
        except:
            self.b_save_jpg = False
            raise Exception("get one frame failed:%s" % e.message)
        if None != img_buff:
            del img_buff
        if None != self.buf_save_image:
            del self.buf_save_image

    def Save_jpg1(self, buf_cache):
        if (None == buf_cache):
            print("û    ͼƬ  ͼƬ ǿյ ")
            return False
        self.buf_save_image = None
        current_path = os.path.dirname(__file__)
        # file_path = str(self.st_frame_info.nFrameNum) + ".jpg"
        global i
        global k
        file_path = current_path + "\image\\test.jpg"
        photo_path = current_path + "\img"
        photolen = count_photos(photo_path)
        photo_path_temp = current_path + "\img\\" + ymdname
        photolen_temp = count_photos(photo_path_temp)
        if photolen <= 1000:
            if photolen_temp < 1000:
                i += 1  # Ҫ ޸
            else:
                k += 1
        global test_path

        test_path = current_path + "\img\\" + ymdname + "\\train" + randomfilename + "-{b}.jpg".format(a=k, b=i)
        self.n_save_image_size = self.st_frame_info.nWidth * self.st_frame_info.nHeight * 3 + 2048
        if self.buf_save_image is None:
            self.buf_save_image = (c_ubyte * self.n_save_image_size)()

        stParam = MV_SAVE_IMAGE_PARAM_EX()
        stParam.enImageType = MV_Image_Jpeg;  # ch:  Ҫ     ͼ       | en:Image format to save
        stParam.enPixelType = self.st_frame_info.enPixelType  # ch:     Ӧ     ظ ʽ | en:Camera pixel type
        stParam.nWidth = self.st_frame_info.nWidth  # ch:     Ӧ Ŀ  | en:Width
        stParam.nHeight = self.st_frame_info.nHeight  # ch:     Ӧ ĸ  | en:Height
        stParam.nDataLen = self.st_frame_info.nFrameLen
        stParam.pData = cast(buf_cache, POINTER(c_ubyte))
        stParam.pImageBuffer = cast(byref(self.buf_save_image), POINTER(c_ubyte))
        stParam.nBufferSize = self.n_save_image_size  # ch: 洢 ڵ Ĵ С | en:Buffer node size
        stParam.nJpgQuality = 80;  # ch:jpg   룬   ڱ   Jpgͼ  ʱ  Ч      BMPʱSDK ں  Ըò
        return_code = self.obj_cam.MV_CC_SaveImageEx2(stParam)

        if return_code != 0:
            tkinter.messagebox.showerror('show error', 'save jpg fail! ret = ' + self.To_hex_str(return_code))
            self.b_save_jpg1 = False
            return False
        file_open = open(file_path.encode('ascii'), 'wb+')

        img_buff = (c_ubyte * stParam.nImageLen)()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(mythread, test_path)
            file_test = future.result()
        try:
            cdll.msvcrt.memcpy(byref(img_buff), stParam.pImageBuffer, stParam.nImageLen)
            file_open.write(img_buff)
            file_test.write(img_buff)
            self.b_save_jpg1 = False
            # tkinter.messagebox.showinfo('show info','save jpg success!')
        except:
            self.b_save_jpg1 = False
            raise Exception("get one frame failed:%s" % e.message)
        with Image.open(file_path.encode('ascii')) as img:
            flipped_img = img.transpose(Image.ROTATE_270)
            flipped_img.save(file_path)
        with Image.open(test_path.encode('ascii')) as img1:
            flipped_img1 = img1.transpose(Image.ROTATE_270)
            flipped_img1.save(test_path)
        if None != img_buff:
            del img_buff
        if None != self.buf_save_image:
            del self.buf_save_image
        return True

    def Save_Bmp(self, buf_cache):
        if (0 == buf_cache):
            return
        self.buf_save_image = None
        file_path = str(self.st_frame_info.nFrameNum) + ".bmp"
        self.n_save_image_size = self.st_frame_info.nWidth * self.st_frame_info.nHeight * 3 + 2048
        if self.buf_save_image is None:
            self.buf_save_image = (c_ubyte * self.n_save_image_size)()

        stParam = MV_SAVE_IMAGE_PARAM_EX()
        stParam.enImageType = MV_Image_Bmp;  # ch:  Ҫ     ͼ       | en:Image format to save
        stParam.enPixelType = self.st_frame_info.enPixelType  # ch:     Ӧ     ظ ʽ | en:Camera pixel type
        stParam.nWidth = self.st_frame_info.nWidth  # ch:     Ӧ Ŀ  | en:Width
        stParam.nHeight = self.st_frame_info.nHeight  # ch:     Ӧ ĸ  | en:Height
        stParam.nDataLen = self.st_frame_info.nFrameLen
        stParam.pData = cast(buf_cache, POINTER(c_ubyte))
        stParam.pImageBuffer = cast(byref(self.buf_save_image), POINTER(c_ubyte))
        stParam.nBufferSize = self.n_save_image_size  # ch: 洢 ڵ Ĵ С | en:Buffer node size
        return_code = self.obj_cam.MV_CC_SaveImageEx2(stParam)
        if return_code != 0:
            tkinter.messagebox.showerror('show error', 'save bmp fail! ret = ' + self.To_hex_str(return_code))
            self.b_save_bmp = False
            return
        file_open = open(file_path.encode('ascii'), 'wb+')
        img_buff = (c_ubyte * stParam.nImageLen)()
        try:
            cdll.msvcrt.memcpy(byref(img_buff), stParam.pImageBuffer, stParam.nImageLen)
            file_open.write(img_buff)
            self.b_save_bmp = False
            tkinter.messagebox.showinfo('show info', 'save bmp success!')
        except:
            self.b_save_bmp = False
            raise Exception("get one frame failed:%s" % e.message)
        if None != img_buff:
            del img_buff
        if None != self.buf_save_image:
            del self.buf_save_image

    def Is_mono_data(self, enGvspPixelType):
        if PixelType_Gvsp_Mono8 == enGvspPixelType or PixelType_Gvsp_Mono10 == enGvspPixelType \
                or PixelType_Gvsp_Mono10_Packed == enGvspPixelType or PixelType_Gvsp_Mono12 == enGvspPixelType \
                or PixelType_Gvsp_Mono12_Packed == enGvspPixelType:
            return True
        else:
            return False

    def Is_color_data(self, enGvspPixelType):
        if PixelType_Gvsp_BayerGR8 == enGvspPixelType or PixelType_Gvsp_BayerRG8 == enGvspPixelType \
                or PixelType_Gvsp_BayerGB8 == enGvspPixelType or PixelType_Gvsp_BayerBG8 == enGvspPixelType \
                or PixelType_Gvsp_BayerGR10 == enGvspPixelType or PixelType_Gvsp_BayerRG10 == enGvspPixelType \
                or PixelType_Gvsp_BayerGB10 == enGvspPixelType or PixelType_Gvsp_BayerBG10 == enGvspPixelType \
                or PixelType_Gvsp_BayerGR12 == enGvspPixelType or PixelType_Gvsp_BayerRG12 == enGvspPixelType \
                or PixelType_Gvsp_BayerGB12 == enGvspPixelType or PixelType_Gvsp_BayerBG12 == enGvspPixelType \
                or PixelType_Gvsp_BayerGR10_Packed == enGvspPixelType or PixelType_Gvsp_BayerRG10_Packed == enGvspPixelType \
                or PixelType_Gvsp_BayerGB10_Packed == enGvspPixelType or PixelType_Gvsp_BayerBG10_Packed == enGvspPixelType \
                or PixelType_Gvsp_BayerGR12_Packed == enGvspPixelType or PixelType_Gvsp_BayerRG12_Packed == enGvspPixelType \
                or PixelType_Gvsp_BayerGB12_Packed == enGvspPixelType or PixelType_Gvsp_BayerBG12_Packed == enGvspPixelType \
                or PixelType_Gvsp_YUV422_Packed == enGvspPixelType or PixelType_Gvsp_YUV422_YUYV_Packed == enGvspPixelType:
            return True
        else:
            return False

    def Mono_numpy(self, data, nWidth, nHeight):
        data_ = np.frombuffer(data, count=int(nWidth * nHeight), dtype=np.uint8, offset=0)
        data_mono_arr = data_.reshape(nHeight, nWidth)
        numArray = np.zeros([nHeight, nWidth, 1], "uint8")
        numArray[:, :, 0] = data_mono_arr
        return numArray

    def Color_numpy(self, data, nWidth, nHeight):
        data_ = np.frombuffer(data, count=int(nWidth * nHeight * 3), dtype=np.uint8, offset=0)
        data_r = data_[0:nWidth * nHeight * 3:3]
        data_g = data_[1:nWidth * nHeight * 3:3]
        data_b = data_[2:nWidth * nHeight * 3:3]

        data_r_arr = data_r.reshape(nHeight, nWidth)
        data_g_arr = data_g.reshape(nHeight, nWidth)
        data_b_arr = data_b.reshape(nHeight, nWidth)
        numArray = np.zeros([nHeight, nWidth, 3], "uint8")

        numArray[:, :, 0] = data_r_arr
        numArray[:, :, 1] = data_g_arr
        numArray[:, :, 2] = data_b_arr
        return numArray