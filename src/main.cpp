#include <Arduino.h>
#include <Wire.h>
#include <RTClib.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <Preferences.h>
#include <freertos/semphr.h>
#define SERVICE_UUID "12345678-1234-1234-1234-1234567890ab"
#define CHARACTERISTIC_UUID "abcd1234-1234-1234-1234-abcdef123456"
RTC_DS3231 rtc;
Preferences preferences;
const int buzzerPin = 23;
int alarmHour = 7, alarmMinute = 0;
bool alarmTriggered = false, alarmCompleted = false, alarmEnabled = false;
String qrHash;
SemaphoreHandle_t alarmMutex;
String pendingCommand;
bool receivingCommand = false;
uint32_t lastFragment = 0;
bool connectionBeep = false;
uint32_t connectionBeepStarted = 0;
bool validHash(const String &value)
{
    if (value.length() != 64) return false;
    for (unsigned int i = 0; i < value.length(); ++i)
        if (!((value[i] >= '0' && value[i] <= '9') || (value[i] >= 'A' && value[i] <= 'F'))) return false;
    return true;
}
bool validTime(const String &value)
{
    return value.length() == 5 && value[2] == ':' &&
        isDigit(value[0]) && isDigit(value[1]) && isDigit(value[3]) && isDigit(value[4]) &&
        value.substring(0, 2).toInt() < 24 && value.substring(3).toInt() < 60;
}
String timeText(int hour, int minute)
{
    char text[6];
    snprintf(text, sizeof(text), "%02d:%02d", hour, minute);
    return String(text);
}
// One NVS value commits the time, enabled flag and QR association together.
bool saveAlarm(int hour, int minute, bool enabled, const String &hash)
{
    String config = timeText(hour, minute) + ":" + (enabled ? "1:" : "0:") + hash;
    if (preferences.putString("configV2", config) != config.length()) return false;
    alarmHour = hour;
    alarmMinute = minute;
    alarmEnabled = enabled;
    qrHash = hash;
    return true;
}
String executeCommand(const String &command)
{
    if (command == "GET")
        return "STATE:" + timeText(alarmHour, alarmMinute) + ":" +
            (alarmEnabled ? "1:" : "0:") + (validHash(qrHash) ? "1:" : "0:") + (alarmTriggered ? "1" : "0");
    // Local calendar time matches the phone's local alarm time (no UTC conversion).
    if (command.startsWith("TIME:"))
    {
        if (command.length() != 19) return "ERR:TIME_FORMAT";
        for (unsigned int i = 5; i < 19; ++i)
            if (!isDigit(command[i])) return "ERR:TIME_FORMAT";
        int year = command.substring(5, 9).toInt();
        int month = command.substring(9, 11).toInt();
        int day = command.substring(11, 13).toInt();
        int hour = command.substring(13, 15).toInt();
        int minute = command.substring(15, 17).toInt();
        int second = command.substring(17, 19).toInt();
        if (year < 2000 || year > 2099 || month < 1 || month > 12 ||
            hour > 23 || minute > 59 || second > 59) return "ERR:TIME_FORMAT";
        const int days[] = {31,28,31,30,31,30,31,31,30,31,30,31};
        int maxDay = days[month - 1] + (month == 2 && year % 4 == 0 ? 1 : 0);
        if (day < 1 || day > maxDay) return "ERR:TIME_FORMAT";
        DateTime target(year, month, day, hour, minute, second);
        rtc.adjust(target);
        uint32_t actual = rtc.now().unixtime();
        uint32_t expected = target.unixtime();
        if (actual < expected || actual - expected > 1) return "ERR:RTC_SYNC";
        Serial.printf("[RTC] Synced to phone: %04d-%02d-%02d %02d:%02d:%02d\n",
            year, month, day, hour, minute, second);
        return "OK:TIME";
    }
    // Explicit user-requested reset is allowed even while ringing, without a QR.
    if (command == "CLEAR")
    {
        alarmTriggered = false;
        alarmEnabled = false;
        alarmCompleted = false;
        connectionBeep = false;
        digitalWrite(buzzerPin, LOW);
        // Erase this alarm namespace, including legacy hour/minute/enabled keys.
        if (!preferences.clear()) return "ERR:CLEAR_STORAGE";
        alarmHour = 0;
        alarmMinute = 0;
        qrHash = "";
        return "OK:CLEAR";
    }
    if (command.startsWith("STOP:"))
    {
        String scannedHash = command.substring(5);
        if (!validHash(scannedHash)) return "ERR:FORMAT";
        if (!alarmTriggered) return "ERR:NOT_RINGING";
        if (!validHash(qrHash) || scannedHash != qrHash) return "ERR:QR_MISMATCH";
        alarmTriggered = false;
        alarmCompleted = true;
        connectionBeep = false;
        digitalWrite(buzzerPin, LOW);
        return "OK:STOP";
    }
    // Changing or disabling the alarm cannot bypass QR dismissal while ringing.
    if (command == "ENABLE" || command == "DISABLE" || command.startsWith("SET:"))
    {
        if (alarmTriggered) return "ERR:RINGING";
        if (command.startsWith("SET:"))
        {
            if (command.length() != 74 || command[9] != ':' ||
                !validTime(command.substring(4, 9)) || !validHash(command.substring(10))) return "ERR:FORMAT";
            if (!saveAlarm(command.substring(4, 6).toInt(), command.substring(7, 9).toInt(),
                           true, command.substring(10))) return "ERR:STORAGE";
            alarmCompleted = false;
            return "OK:SET";
        }
        if (!validHash(qrHash)) return "ERR:QR_REQUIRED";
        if (!saveAlarm(alarmHour, alarmMinute, command == "ENABLE", qrHash)) return "ERR:STORAGE";
        alarmCompleted = false;
        return command == "ENABLE" ? "OK:ENABLE" : "OK:DISABLE";
    }
    return "ERR:COMMAND";
}
class AlarmServerCallbacks : public BLEServerCallbacks
{
    void onConnect(BLEServer *) override
    {
        xSemaphoreTake(alarmMutex, portMAX_DELAY);
        if (!alarmTriggered)
        {
            connectionBeep = true;
            connectionBeepStarted = millis();
            digitalWrite(buzzerPin, HIGH);
        }
        xSemaphoreGive(alarmMutex);
        Serial.println("[BLE] Connected.");
    }
    void onDisconnect(BLEServer *) override
    {
        xSemaphoreTake(alarmMutex, portMAX_DELAY);
        pendingCommand = "";
        receivingCommand = false;
        xSemaphoreGive(alarmMutex);
        BLEDevice::startAdvertising();
    }
};
class AlarmCommandCallback : public BLECharacteristicCallbacks
{
    void onWrite(BLECharacteristic *characteristic) override
    {
        String command = characteristic->getValue().c_str();
        xSemaphoreTake(alarmMutex, portMAX_DELAY);
        String response;
        // Framing keeps every write within the default 20-byte BLE payload.
        if (command == "BEGIN")
        {
            pendingCommand = "";
            receivingCommand = true;
            lastFragment = millis();
            response = "OK:BEGIN";
        }
        else if (command.startsWith("+") || command == "COMMIT")
        {
            if (!receivingCommand || millis() - lastFragment > 10000)
            {
                receivingCommand = false;
                pendingCommand = "";
                response = "ERR:TRANSFER";
            }
            else if (command == "COMMIT")
            {
                receivingCommand = false;
                response = executeCommand(pendingCommand);
                pendingCommand = "";
            }
            else if (command.length() < 2 || command.length() > 20 || pendingCommand.length() + command.length() - 1 > 74)
            {
                receivingCommand = false;
                pendingCommand = "";
                response = "ERR:FORMAT";
            }
            else
            {
                pendingCommand += command.substring(1);
                lastFragment = millis();
                response = "OK:PART";
            }
        }
        else
        {
            receivingCommand = false;
            pendingCommand = "";
            response = executeCommand(command);
        }
        // Log responses only; never print QR data or fingerprints.
        Serial.printf("[BLE] response=%s\n", response.c_str());
        characteristic->setValue(response.c_str());
        xSemaphoreGive(alarmMutex);
    }
};
void setup()
{
    Serial.begin(115200);
    pinMode(buzzerPin, OUTPUT);
    digitalWrite(buzzerPin, LOW);
    alarmMutex = xSemaphoreCreateMutex();
    Wire.begin(21, 22);
    if (!rtc.begin())
    {
        Serial.println("DS3231 NOT FOUND!");
        while (true) delay(1000);
    }
    if (rtc.lostPower())
    {
        Serial.println("[RTC] Lost power: restoring firmware compile time.");
        rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
    }
    preferences.begin("alarm", false);
    String config = preferences.getString("configV2", "");
    if (config.length() == 72 && validTime(config.substring(0, 5)) && config[5] == ':' &&
        (config[6] == '0' || config[6] == '1') && config[7] == ':' && validHash(config.substring(8)))
    {
        alarmHour = config.substring(0, 2).toInt();
        alarmMinute = config.substring(3, 5).toInt();
        alarmEnabled = config[6] == '1';
        qrHash = config.substring(8);
    }
    else
    {
        // Preserve the old time, but require QR setup before enabling.
        alarmHour = preferences.getInt("hour", 0);
        alarmMinute = preferences.getInt("minute", 0);
        if (alarmHour < 0 || alarmHour > 23) alarmHour = 7;
        if (alarmMinute < 0 || alarmMinute > 59) alarmMinute = 0;
    }
    BLEDevice::init("AlarmPrototype");
    BLEServer *server = BLEDevice::createServer();
    server->setCallbacks(new AlarmServerCallbacks());
    BLEService *service = server->createService(SERVICE_UUID);
    BLECharacteristic *characteristic = service->createCharacteristic(
        CHARACTERISTIC_UUID, BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_WRITE);
    characteristic->setCallbacks(new AlarmCommandCallback());
    characteristic->setValue(executeCommand("GET").c_str());
    service->start();
    BLEAdvertising *advertising = BLEDevice::getAdvertising();
    advertising->addServiceUUID(SERVICE_UUID);
    advertising->start();
    Serial.println("Alarm ready. Scan a QR in the app to configure.");
}
void loop()
{
    xSemaphoreTake(alarmMutex, portMAX_DELAY);
    DateTime now = rtc.now();
    if (alarmEnabled && validHash(qrHash) && !alarmTriggered && !alarmCompleted &&
        now.hour() == alarmHour && now.minute() == alarmMinute)
    {
        alarmTriggered = true;
        Serial.println("[ALARM] Triggered: buzzer output enabled on GPIO 23.");
    }
    // Diagnostic snapshot on first loop and every five seconds.
    static bool firstDiagnostic = true;
    static uint32_t lastDiagnostic = 0;
    if (firstDiagnostic || millis() - lastDiagnostic >= 5000)
    {
        firstDiagnostic = false;
        lastDiagnostic = millis();
        Serial.printf("[ALARM] RTC=%02d:%02d:%02d SET=%02d:%02d enabled=%d qr=%d triggered=%d completed=%d match=%d\n",
            now.hour(), now.minute(), now.second(), alarmHour, alarmMinute,
            alarmEnabled, validHash(qrHash), alarmTriggered, alarmCompleted,
            now.hour() == alarmHour && now.minute() == alarmMinute);
    }
    // Nonblocking updates allow an accepted QR to stop the sound immediately.
    // Connection confirmation shares the existing buzzer without blocking BLE.
    // Alarm ringing takes priority and cancels any pending confirmation beep.
    if (alarmTriggered || (connectionBeep && millis() - connectionBeepStarted >= 150))
        connectionBeep = false;
    digitalWrite(buzzerPin, (alarmTriggered ? (millis() / 500) % 2 == 0 : connectionBeep) ? HIGH : LOW);
    xSemaphoreGive(alarmMutex);
    delay(20);
}
