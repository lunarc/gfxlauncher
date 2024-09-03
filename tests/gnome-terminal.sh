#!/bin/bash

dbus-launch --exit-with-session gnome-terminal --wait
killall dbus-launch
