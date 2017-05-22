#!/usr/bin/python

"""
**************************************************************************************************
Project: HOME SECURITY SYSTEM WITH RASPBERRY PI 3 AND MOTION SENSOR
Author: namdothanh (namdothanh87@gmail.com)
Date: 5/2017
Features:
   + Center controller: Raspberry Pi 3
   + Motion sensor: PIR SRF501
   + Receive control command from boss over Facebook messenger account: Start, Stop, Status, Restart,...
   + Detect motion and send alarm message over SMS, Email and Facebook messenger
   + Update current time from Internet
Usage: sudo python homesecurity.py
Libraries:
       fbchat: create Command Bot to listen command from Boss and send Facebook message
       twilio: free SMS API
               + Need to enable geo perimision for Vietnam (+84) or your country
               + Trial account only send to verified phone number: https://www.twilio.com/console/phone-numbers/verified
       smtp: send emails
       ntplib: update Internet time from NTP Server
Command:
        START_COMMAND = "start"     #(Send "start" over facebook message)
        STOP_COMMAND = "stop"
        STATUS_COMMAND = "status"
        TEST_COMMAND = "test"
        SHUTDOWN_COMMAND = "shutdown"
        RESTART_COMMAND = "restart"
Details: see README.md file
License: see LICENSE file (Open source)
**************************************************************************************************
"""

"""
Included libraries
"""
import os
import sys
import datetime
from time import sleep
import RPi.GPIO as gpio

try:
    import fbchat
except:
    print "You need install fbchat package for Python"

try:
    from twilio.rest import Client as SmsClient
except:
    print "You need install twilio package for Python"

try:
    import smtplib
    from email.MIMEMultipart import MIMEMultipart
    from email.MIMEText import MIMEText
except:
    print "You need install smtplib & email packages for Python"

# ------------------------------------------------------------------------------
"""
Print messages for Debug (screen) and Log (file)
"""
DEBUG = 1
LOG = 1
LOG_FILE_NAME = "log.txt"
def printLog(msg):
    _msg = str(datetime.datetime.now()) + ": " + msg
    if DEBUG == 1:
        print _msg
    if LOG == 1:
        logFile = open(LOG_FILE_NAME, "a")
        logFile.write("\r\n" + _msg)
        logFile.close()

# ------------------------------------------------------------------------------
"""
Facebook Messenger alert
View facebook nickname by id:    https://www.facebook.com/profile.php?id=100016918871312
This system need a facebook account. I use Facebook ID to specificed account.
Please google "find facebook id"
"""
faceID = ""          # EX: 1000169xxxxxxxx
facePass = ""        # Password
faceidBoss = ["10000119xxxxx",        #Facebook account of this system Boss
              "10000272xxxxxx"]
faceBossName = ["Nick 1 name",
                "Nick 2 name"]

def sendAlertFacebook(times):
    printLog("[Alert.Facebook] Send facebook messenger.........")
    try:
        msg = "Motion detected:\r\n" \
               "- Sensor position: Main door.\r\n" \
               "- Time: " + str(times)
        for i in range(len(faceidBoss)):
            sent = cmdBot.send(faceidBoss[i], msg)
            if sent:
                printLog("Send face message to " + faceBossName[i] + " account is successful.")
            else:
                printLog("Send face message to " + faceBossName[i] + " account is NOT successful.")
        printLog("[Alert.Facebook] Done.")
    except:
        printLog("[Alert.Facebook] Send facebook messenger is not successful.")

"""
Command Bot based on fbchat.Client
- Receive and process control command from boss over facebook messenger
"""
START_COMMAND = "start"                
STOP_COMMAND = "stop"
STATUS_COMMAND = "status"
TEST_COMMAND = "test"
SHUTDOWN_COMMAND = "shutdown"
RESTART_COMMAND = "restart"
class CommandBot(fbchat.Client):
    global flagCommand

    def __init__(self, id, password, debug=False):
        fbchat.Client.__init__(self, id, password, debug)

    def on_message_new(self, mid, author_id, message, metadata, recipient_id, thread_type):
        global flagCommand

        self.markAsDelivered(author_id, mid)  # mark delivered
        self.markAsRead(author_id)  # mark read

        if str(author_id) == faceID:
            return

        if str(author_id) in faceidBoss:
            if message.lower() == START_COMMAND:
                flagCommand = True
                self.send(author_id, "Yes! My boss. I will START the alarm feature.")
                printLog("Receive **start command** from my boss.")
            elif message.lower() == STOP_COMMAND:
                flagCommand = False
                self.send(author_id, "Yes! My boss. I will STOP the alarm feature.")
                printLog("Receive **stop command** from my boss.")
            elif message.lower() == STATUS_COMMAND:
                if (flagCommand):
                    self.send(author_id, "System status: ALARM ENABLE")
                else:
                    self.send(author_id, "System status: ALARM DISABLE")
                printLog("Receive **status command** from my boss.")
            elif message.lower() == TEST_COMMAND:
                printLog("Receive **test command** from my boss.")
                temp = flagCommand
                flagCommand = True
                alertToBoss(datetime.datetime.now())
                flagCommand = temp
            elif message.lower() == SHUTDOWN_COMMAND:
                printLog("Receive **shutdown command** from my boss.")
                self.send(author_id, "Yes! My boss. I will SHUTDOWN embedded computer.")
                os.system("sudo shutdown -h now")
            elif message.lower() == RESTART_COMMAND:
                printLog("Receive **restart command** from my boss.")
                self.send(author_id, "Yes! My boss. I will RESTART embedded computer.")
                os.system("sudo reboot")

        else:
            self.send(faceidBoss[0], "Received a message from " +
                                      str(author_id) +
                                      " with content: " +
                                      message)

# ------------------------------------------------------------------------------
"""
send SMS Alert
- Use twilio API with Trial account
"""
srcPhoneNumber = ""                                 #twillo phone number
dstPhoneNumber = ["+84975111111",
                  "+84976222222"]
accountSID = ""                                     #see twilio API
accountToken = ""                                   #see twilio API

def sendAlertSMS(times):
    printLog("[Alert.SMS] Send sms........")
    try:
        client = SmsClient(accountSID, accountToken)
        for i in range(len(dstPhoneNumber)):
            printLog("Send SMS to " + dstPhoneNumber[i] + ". Wait.....")
            client.api.account.messages.create(to=dstPhoneNumber[i],
                                               from_=srcPhoneNumber,
                                               body="\r\nMotion detected:\r\n" \
                                                    "- Sensor position: Main door.\r\n" \
                                                    "- Time: " + str(times))
            printLog("successful.")
        printLog("[Alert.SMS] Done.")
    except:
        printLog("[Alert.SMS] Send sms is not successful.")

# ------------------------------------------------------------------------------
"""
Send alert emails to bosses email (list)
"""
srcEmail = "xxxxxxx1@gmail.com"            #Email of this system
password = ""                              #password
dstEmail = ["",                             #boss email
            ""]

def sendAlertEmail(times):
    printLog("[Alert.Email] Send emails........")
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(srcEmail, password)
        msg = MIMEMultipart()
        msg['From'] = srcEmail
        msg['Subject'] = "[Alert] Motion detected at main door."
        body = "Motion detected:\r\n" \
               "- Sensor position: Main door.\r\n" \
               "- Time: " + str(times)
        msg.attach(MIMEText(body, 'plain'))
        for i in range(len(dstEmail)):
            msg['To'] = dstEmail[i]
            text = msg.as_string()
            try:
                server.sendmail(srcEmail, dstEmail[i], text)
                printLog("Send email to " + dstEmail[i] + " is done.")
            except SMTPException:
                printLog("Error: unable to send email")
        server.quit()
        printLog("[Alert.Email] Done")
    except:
        printLog("[Alert.Email] Sending emails has some errors.")

# ------------------------------------------------------------------------------
"""
Alarm function
- Send SMS
- Send Facebook message
- Send email
"""
def alertToBoss(times):
    if(flagCommand == True):
        printLog("----> Send alert message to my boss over SMS, Facebook, Email.")
        sendAlertSMS(times)
        sendAlertFacebook(times)
        sendAlertEmail(times)
        printLog("-----------------------------")
        sleep(5)
    else:
        printLog("----> DO NOT send alert message.")

# ------------------------------------------------------------------------------
"""
Init and callback function for PIR Sensor (Motion detect)
"""
# Gpio Pinnames
PIN_PIR = 23
PIN_LED = 24
counter = 0

# Callback function to run when motion detected
def motionSensor(channel):
    gpio.output(PIN_LED, gpio.LOW)
    if gpio.input(PIN_PIR):     # True = Rising
        global counter
        counter += 1
        times = datetime.datetime.now()
        gpio.output(PIN_LED, gpio.HIGH)
        printLog("-----------------------------")
        printLog("Motion Detected: " + str(counter))
        printLog(" - Sensor position: Main door.")
        printLog(" - Time: " + str(times))
        alertToBoss(times)

def initSensor():
    gpio.setmode(gpio.BCM)  # set up BCM GPIO numbering
    # Set up input pin
    gpio.setup(PIN_PIR, gpio.IN, pull_up_down=gpio.PUD_DOWN)
    # Set up LED output
    gpio.setup(PIN_LED, gpio.OUT)
    # add event listener on pin 21
    gpio.add_event_detect(PIN_PIR, gpio.BOTH, callback=motionSensor, bouncetime=300)
    # 1 blink
    gpio.output(PIN_LED, gpio.HIGH)
    sleep(2)
    gpio.output(PIN_LED, gpio.LOW)

# ------------------------------------------------------------------------------
"""
Update current time from Internet
"""
def updateCurrentTime():
    printLog("Please wait until set time for this computer.......")
    try:
        import ntplib
        c = ntplib.NTPClient()
        response = c.request('europe.pool.ntp.org')
        t = datetime.datetime.utcfromtimestamp(response.tx_time)
        current_time = (t.year,  # Year
                      t.month,  # Month
                      t.day,  # Day
                      (t.hour + 7) % 24,  # Hour. For Vietnam, timezone is GMT+7
                      t.minute,  # Minute
                      t.second,  # Second
                      t.microsecond,  # Millisecond
                      )

        def _linux_set_time(time_tuple):
            import ctypes
            import ctypes.util
            import time

            # /usr/include/linux/time.h:
            #
            # define CLOCK_REALTIME                     0
            CLOCK_REALTIME = 0

            # /usr/include/time.h
            #
            # struct timespec
            #  {
            #    __time_t tv_sec;            /* Seconds.  */
            #    long int tv_nsec;           /* Nanoseconds.  */
            #  };
            class timespec(ctypes.Structure):
                _fields_ = [("tv_sec", ctypes.c_long),
                            ("tv_nsec", ctypes.c_long)]

            librt = ctypes.CDLL(ctypes.util.find_library("rt"))

            ts = timespec()
            ts.tv_sec = int(time.mktime(datetime.datetime(*time_tuple[:6]).timetuple()))
            ts.tv_nsec = time_tuple[6] * 1000000  # Millisecond to nanosecond

            # http://linux.die.net/man/3/clock_settime
            librt.clock_settime(CLOCK_REALTIME, ctypes.byref(ts))

        _linux_set_time(current_time)
        printLog(datetime.datetime.now())
        printLog("Update clock for RaspberryPi3 board is ok.")
    except:
        printLog("Could not sync with time server.")

# ------------------------------------------------------------------------------
"""
Check internet connection.
If internet connection is not good, system is not active.
But motions will be detected and print to screen and log file
"""
def checkInternetConnect():
    for timeout in [1, 5, 10, 15]:
        try:
            import urllib2
            response = urllib2.urlopen('http://google.com', timeout=timeout)
            return True
        except urllib2.URLError as err: pass
    return False

# ------------------------------------------------------------------------------
"""
Main function for system
"""
flagCommand = False
cmdBot = None
def main():
    global cmdBot
    printLog("------------------------------------------------------")
    printLog("--------HOME SECURITY SYSTEM WITH RASPBERRY PI3-------")
    printLog("------------------------------------------------------")
    sleep(2)

    # Init PIR sensor
    initSensor()

    while True:
        # Check internet connection
        printLog("Please wait while check internet connection....")
        while (checkInternetConnect() == False):
            pass
        printLog("Connection is ok.")

        #Update current time from NTP server
        updateCurrentTime()

        # Start a bot for process commands from my boss
        printLog("Start command bot........")
        try:
            cmdBot = CommandBot(faceID, facePass)  # command listening
            cmdBot.listen()
            printLog(" is successful.")
            break
        except:
            printLog(" failed. Try again")

    try:
        while True:
            sleep(1)         # wait 1 second
    finally:                   # run on exit
        gpio.cleanup()         # clean up
        printLog("All cleaned up.")

# ------------------------------------------------------------------------------
"""
If this file is run from CLI, main() function is used
"""
if __name__ == "__main__":
    main()
