# -- coding: utf-8 --
import tkinter.messagebox
from tkinter import messagebox
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
# from bounding import bounding

matplotlib.use('TkAgg')
from matplotlib import pyplot as plt

logger.add('log\\runtime_{time}.log', rotation='00:00', retention='15 days', backtrace=True, diagnose=True)


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
    loginflag = True
    # 需要解开
    # stop_grabbing()
    show_frame(frame)
    # start_grabbing1()


# 返回登陆结果信息

loginflag = True


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
            # stop_grabbing()
            show_frame(frame2)
        else:
            tk.messagebox.showerror("登录失败", "用户名或密码错误！")
            login_win.destroy()
            loginflag = True
            show_frame(frame1)
    else:
        tk.messagebox.showerror("登录失败", "请填写用户名和密码！")
        login_win.destroy()
        loginflag = True
        show_frame(frame1)


# 登陆取消

@logger.catch
def do_cancel(login_win):
    global loginflag
    login_win.destroy()
    loginflag = True


@logger.catch
def on_exit(login_win):
    global loginflag
    loginflag = True
    login_win.destroy()


# 显示登陆页面
@logger.catch
def show_login_page(frame2):
    global loginflag
    if loginflag:
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
        loginflag = False
    else:
        pass


@logger.catch
def show_label(show):
    if show:
        labelORIGIN.grid(row=7, column=0, columnspan=2, sticky='w', padx=30, pady=10)
        time.sleep(0.1)
        labelORIGIN.grid_forget()
        labelNG.grid_forget()
        labelOK.grid(row=7, column=0, columnspan=2, sticky='w', padx=30, pady=10)
    else:
        labelORIGIN.grid(row=7, column=0, columnspan=2, sticky='w', padx=30, pady=10)
        time.sleep(0.1)
        labelORIGIN.grid_forget()
        labelOK.grid_forget()
        labelNG.grid(row=7, column=0, columnspan=2, sticky='w', padx=30, pady=10)


@logger.catch
def handle_space(event):
    labelORIGIN.grid_forget()
    labelOK.grid_forget()
    labelNG.grid_forget()
    labelORIGIN.grid(row=7, column=0, columnspan=2, sticky='w', padx=30, pady=10)


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
        b_is_run = False
        lastresult = None
        threadflag = None
        COMGUNNUM = "COM11"
        COMSIGNALNUM = ""
        previous_COMGUNNUM = ""
        previous_COMSIGNALNUM = ""

        signalbuttonup = ''
        signalbuttondown = ''

        COM_sharedata = {'sedata': None}
        current_file = base_path('')
        parentdir = current_file + 'image\\test.jpg'
        folder_path = current_file + 'cuts'
        # 界面设计代码
        window = tk.Tk()
        window.title('条码比对系统')
        window.iconbitmap(current_file + 'logo.ico')
        # window.geometry('1400x800')
        main_menu = tk.Menu(window)
        picklename = 'settings.dat'
        picklename1 = 'parameter.dat'
        compickle = 'comport.dat'
        signaldata = 'signal.dat'
        imagepickle = 'imagepickle.dat'
        screenshot = 'screenshot.dat'
        saveImg = 'saveImg.dat'
        thresholdpickle = 'thresholdpickle.dat'
        cut_Pos = np.zeros((2, 2), int)
        global screenshotNum
        screenshotNum = 0
        global screen_img
        event = threading.Event()
        try:
            with open(signaldata, 'rb') as f:
                signalbuttonup = pickle.load(f)
                signalbuttondown = pickle.load(f)
                # print(checked,'withwith')
        except:
            signalbuttonup = ''
            signalbuttondown = ''

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
                # COMSIGNALNUM=pickle.load(f)
        except:
            COMGUNNUM = ""
        try:
            with open(screenshot, 'rb') as f:
                screenshotNum = int(pickle.load(f))
        except:
            screenshotNum = 0

        try:
            with open(imagepickle, 'rb') as f:
                IMAGEMatchValue = pickle.load(f)
        except:
            IMAGEMatchValue = "TM_CCOEFF_NORMED"

        output_directory = 'image'
        os.makedirs(output_directory, exist_ok=True)
        output_directory = 'csv'
        os.makedirs(output_directory, exist_ok=True)
        global frame1
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
        frame1.grid_columnconfigure(2, weight=1)
        frame1.grid_columnconfigure(3, weight=1)
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
        frame2.grid_columnconfigure(6, weight=1)
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
        page2 = Frame(frame2, height=384, width=512, relief=GROOVE, borderwidth=2, bg="red")
        page1 = Frame(frame1, height=384, width=512, relief=GROOVE, borderwidth=2, bg="red")
        # page.pack(expand=True, fill=BOTH)
        # page1.pack(expand=True, fill=BOTH)
        # panel = Label(page)
        # panel1 = Label(page1)
        page2.grid(row=2, column=6, rowspan=10, padx=10, pady=10, )
        page1.grid(row=3, column=3, rowspan=10, padx=10, pady=10, )
        global labelOK
        global labelNG
        global labelORIGIN
        labelOK = tk.Label(frame1, text="OK", background="green", font=('黑体', 40, 'bold'), padx=80, pady=80)
        labelNG = tk.Label(frame1, text="NG", background="red", font=('黑体', 40, 'bold'), padx=80, pady=80)
        labelORIGIN = tk.Label(frame1, text="AB", font=('黑体', 40, 'bold'), background="white", padx=80, pady=80)
        labelOK.grid(row=7, column=0, columnspan=2, sticky='we', padx=30, pady=10)
        canvas = tk.Canvas(frame1, width=512, height=384, bg='gray')
        canvas.grid(row=3, column=2, rowspan=10, padx=10, pady=10, )
        try:
            image = Image.open(parentdir)
        except:
            image = Image.open(current_file + 'logo.ico')
        photo = ImageTk.PhotoImage(image.resize((512, 384), Image.LANCZOS))
        image_item = canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        # print(parentdir)
        ocr = CnOcr(rec_model_name='densenet_lite_136-gru', det_model_name='en_PP-OCRv3_det',
                    det_more_configs={'use_angle_clf': True})
        now = datetime.datetime.now()
        year = now.year
        month = now.month


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
            devicestatucl.grid(row=0, column=1, columnspan=2, padx=10, pady=10, sticky="we")
            devicestatuclose.grid(row=1, column=2, columnspan=2, padx=10, pady=10, sticky="we")


        # ch:开始取流 | en:Start grab image

        @logger.catch
        def start_grabbing():
            global obj_cam_operation
            obj_cam_operation.Start_grabbing(frame2, page2)


        @logger.catch
        def start_grabbing1():
            global obj_cam_operation
            obj_cam_operation.Start_grabbing(frame1, page1)


        # ch:停止取流 | en:Stop grab image
        @logger.catch
        def stop_grabbing():
            global obj_cam_operation
            obj_cam_operation.Stop_grabbing()


        @logger.catch
        def stop_grabbing1():
            global obj_cam_operation
            obj_cam_operation.Stop_grabbing()

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
            devicestatucl.grid(row=0, column=1, columnspan=2, padx=10, pady=10, sticky="we")
            devicestatuclose.grid(row=1, column=2, columnspan=2, padx=10, pady=10, sticky="we")


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
            ser1 = serial.Serial(COMGUNNUM, 9600, timeout=0.5)
            try:
                # print(COMGUNNUM)
                data = ser1.readline()
                serialdata = data.decode().strip()
                if (serialdata != ''):
                    return serialdata
                else:
                    pass
            except:
                time.sleep(1)  # 等待1秒后重试
                return False
            finally:
                # Close the serial port
                ser1.close()


        @logger.catch  # 发送扫描命令
        def sendSerialOrder():
            ser1 = serial.Serial(COMGUNNUM, 9600, timeout=0.5)
            try:
                hexStr = "03 53 80 ff 2a"
                bytes_hex = bytes.fromhex(hexStr)
                ser1.write(bytes_hex)
            except:
                time.sleep(0.5)  # 等待1秒后重试
                return False
            finally:
                # Close the serial port
                ser1.close()


        # 获得图片OCR识别结果
        @logger.catch
        def getSnCode():
            sub = 'SN:'
            nub = 'PN:'
            serachnum = 'N:'
            SnCode = ''
            position = ''
            res = ocr.ocr(parentdir)
            # print(res)
            if (res):
                for i in res:
                    if sub in i['text'] or nub in i['text'] and len(i['text']) >= 17:
                        if sub in i['text'] and len(i['text']) <= 21:
                            firstSnCode = i['text']
                            tempcode = ''.join(str(firstSnCode).split())
                            SnCode = tempcode[3:].replace(" ", "")
                            position = i['position']
                            print(SnCode, 'subsubsubsubsub')
                            print(len(SnCode))
                        else:
                            try:
                                second_coourenceN = i['text'].index(serachnum, i['text'].index(serachnum) + 1)
                                SnCode = str(i['text'][second_coourenceN + len(serachnum):]).replace(" ", "")
                                position = i['position']
                                print(SnCode, 'trytrytrytrytry')
                            except:
                                firstSnCode = i['text']
                                tempcode = ''.join(str(firstSnCode).split())
                                SnCode = tempcode[-17:].replace(" ", "")
                                position = i['position']
                                print(SnCode, 'exceptexceptexceptexcept')  # 特殊情况取后十七位
                    else:
                        pass
                        # print(i['text'], 'pass')
                if SnCode == '':
                    for i in res:
                        if 'text' in i and len(i['text']) == 17:
                            max_length_dict = i
                            SnCode = max_length_dict['text']
                            position = max_length_dict['position']
                        else:
                            SnCode = '未识别到合适数据'
                            position = np.zeros((4, 2))
                else:
                    pass

            else:
                SnCode = '没找到数据'
                position = np.zeros((4, 2))
            if SnCode:
                preCode = SnCode[:1]
                nextSnCode = SnCode[1:]
                SnCode = (preCode + str(nextSnCode).replace('O', '0'))
            else:
                SnCode = '没找到数据'
                position = np.zeros((4, 2))
            return SnCode, position


        @logger.catch
        def jpg_save1(event=None):
            global obj_cam_operation
            obj_cam_operation.b_save_jpg1 = True

            # return comflag


        @logger.catch
        def on_save_img(event=None):
            with open(picklename, 'wb') as f:
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
        def wait_for_response1():
            while True:
                serialdata = getSerialdata()
                if serialdata:
                    flag = False
                    global lastresult
                    result = ''
                    jpg_save1()
                    time.sleep(0.2)
                    SnCode, position = getSnCode()
                    rect = canvas.create_rectangle(0, 0, canvas.winfo_width(), canvas.winfo_height(), fill='white',
                                                   outline='white')
                    canvas.update()
                    start_updateimg_task(position)
                    label_frame_rate4.config(text=lastresult)
                    label_frame_rate4.grid(row=4, column=1, padx=10, pady=10, sticky="w")
                    label_frame_rate5.config(text=serialdata)
                    label_frame_rate5.grid(row=5, column=1, padx=10, pady=10, sticky="w")
                    label_frame_rate6.config(text=SnCode)
                    label_frame_rate6.grid(row=6, column=1, padx=10, pady=10, sticky="w")
                    canvas.delete(rect)
                    image1 = Image.open(parentdir)
                    photo1 = ImageTk.PhotoImage(image1.resize((640, 480), Image.LANCZOS))
                    canvas.itemconfig(image_item, image=photo1)
                    canvas.update()
                    if serialdata == lastresult:
                        flag = False
                        result = 'continue'
                        show_label(flag)
                    else:
                        if SnCode == serialdata:
                            flag = True
                            result = 'OK'
                            show_label(flag)
                        else:
                            flag = False
                            result = 'NG'
                            show_label(flag)
                    if checked_val.get():
                        openflag = file_not_exist(
                            base_path('csv\{year}.{mon}.csv').format(year=year, mon=month).strip())
                        with open(base_path('csv\{year}.{mon}.csv').format(year=year, mon=month), mode='a',
                                  encoding='utf-8', newline='') as file:
                            writer = csv.writer(file)
                            column_names = ['serialdata', 'SnCode', 'result', 'costrattime']
                            if openflag:
                                writer.writerow(column_names)
                            costrattime = datetime.datetime.now()
                            data = [serialdata, SnCode, result, costrattime]
                            if result != 'continue':
                                writer.writerow(data)
                    else:
                        pass

                    # print(SnCode,'wait_for_response1')

                    lastresult = serialdata
                    result_list = CountProducts()
                    ok_count = result_list[0]
                    ng_count = result_list[1]
                    all_count = result_list[2]
                    with open(picklename1, 'wb') as f:
                        pickle.dump(ok_count, f)
                        pickle.dump(ng_count, f)
                        pickle.dump(all_count, f)
                    text_frame1_rate4.config(text=result_list[0])
                    text_frame1_rate4.grid(row=14, column=1, padx=10, pady=10, sticky="w")
                    text_frame1_rate5.config(text=result_list[1])
                    text_frame1_rate5.grid(row=15, column=1, padx=10, pady=10, sticky="w")
                    text_frame1_rate6.config(text=result_list[2])
                    text_frame1_rate6.grid(row=16, column=1, padx=10, pady=10, sticky="w")
                else:
                    pass
            # start_reset_task()1


        @logger.catch
        def start_long_task():
            tkinter.messagebox.showinfo('show info', '已开始！')
            t = threading.Thread(target=wait_for_response1)
            t.daemon = True
            t.start()
            showimg()


        @logger.catch
        def start_updateimg_task(position):
            t = threading.Thread(target=updateimg, args=(position,))
            t.daemon = True
            t.start()
            t.join()


        # @logger.catch
        # def start_jpg_save1():
        #     t = threading.Thread(target=jpg_save1())
        #     t.daemon = True
        #     t.start()
        #     t.join()
        # @logger.catch
        # def start_reset_task():
        #     t=threading.Thread(target=reset_result)
        #     t.daemon=True
        #     t.start()

        @logger.catch
        def updateimg(position):
            if np.all(position != 0):
                image = cv2.imread(parentdir)
                color = (0, 255, 0)
                x, y, w, h = cv2.boundingRect(position)
                # cv2.rectangle(image,(x-15,y-10),(x+w+5,y+h+5),color,6)
                cv2.rectangle(image, (x, y), (x + w, y + h), color, 6)
                cv2.imwrite(current_file + "image\\test.jpg", image)
            else:
                pass


        @logger.catch
        def showimg():
            canvas.grid(row=3, column=2, rowspan=10, padx=10, pady=10, sticky="nsew")


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
        # 需要解开
        # enum_devices()
        # time.sleep(1)
        # open_device()
        # start_grabbing1()

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

        btn_enum_devices = tk.Button(frame2, text='发现设备', width=35, height=1)  # , command=enum_devices
        btn_enum_devices.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="we")

        # commonuser
        btn_open_device = tk.Button(frame2, text='打开设备', width=15, height=1)  # , command=open_device
        btn_open_device.grid(row=2, column=0, padx=10, pady=10, sticky="we")

        btn_close_device = tk.Button(frame2, text='关闭设备', width=15, height=1)  # , command=close_device
        btn_close_device.grid(row=2, column=1, padx=10, pady=10, sticky="we")

        radio_continuous = tk.Radiobutton(frame2, text='持续性抓取', variable=model_val, value='continuous', width=15,
                                          height=1)  # , command=set_triggermode
        radio_continuous.grid(row=3, column=0, padx=10, pady=10, sticky="we")

        radio_trigger = tk.Radiobutton(frame2, text='触发模式', variable=model_val, value='triggermode', width=15,
                                       height=1)  # , command=set_triggermode
        radio_trigger.grid(row=3, column=1, padx=10, pady=10, sticky="we")
        model_val.set(1)

        btn_start_grabbing = tk.Button(frame2, text='开始抓取', width=15, height=1)  # , command=start_grabbing
        btn_start_grabbing.grid(row=4, column=0, padx=10, pady=10, sticky="we")

        btn_stop_grabbing = tk.Button(frame2, text='停止抓取', width=15, height=1)  # , command=stop_grabbing
        btn_stop_grabbing.grid(row=4, column=1, padx=10, pady=10, sticky="we")

        checkbtn_trigger_software = tk.Checkbutton(frame2, text='Tigger by Software', variable=triggercheck_val,
                                                   onvalue=1, offvalue=0)
        checkbtn_trigger_software.grid(row=5, column=0, padx=10, pady=10, sticky="we")
        btn_trigger_once = tk.Button(frame2, text='触发一次', width=15, height=1)  # , command=trigger_once
        btn_trigger_once.grid(row=5, column=1, padx=10, pady=10, sticky="we")

        btn_save_bmp = tk.Button(frame2, text='Save as BMP', width=15, height=1)  # , command=bmp_save
        btn_save_bmp.grid(row=6, column=0, padx=10, pady=10, sticky="we")
        btn_save_jpg = tk.Button(frame2, text='Save as JPG', width=15, height=1)  # , command=jpg_save
        btn_save_jpg.grid(row=6, column=1, padx=10, pady=10, sticky="we")
        label_frame1_all = tk.Label(frame1, text='总数量：', bg='skyblue', width=8, height=1, anchor='e')
        label_frame1_ng = tk.Label(frame1, text='不良数量：', bg='skyblue', width=8, height=1, anchor='e')
        label_frame1_per = tk.Label(frame1, text='可靠率：', bg='skyblue', width=8, height=1, anchor='e')
        text_frame1_rate4 = tk.Label(frame1, text='', width=20, height=1, anchor='w', bg='red')
        text_frame1_rate4.grid(row=14, column=1, padx=10, pady=10, sticky="w")
        text_frame1_rate5 = tk.Label(frame1, text='', width=16, height=1, anchor='w')
        text_frame1_rate6 = tk.Label(frame1, text='', width=8, height=1, anchor='w')
        label_frame1_all.grid(row=14, column=0, padx=10, pady=10, sticky="e")
        label_frame1_ng.grid(row=15, column=0, padx=10, pady=10, sticky="e")
        label_frame1_per.grid(row=16, column=0, padx=10, pady=10, sticky="e")
        try:
            with open(picklename1, 'rb') as f:
                ok_count = pickle.load(f)
                ng_count = pickle.load(f)
                all_count = pickle.load(f)
                text_frame1_rate4.config(text=ok_count)
                text_frame1_rate4.grid(row=14, column=1, padx=10, pady=10, sticky="nsew")
                text_frame1_rate5.config(text=ng_count)
                text_frame1_rate5.grid(row=15, column=1, padx=10, pady=10, sticky="nsew")
                text_frame1_rate6.config(text=all_count)
                text_frame1_rate6.grid(row=16, column=1, padx=10, pady=10, sticky="nsew")
        except:
            result_list = ['0', '0', '0%']
            text_frame1_rate4.config(text=result_list[0])
            text_frame1_rate4.grid(row=14, column=1, padx=10, pady=10, sticky="nsew")
            text_frame1_rate5.config(text=result_list[1])
            text_frame1_rate5.grid(row=15, column=1, padx=10, pady=10, sticky="nsew")
            text_frame1_rate6.config(text=result_list[2])
            text_frame1_rate6.grid(row=16, column=1, padx=10, pady=10, sticky="nsew")

        label_frame_rate1 = tk.Label(frame1, text='上一个SN：', font=('黑体', 12, "bold"), bg='skyblue', height=1)
        label_frame_rate2 = tk.Label(frame1, text='  本次SN：', font=('黑体', 12, "bold"), bg='skyblue', height=1)
        label_frame_rate3 = tk.Label(frame1, text=' OCR结果：', font=('黑体', 12, "bold"), bg='skyblue', height=1)
        label_frame_rate4 = tk.Label(frame1, text='', font=('Arial', 12), width=18, height=1, bg='red')
        label_frame_rate5 = tk.Label(frame1, text='', font=('Arial', 12), width=18, height=1)
        label_frame_rate6 = tk.Label(frame1, text='', font=('Arial', 12), width=18, height=1)
        label_frame_rate4.config(text='A2001021448325486')
        label_frame_rate4.grid(row=4, column=1, pady=10, sticky="nsew")
        label_frame_rate1.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")
        label_frame_rate2.grid(row=5, column=0, padx=10, pady=10, sticky="nsew")
        label_frame_rate3.grid(row=6, column=0, padx=10, pady=10, sticky="nsew")
        text_frame1_tips = tk.Label(frame1,
                                    text='如果点击开始后扫码枪为一天内的第一次开机，请等待扫码枪开机声音结束后再次点击开始比对按钮',
                                    font=(12), width=90, height=1, anchor='w')
        text_frame1_tips.grid(row=13, column=2, columnspan=2, sticky="w", padx=10, pady=10, )

        checkbutton = tk.Checkbutton(frame1, text="保存比对数据信息", variable=checked_val, state=DISABLED)
        checkbutton.grid(row=3, column=0, padx=10, pady=10, sticky="we")
        checkbutton = tk.Checkbutton(frame2, text="保存比对数据信息", variable=checked_val)  # , command=on_checked
        checkbutton.grid(row=11, column=0, padx=10, pady=10, sticky="we")

        leidiaobutton = tk.Checkbutton(frame1, text="镭雕机模式", state=DISABLED)
        leidiaobutton.grid(row=3, column=1, padx=10, pady=10, sticky="we")
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
            COMGUNNUM = xVariableCOM.get()
            previous_COMGUNNUM = COMGUNNUM


        COMLIST = getCOMS()
        COMGUN_list['value'] = COMLIST
        COMGUN_list.grid(row=12, column=1, padx=10, pady=10, sticky="we")
        COMGUN_list.bind("<<ComboboxSelected>>", changeCOMS)


        @logger.catch
        def comportfunction():
            global COMGUNNUM
            COMGUNNUM = xVariableCOM.get()
            if COMGUNNUM:  # and COMSIGNAL
                with open(compickle, 'wb') as f:
                    pickle.dump(COMGUNNUM, f)
                    # pickle.dump(COMSIGNALNUM,f)
                tkinter.messagebox.showinfo('show info', '提交成功！')
            else:
                tk.messagebox.showerror('show error', "请选择端口！")


        combutton = tk.Button(frame2, text='提交', bg='skyblue', width=10, height=1)  # , command=comportfunction
        combutton.grid(row=12, column=2, padx=10, pady=10, sticky="we")
        btn_save_jpg = tk.Button(frame1, text='开始比对', width=15, height=1)  # , command=start_long_task
        btn_save_jpg.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="we")
        videostream = tk.Label(frame1, text='实时视频流', font=('黑体', 12, "bold"), width=20, height=1)
        videostream.grid(row=2, column=3, padx=10, pady=10)
        picturescreen = tk.Label(frame1, text='本次样本', font=('黑体', 12, "bold"), width=20, height=1)
        picturescreen.grid(row=2, column=2, padx=10, pady=10)
        btn_get_parameter = tk.Button(frame2, text='获取参数', width=15, height=1)  # , command=get_parameter
        btn_get_parameter.grid(row=10, column=0, padx=10, pady=10, sticky="we")
        btn_set_parameter = tk.Button(frame2, text='设置参数', width=15, height=1)  # , command=set_parameter
        btn_set_parameter.grid(row=10, column=1, padx=10, pady=10, sticky="we")


        @logger.catch
        def look_picture():
            img = cv2.imread(parentdir)
            plt.subplot(111), plt.imshow(img),
            plt.title('Detected Point'), plt.axis('off')
            plt.show()


        @logger.catch
        def look_diff_picture():
            pic_path = current_file + 'image/diff_image.jpg'
            img = cv2.imread(pic_path)
            plt.subplot(111), plt.imshow(img),
            plt.title('Different Point'), plt.axis('off')
            plt.show()


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
            cv2.imwrite(save_path + '/line.jpg', cropped)


        @logger.catch
        def add_Template_picture():
            pic_save_dir_path = folder_path
            if not os.path.isdir(pic_save_dir_path):
                os.makedirs(pic_save_dir_path)
            left_left = int(left_left_text.get("1.0", "end-1c"))
            left_upper = int(left_upper_text.get("1.0", "end-1c"))
            right_left = int(right_left_text.get("1.0", "end-1c"))
            right_lower = int(right_lower_text.get("1.0", "end-1c"))
            if left_left == '' or left_upper == '' or right_left == '' or right_lower == '':
                messagebox.showinfo(title='提示', message='请输入模板图片位置')
            else:
                print(type(left_left))
                print(left_left, left_upper, right_left, right_lower)
                show_cut(parentdir, left_left, left_upper, right_left, right_lower)
                image_cut_save(parentdir, left_left, left_upper, right_left, right_lower, pic_save_dir_path)
            pass


        @logger.catch
        def look_this_picture():
            selected_item = listbox.get(listbox.curselection())
            if selected_item:
                file_path = os.path.join(folder_path, selected_item)
                img = cv2.imread(file_path)
                image_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                plt.subplot(111), plt.imshow(image_rgb),
                plt.title(selected_item), plt.axis('off')
                plt.show()


        @logger.catch
        def delete_this_picture():
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


        @logger.catch
        def refresh():
            listbox.delete(0, tk.END)
            image_files = [f for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            # 将图片文件名添加到列表框中
            for file in image_files:
                listbox.insert(tk.END, file)


        @logger.catch
        def on_mouse(event, x, y, flags, param):
            global screen_img, point1, point2, screenshotNum
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
                cv2.imshow('image', screen_img[cut_Pos[1][0]:cut_Pos[1][1], cut_Pos[0][0]:cut_Pos[0][1]])
                file_name = folder_path + f"\\screen_img_{screenshotNum + 1}.jpg"
                screenshotNum += 1
                cv2.imwrite(file_name, screen_img[cut_Pos[1][0]:cut_Pos[1][1], cut_Pos[0][0]:cut_Pos[0][1]])


        @logger.catch
        def screen_shot():
            global screenshotNum
            global screen_img
            screen_img = cv2.imread('image/test.jpg')
            cv2.namedWindow('image')
            cv2.setMouseCallback('image', on_mouse)
            cv2.imshow('image', screen_img)
            cv2.waitKey(0)


        @logger.catch
        def threshold_confirm():
            param1 = img_threshold_text.get(1.0, tk.END)
            param2 = binary_image_threshold_text.get(1.0, tk.END)
            param3 = kernel_threshold_text.get(1.0, tk.END)
            params = (param1, param2, param3)  # 将三个参数打包成元组
            if params:
                with open(thresholdpickle, "wb") as f:
                    pickle.dump(params, f)
                tkinter.messagebox.showinfo('show info', '提交成功！')
            else:
                tk.messagebox.showerror('show error', "填写数据！")


        btn_look_picture = tk.Button(frame2, text='查看目标图片', width=10, height=1, command=look_picture)  #
        btn_look_picture.grid(row=2, column=4, padx=10, pady=10, sticky="w")
        btn_add_picture = tk.Button(frame2, text='查看不同图片', width=12, height=1, command=look_diff_picture)  #
        btn_add_picture.grid(row=2, column=5, padx=10, pady=10, sticky="w")
        btn_add_template = tk.Button(frame2, text='添加模板图片', width=12, height=1, command=add_Template_picture)  #
        btn_add_template.grid(row=6, column=2, padx=10, pady=10, sticky="wens")
        btn_screenshot = tk.Button(frame2, text='目标位置截图', width=12, height=1, command=screen_shot)  #
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
        img_threshold = tk.Label(frame2, text='图片比对阈值', width=10, height=1)
        img_threshold.grid(row=8, column=2, padx=10, pady=10, sticky="e")
        img_threshold_text = tk.Text(frame2, width=10, height=1)
        img_threshold_text.grid(row=8, column=3, padx=10, pady=10, sticky="w")
        # 二值化阈值
        binary_image_threshold = tk.Label(frame2, text='二值化阈值', width=10, height=1)
        binary_image_threshold.grid(row=9, column=2, padx=10, pady=10, sticky="e")
        binary_image_threshold_text = tk.Text(frame2, width=10, height=1)
        binary_image_threshold_text.grid(row=9, column=3, padx=10, pady=10, sticky="w")
        # 卷积核
        kernel_threshold = tk.Label(frame2, text='卷积核', width=10, height=1)
        kernel_threshold.grid(row=10, column=2, padx=10, pady=10, sticky="e")
        kernel_threshold_text = tk.Text(frame2, width=10, height=1)
        kernel_threshold_text.grid(row=10, column=3, padx=10, pady=10, sticky="w")

        thresholdbutton = tk.Button(frame2, text='提交', bg='skyblue', width=10, height=1,
                                    command=threshold_confirm)  # , command=comportfunction
        thresholdbutton.grid(row=8, column=4, padx=10, pady=10, sticky="w")

        try:
            with open(thresholdpickle, "rb") as f:
                loaded_params = pickle.load(f)
                param1_loaded, param2_loaded, param3_loaded = loaded_params
                img_threshold_text.delete("1.0", "end")  # 清空Text组件
                img_threshold_text.insert("1.0", param1_loaded)
                binary_image_threshold_text.delete("1.0", "end")
                binary_image_threshold_text.insert("1.0", param2_loaded)
                kernel_threshold_text.delete("1.0", "end")
                kernel_threshold_text.insert("1.0", param3_loaded)
        except FileNotFoundError:
            img_threshold_text.delete("1.0", "end")  # 清空Text组件
            img_threshold_text.insert("1.0", '0')
            binary_image_threshold_text.delete("1.0", "end")
            binary_image_threshold_text.insert("1.0", '0')
            kernel_threshold_text.delete("1.0", "end")
            kernel_threshold_text.insert("1.0", '0')

        img_save_button = tk.Checkbutton(frame2, text="保存比对图片", variable=on_save_img_val,
                                         command=on_save_img)  # , command=on_checked
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


        @logger.catch()
        def changeImageMethods(event):
            global IMAGEMatchValue
            IMAGEMatchValue = xVariableMatch.get()
            if IMAGEMatchValue:
                with open(imagepickle, 'wb') as f:
                    pickle.dump(IMAGEMatchValue, f)
                tkinter.messagebox.showinfo('show info', '修改成功！')
            else:
                tk.messagebox.showerror('show error', "请选择方法！")


        @logger.catch()
        def on_closing():
            if messagebox.askokcancel("关闭窗口", "你确定要关闭窗口吗？"):
                # 执行其他关闭窗口前需要进行的操作
                with open(screenshot, 'wb') as f:
                    pickle.dump(screenshotNum, f)
                window.destroy()


        IMAGEMatch = tk.Label(frame2, text='图片匹配方法', width=10, height=1)
        IMAGEMatch.grid(row=7, column=2, padx=10, pady=10, sticky="e")
        xVariableMatch = tkinter.StringVar(value=IMAGEMatchValue)
        ImageMatch_list = ttk.Combobox(frame2, textvariable=xVariableMatch)
        methods = ['cv2.TM_CCOEFF_NORMED', 'cv2.TM_CCORR_NORMED', 'cv2.TM_SQDIFF_NORMED']
        ImageMatch_list['value'] = methods
        ImageMatch_list.grid(row=7, column=3, padx=10, pady=10, sticky="w")
        ImageMatch_list.bind("<<ComboboxSelected>>", changeImageMethods)
        window.bind("<space>", handle_space)
        window.protocol("WM_DELETE_WINDOW", on_closing)
        window.mainloop()
        try:
            win32event.ReleaseMutex(mutex)
            win32api.CloseHandle(mutex)
        except:
            pass
