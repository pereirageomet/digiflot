To ensure that every component is working properly, a log file is provided at `~/.local/share/DigiFloat/log.txt` for every start of the DigiFlot Lab Assistant.

Each module that tries to import dependencies linked to an external service, such as the vlc player for sound or the RasPi cam libraries for accessing the camera, logs the result of this import in the `log.txt` file.

As a result one get a list of the services that were not successfully started, i.e. because some python libraries or debian packages are not yet installed, or some device is not connected or not working properly. 

A list of modules that log failed import attempts and their meaning are:
- atlasI2C: Atlas Scientific software is not installed
- bronkHorstFlowControlModel: Bronkhorst driver not installed or device not connected
- dahengCamSubProcess: Module not installed or device not connected
- imageStorageSubProcess: Module not installed or device not connected
- lidar: Module not installed
- raspiCamSubProcess: Module not installed or device not connected
- vlcBeepAndSkim: Module not installed