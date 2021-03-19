# Webex-Virtual-Background-Logo
Use this script to 'insert' a (customer) logo into an existing virtual background.



# REQUIREMENTS
* A Cisco [Webex Desk Pro](https://www.cisco.com/c/en/us/products/collaboration-endpoints/webex-desk-pro/index.html) video device with a local (user) account.
* Python 3.x or higher (tested with 3.7.x and 3.9.x)
* Python '[requests](http://docs.python-requests.org/en/master/user/install/#install)' library (api calls)
* Python '[pillow](https://pillow.readthedocs.io/en/stable/installation.html )' library (image manipulation)
* Have the Python script run on the same network as your Webex Desk Pro
* A 'base' image that you want to use as a virtual background.  

TESTED on a Webex Desk Pro: RoomOS 10.2.1, Personal Mode, cloud registered
TESTED on Mac: Python 3.9.1, requests 2.25.1, pillow 8.1.0
TESTED on Win 10: Python 3.7.2, requests 2.21.0, pillow 8.1.0


<a name="features"/>
        
# Features

<img src="https://github.com/DJF3/Webex-Virtual-Background-Logo/blob/main/_image/webexlogo_capabilities-1.png?raw=true" width="600px">
<img src="https://github.com/DJF3/Webex-Virtual-Background-Logo/blob/main/_image/webexlogo_capabilities-2.png?raw=true" width="600px">


# How does it work?
<img src="https://github.com/DJF3/Webex-Virtual-Background-Logo/blob/main/_image/webexlogo_how-1.png?raw=true" width="600px">
  

# Start

1. Install Python  ([instructions](https://realpython.com/installing-python/))
2. Install Requests library  ([instructions](https://requests.readthedocs.io/en/master/user/install/))
   > short version: "python3 -m pip install requests"
4. Install Pillow library  ([instructions](https://pillow.readthedocs.io/en/stable/installation.html))
   > short version: "python3 -m pip install pillow"
6. Create a base64 login token for API access:
   > **MAC:** 'echo -n "myusername:mypassword" | base 64'
   > 
   > **WIN:** use an online service like [base64encode.org](https://www.base64encode.org) if you trust them
   > 
   > **WIN:** put 'myusername:mypassword' in a file called 'xtoken.txt' and in a command prompt run: 
   > 
   >      certutil -encode xtoken.txt xtoken.b64 && type xtoken.b64 && del xtoken.*
7. Create a configuration file by running the Python script. If it doesn't find webexlogo_settings.ini it will create one in the right format.
   > **python webexlogo.py**
8. Edit webexlogo_config.ini and update parameters as described in the next paragraph. Instructions are also in the .ini file itself.


# Settings File

<img src="https://github.com/DJF3/Webex-Virtual-Background-Logo/blob/main/_image/webexlogo_settings-1.png?raw=true" width="600px">
<img src="https://github.com/DJF3/Webex-Virtual-Background-Logo/blob/main/_image/webexlogo_settings-2.png?raw=true" width="600px">

  
# Define Logo Area

<img src="https://github.com/DJF3/Webex-Virtual-Background-Logo/blob/main/_image/webexlogo_settings-3logoarea.png?raw=true" width="600px">


# Good to know

* The script caches all downloaded images in the script folder. If needed later it won’t have to download them again.
* If you update an active background, you need to switch to another mode (like ‘Blur’) and back in order to see the changes. 
* When pulling a list of call participants, it will ignore users with a generic ‘email provider’ domain like hotmail.com, gmail.com, yahoo.com
* A DeskPro in a Webex Meeting cannot access email addresses of participants. Solution: run script with domain name, logo url, etc.
* Long URL’s with special characters in it ($,%,&) may need quotes  (python3 webexlogo.py “https://site.com/image?url=longurl”… etc.)

