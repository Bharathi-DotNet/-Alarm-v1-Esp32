#include <Arduino.h>
#include <Wire.h>
#include <RTClib.h>

#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>

#include <Preferences.h>

RTC_DS3231 rtc;

Preferences preferences;

#define SERVICE_UUID        "12345678-1234-1234-1234-1234567890ab"
#define CHARACTERISTIC_UUID "abcd1234-1234-1234-1234-abcdef123456"

const int buzzerPin = 23;

int alarmHour = 22;
int alarmMinute = 44;

bool alarmTriggered = false;
bool alarmCompleted = false;
bool alarmEnabled = true;


class AlarmServerCallbacks : public BLEServerCallbacks
{
    void onConnect(BLEServer *pServer) override
    {
        Serial.println("BLE client connected!");
    }

    void onDisconnect(BLEServer *pServer) override
    {
        Serial.println("BLE client disconnected!");

        delay(500);

        BLEDevice::startAdvertising();

        Serial.println("BLE advertising restarted!");
    }
};

class AlarmCommandCallback : public BLECharacteristicCallbacks
{
    void onWrite(BLECharacteristic *pCharacteristic) override
    {
        String command = pCharacteristic->getValue().c_str();

        command.trim();

        Serial.print("BLE Command Received: ");
        Serial.println(command);


        // =========================
        // STOP ALARM
        // =========================
        if (command == "STOP")
        {
            alarmTriggered = false;
            alarmCompleted = true;

            digitalWrite(
                buzzerPin,
                LOW
            );

            Serial.println(
                "Alarm stopped through BLE!"
            );
        }


        // =========================
        // GET CURRENT ALARM STATE
        // Response:
        // STATE:07:30:1
        // =========================
        else if (command == "GET")
        {
            String response = "STATE:";

            if (alarmHour < 10)
            {
                response += "0";
            }

            response += String(alarmHour);

            response += ":";

            if (alarmMinute < 10)
            {
                response += "0";
            }

            response += String(alarmMinute);

            response += ":";

            response += alarmEnabled
                ? "1"
                : "0";


            pCharacteristic->setValue(
                response.c_str()
            );


            Serial.print(
                "State sent: "
            );

            Serial.println(
                response
            );
        }


        // =========================
        // ENABLE ALARM
        // =========================
        else if (command == "ENABLE")
        {
            alarmEnabled = true;

            alarmCompleted = false;
            alarmTriggered = false;

            preferences.putBool(
                "enabled",
                true
            );

            Serial.println(
                "Alarm enabled!"
            );

            Serial.println(
                "Alarm enabled state saved to NVS!"
            );
        }


        // =========================
        // DISABLE ALARM
        // =========================
        else if (command == "DISABLE")
        {
            alarmEnabled = false;

            alarmTriggered = false;
            alarmCompleted = false;

            digitalWrite(
                buzzerPin,
                LOW
            );

            preferences.putBool(
                "enabled",
                false
            );

            Serial.println(
                "Alarm disabled!"
            );

            Serial.println(
                "Alarm disabled state saved to NVS!"
            );
        }


        // =========================
        // SET ALARM TIME
        // Example: SET:05:30
        // =========================
        else if (command.startsWith("SET:"))
        {
            String timeValue =
                command.substring(4);

            int separatorIndex =
                timeValue.indexOf(':');

            if (separatorIndex > 0)
            {
                String hourText =
                    timeValue.substring(
                        0,
                        separatorIndex
                    );

                String minuteText =
                    timeValue.substring(
                        separatorIndex + 1
                    );

                int hour =
                    hourText.toInt();

                int minute =
                    minuteText.toInt();


                if (hour >= 0 &&
                    hour <= 23 &&
                    minute >= 0 &&
                    minute <= 59)
                {
                    alarmHour = hour;
                    alarmMinute = minute;

                    preferences.putInt(
                        "hour",
                        alarmHour
                    );

                    preferences.putInt(
                        "minute",
                        alarmMinute
                    );

                    alarmCompleted = false;
                    alarmTriggered = false;

                    Serial.print(
                        "New alarm set: "
                    );

                    Serial.print(
                        alarmHour
                    );

                    Serial.print(":");

                    if (alarmMinute < 10)
                    {
                        Serial.print("0");
                    }

                    Serial.println(
                        alarmMinute
                    );

                    Serial.println(
                        "Alarm saved to NVS!"
                    );
                }
                else
                {
                    Serial.println(
                        "Invalid alarm time!"
                    );
                }
            }
            else
            {
                Serial.println(
                    "Invalid SET command format!"
                );
            }
        }
    }
};


void setup()
{
    Serial.begin(115200);

    delay(1000);


    // =========================
    // RTC
    // =========================

    Wire.begin(
        21,
        22
    );


    if (!rtc.begin())
    {
        Serial.println(
            "DS3231 NOT FOUND!"
        );

        while (true)
        {
            delay(1000);
        }
    }


    Serial.println(
        "DS3231 FOUND!"
    );


    if (rtc.lostPower())
    {
        Serial.println(
            "RTC lost power - setting time..."
        );

        rtc.adjust(
            DateTime(
                F(__DATE__),
                F(__TIME__)
            )
        );
    }


    // =========================
    // BUZZER
    // =========================

    pinMode(
        buzzerPin,
        OUTPUT
    );

    digitalWrite(
        buzzerPin,
        LOW
    );


    Serial.println(
        "Alarm system started"
    );


    // =========================
    // NVS
    // =========================

    preferences.begin(
        "alarm",
        false
    );


    alarmHour =
        preferences.getInt(
            "hour",
            7
        );


    alarmMinute =
        preferences.getInt(
            "minute",
            0
        );


    alarmEnabled =
        preferences.getBool(
            "enabled",
            true
        );


    Serial.print(
        "Loaded saved alarm: "
    );

    Serial.print(
        alarmHour
    );

    Serial.print(":");

    if (alarmMinute < 10)
    {
        Serial.print("0");
    }

    Serial.println(
        alarmMinute
    );


    Serial.print(
        "Alarm enabled: "
    );

    Serial.println(
        alarmEnabled
            ? "YES"
            : "NO"
    );


    // =========================
    // BLE
    // =========================

    Serial.println(
        "Starting BLE..."
    );


    BLEDevice::init(
        "AlarmPrototype"
    );


    BLEServer *pServer =
        BLEDevice::createServer();

        pServer->setCallbacks(new AlarmServerCallbacks());


    BLEService *pService =
        pServer->createService(
            SERVICE_UUID
        );


    BLECharacteristic *pCharacteristic =
        pService->createCharacteristic(
            CHARACTERISTIC_UUID,

            BLECharacteristic::PROPERTY_READ |
            BLECharacteristic::PROPERTY_WRITE
        );


    pCharacteristic->setCallbacks(
        new AlarmCommandCallback()
    );


    // Initial readable value
    pCharacteristic->setValue(
        "STATE:00:00:0"
    );


    pService->start();


    BLEAdvertising *pAdvertising =
        BLEDevice::getAdvertising();


    pAdvertising->addServiceUUID(
        SERVICE_UUID
    );


    pAdvertising->start();


    Serial.println(
        "BLE started!"
    );


    Serial.println(
        "Device name: AlarmPrototype"
    );
}


void loop()
{
    DateTime now =
        rtc.now();


    Serial.print(
        "Time: "
    );

    Serial.print(
        now.hour()
    );

    Serial.print(":");

    Serial.print(
        now.minute()
    );

    Serial.print(":");

    Serial.println(
        now.second()
    );


    // =========================
    // TRIGGER ALARM
    // =========================

    if (alarmEnabled &&
        !alarmTriggered &&
        !alarmCompleted &&
        now.hour() == alarmHour &&
        now.minute() == alarmMinute)
    {
        alarmTriggered = true;

        Serial.println(
            "ALARM TRIGGERED!"
        );
    }


    // =========================
    // SERIAL DEBUG STOP
    // =========================

    if (Serial.available() > 0)
    {
        String command =
            Serial.readStringUntil(
                '\n'
            );

        command.trim();


        if (command == "STOP")
        {
            alarmTriggered = false;
            alarmCompleted = true;

            digitalWrite(
                buzzerPin,
                LOW
            );

            Serial.println(
                "Alarm stopped through Serial!"
            );
        }
    }


    // =========================
    // BUZZER
    // =========================

    if (alarmTriggered)
    {
        digitalWrite(
            buzzerPin,
            HIGH
        );

        delay(500);

        digitalWrite(
            buzzerPin,
            LOW
        );

        delay(500);
    }
    else
    {
        digitalWrite(
            buzzerPin,
            LOW
        );

        delay(500);
    }
}