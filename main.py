from machine import Pin, PWM, ADC
import network
import machine
import time
import json
import _thread
import urequests

定时重启时间 = 3600
ssid = "**********"
passwd = "************"
ipv4域名 = "***.*******.***"
token = "****************************************"
检查延迟 = 60

def connectWiFi():
    global led
    """
    连接到WiFi网络
    """
    global wlan
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.disconnect()
    wlan.connect(ssid, passwd)
    while wlan.ifconfig()[0] == "0.0.0.0":
        print("connecting...")
        time.sleep(1)
        # led.value(0 if led.value() else 1)
    # led.value(1)


def 定时重启():
    global 定时重启时间
    time.sleep(定时重启时间)
    machine.reset()


def 当前ip():
    try:
        response = urequests.get("https://ddns.oray.com/checkip")
        return response.text.split(":")[-1].strip()
    except Exception as e:
        print(e)
        machine.reset()
        # return None


def 当前dns():
    global token
    global ipv4域名
    try:
        response = urequests.get(
            "https://api.cloudflare.com/client/v4/zones?name="
            + ipv4域名.split(".")[-2]
            + "."
            + ipv4域名.split(".")[-1],
            headers={"authorization": "Bearer " + token},
        )

        id = json.loads(response.text)["result"][0]["id"]
        response = urequests.get(
            "https://api.cloudflare.com/client/v4/zones/"
            + id
            + "/dns_records?type=A&name="
            + ipv4域名,
            headers={"authorization": "Bearer " + token},
        )

        return (
            id,
            json.loads(response.text)["result"][0]["id"],
            json.loads(response.text)["result"][0]["content"],
        )

    except Exception as e:
        print(e)
        machine.reset()


def 更新dns(zoneid, id, 新ip):
    global token
    global ipv4域名
    try:
        response = urequests.put(
            "https://api.cloudflare.com/client/v4/zones/"
            + zoneid
            + "/dns_records/"
            + id,
            headers={"authorization": "Bearer " + token},
            data=json.dumps(
                {
                    "type": "A",
                    "name": ipv4域名,
                    "content": 新ip,
                    "ttl": 1,
                }
            ).encode("utf-8"),
        )
        return json.loads(response.text)["success"]
    except Exception as e:
        print(e)
        machine.reset()
        # return False
def 循环():
    global 上次ip
    global 检查延迟
    ip = 当前ip()
    上次ip = ip
    print("ip:", ip)
    zid, did, dns = 当前dns()
    print("dns:", dns)
    while True:
        if dns != ip:
            res = 更新dns(zid, did, ip)
            if res:
                print("更新成功")
            else:
                print("更新失败")
                machine.reset()
        for i in range(5):
            ip = 当前ip()
            print("当前ip:", ip)
            if ip != 上次ip:
                上次ip = ip
                break
            time.sleep(检查延迟)
        zid, did, dns = 当前dns()
        print("当前dns:", dns)

if __name__ == "__main__":
    _thread.start_new_thread(定时重启, ())
    # led = Pin(2, Pin.OUT)
    connectWiFi()
    _thread.start_new_thread(循环, ())
    while True:
        if not wlan.isconnected():
            # for i in range(10):
            #     led.value(0 if led.value() else 1)
            #     time.sleep(0.2)
            machine.reset()
        time.sleep(1)
