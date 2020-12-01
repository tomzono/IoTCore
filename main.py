# ------------------------------------------------------------------------------
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
# -----------------------------------------
# Consuming sample, demonstrating how a device process would leverage the provisioning class.
#  The handler makes use of the asycio library and therefore requires Python 3.7.
#
#  Prereq's:
#      1) A provisioning claim certificate has been cut from AWSIoT.
#	   2) A restrictive "birth" policy has been associated with the certificate.
#      3) A provisioning template was created to manage the activities to be performed during new certificate activation.
#	   4) The claim certificate was placed securely on the device fleet and shipped to the field. (along with root/ca and private key)
#
#  Execution:
#      1) The paths to the certificates, and names of IoTCore endpoint and provisioning template are set in config.ini (this project)
#	   2) A device boots up and encounters it's "first run" experience and executes the process (main) below.
# 	   3) The process instatiates a handler that uses the bootstrap certificate to connect to IoTCore.
#	   4) The connection only enables calls to the Foundry provisioning services, where a new certificate is requested.
#      5) The certificate is assembled from the response payload, and a foundry service call is made to activate the certificate.
#	   6) The provisioning template executes the instructions provided and the process rotates to the new certificate.
#      7) Using the new certificate, a pub/sub call is demonstrated on a previously forbidden topic to test the new certificate.
#      8) New certificates are saved locally, and can be stored/consumed as the application deems necessary.
#
#
# Initial version - Raleigh Murch, AWS
# email: murchral@amazon.com
# ------------------------------------------------------------------------------
import AWS_conf as conf
import socket
from provisioning_handler import ProvisioningHandler
from utils.config_loader import Config
from pyfiglet import Figlet



#Set Config path
thingName = socket.gethostname()
bootstrap_cert = conf.PATH_TO_CERT
host = conf.ENDPOINT
rootCAPath = conf.PATH_TO_ROOT
certificatePath = "cert/{}-certificate.pem.crt".format(thingName)
privateKeyPath = "cert/{}-private.pem.key".format(thingName)
port = conf.MQTT_PORT
useWebsocket = conf.USE_WEBSOCKET
clientId = conf.CLIENT_ID
topic = conf.TOPIC

# Demo Theater
f = Figlet(font='slant')
print(f.renderText('      F l e e t'))
print(f.renderText('Provisioning'))
print(f.renderText('----------'))

# Provided callback for provisioning method feedback.
def callback(payload):
    print(payload)

# Used to kick off the provisioning lifecycle, exchanging the bootstrap cert for a
# production certificate after being validated by a provisioning hook lambda.
#
# isRotation = True is used to rotate from one production certificate to a new production certificate.
# Certificates signed by AWS IoT Root CA expire on 12/31/2049. Security best practices
# urge frequent rotation of x.509 certificates and this method (used in conjunction with
# a cloud cert management pattern) attempts to make cert exchange easy.
def run_provisioning(isRotation):

    provisioner = ProvisioningHandler()

    if isRotation:
        provisioner.get_official_certs(callback, isRotation=True)
    else:
        #Check for availability of bootstrap cert
        try:
             with open("{}".format(bootstrap_cert)) as f:
                # Call super-method to perform aquisition/activation
                # of certs, creation of thing, etc. Returns general
                # purpose callback at this point.
                # Instantiate provisioning handler, pass in path to config
                provisioner.get_official_certs(callback)

        except IOError:
            print("### Bootstrap cert non-existent. Official cert may already be in place.")

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


if __name__ == "__main__":
    run_provisioning(isRotation=False)

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
