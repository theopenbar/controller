# controller
Controller Daemon for The Open Bar

##Installation Instructions
For complete functionality, install on a Raspberry Pi running Raspbian.

1. Install Adafruit Python GPIO Library:
```
cd libraries/Adafruit_Python_GPIO
sudo python setup.py install
```
2. Build `rpi_ws281x`:
    1.  Install `scons`
        - On linux:
        ```
        sudo apt-get install scons
        ```
        - On OSX:
        ```
        brew install scons
        ```
    2. Build using `scons`
    ```
    cd libraries/rpi_ws281x/
    scons
    ```
