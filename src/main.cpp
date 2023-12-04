#include <Arduino.h>
#include <ArduinoJson.h>
#include <ESP8266WiFi.h>
#include <time.h>      // time() ctime()
#include <sys/time.h>  // struct timeval
#include <coredecls.h> // settimeofday_cb()
#include <LTC2942.h>

#include <ESP8266HTTPClient.h>

timeval cbtime; // time set in callback
bool cbtime_set = false;

void time_is_set(void)
{
  gettimeofday(&cbtime, NULL);
  cbtime_set = true;
  Serial.println("------------------ settimeofday() was called ------------------");
}

#define SSID "NanoLab"
#define STAPSK "********"

WiFiEventHandler gotIpEventHandler;
void onWiFiEventStationModeGotIP(const WiFiEventStationModeGotIP &evt)
{
  Serial.print("Station connected, IP: ");
  Serial.println(WiFi.localIP());
}

const unsigned int fullCapacity = 240; // Maximum value is 5500 mAh

LTC2942 gauge(100); // Takes R_SENSE value (in milliohms) as constructor argument, can be omitted if using LTC2942-1

int uptime = -1;

void setup()
{
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(74880);
  Serial.print("Hello\n");

  gotIpEventHandler = WiFi.onStationModeGotIP(&onWiFiEventStationModeGotIP);
  settimeofday_cb(time_is_set);

  //  https://www.di-mgt.com.au/wclock/help/wclo_tzexplain.html
  configTime("EET-2EEST,M3.5.0/3,M10.5.0/4", //  Europe/Riga
             nullptr);                       // NTP from DHCP

  Wire.begin();

  while (gauge.begin() == false)
  {
    Serial.println("Failed to detect LTC2941 or LTC2942!");
    delay(5000);
  }

  unsigned int model = gauge.getChipModel();
  Serial.print("Detected LTC");
  Serial.println(model);

  gauge.setBatteryCapacity(fullCapacity);
  gauge.setBatteryToFull();         // Sets accumulated charge registers to the maximum value
  gauge.setADCMode(ADC_MODE_SLEEP); // In sleep mode, voltage and temperature measurements will only take place when requested
  gauge.startMeasurement();

  WiFi.mode(WIFI_STA);
  WiFi.begin(SSID, STAPSK);
}

timeval tv;

// HTTPClient http;
// WiFiClient client;

#define TMP_SERVER_JSON_BUF_LEN 2000
uint8_t tmp_server_json_buf[TMP_SERVER_JSON_BUF_LEN + 1] = {0};
const char *jskSystem = "system";
const char *jskUptime = "uptime";
const char *jskTimestamp = "timestamp";
const char *jskRSSI = "RSSI";
const char *jskLTC2942 = "LTC2942";
const char *jskTemperature = "temperature";
const char *jskVoltage = "voltage";
const char *jskSample_n = "sample_n";

void loop()
{
  gettimeofday(&tv, nullptr);

  static time_t lastv = 0;
  if (lastv != tv.tv_sec)
  {
    lastv = tv.tv_sec;
    uptime++;
    //    Serial.print(tv.tv_sec);
    //    Serial.print("\t");
    //    Serial.print(ctime(&tv.tv_sec));
    if (tv.tv_sec & 0x1)
    {
      digitalWrite(LED_BUILTIN, LOW);
    }
    else
    {
      digitalWrite(LED_BUILTIN, HIGH);
    }

    if (tv.tv_sec % 5 == 0)
    {
      unsigned int raw = gauge.getRawAccumulatedCharge();
      Serial.print(F("Raw Accumulated Charge: "));
      Serial.println(raw, DEC);

      float capacity = gauge.getRemainingCapacity();
      Serial.print(F("Battery Capacity: "));
      Serial.print(capacity, 3);
      Serial.print(F(" / "));
      Serial.print(fullCapacity, DEC);
      Serial.println(F(" mAh"));

      float voltage = gauge.getVoltage();
      Serial.print(F("Voltage: "));
      if (voltage >= 0)
      {
        Serial.print(voltage, 3);
        Serial.println(F(" V"));
      }
      else
      {
        Serial.println(F("Not supported by LTC2941"));
      }

      float temperature = gauge.getTemperature();
      Serial.print(F("Temperature: "));
      if (temperature >= 0)
      {
        Serial.print(temperature, 2);
        Serial.println(F(" 'C"));
      }
      else
      {
        Serial.println(F("Not supported by LTC2941"));
      }

      if ((WiFi.status() == WL_CONNECTED))
      {
        HTTPClient http;
        WiFiClient client;
        http.begin(client, "http://192.168.5.35"); // HTTP
        http.addHeader("Content-Type", "application/json");

        Serial.print("[HTTP] POST...\n");
        // start connection and send HTTP header and body

        const int capacity = JSON_OBJECT_SIZE(100);
        StaticJsonDocument<capacity> doc;

        JsonObject jso_system = doc.createNestedObject(jskSystem);
        jso_system[jskUptime] = uptime;
        jso_system[jskTimestamp] = tv.tv_sec;
        jso_system[jskRSSI] = WiFi.RSSI();
        static int sample_n = 0;
        jso_system[jskSample_n] = sample_n++;

        JsonObject jso_LTC2942 = doc.createNestedObject(jskLTC2942);
        jso_LTC2942[jskTemperature] = temperature;
        jso_LTC2942[jskVoltage] = voltage;

        size_t n_bytes = serializeJson(doc, tmp_server_json_buf, TMP_SERVER_JSON_BUF_LEN);

        int httpCode = http.POST(tmp_server_json_buf, n_bytes);

        // httpCode will be negative on error
        if (httpCode > 0)
        {
          // HTTP header has been send and Server response header has been handled
          Serial.printf("[HTTP] POST... code: %d\n", httpCode);

          // file found at server
          if (httpCode == HTTP_CODE_OK)
          {
            const String &payload = http.getString();
            Serial.println("received payload:\n<<");
            Serial.println(payload);
            Serial.println(">>");
          }
        }
        else
        {
          Serial.printf("[HTTP] POST... failed, error: %s\n", http.errorToString(httpCode).c_str());
        }

        http.end();
      }

      Serial.println();
    }
  }
}
