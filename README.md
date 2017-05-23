# HOME SECURITY SYSTEM WITH RASPBERRY PI 3 AND MOTION SENSOR

***
## Information:

Author: namdothanh (namdothanh87@gmail.com)

Date: 5/2017

## Features:
   + Center controller: Raspberry Pi 3
   + Motion sensor: PIR SRF501 (1 sensor for this version)
   + Receive control command from boss over Facebook messenger account: Start, Stop, Status, Restart,...
   + Detect motion and send alarm message over SMS, Email and Facebook messenger
   + Update current time from Internet

## Pin connection:

| TT | Raspberry Pi3 PIN |   Peripheral PIN   | Note                 |
|:--:|:-------------:|:--------------:|----------------------|
|  1 |     BCM23     | PIR Sensor/Out | Input                |
|  2 |     BCM24     |    LED Indicator/Anot    | Output (Active High) |

## Usage: 

sudo python code/homesecurity.py

Note: Before run this command, you need modify code to add information for fbchat, sms and email config. 

## Libraries:
       fbchat: create Command Bot to listen command from Boss and send Facebook message
       twilio: free SMS API
               + Need to enable geo perimision for Vietnam (+84) or your country
               + Trial account only send to verified phone number: https://www.twilio.com/console/phone-numbers/verified
       smtp: send emails
       ntplib: update Internet time from NTP Server

## Command:

        START_COMMAND = "start"     #(Send "start" over facebook message)

        STOP_COMMAND = "stop"

        STATUS_COMMAND = "status"

        TEST_COMMAND = "test"

        SHUTDOWN_COMMAND = "shutdown"

        RESTART_COMMAND = "restart"

## Open source license: GNU GPL v3.0 (see LICENSE file)
