# -- coding: utf-8 --
import sys
from tkinter import *
from tkinter.messagebox import *
import _tkinter
import tkinter.messagebox
import tkinter as tk
import sys, os
from tkinter import ttk
from MvImport.MvCameraControl_class import *
import datetime
from CamOperation_class import *
from PIL import Image, ImageTk
import serial
import csv
import cnocr
from cnocr import CnOcr
import threading
import pickle
import win32event
import win32api
import winerror
import pandas as pd
from loguru import logger
import concurrent.futures
import serial.tools.list_ports

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
    stop_grabbing()
    show_frame(frame)
    start_grabbing1()


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
        login_win.geometry('300x200+300+300')
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
        labelORIGIN.place(x=40, y=350)
        time.sleep(0.1)
        labelORIGIN.place_forget()
        labelNG.place_forget()
        # print("ok放置了一次")
        labelOK.place(x=40, y=350)
    else:
        labelORIGIN.place(x=40, y=350)
        time.sleep(0.1)
        labelORIGIN.place_forget()
        labelOK.place_forget()
        # print("ng放置了一次")
        labelNG.place(x=40, y=350)


@logger.catch
def handle_space(event):
    labelORIGIN.place_forget()
    labelOK.place_forget()
    labelNG.place_forget()
    labelORIGIN.place(x=40, y=350)


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
        # 界面设计代码
        window = tk.Tk()
        window.title('条码比对系统')
        window.iconbitmap(current_file + 'logo.ico')
        window.geometry('1650x800')
        # window.grid_rowconfigure(0, weight=1)
        # window.grid_columnconfigure(0, weight=1)
        # window.grid_columnconfigure(1, weight=1)
        # window.grid_rowconfigure(0, weight=1)
        # window.grid_columnconfigure(2, weight=1)
        # window.grid_rowconfigure(0, weight=1)
        main_menu = tk.Menu(window)
        picklename = 'settings.dat'
        picklename1 = 'parameter.dat'
        compickle = 'comport.dat'
        signaldata = 'signal.dat'
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
            with open(compickle, 'rb') as f:
                COMGUNNUM = pickle.load(f)
                # COMSIGNALNUM=pickle.load(f)
        except:
            COMGUNNUM = ""
            # COMSIGNALNUM=""
        global frame1
        frame1 = tk.Frame(window, width=1650, height=800)
        frame2 = tk.Frame(window, width=1650, height=800)
        main_menu.add_command(label="比对界面", command=lambda: show_mianframe(frame1))
        main_menu.add_command(label="管理员界面", command=lambda: show_login_page(frame2))
        window.config(menu=main_menu)
        window.grid_rowconfigure(0, weight=1)
        window.grid_columnconfigure(0, weight=1)
        frame1.grid(row=0, column=0, sticky="nsew")
        frame2.grid(row=0, column=0, sticky="nsew")
        frame1.tkraise()
        checked_val = tk.BooleanVar()
        checked_val.set(checked)
        model_val = tk.StringVar()
        global triggercheck_val
        triggercheck_val = tk.IntVar()
        page = Frame(frame2, height=800, width=1650, relief=GROOVE, borderwidth=4)
        page1 = Frame(frame1, height=800, width=1650, relief=GROOVE, borderwidth=4)
        page.pack(expand=True, fill=BOTH)
        page1.pack(expand=True, fill=BOTH)
        panel = Label(page)
        panel1 = Label(page1)
        panel.place(x=900, y=20, height=600, width=800)
        panel1.place(x=900, y=20, height=600, width=800)
        global labelOK
        global labelNG
        global labelORIGIN
        labelOK = tk.Label(frame1, text="OK", background="green", font=('黑体', 40, 'bold'), padx=80, pady=80)
        labelNG = tk.Label(frame1, text="NG", background="red", font=('黑体', 40, 'bold'), padx=80, pady=80)
        labelORIGIN = tk.Label(frame1, background="white", padx=108, pady=98)
        # labelOK.place(x=50, y=400)
        canvas = tk.Canvas(frame1, width=640, height=480, bg='gray')
        canvas.place(x=300, y=82)
        try:
            image = Image.open(parentdir)
        except:
            image = Image.open(current_file + 'logo.ico')
        photo = ImageTk.PhotoImage(image.resize((640, 480), Image.LANCZOS))
        image_item = canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        # print(parentdir)
        ocr = CnOcr(rec_model_name='densenet_lite_136-gru', det_model_name='en_PP-OCRv3_det')
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
            devicestatuclose.place_forget()
            devicestatucl.place_forget()
            devicestatuop.place(x=300, y=20)
            devicestatuopen.place(x=300, y=100)


        # ch:开始取流 | en:Start grab image

        @logger.catch
        def start_grabbing():
            global obj_cam_operation
            obj_cam_operation.Start_grabbing(frame2, panel)


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
            devicestatuopen.place_forget()
            devicestatuop.place_forget()
            devicestatucl.place(x=300, y=20)
            devicestatuclose.place(x=300, y=100)


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
                if(serialdata!=''):
                    return serialdata
                else:
                    pass
                    # print('串口传了一次数据')

            except:
                time.sleep(1)  # 等待1秒后重试
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
                max_length_dict = None
                for i in res:
                    if sub in i['text'] or nub in i['text'] and len(i['text']) >= 17:
                        if sub in i['text'] and len(i['text']) <= 21:
                            firstSnCode = i['text']
                            tempcode = ''.join(str(firstSnCode).split())
                            SnCode = tempcode[3:].replace(" ", "")
                            position = i['position']
                            # print(SnCode, 'subsubsubsubsub')
                            # print(len(SnCode))
                        else:
                            try:
                                second_coourenceN = i['text'].index(serachnum, i['text'].index(serachnum) + 1)
                                SnCode = str(i['text'][second_coourenceN + len(serachnum):]).replace(" ", "")
                                position = i['position']
                                # print(SnCode, 'trytrytrytrytry')
                            except:
                                firstSnCode = i['text']
                                tempcode = ''.join(str(firstSnCode).split())
                                SnCode = tempcode[-17:].replace(" ", "")
                                position = i['position']
                                # print(SnCode, 'exceptexceptexceptexcept')  # 特殊情况取后十七位
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

            elif SnCode:
                preCode = SnCode[:1]
                nextSnCode = SnCode[1:]
                SnCode = (preCode + str(nextSnCode).replace('O', '0'))
            else:
                SnCode = '没有找到数据'
                position = np.zeros((4, 2))
            return SnCode, position


        @logger.catch
        def jpg_save1():
            global obj_cam_operation
            obj_cam_operation.b_save_jpg1 = True
            # comflag = obj_cam_operation.comflag
            # return comflag


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
                    # print('getSerialdata执行了一次')
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
                    label_frame_rate4.place(x=120, y=200)
                    label_frame_rate5.config(text=serialdata)
                    label_frame_rate5.place(x=120, y=240)
                    label_frame_rate6.config(text=SnCode)
                    label_frame_rate6.place(x=120, y=280)
                    canvas.delete(rect)
                    image1 = Image.open(parentdir)
                    photo1 = ImageTk.PhotoImage(image1.resize((640, 480), Image.LANCZOS))
                    canvas.itemconfig(image_item, image=photo1)
                    canvas.update()
                    # print("图片更新了")
                    if serialdata == lastresult:
                        # print("请更换下一个")
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
                    text_frame1_rate4.place(x=110, y=600)
                    text_frame1_rate5.config(text=result_list[1])
                    text_frame1_rate5.place(x=110, y=640)
                    text_frame1_rate6.config(text=result_list[2])
                    text_frame1_rate6.place(x=110, y=680)
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


        @logger.catch
        def start_jpg_save1():
            t=threading.Thread(target=jpg_save1())
            t.daemon=True
            t.start()
            t.join()

        @logger.catch
        def updateimg(position):
            if np.all(position != 0):
                image = cv2.imread(parentdir)
                color = (0, 255, 0)
                x, y, w, h = cv2.boundingRect(position)
                # cv2.rectangle(image,(x-15,y-10),(x+w+5,y+h+5),color,6)
                cv2.rectangle(image, (x, y), (x + w, y + h), color, 6)
                cv2.imwrite(current_file + "image\\111.jpg", image)
            else:
                pass


        @logger.catch
        def showimg():
            canvas.place(x=300, y=82)


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
        device_list = ttk.Combobox(frame2, textvariable=xVariable, width=30)
        device_list.place(x=20, y=20)
        device_list.bind("<<ComboboxSelected>>", xFunc)
        devicestatuopen = tk.Label(frame2, text='设备处于打开状态,请直接点击开始抓取', bg='skyblue', width=30, height=1)
        devicestatuclose = tk.Label(frame2, text='设备处于关闭状态,请点击打开设备再点击开始抓取', bg='skyblue',
                                    width=40, height=1)
        devicestatucl = tk.Label(frame1, text='设备已关闭', bg='skyblue', width=10, height=1)
        devicestatuop = tk.Label(frame1, text='设备已开启', bg='skyblue', width=10, height=1)
        # 需要解开
        enum_devices()
        time.sleep(1)
        open_device()
        start_grabbing1()

        # commonuser
        xVariable1 = tkinter.StringVar()
        device_list1 = ttk.Combobox(frame1, textvariable=xVariable, width=30)
        device_list1.place(x=20, y=20)
        device_list1.bind("<<ComboboxSelected>>", xFunc)

        label_exposure_time = tk.Label(frame2, text='曝光时间', width=15, height=1)
        label_exposure_time.place(x=20, y=350)
        text_exposure_time = tk.Text(frame2, width=15, height=1)
        text_exposure_time.place(x=160, y=350)

        label_gain = tk.Label(frame2, text='增益', width=15, height=1)
        label_gain.place(x=20, y=400)
        text_gain = tk.Text(frame2, width=15, height=1)
        text_gain.place(x=160, y=400)

        label_frame_rate = tk.Label(frame2, text='帧速率', width=15, height=1)
        label_frame_rate.place(x=20, y=450)
        text_frame_rate = tk.Text(frame2, width=15, height=1)
        text_frame_rate.place(x=160, y=450)

        btn_enum_devices = tk.Button(frame2, text='发现设备', width=35, height=1, command=enum_devices)
        btn_enum_devices.place(x=20, y=50)

        # commonuser
        btn_open_device = tk.Button(frame2, text='打开设备', width=15, height=1, command=open_device)
        btn_open_device.place(x=20, y=100)

        btn_close_device = tk.Button(frame2, text='关闭设备', width=15, height=1, command=close_device)
        btn_close_device.place(x=160, y=100)

        radio_continuous = tk.Radiobutton(frame2, text='持续性抓取', variable=model_val, value='continuous', width=15,
                                          height=1, command=set_triggermode)
        radio_continuous.place(x=20, y=150)

        radio_trigger = tk.Radiobutton(frame2, text='触发模式', variable=model_val, value='triggermode', width=15,
                                       height=1, command=set_triggermode)
        radio_trigger.place(x=160, y=150)
        model_val.set(1)

        btn_start_grabbing = tk.Button(frame2, text='开始抓取', width=15, height=1, command=start_grabbing)
        btn_start_grabbing.place(x=20, y=200)

        btn_stop_grabbing = tk.Button(frame2, text='停止抓取', width=15, height=1, command=stop_grabbing)
        btn_stop_grabbing.place(x=160, y=200)

        checkbtn_trigger_software = tk.Checkbutton(frame2, text='Tigger by Software', variable=triggercheck_val,
                                                   onvalue=1, offvalue=0)
        checkbtn_trigger_software.place(x=20, y=250)
        btn_trigger_once = tk.Button(frame2, text='触发一次', width=15, height=1, command=trigger_once)
        btn_trigger_once.place(x=160, y=250)

        btn_save_bmp = tk.Button(frame2, text='Save as BMP', width=15, height=1, command=bmp_save)
        btn_save_bmp.place(x=20, y=300)
        btn_save_jpg = tk.Button(frame2, text='Save as JPG', width=15, height=1, command=jpg_save)
        btn_save_jpg.place(x=160, y=300)
        label_frame1_all = tk.Label(frame1, text='总数量：', bg='skyblue', width=8, height=1, anchor='e')
        label_frame1_ng = tk.Label(frame1, text='不良数量：', bg='skyblue', width=8, height=1, anchor='e')
        label_frame1_per = tk.Label(frame1, text='可靠率：', bg='skyblue', width=8, height=1, anchor='e')
        text_frame1_rate4 = tk.Label(frame1, text='', width=20, height=1, anchor='w')
        text_frame1_rate5 = tk.Label(frame1, text='', width=16, height=1, anchor='w')
        text_frame1_rate6 = tk.Label(frame1, text='', width=8, height=1, anchor='w')
        label_frame1_all.place(x=40, y=600)
        label_frame1_ng.place(x=40, y=640)
        label_frame1_per.place(x=40, y=680)
        try:
            with open(picklename1, 'rb') as f:
                ok_count = pickle.load(f)
                ng_count = pickle.load(f)
                all_count = pickle.load(f)
                text_frame1_rate4.config(text=ok_count)
                text_frame1_rate4.place(x=110, y=600)
                text_frame1_rate5.config(text=ng_count)
                text_frame1_rate5.place(x=110, y=640)
                text_frame1_rate6.config(text=all_count)
                text_frame1_rate6.place(x=110, y=680)
        except:
            result_list = ['0', '0', '0%']
            text_frame1_rate4.config(text=result_list[0])
            text_frame1_rate4.place(x=110, y=600)
            text_frame1_rate5.config(text=result_list[1])
            text_frame1_rate5.place(x=110, y=640)
            text_frame1_rate6.config(text=result_list[2])
            text_frame1_rate6.place(x=110, y=680)

        label_frame_rate1 = tk.Label(frame1, text='上一个SN：', font=('黑体', 12, "bold"), bg='skyblue', width=10,
                                     height=1)
        label_frame_rate2 = tk.Label(frame1, text='  本次SN：', font=('黑体', 12, "bold"), bg='skyblue', width=10,
                                     height=1)
        label_frame_rate3 = tk.Label(frame1, text=' OCR结果：', font=('黑体', 12, "bold"), bg='skyblue', width=10,
                                     height=1)
        label_frame_rate4 = tk.Label(frame1, text='', font=('Arial', 12), width=18, height=1)
        label_frame_rate5 = tk.Label(frame1, text='', font=('Arial', 12), width=18, height=1)
        label_frame_rate6 = tk.Label(frame1, text='', font=('Arial', 12), width=18, height=1)
        label_frame_rate1.place(x=20, y=200)
        label_frame_rate2.place(x=20, y=240)
        label_frame_rate3.place(x=20, y=280)
        text_frame1_tips = tk.Label(frame1,
                                    text='如果点击开始后扫码枪为一天内的第一次开机，请等待扫码枪开机声音结束后再次点击开始比对按钮',
                                    font=(18), width=90, height=1, anchor='w')
        text_frame1_tips.place(x=300, y=600)

        checkbutton = tk.Checkbutton(frame1, text="保存比对数据信息", variable=checked_val, state=DISABLED)
        checkbutton.place(x=80, y=120)
        checkbutton = tk.Checkbutton(frame2, text="保存比对数据信息", variable=checked_val, command=on_checked)
        checkbutton.place(x=20, y=540)


        def getCOMS():
            all_comports = serial.tools.list_ports.comports()
            available_ports = []
            for comport in all_comports:
                available_ports.append(comport.device)
            return available_ports


        COMGUN = tk.Label(frame2, text='扫码枪端口', width=8, height=1)
        COMGUN.place(x=20, y=590)
        xVariableCOM = tkinter.StringVar(value=COMGUNNUM)
        COMGUN_list = ttk.Combobox(frame2, textvariable=xVariableCOM, width=8)


        def changeCOMS(event):
            global COMGUNNUM
            global previous_COMGUNNUM
            COMGUNNUM = xVariableCOM.get()
            previous_COMGUNNUM = COMGUNNUM


        COMLIST = getCOMS()
        COMGUN_list['value'] = COMLIST
        COMGUN_list.place(x=120, y=590)
        COMGUN_list.bind("<<ComboboxSelected>>", changeCOMS)


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


        combutton = tk.Button(frame2, text='提交', bg='skyblue', width=10, height=1, command=comportfunction)
        combutton.place(x=200, y=590)

        btn_save_jpg = tk.Button(frame1, text='开始比对', width=15, height=1, command=start_long_task)
        btn_save_jpg.place(x=80, y=80)

        videostream = tk.Label(frame1, text='实时视频流', font=('黑体', 12, "bold"), width=20, height=1)
        videostream.place(x=1200, y=50)
        picturescreen = tk.Label(frame1, text='本次样本', font=('黑体', 12, "bold"), width=20, height=1)
        picturescreen.place(x=500, y=50)

        btn_get_parameter = tk.Button(frame2, text='获取参数', width=15, height=1, command=get_parameter)
        btn_get_parameter.place(x=20, y=500)
        btn_set_parameter = tk.Button(frame2, text='设置参数', width=15, height=1, command=set_parameter)
        btn_set_parameter.place(x=160, y=500)
        # window.state("zoomed")

        window.bind("<space>", handle_space)

        window.mainloop()
        try:
            win32event.ReleaseMutex(mutex)
            win32api.CloseHandle(mutex)
        except:
            pass
