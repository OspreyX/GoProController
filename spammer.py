#!/usr/bin/python

# force.py
# Josh Villbrandt <josh@javconcepts.com>
# 2015/01/26


import argparse
import django
import logging
import copy
import time
import sys
import os
from colorama import Fore

# import django models
sys.path.append('/home/GoProController')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "GoProController.settings")
django.setup()
from GoProController.models import Camera, Command


# make sure the cameras are always in the state we want them in
class GoProSpammer:
    maxRetries = 3
    status = None

    # init
    def __init__(self, log_level=logging.INFO):
        # setup log
        log_file = '/var/log/gopro-spammer.log'
        log_format = '%(asctime)s   %(message)s'
        logging.basicConfig(format=log_format, level=log_level)

        # file logging
        fh = logging.FileHandler(log_file)
        fh.setLevel(log_level)
        fh.setFormatter(logging.Formatter(log_format))
        logger = logging.getLogger()
        logger.setLevel(log_level)
        logger.addHandler(fh)

        # parse command line arguments
        parser = argparse.ArgumentParser(description=(
            'Automatically re-issue GoPro commands as needed.'))
        parser.add_argument(
            '-i, --interval', dest='interval', type=int, default=1,
            help='the interval to query the database in seconds')
        parser.add_argument(
            '-p, --param', dest='param',
            help='the parameter to be changed or "status" for status')
        parser.add_argument(
            '-v, --value', dest='value',
            help='the value to set the parameter to')
        args = parser.parse_args()
        self.interval = args.interval
        self.param = args.param
        self.value = args.value

    # # connect to the camera's network
    # def connect(self, camera):
    #     func_str = 'GoProProxy.connect({}, {})'.format(
    #         camera.ssid, camera.password)

    #     # jump to a new network only if needed
    #     if self.wireless.current() != camera.ssid:
    #         r = self.wireless.connect(
    #             ssid=camera.ssid, password=camera.password)

    #     # evaluate connection request
    #     if self.wireless.current() == camera.ssid:
    #         # reconfigure the password in the camera instance
    #         self.camera.password(camera.password)

    #         logging.info('{}{}{}'.format(Fore.CYAN, func_str, Fore.RESET))
    #         return True
    #     else:
    #         logging.info('{}{} - network not found{}'.format(
    #             Fore.YELLOW, func_str, Fore.RESET))
    #         return False

    # # send command
    # def sendCommand(self, command):
    #     # make sure we are connected to the right camera
    #     if self.connect(command.camera):
    #         # try to send the command, a few times if needed
    #         i = 0
    #         result = False
    #         while i < self.maxRetries and result is False:
    #             result = self.camera.command(command.command, command.value)
    #             i += 1
    #         command.time_completed = timezone.now()

    #         # did we successfully talk to the camera?
    #         self.updateCounters(command.camera, result)

    #         # save result
    #         command.save()

    # # get status
    # def getStatus(self, camera):
    #     # make sure we are connected to the right camera
    #     camera.last_attempt = timezone.now()
    #     connected = self.connect(camera)

    #     # could we find the camera?
    #     if connected:
    #         # update counters
    #         camera.last_update = camera.last_attempt
    #         self.updateCounters(camera, True)

    #         # try to get the camera's status
    #         status = self.camera.status()
    #         camera.summary = status['summary']

    #         # extend existing status if possible
    #         if camera.status != '':
    #             # allows us to retain knowledge of settings when powered off
    #             try:
    #                 old_status = json.loads(camera.status)
    #                 if old_status != '':
    #                     old_status.update(status)
    #                     status = old_status
    #             except ValueError:
    #                 logging.info('{}{} - existing status malformed{}'.format(
    #                     Fore.YELLOW, 'GoProProxy.getStatus()', Fore.RESET))

    #         # save status to camera
    #         camera.status = json.dumps(status)

    #         # grab snapshot when the camera is powered on
    #         if self.snapshots is True and 'power' in status \
    #                 and status['power'] == 'on':
    #             camera.save()
    #             image = self.camera.image()
    #             if image is not False:
    #                 camera.image = image
    #                 camera.image_last_update = camera.last_attempt
    #     else:
    #         # update counters
    #         self.updateCounters(camera, False)

    #         # update status
    #         camera.summary = 'notfound'

    #     # save result
    #     camera.save()

    # def shouldBeOn(self, command):
    #     return command.command != 'power' or command.value != 'sleep'

    # def updateCounters(self, camera, success):
    #     camera.connection_attempts += 1
    #     if success is not True:
    #         camera.connection_failures += 1

    # spam the command
    def spam(self):
        if self.param is not 'status':
            logging.info('time for spam')

    # report status of all cameras
    def getStatus(self):
        status = {}
        # get status of all cameras
        cameras = Camera.objects.all()
        for camera in cameras:
            # we only care about power and record here
            if power in camera.status and camera.status['power'] == 'on':
                pass
            else:
                status[camera.ssid] = 'off'

        return status

    # report status of all cameras
    def printStatus(self):
        # color statuses
        colored_status = copy.deepcopy(self.status)

        # now print
        print 'Status: {}'.format(colored_status.join(','))

    # report status of all cameras
    def status(self):
        # get status
        status = self.getStatus()

        # print if different
        if status != self.status:
            self.status = status
            self.printStatus()

    # main loop
    def run(self):
        logging.info('{}GoProSpammer.run(){}'.format(Fore.GREEN, Fore.RESET))
        logging.info('Interval: {}'.format(self.interval))

        # keep running until we land on Mars
        last = None
        while 'people' != 'on Mars':
            # check if we should run the spammer now or not
            now = time.time()
            print(now, last)
            if last is None or (now - last) > self.interval:
                last = now
                self.spam()
                self.status()

            # protect the cpu in the event that there was nothing to do
            time.sleep(0.1)


# run spammer if called directly
if __name__ == '__main__':
    spammer = GoProSpammer()
    spammer.run()
