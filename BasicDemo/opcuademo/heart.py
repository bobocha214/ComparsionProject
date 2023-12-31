import time

from opcua import Client, ua

client = Client("opc.tcp://127.0.0.1:4840")
client.connect()
client.load_type_definitions()  # load definition of server specific structures/extension objects
takephoto_NUM='ns=2;s=factory_1/line1/D311'
finalresult_NUM='ns=2;s=factory_1/line1/D312'
timeout = 10  # 设置超时时间为10秒
last_heartbeat_time = time.time()  # 记录上次接收到心跳信号的时间
heartbeat = client.get_node("ns=4;s=TD38_Rec.D00")
class SubHandler(object):

    """
    Client to subscription. It will receive events from server
    """

    def datachange_notification(self, node, val, data):
        print("Python: New data change event", node, val)

    def event_notification(self, event):
        print("Python: New event", event)
def subscribe_nodes():
    handler = SubHandler()
    myvar=client.get_node("ns=4;s=TD38_Rec.D03")
    sub = client.create_subscription(500, handler)
    handle = sub.subscribe_data_change(myvar)
    time.sleep(0.1)
def send_heartbeat():
    last_heartbeat_time = time.time()  # 记录上次接收到心跳信号的时间
    subscribe_nodes()
    while True:
        current_time = time.time()  # 获取当前时间
        elapsed_time = current_time - last_heartbeat_time  # 计算与上次心跳信号的时间间隔
        # 如果超过了设定的超时时间，则触发报错操作
        if elapsed_time >= timeout:
            print('show info', '心跳超时，请检查设备！')
        heartbeat_value = heartbeat.get_value()
        print(heartbeat_value)
        if (heartbeat_value == 100):
            write_value = ua.DataValue(ua.Variant(200, ua.VariantType.Int16))
            heartbeat.set_value(write_value)
        elif (heartbeat_value == 200):
            write_value = ua.DataValue(ua.Variant(100, ua.VariantType.Int16))
            heartbeat.set_value(write_value)
        last_heartbeat_time = current_time  # 更新上次接收到心跳信号的时间
        time.sleep(2)  # 等待1秒钟，避免频繁发送心跳

def send_order_to_zero():
    global client
    write_value_zero = ua.DataValue(ua.Variant(0, ua.VariantType.Int16))
    take_photo_NUM_flag = client.get_node(takephoto_NUM)
    final_result_NUM_flag = client.get_node(finalresult_NUM)
    temp_take_photo_NUM = take_photo_NUM_flag.get_value()
    temp_final_result_NUM = final_result_NUM_flag.get_value()
    if temp_take_photo_NUM != 0:
        take_photo_NUM_flag.set_value(write_value_zero)
    if temp_final_result_NUM != 0:
        final_result_NUM_flag.set_value(write_value_zero)

send_order_to_zero()
