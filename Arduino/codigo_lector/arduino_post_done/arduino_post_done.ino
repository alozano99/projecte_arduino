#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN 5
#define RST_PIN 22
#define BUZZER_PIN 26

const char* ssid = "DIGIFIBRA-E0EC";
const char* password = "MR43YY3M7Y";

const char* mqtt_server = "a3thxs542ooxbt-ats.iot.us-east-1.amazonaws.com";  
const int mqtt_port = 8883;
const char* mqtt_topic = "asix/fichajes";
const char* client_id = "asix_device_1";

// Certificados incrustados como strings
const char* ca_cert = R"EOF(
-----BEGIN CERTIFICATE-----
MIIDQTCCAimgAwIBAgITBmyfz5m/jAo54vB4ikPmljZbyjANBgkqhkiG9w0BAQsF
ADA5MQswCQYDVQQGEwJVUzEPMA0GA1UEChMGQW1hem9uMRkwFwYDVQQDExBBbWF6
b24gUm9vdCBDQSAxMB4XDTE1MDUyNjAwMDAwMFoXDTM4MDExNzAwMDAwMFowOTEL
MAkGA1UEBhMCVVMxDzANBgNVBAoTBkFtYXpvbjEZMBcGA1UEAxMQQW1hem9uIFJv
b3QgQ0EgMTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALJ4gHHKeNXj
ca9HgFB0fW7Y14h29Jlo91ghYPl0hAEvrAIthtOgQ3pOsqTQNroBvo3bSMgHFzZM
9O6II8c+6zf1tRn4SWiw3te5djgdYZ6k/oI2peVKVuRF4fn9tBb6dNqcmzU5L/qw
IFAGbHrQgLKm+a/sRxmPUDgH3KKHOVj4utWp+UhnMJbulHheb4mjUcAwhmahRWa6
VOujw5H5SNz/0egwLX0tdHA114gk957EWW67c4cX8jJGKLhD+rcdqsq08p8kDi1L
93FcXmn/6pUCyziKrlA4b9v7LWIbxcceVOF34GfID5yHI9Y/QCB/IIDEgEw+OyQm
jgSubJrIqg0CAwEAAaNCMEAwDwYDVR0TAQH/BAUwAwEB/zAOBgNVHQ8BAf8EBAMC
AYYwHQYDVR0OBBYEFIQYzIU07LwMlJQuCFmcx7IQTgoIMA0GCSqGSIb3DQEBCwUA
A4IBAQCY8jdaQZChGsV2USggNiMOruYou6r4lK5IpDB/G/wkjUu0yKGX9rbxenDI
U5PMCCjjmCXPI6T53iHTfIUJrU6adTrCC2qJeHZERxhlbI1Bjjt/msv0tadQ1wUs
N+gDS63pYaACbvXy8MWy7Vu33PqUXHeeE6V/Uq2V8viTO96LXFvKWlJbYK8U90vv
o/ufQJVtMVT8QtPHRh8jrdkPSHCa2XV4cdFyQzR1bldZwgJcJmApzyMZFo6IQ6XU
5MsI+yMRQ+hDKXJioaldXgjUkK642M4UwtBV8ob2xJNDd2ZhwLnoQdeXeGADbkpy
rqXRfboQnoZsG4q5WTP468SQvvG5
-----END CERTIFICATE-----
)EOF";

const char* client_cert = R"KEY(
-----BEGIN CERTIFICATE-----
MIIDWTCCAkGgAwIBAgIUdq1cot1Ru+e1yx3UeVrBA0kbc3owDQYJKoZIhvcNAQEL
BQAwTTFLMEkGA1UECwxCQW1hem9uIFdlYiBTZXJ2aWNlcyBPPUFtYXpvbi5jb20g
SW5jLiBMPVNlYXR0bGUgU1Q9V2FzaGluZ3RvbiBDPVVTMB4XDTI1MDYwNTEwMTIz
NloXDTQ5MTIzMTIzNTk1OVowHjEcMBoGA1UEAwwTQVdTIElvVCBDZXJ0aWZpY2F0
ZTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALjeOm0i9vhh05SEa5pL
0f4+l4V+qFBc/QHw3BtZq9dWwob79r2sVvqtJTRslZGZnoSwMBgbyX67Jw7Jx4LQ
Lj/PPIKp+Z9ZbFiF8ajsgWqL9pWgOL1zPGa7W9y2plAytg3FbkzwgMLzby1JgOvk
QMlOftVXNhbFoTvqblHXv1DkzlCSJfyRbUWeUZGMpxxI82ExhNYnsTR4KVr3Gp0e
7rVVZntZ+Elj6/ZGIm0I+r39WObpaXvl0xz8jBXRWSxqNiRppdodEeSJAfxKMezn
CtvLhbGarN8DtyWkmeNS69BDghSk288aaTcP/UK46OVddSvz3m0XZjU6j2s7WSju
6PsCAwEAAaNgMF4wHwYDVR0jBBgwFoAUfjZJv+VGqtUJdsuB/x8V8QK7GOgwHQYD
VR0OBBYEFLLCfxoqH3NVyE71r8/iOb7yxtHPMAwGA1UdEwEB/wQCMAAwDgYDVR0P
AQH/BAQDAgeAMA0GCSqGSIb3DQEBCwUAA4IBAQCrW3M574gXuccc6woAdwGy7qWY
jhLzXkDQ6aE5lvEnOh3S7d+0h9Mur0K0RlG26zAnAaOZOqS7rV6XDIgeQsXgI7+7
2YiE3V2cN6z7yF0zLVubfFvcnhVg7hMQ0Ti8syp1sVQJpP/5nKfqmmsxtuaambmZ
iI7HGLK4TM/0ZvWtoDbDz8b0L8JmSZLxMPxXie+tU4MrI76UbgDCxzHYiVntOXKc
q+zfkuK7U8YVmmf/IgCdlxWtaJZBEE+DIkVSNgWtTWyhVjybtjfpZy0TtFw78noL
TEfsDTTovts6rSsrfWCbj5BShiG+Yx45UBoekbxk3BDE4PHNjofFSsbeyhl8
-----END CERTIFICATE-----
)KEY";

const char* client_key = R"KEY(
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAuN46bSL2+GHTlIRrmkvR/j6XhX6oUFz9AfDcG1mr11bChvv2
vaxW+q0lNGyVkZmehLAwGBvJfrsnDsnHgtAuP888gqn5n1lsWIXxqOyBaov2laA4
vXM8Zrtb3LamUDK2DcVuTPCAwvNvLUmA6+RAyU5+1Vc2FsWhO+puUde/UOTOUJIl
/JFtRZ5RkYynHEjzYTGE1iexNHgpWvcanR7utVVme1n4SWPr9kYibQj6vf1Y5ulp
e+XTHPyMFdFZLGo2JGml2h0R5IkB/Eox7OcK28uFsZqs3wO3JaSZ41Lr0EOCFKTb
zxppNw/9Qrjo5V11K/PebRdmNTqPaztZKO7o+wIDAQABAoIBAQCOK1kDVUBZA+KS
9MNLhcOYosoj/6OxKdHpDDI5Vlyw3if7Zwn6E+9QGJfkGR1tO5aMtHJIGBZ9P7Bp
zwN/tlna+KSwV8eApGSOL3QJVNix97FKoE0CZPyuhKfAtTZxto4LSSnqQYrEYjG9
wilDP+YS6irgJpGSMaotSbxNdH3M1tjfvFHjzBd+WUxwCzksGUtsOkbo3isjUtj1
kZhtmwogbHKwMvluhNDb3WbHADhGh4Ip5MEi9Mlw1dopgNf0fNs4VkbbxuOPWSjj
Q8H9DhNYgVrYSl/qr1rW4kKrVWfw0pbYhEoQ36PS8yoB8dTjmXSywCnEBZrh86gt
f4f4mHcBAoGBAPGjc3BUJcwf5WD/D0wZ/UhSWKeN3gLwOMv3rodBAM5/WaBgzDyE
v2d5Cg+YOKJcKYyUs2bHUsuNDH0dULv7ul1ygV/Tv/Frtu47dW3Kj1ieouaIdmRu
8iXNj7eI9LAl99XkjKMnzeIMYRTI5d+09LnMTVLd02onzeB/UHLaqzuHAoGBAMPb
AtNm7VwtcGRqYn1ZUrNRyNaaLpj3YGEVX5XNTxeei1yh66Hqr5LKCyK84o2pLvBR
Cb5mSAkouobtozpB+RJzkNTON77/a43WtbHDVnmkRCe58CW1uHfLLKXRtmTrLT0d
6jWezC3WiJBvR8kzv+RvJf50NLYfOuUKmTIW1gvtAoGAGPFjYCv/ftOoDNwnSxa/
s3B0oE8fpLQBWOSnSmTmXWp96PU0/+ZAD8FJzZRL/E6BJ3bOEgTvQf28VUnqZI02
jqDcQ/UKsjQJPQw8Meof4+j0LdHWTsW5Dzfp5usnPuucaqLd9ZWNRhE7EDcwq2f1
fxxcuvoU8bdMJClgN4rk9A8CgYA76CuvGhaUUVnFfTzu9nlzXBrAeZyzMUeLqov4
ODpvERGznduDRVO65I4PbBMoHY27+C2wzXxPQOP9DYcV9MQIvsyYKxOmGl59niUp
YIR85J/sPtWT00e/bKgVeFX//Gd0AEh5aj8t7icLdt5QTsHtT4ohkM3mvxq2oE1H
ovCJ6QKBgQDRPu6ZCol7YWwx6sQoyo/Z6JAqxWklJKvu1TdC2NvwdyIcqSnQyKMy
m1S2tS9M5ZR8akRWDOAq27EkoNg2HIST9llwEm2kniRZfSUMhgnT6IvBFiCSfuia
AFHDiIrP+25VFZ3+cBMkZrQyRsiVpsAxgPxrTY2cnYYiWOyTf8/jYg==
-----END RSA PRIVATE KEY-----
)KEY";

// NFC y WiFi
MFRC522 mfrc522(SS_PIN, RST_PIN);
WiFiClientSecure net;
PubSubClient client(net);
bool tarjetaPresente = false;

void successBeep() {
  digitalWrite(BUZZER_PIN, HIGH);
  delay(200);
  digitalWrite(BUZZER_PIN, LOW);
}

void errorBeep() {
  for (int i = 0; i < 2; i++) {
    digitalWrite(BUZZER_PIN, HIGH);
    delay(100);
    digitalWrite(BUZZER_PIN, LOW);
    delay(100);
  }
}

void connectAWS() {
  net.setCACert(ca_cert);
  net.setCertificate(client_cert);
  net.setPrivateKey(client_key);
  client.setServer(mqtt_server, mqtt_port);

  while (!client.connected()) {
    Serial.println("Conectando a AWS IoT...");
    if (client.connect(client_id)) {
      Serial.println("✅ Conectado a AWS IoT");
    } else {
      Serial.print("❌ Falló conexión: ");
      Serial.println(client.state());
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  SPI.begin();
  mfrc522.PCD_Init();
  pinMode(BUZZER_PIN, OUTPUT);

  WiFi.begin(ssid, password);
  Serial.println("Conectando a WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ WiFi conectado");
  connectAWS();
}

void loop() {
  if (!client.connected()) {
    connectAWS();
  }
  client.loop();

  if (mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial()) {
    if (!tarjetaPresente) {
      tarjetaPresente = true;

      String uid = "";
      for (byte i = 0; i < mfrc522.uid.size; i++) {
        uid += String(mfrc522.uid.uidByte[i], HEX);
      }
      uid.toUpperCase();
      Serial.println("UID leído: " + uid);

      String payload = "{\"uid\":\"" + uid + "\"}";
      client.publish(mqtt_topic, payload.c_str());
      Serial.println("📤 UID publicado vía MQTT");
      successBeep();

      mfrc522.PICC_HaltA();
      mfrc522.PCD_StopCrypto1();

      delay(1000); // Espera para evitar lecturas duplicadas muy rápidas
    }
  } else {
    tarjetaPresente = false;  // Resetea si se retira la tarjeta
  }
}
