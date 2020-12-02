#Enter the configuration value of IoTCore
#Change the following values if necessary

#CertFile_Path
CERT_FOLDER_PATH = "./cert"
PATH_TO_CERT = "cert/certificate.pem.crt"
PATH_TO_KEY = "cert/private.pem.key"
PATH_TO_ROOT = "cert/root.pem"

#IoTCore_ConectionSetting
ENDPOINT = "IoTCore_CustomEndpoint"
CLIENT_ID = "IoTCore_ClientID"
THING_NAME = "IoTCore_ThingName"
TOPIC = "MQTT_MessagingTopic"
MQTT_PORT = 8883
USE_WEBSOCKET = False

#FleetProvisioning_ProvisioningConfig
PROVISIONING_TEMPLATE = "IoTCoreProvisioningtemplateName"
CERT_ROTATION_TEMPRATE ="IoTCoreCertRotationtemplateName"
