# Plugging in a raspi_camera

1. Mount objective to cam sensor of Raspberry Pi.
2. Plug in HDMI cable of cam into raspberry pi.
3. Check if there is a device video0 by entering `ls -al /dev/video0`
4. If not, restart.
5. Check if user is in group "video" by entering `groups $USER`
6. If not, add user to group "video" by entering `adduser $USER video`
7. If successfull, restart. Otherwise move back to 6. with super user rights.
8. Check for raspi cam configuration by entering `sudo raspi-config` and searching for legacy drivers for camera. If they are enabled, unenable them. Then restart.
9. Hopefully, now the raspi cam is recognized immediately when starting the DigiFlot software.