#include <Arduino.h>

#include <ESP8266WiFi.h>
#include <time.h>      // time() ctime()
#include <sys/time.h>  // struct timeval
#include <coredecls.h> // settimeofday_cb()
#include <LTC2942.h>

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

LTC2942 gauge(50); // Takes R_SENSE value (in milliohms) as constructor argument, can be omitted if using LTC2942-1

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

void loop()
{
  gettimeofday(&tv, nullptr);

  static time_t lastv = 0;
  if (lastv != tv.tv_sec)
  {
    lastv = tv.tv_sec;
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

      Serial.println();
    }
  }
}
