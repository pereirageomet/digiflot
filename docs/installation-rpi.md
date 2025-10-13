# 1. Install the Raspberry Pi OS
- follow the [official guide](https://www.raspberrypi.com/software/) 

# 2. Basic requirements
- Update the system install dependencies

```bash
sudo apt update && apt upgrade -y
sudo apt install -y python3-full python3-pip libcap-dev vlc python3-build python3-picamera2 python3-pyqt5 xterm timeshift
```

- Install the Daheng software
    - Go to https://va-imaging.com/pages/customerdownloads and download the latest API for DAHENG (Linux-ARM). 
    - Inside the zip you will find the installation instructions 

enable the following interfaces: i2c, serial, remote GPIO in
```bash
raspi-config 
```
# 3. Reboot the system

# 4. Backup
- To prevent possible issues, make a backup of your system, which you can come back to:
    - open timeshift under system tools
    - choose RSYNC as snapshot type
    - Choose weekly backups and to keep at least 3 saved in the disk
    - Press Create to make a backup now

# 5. Install DigiFlot

```bash
cd Documents
git clone https://github.com/pereirageomet/digiflot.git
cd digiflot
python -m build --wheel
sudo pip install --break-system-packages dist/*.whl
```

# 7. Create an executable file to lauch the system

```bash
touch ~/Desktop/DigiFlot.sh
echo "python -m digiflot.DigiFlot" >> ~/Desktop/DigiFlot.sh  
sudo chmod 777 ~/Desktop/DigiFlot.sh
```
- **Copy this file to the folder of each DigiFlot project. This will automatize the finding of folders by the user and make sure that the correct config file is loaded**

# 6. Recommended: add a new user without sudo rights

```bash
sudo adduser laboratory # password 123456
sudo usermod -aG i2c,video,audio,cdrom,plugdev,input,netdev,gpio,spi,dialout laboratory
sudo nano /etc/lightdm/lightdm.conf # search for autologin-user=pi and change the user to laboratory -> this makes the system automatically login to this user, easing the work
```

## if you need to delete a user
```bash
sudo pkill -KILL -u laboratory
sudo userdel laboratory
sudo userdel -r laboratory
```