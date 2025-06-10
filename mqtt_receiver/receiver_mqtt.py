import ssl
import json
import requests
from paho.mqtt.client import Client

AWS_ENDPOINT = "a3thxs542ooxbt-ats.iot.us-east-1.amazonaws.com" 
PORT = 8883
CLIENT_ID = "mqtt_receiver"
TOPIC = "asix/fichajes"

# Ruta absoluta o relativa a tus certificados
CA_PATH = "C:/Users/alexl/OneDrive/Escritorio/Proyecto_1/mqtt_receiver/certs/AmazonRootCA1.pem"
CERT_PATH = "C:/Users/alexl/OneDrive/Escritorio/Proyecto_1/mqtt_receiver/certs/8f3b763e1edb8f1eac0d9f83fa59a9937ca1ccd653d3604aad0f3ad511bf505e-certificate.pem.crt"
KEY_PATH = "C:/Users/alexl/OneDrive/Escritorio/Proyecto_1/mqtt_receiver/certs/8f3b763e1edb8f1eac0d9f83fa59a9937ca1ccd653d3604aad0f3ad511bf505e-private.pem.key"


BACKEND_URL = "http://localhost:8000/api/fichaje"  # o IP LAN si FastAPI no corre en localhost

def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Conectado con código {rc}")
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        uid = payload.get("uid")
        print(f"[MQTT] UID recibido: {uid}")
        if uid:
            response = requests.post(BACKEND_URL, json={"uid": uid})
            print(f"[POST] {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[ERROR] Procesando mensaje: {e}")

client = Client(client_id=CLIENT_ID)
client.tls_set(ca_certs=CA_PATH, certfile=CERT_PATH, keyfile=KEY_PATH, tls_version=ssl.PROTOCOL_TLSv1_2)
client.on_connect = on_connect
client.on_message = on_message

client.connect(AWS_ENDPOINT, PORT)
client.loop_forever()
