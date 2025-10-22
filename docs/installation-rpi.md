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

# 4. Install DigiFlot

```bash
cd Documents
git clone https://github.com/pereirageomet/digiflot.git
cd digiflot
python -m build --wheel
pip install dist/*.whl
```

- keep in mind that this installation method will only work for the user you are logged in with. To install digiflot system wide we recommend you to create a python virtual environment. You can read more about that [here](https://virtualenv.pypa.io/en/latest/user_guide.html).
- in any case, we do recommend you to add a new user without sudo rights. Remember to add the user to the following groups: i2c,video,audio,cdrom,plugdev,input,netdev,gpio,spi,dialout

# 5. Create an executable file to lauch the system

```bash
touch ~/Desktop/DigiFlot.sh
echo "python -m digiflot.DigiFlot" >> ~/Desktop/DigiFlot.sh  
sudo chmod 777 ~/Desktop/DigiFlot.sh
```
- **Copy this file to the folder of each DigiFlot project. This will automatize the finding of folders by the user and make sure that the correct config file is loaded**
