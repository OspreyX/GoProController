from django.db import models
from datetime import datetime


class Camera(models.Model):
    ssid = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    date_added = models.DateTimeField(auto_now_add=True)
    last_attempt = models.DateTimeField(auto_now=True)
    last_update = models.DateTimeField(null=True, blank=True)
    image = models.TextField(blank=True)
    status = models.TextField(blank=True)
    connection_attempts = models.IntegerField(default=0)
    connection_successes = models.IntegerField(default=0)
    connection_failures = models.IntegerField(default=0)

    def __unicode__(self):
        return self.name


class Command(models.Model):
    camera = models.ForeignKey(Camera)
    command = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    date_added = models.DateTimeField(auto_now_add=True)
    time_completed = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return self.camera.__unicode__() + ' > ' + self.command
