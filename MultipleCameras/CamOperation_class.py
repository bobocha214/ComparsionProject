# -- coding: utf-8 --
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
import datetime
import inspect
import ctypes
import random
from PIL import Image,ImageTk
from ctypes import *
from tkinter import ttk

# sys.path.append("../MvImport")
sys.path.append(os.path.join(os.path.dirname(__file__),"../MvImport"))
from MvCameraControl_class import *

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

class CameraOperation():

    def __init__(self,obj_cam,st_device_list,n_connect_num=0,b_open_device=False,b_start_grabbing = False,h_thread_handle=None,\
                b_thread_closed=False,st_frame_info=None,b_exit=False,b_save_bmp=False,b_save_jpg=False,buf_save_image=None,\
                n_save_image_size=0,frame_rate=0,exposure_time=0,gain=0):

        self.obj_cam = obj_cam
        self.st_device_list = st_device_list
        self.n_connect_num = n_connect_num
        self.b_open_device = b_open_device
        self.b_start_grabbing = b_start_grabbing 
        self.b_thread_closed = b_thread_closed
        self.st_frame_info = st_frame_info
        self.b_exit = b_exit
        self.b_save_bmp = b_save_bmp
        self.b_save_jpg = b_save_jpg
        self.buf_save_image = buf_save_image
        self.h_thread_handle = h_thread_handle
        self.n_save_image_size = n_save_image_size
        self.frame_rate = frame_rate
        self.exposure_time = exposure_time
        self.gain = gain

    def To_hex_str(self,num):
        chaDic = {10: 'a', 11: 'b', 12: 'c', 13: 'd', 14: 'e', 15: 'f'}
        hexStr = ""
        if num < 0:
            num = num + 2**32
        while num >= 16:
            digit = num % 16
            hexStr = chaDic.get(digit, str(digit)) + hexStr
            num //= 16
        hexStr = chaDic.get(num, str(num)) + hexStr   
        return hexStr


    def Open_device(self):
        if False == self.b_open_device:
            # ch:选择设备并创建句柄 | en:Select device and create handle
            nConnectionNum = int(self.n_connect_num)
            stDeviceList = cast(self.st_device_list.pDeviceInfo[int(nConnectionNum)], POINTER(MV_CC_DEVICE_INFO)).contents
            self.obj_cam = MvCamera()
            ret = self.obj_cam.MV_CC_CreateHandle(stDeviceList)
            if ret != 0:
                self.obj_cam.MV_CC_DestroyHandle()
                return ret

            ret = self.obj_cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
            if ret != 0:
                self.b_open_device = False
                self.b_thread_closed = False
                return ret
            self.b_open_device = True
            self.b_thread_closed = False

            # ch:探测网络最佳包大小(只对GigE相机有效) | en:Detection network optimal package size(It only works for the GigE camera)
            if stDeviceList.nTLayerType == MV_GIGE_DEVICE:
                nPacketSize = self.obj_cam.MV_CC_GetOptimalPacketSize()
                if int(nPacketSize) > 0:
                    ret = self.obj_cam.MV_CC_SetIntValue("GevSCPSPacketSize",nPacketSize)
                    if ret != 0:
                        print ("warning: set packet size fail! ret[0x%x]" % ret)
                else:
                    print ("warning: set packet size fail! ret[0x%x]" % nPacketSize)

            stBool = c_bool(False)
            ret =self.obj_cam.MV_CC_GetBoolValue("AcquisitionFrameRateEnable", stBool)
            if ret != 0:
                print ("get acquisition frame rate enable fail! ret[0x%x]" % ret)

            # ch:设置触发模式为off | en:Set trigger mode as off
            ret = self.obj_cam.MV_CC_SetEnumValueByString("TriggerMode", "Off")
            if ret != 0:
                print ("set trigger mode fail! ret[0x%x]" % ret)
            return 0

    def Start_grabbing(self,index,root,panel,lock):
        if False == self.b_start_grabbing and True == self.b_open_device:
            self.b_exit = False
            ret = self.obj_cam.MV_CC_StartGrabbing()
            if ret != 0:
                self.b_start_grabbing = False
                return ret
            self.b_start_grabbing = True
            try:
                self.h_thread_handle = threading.Thread(target=CameraOperation.Work_thread, args=(self,index,root,panel,lock))
                self.h_thread_handle.start()
                self.b_thread_closed = True
            except:
                tkinter.messagebox.showerror('show error','error: unable to start thread')
                False == self.b_start_grabbing
            return ret

    def Stop_grabbing(self):
        if True == self.b_start_grabbing and self.b_open_device == True:
            #退出线程
            ret = 0
            if True == self.b_thread_closed:
                Stop_thread(self.h_thread_handle)
                self.b_thread_closed = False
            ret = self.obj_cam.MV_CC_StopGrabbing()
            if ret != 0:
                self.b_start_grabbing = True
                self.b_exit  = False  
                return ret
            self.b_start_grabbing = False
            self.b_exit  = True 
            return ret     

    def Close_device(self):
        if True == self.b_open_device:
            #退出线程
            if True == self.b_thread_closed:
                self.b_thread_closed = False
                Stop_thread(self.h_thread_handle)
            ret = self.obj_cam.MV_CC_StopGrabbing()
            ret = self.obj_cam.MV_CC_CloseDevice()
            return ret
                
        # ch:销毁句柄 | Destroy handle
        self.obj_cam.MV_CC_DestroyHandle()
        self.b_open_device = False
        self.b_start_grabbing = False
        self.b_exit  = True

    def Set_trigger_mode(self,strMode):
        if True == self.b_open_device:
            if "continuous" == strMode: 
                ret = self.obj_cam.MV_CC_SetEnumValueByString("TriggerMode","Off")
                if ret != 0:
                    return ret
            if "triggermode" == strMode:
                ret = self.obj_cam.MV_CC_SetEnumValueByString("TriggerMode","On")
                if ret != 0:
                    return ret
                ret = self.obj_cam.MV_CC_SetEnumValueByString("TriggerSource","Software")
                if ret != 0:
                    return ret
                return ret

    def Trigger_once(self,nCommand):
        if True == self.b_open_device:
            if 1 == nCommand: 
                ret = self.obj_cam.MV_CC_SetCommandValue("TriggerSoftware")
                return ret

    def Get_parameter(self):
        if True == self.b_open_device:
            stFloatParam_FrameRate =  MVCC_FLOATVALUE()
            memset(byref(stFloatParam_FrameRate), 0, sizeof(MVCC_FLOATVALUE))
            stFloatParam_exposureTime = MVCC_FLOATVALUE()
            memset(byref(stFloatParam_exposureTime), 0, sizeof(MVCC_FLOATVALUE))
            stFloatParam_gain = MVCC_FLOATVALUE()
            memset(byref(stFloatParam_gain), 0, sizeof(MVCC_FLOATVALUE))
            ret = self.obj_cam.MV_CC_GetFloatValue("AcquisitionFrameRate", stFloatParam_FrameRate)
            self.frame_rate = stFloatParam_FrameRate.fCurValue
            ret = self.obj_cam.MV_CC_GetFloatValue("ExposureTime", stFloatParam_exposureTime)
            self.exposure_time = stFloatParam_exposureTime.fCurValue
            ret = self.obj_cam.MV_CC_GetFloatValue("Gain", stFloatParam_gain)
            self.gain = stFloatParam_gain.fCurValue
            return ret

    def Set_parameter(self,frameRate,exposureTime,gain):
        if '' == frameRate or '' == exposureTime or '' == gain:
            return -1
        if True == self.b_open_device:
            ret = self.obj_cam.MV_CC_SetFloatValue("ExposureTime",float(exposureTime))
            ret = self.obj_cam.MV_CC_SetFloatValue("Gain",float(gain))
            ret = self.obj_cam.MV_CC_SetFloatValue("AcquisitionFrameRate",float(frameRate))
            return ret

    def Work_thread(self,index,root,panel,lock):
        stOutFrame = MV_FRAME_OUT() 
        memset(byref(stOutFrame), 0, sizeof(stOutFrame))
        img_buff = None
        buf_cache = None
        numArray = None
        while True:
            ret = self.obj_cam.MV_CC_GetImageBuffer(stOutFrame, 5000)
            if 0 == ret:
                if None == buf_cache:
                    buf_cache = (c_ubyte * stOutFrame.stFrameInfo.nFrameLen)()
                self.st_frame_info = stOutFrame.stFrameInfo
                cdll.msvcrt.memcpy(byref(buf_cache), stOutFrame.pBufAddr, self.st_frame_info.nFrameLen)
                print ("Camera[%d]:get one frame: Width[%d], Height[%d], nFrameNum[%d]"  % (index,self.st_frame_info.nWidth, self.st_frame_info.nHeight, self.st_frame_info.nFrameNum))
                self.n_save_image_size = self.st_frame_info.nWidth * self.st_frame_info.nHeight * 3 + 2048
                if img_buff is None:
                    img_buff = (c_ubyte * self.n_save_image_size)()
            else:
                print("Camera[" + str(index) + "]:no data, ret = "+self.To_hex_str(ret))
                if self.b_exit == True:
                    break
                continue

            #转换像素结构体赋值
            stConvertParam = MV_CC_PIXEL_CONVERT_PARAM()
            memset(byref(stConvertParam), 0, sizeof(stConvertParam))
            stConvertParam.nWidth = self.st_frame_info.nWidth
            stConvertParam.nHeight = self.st_frame_info.nHeight
            stConvertParam.pSrcData = cast(buf_cache, POINTER(c_ubyte))
            stConvertParam.nSrcDataLen = self.st_frame_info.nFrameLen
            stConvertParam.enSrcPixelType = self.st_frame_info.enPixelType 

            # RGB直接显示
            if PixelType_Gvsp_RGB8_Packed == self.st_frame_info.enPixelType:
                numArray = CameraOperation.Color_numpy(self,buf_cache,self.st_frame_info.nWidth,self.st_frame_info.nHeight)
            else:
                nConvertSize = self.st_frame_info.nWidth * self.st_frame_info.nHeight * 3
                stConvertParam.enDstPixelType = PixelType_Gvsp_RGB8_Packed
                stConvertParam.pDstBuffer = (c_ubyte * nConvertSize)()
                stConvertParam.nDstBufferSize = nConvertSize
                ret = self.obj_cam.MV_CC_ConvertPixelType(stConvertParam)
                if ret != 0:
                    continue
                cdll.msvcrt.memcpy(byref(img_buff), stConvertParam.pDstBuffer, nConvertSize)
                numArray = CameraOperation.Color_numpy(self,img_buff,self.st_frame_info.nWidth,self.st_frame_info.nHeight)

            #合并OpenCV到Tkinter界面中
            current_image = Image.fromarray(numArray).resize((500, 500), Image.ANTIALIAS)
            lock.acquire()  #加锁
            imgtk = ImageTk.PhotoImage(image=current_image, master=root)
            panel.imgtk = imgtk        
            panel.config(image=imgtk)
            root.obr = imgtk
            lock.release() #释放锁
            nRet = self.obj_cam.MV_CC_FreeImageBuffer(stOutFrame)
            if self.b_exit == True:
                if img_buff is not None:
                    del img_buff
                break

    def Save_jpg(self,buf_cache):
        if(None == buf_cache):
            return
        self.buf_save_image = None
        file_path = str(self.st_frame_info.nFrameNum) + ".jpg"
        self.n_save_image_size = self.st_frame_info.nWidth * self.st_frame_info.nHeight * 3 + 2048
        if self.buf_save_image is None:
            self.buf_save_image = (c_ubyte * self.n_save_image_size)()

        stParam = MV_SAVE_IMAGE_PARAM_EX()
        stParam.enImageType = MV_Image_Jpeg;                                        # ch:需要保存的图像类型 | en:Image format to save
        stParam.enPixelType = self.st_frame_info.enPixelType                               # ch:相机对应的像素格式 | en:Camera pixel type
        stParam.nWidth      = self.st_frame_info.nWidth                                    # ch:相机对应的宽 | en:Width
        stParam.nHeight     = self.st_frame_info.nHeight                                   # ch:相机对应的高 | en:Height
        stParam.nDataLen    = self.st_frame_info.nFrameLen
        stParam.pData       = cast(buf_cache, POINTER(c_ubyte))
        stParam.pImageBuffer=  cast(byref(self.buf_save_image), POINTER(c_ubyte)) 
        stParam.nBufferSize = self.n_save_image_size                                 # ch:存储节点的大小 | en:Buffer node size
        stParam.nJpgQuality = 80;                                                    # ch:jpg编码，仅在保存Jpg图像时有效。保存BMP时SDK内忽略该参数
        return_code = self.obj_cam.MV_CC_SaveImageEx2(stParam)            

        if return_code != 0:
            tkinter.messagebox.showerror('show error','save jpg fail! ret = '+self.To_hex_str(return_code))
            self.b_save_jpg = False
            return
        file_open = open(file_path.encode('ascii'), 'wb+')
        img_buff = (c_ubyte * stParam.nImageLen)()
        try:
            cdll.msvcrt.memcpy(byref(img_buff), stParam.pImageBuffer, stParam.nImageLen)
            file_open.write(img_buff)
            self.b_save_jpg = False
            tkinter.messagebox.showinfo('show info','save jpg success!')
        except:
            self.b_save_jpg = False
            raise Exception("get one frame failed:%s" % e.message)
        if None != img_buff:
            del img_buff
        if None != self.buf_save_image:
            del self.buf_save_image

    def Save_Bmp(self,buf_cache):
        if(0 == buf_cache):
            return
        self.buf_save_image = None
        file_path = str(self.st_frame_info.nFrameNum) + ".bmp"    
        self.n_save_image_size = self.st_frame_info.nWidth * self.st_frame_info.nHeight * 3 + 2048
        if self.buf_save_image is None:
            self.buf_save_image = (c_ubyte * self.n_save_image_size)()

        stParam = MV_SAVE_IMAGE_PARAM_EX()
        stParam.enImageType = MV_Image_Bmp;                                        # ch:需要保存的图像类型 | en:Image format to save
        stParam.enPixelType = self.st_frame_info.enPixelType                               # ch:相机对应的像素格式 | en:Camera pixel type
        stParam.nWidth      = self.st_frame_info.nWidth                                    # ch:相机对应的宽 | en:Width
        stParam.nHeight     = self.st_frame_info.nHeight                                   # ch:相机对应的高 | en:Height
        stParam.nDataLen    = self.st_frame_info.nFrameLen
        stParam.pData       = cast(buf_cache, POINTER(c_ubyte))
        stParam.pImageBuffer=  cast(byref(self.buf_save_image), POINTER(c_ubyte)) 
        stParam.nBufferSize = self.n_save_image_size                                 # ch:存储节点的大小 | en:Buffer node size
        return_code = self.obj_cam.MV_CC_SaveImageEx2(stParam)            
        if return_code != 0:
            tkinter.messagebox.showerror('show error','save bmp fail! ret = '+self.To_hex_str(return_code))
            self.b_save_bmp = False
            return
        file_open = open(file_path.encode('ascii'), 'wb+')
        img_buff = (c_ubyte * stParam.nImageLen)()
        try:
            cdll.msvcrt.memcpy(byref(img_buff), stParam.pImageBuffer, stParam.nImageLen)
            file_open.write(img_buff)
            self.b_save_bmp = False
            tkinter.messagebox.showinfo('show info','save bmp success!')
        except:
            self.b_save_bmp = False
            raise Exception("get one frame failed:%s" % e.message)
        if None != img_buff:
            del img_buff
        if None != self.buf_save_image:
            del self.buf_save_image

    def Mono_numpy(self,data,nWidth,nHeight):
        data_ = np.frombuffer(data, count=int(nWidth * nHeight), dtype=np.uint8, offset=0)
        data_mono_arr = data_.reshape(nHeight, nWidth)
        numArray = np.zeros([nHeight, nWidth, 1],"uint8") 
        numArray[:, :, 0] = data_mono_arr
        return numArray

    def Color_numpy(self,data,nWidth,nHeight):
        data_ = np.frombuffer(data, count=int(nWidth*nHeight*3), dtype=np.uint8, offset=0)
        data_r = data_[0:nWidth*nHeight*3:3]
        data_g = data_[1:nWidth*nHeight*3:3]
        data_b = data_[2:nWidth*nHeight*3:3]

        data_r_arr = data_r.reshape(nHeight, nWidth)
        data_g_arr = data_g.reshape(nHeight, nWidth)
        data_b_arr = data_b.reshape(nHeight, nWidth)
        numArray = np.zeros([nHeight, nWidth, 3],"uint8")

        numArray[:, :, 0] = data_r_arr
        numArray[:, :, 1] = data_g_arr
        numArray[:, :, 2] = data_b_arr
        return numArray