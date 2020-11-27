from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import time
import json
import argparse
from cert.AWS_conf import AWS_conf as conf
# Global variables
UpdateCount = 10
# Read in AWSconf
host = conf.ENDPOINT
rootCAPath = conf.PATH_TO_ROOT
certificatePath = conf.PATH_TO_CERT
privateKeyPath = conf.PATH_TO_KEY
port = conf.MQTT_PORT
useWebsocket = conf.USE_WEBSOCKET
thingName = conf.THING_NAME
clientId = conf.CLIENT_ID
topic = conf.TOPIC

# Custom Shadow callback
def customShadowCallback_Get(payload, responseStatus, token):
    global UpdateCount
    if responseStatus == "timeout":
        print("get request " + token + " time out!")
    if responseStatus == "accepted":
        payloadDict = json.loads(payload)
        UpdateCount = payloadDict["state"]["desired"]["UpdateCount"]
        print("~~~~~~~~~~~~~~~~~~~~~~~")
        print("Get request with token: " + token + " accepted!")
        print(str(payloadDict["state"]))
        print("~~~~~~~~~~~~~~~~~~~~~~~\n")
    if responseStatus == "rejected":
        print("Update request " + token + " rejected!")

def customShadowCallback_Update(payload, responseStatus, token):
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
    if responseStatus == "timeout":
        print("Update request " + token + " time out!")
    if responseStatus == "accepted":
        payloadDict = json.loads(payload)
        print("~~~~~~~~~~~~~~~~~~~~~~~")
        print("Update request with token: " + token + " accepted!")
        print("property: " + str(payloadDict["state"]))
        print("~~~~~~~~~~~~~~~~~~~~~~~\n")
    if responseStatus == "rejected":
        print("Update request " + token + " rejected!")

# Init AWSIoTMQTTShadowClient
myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(clientId)
myAWSIoTMQTTShadowClient.configureEndpoint(host, port)
myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)
# AWSIoTMQTTShadowClient configuration
myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5)  # 5 sec
# Connect to AWS IoT
# Create a deviceShadow with persistent subscription
deviceShadowHandler = myAWSIoTMQTTShadowClient.createShadowHandlerWithName(thingName, True)
myAWSIoTMQTTShadowClient.connect()

# UpdateShadow & MessageSend in a loop
loopCount = 0
while True:
    loopCount = loopCount+1
    JSONPayload = '{"state":{"reported":{"MessageCount":' + str(loopCount) + '}}}'
    data = "{} [{}]".format("RaspberryPi_SendMessage", loopCount)
    message = {"message" : data}

    try:
        deviceShadowHandler.shadowGet(customShadowCallback_Get, 5)
        deviceShadowHandler.shadowUpdate(JSONPayload,customShadowCallback_Update, 5)
    except:
        print("ShadowUpdate_Error!!")
    try:
        myAWSIoTMQTTShadowClient.getMQTTConnection().publish(topic, json.dumps(message), 1)
        print("Published: '" + json.dumps(message) + "' to the topic: " + "'test/testing'")
    except:
        print("MQTTMessagePublish_Error!!")

    print("NextGetshadow "+str(UpdateCount)+"sec After")
    time.sleep(UpdateCount)
