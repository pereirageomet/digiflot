# How to launch the Lab Assistant

**The command**

After successfull installation the Lab Assistant can easily be started as a module of the python library. Just open the terminal and run the command `python -m digifloat.DigiFloat`.

**Tips for first-time users**

You don't need to  remember the command. Instead, just put it in a file, say _start.sh_, and make this file runnable. The following command does exactly that: `echo "python -m digifloat.DigiFloat" > start.sh && chmod +x start.sh`. Now, the file can be run from terminal by the command `./start.sh`, or just double-click _start.sh_ and select "execute" in the pop-up window. 

Another thing worth knowing is that the default working folder of the application is set by the directory from which the application is started. Say, _start.sh_ is located at the desktop, that is, its path is _~/Desktop/start.sh_. When starting the application from the desktop by double-clicking it, the current working directory will be _~/Desktop_. But do not worry, it can be set within the application, if necessary.