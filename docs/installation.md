# Installation

Here’s how to get started with installing **DigiFlot Lab Assistant** on your device:

- **Check System Requirements**  
  Ensure your device meets the minimum system requirements:
  - Raspian OS (tested), Ubuntu(tested), or another Debian derivate (untested).
  - 4 GiB of RAM
  - at least a CPU with four cores
  - at the very least 10 GiB of disk space

- **Clone the up-to-date repository**  
  - cd to a directory of your choice, e.g. mkdir ~/repo && cd repo
  - clone the repository: git clone https://codebase.helmholtz.cloud/pereir41/digifloat.git

- **Install Dependencies**  
1. `sudo apt install -y python3-picamera2`
2. `sudo apt install -y python3-pyqt5`
3. `sudo apt install vlc`
4. `pip install build`

- **Build the library**

run `python -m pip install build` from the root directory of the repository

- **And install it**

install the build with `python -m pip install .`

- **Verify Installation**  
  - Open the software to confirm it launches properly by calling `python -m digifloat.DigiFloat`.

These steps will guide you through a seamless installation process!
