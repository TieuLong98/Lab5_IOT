print("IoT Gateway")
import paho.mqtt.client as mqttclient
import time
import json
import serial.tools.list_ports

BROKER_ADDRESS = "demo.thingsboard.io"
serial_data_available = 0
mqtt_data_available = 0
temp_data = ""
counter_failure = 0
ack_available = 0
MAX = 5
status = 0
timer_counter = 0
timer_flag = 0
PORT = 1883
mess = ""
cmd = 0
temperature = 0
lightning = 0
check = 0

# TODO: Add your token and your comport
# Please check the comport in the device manager
THINGS_BOARD_ACCESS_TOKEN = "jsc3EqiuI10DZsvfj7oe"
bbc_port = "COM7"
if len(bbc_port) > 0:
    ser = serial.Serial(port=bbc_port, baudrate=115200)


def setTimer(counter):
    global timer_counter, timer_flag
    timer_counter = counter
    timer_flag = 0


def cancelTimer():
    global timer_counter, timer_flag
    timer_counter = 0
    timer_flag = 0


def runTimer():
    global timer_counter, timer_flag
    if timer_counter > 0:
        timer_counter = timer_counter - 1
        if timer_counter <= 0:
            timer_flag = 1


def processData(data):
    global ack_available
    global serial_data_available
    serial_data_available = 1
    data = data.replace("!", "")
    data = data.replace("#", "")
    splitData = data.split(":")
    #print(splitData)
    # TODO: Add your source code to publish data to the server
    temp = 0
    light = 0
    if splitData[1] == "TEMP":
        temp = splitData[2]
        global temperature
        temperature = {'temperature': temp}
        client.publish('v1/devices/me/attributes', json.dumps(temperature), 1)

    if splitData[1] == "LIGHT":
        light = splitData[2]
        global lightning
        lightning = {'light': light}
        client.publish('v1/devices/me/attributes', json.dumps(lightning), 1)

    if splitData[1] == "CONFIRM":
        ack_available = 1



def readSerial():
    bytesToRead = ser.inWaiting()
    if (bytesToRead > 0):
        global mess
        mess = mess + ser.read(bytesToRead).decode("UTF-8")
        while ("#" in mess) and ("!" in mess):
            start = mess.find("!")
            end = mess.find("#")
            processData(mess[start:end + 1])
            if (end == len(mess)):
                mess = ""
            else:
                mess = mess[end + 1:]


def subscribed(client, userdata, mid, granted_qos):
    print("Subscribed...")


def recv_message(client, userdata, message):
    global mqtt_data_available
    mqtt_data_available = 1
    print("Received: ", message.payload.decode("utf-8"))
    global temp_data
    temp_data = {'value': True}
    global cmd
    # TODO: Update the cmd to control 2 devices
    try:
        jsonobj = json.loads(message.payload)
        if jsonobj['method'] == "setLed" and jsonobj['params'] is True:
            cmd = 1
        if jsonobj['method'] == "setLed" and jsonobj['params'] is False:
            cmd = 2
        if jsonobj['method'] == "setFan" and jsonobj['params'] is True:
            cmd = 3
        if jsonobj['method'] == "setFan" and jsonobj['params'] is False:
            cmd = 4
        temp_data['value'] = jsonobj['params']
        client.publish('v1/devices/me/attributes', json.dumps(temp_data), 1)
    except:
        pass

    #if len(bbc_port) > 0:
    #    ser.write((str(cmd) + "#").encode())


def connected(client, usedata, flags, rc):
    if rc == 0:
        print("Thingsboard connected successfully!!")
        client.subscribe("v1/devices/me/rpc/request/+")
    else:
        print("Connection is failed")


def send_ack():
    ser.write(("ACK_RECEIVED" + "#").encode())


def send_data():
    ser.write((str(cmd) + "#").encode())


client = mqttclient.Client("Gateway_Thingsboard")
client.username_pw_set(THINGS_BOARD_ACCESS_TOKEN)

client.on_connect = connected
client.connect(BROKER_ADDRESS, 1883)
client.loop_start()

client.on_subscribe = subscribed
client.on_message = recv_message

while True:
    if len(bbc_port) > 0:
        readSerial()

    print("Current Status: ", status)

    if status == 0:
        if serial_data_available == 1:
            serial_data_available = 0
            status = 1
        if mqtt_data_available == 1:
            mqtt_data_available = 0
            status = 2

    elif status == 1:
        send_ack()
        status = 0

    elif status == 2:
        #readSerial()
        send_data()
        print("Send data: ", counter_failure + 1, "times")
        if check == 0:
            setTimer(3)
            check = 1
        status = 3

    elif status == 3:
        if ack_available == 1:
            print("ACK_RECEIVED_SUCCESSFUL")
            cancelTimer()
            counter_failure = 0
            status = 0
        if timer_flag == 1:
            counter_failure += 1
            check = 0
            if counter_failure < MAX:
                status = 2
            if counter_failure >= MAX:
                status = 4

    elif status == 4:
        status = 0
        counter_failure = 0
        print("!!!Failure NO ACK_RECEIVED!!!")

    else:
        print("Error Status: ", status)

    runTimer()
    time.sleep(1)
