#!/usr/bin/python

# proxy.py
# Josh Villbrandt <josh@javconcepts.com>
# 8/24/2013

import django
import logging
import json
import time
import sys
import os
from gopro import GoPro
from django.utils import timezone
import subprocess

# import django models
sys.path.append('/home/GoProController')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "GoProController.settings")
django.setup()
from django.conf import settings
from GoProController.models import Camera, Command


# asynchronous daemon to do our` bidding
class GoProProxy:
    maxRetries = 3

    # init
    def __init__(self, interface, log_level=logging.INFO):
        self.camera = GoPro()
        self.wireless = Wireless(interface)

        # setup log
        log_format = '%(asctime)s   %(message)s'
        logging.basicConfig(format=log_format, level=log_level)

    # connect to the camera's network
    def connect(self, camera):
        logging.info('GoProProxy.connect({}, {})'.format(
            camera.ssid, camera.password))

        # jump to a new network only if needed
        if self.wireless.current() != camera.ssid:
            self.wireless.connect(camera.ssid, camera.password)

            # reconfigure the password in the camera instance
            self.camera.password(camera.password)

    # send command
    def sendCommand(self, command):
        # make sure we are connected to the right camera
        self.connect(command.camera)

        # try to send the command, a few times if needed
        i = 0
        result = False
        while i < self.maxRetries and result is False:
            result = self.camera.command(command.command, command.value)
            i += 1
        command.time_completed = timezone.now()

        # did we successfully talk to the camera?
        self.updateCounters(command.camera, result)

        # save result
        command.save()

    # get status
    def getStatus(self, camera):
        # make sure we are connected to the right camera
        self.connect(camera)

        # try to get the camera's status
        camera.last_attempt = timezone.now()
        status = self.camera.status()
        camera.status = json.dumps(status)

        # did we successfully talk to the camera?
        if 'power' in status:
            # power only shows up if we received feedback from the cam
            camera.last_update = camera.last_attempt
            self.updateCounters(camera, True)
        else:
            self.updateCounters(camera, False)

        # grab snapshot
        # if 'power' in status and status['power'] == 'on':
        #     image = controller.getImage(camera.ssid, camera.password)
        #     if image is not False:
        #         camera.image = image

        # save result
        camera.save()

    def shouldBeOn(self, command):
        return command.command != 'power' or command.value != 'sleep'

    def updateCounters(self, camera, success):
        camera.connection_attempts += 1
        if success is not True:
            camera.connection_failures += 1

    # main loop
    def run(self):
        logging.info('GoProProxy.run()')
        # keep running until we land on Mars
        # keep the contents of this loop short (limit to one cmd/status or one
        # status) so that we can quickly catch KeyboardInterrupt, SystemExit
        while 'people' != 'on Mars':
            # PRIORITY 1: send command for the current network on if possible
            command_set = Command.objects.filter(
                time_completed__isnull=True,
                camera__ssid__exact=self.wireless.current())
            if len(command_set) > 0:
                self.sendCommand(command_set[0])
                if self.shouldBeOn(command_set[0]):
                    # get the status now because it is cheap
                    self.getStatus(command_set[0].camera)
            else:
                # PRIORITY 2: send the oldest command still in the queue
                command_set = Command.objects.filter(
                    time_completed__isnull=True).order_by('-date_added')
                if len(command_set) > 0:
                    self.sendCommand(command_set[0])
                    if self.shouldBeOn(command_set[0]):
                        # get the status now because it is cheap
                        self.getStatus(command_set[0].camera)
                else:
                    # PRIORITY 3: check status of the most stale camera
                    camera_set = Camera.objects.all().order_by('last_attempt')
                    if len(camera_set) > 0:
                        self.getStatus(camera_set[0])

            # protect the cpu in the event that there was nothing to do
            time.sleep(0.1)


# abstracts away the wifi details
class Wireless:
    # _interface = None
    _currentSSID = None

    # init
    def __init__(self, interface):
        pass
        # self._interface = interface

    # connect to a network
    def connect(self, ssid, password):
        response = self._cmd('nmcli dev wifi connect {} password {}'.format(
            ssid, password))

        if len(response) == 0:
            self._currentSSID = ssid
            return True
        else:
            return False

    # disconnect from the current network
    def disconnect(self):
        # TODO
        pass

    # returned the ssid of the current network
    def current(self):
        # TODO: actually check the current SSID with a shell call
        # nmcli dev wifi | grep yes
        return self._currentSSID

    # attempt to retrieve the iwlist response for a given ssid
    def _cmd(self, cmd):
        return subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE).stdout.read()

# run proxy if called directly
if __name__ == '__main__':
    proxy = GoProProxy(settings.WIFI_INTERFACE)
    proxy.run()
