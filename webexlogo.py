# -*- coding: utf-8 -*-
# EMBED logo in virtual background image
#    DJ Uittenbogaard (duittenb@cisco.com)
#    more info: https://github.com/DJF3/Webex-Virtual-Background-Logo
"""Webex Virtual Background Logo Insertion Script.
Allows you to insert an image (like a logo) in a specific space on a
virtual background of a Cisco Webex Desk Pro video device.
Copyright (c) 2019 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""
import requests
import shutil
import os
import xml.etree.ElementTree as ET
import urllib3   # <- and below: added to skip insecure SSH errors
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import http.client
import ssl
import sys
import operator         # to find the most used participant domain
from PIL import Image, ImageDraw, ImageFont
import base64
from io import BytesIO
import configparser     # for .ini support
myVersion = "0.4"
configFile = "webexlogo_settings.ini"
min_fontsize = 16


# ___ Beep x times
def beep(number):
    for _ in range(number):
        print("\a", end="", flush=True)
    return


# ___ Read key from .ini file
def get_from_ini(key):
    if config.has_option('Settings', key):  # does the key exist?
        key_value = config['Settings'][key]
        if key == "scale_logo":             # this should be a boolean
            key_value = config.getboolean('Settings',key)
        elif len(key_value) > 0 and key_value[0] == "_" and key_value[-1:] == "_":
            # key is present but has not been configured
            print(f"\n**ERROR** please configure item '{key}' in the .ini file\n")
            beep(3)
            exit()
        return key_value
    else:
        print(f"\n**ERROR** missing entry in .ini file: {key}\nAdd this key or rename the .ini file to create a new one.")
        beep(3)
        exit()


# ___ Read .ini file, if it doesn't exist: create an empty template
config = configparser.ConfigParser(allow_no_value=True)
if os.path.isfile("./" + configFile):
    try:
        config.read('./' + configFile)
        endpoint_ip = get_from_ini("endpoint_ip")
        my_inputfile = get_from_ini("my_inputfile")
        my_logofolder = r'{}'.format(get_from_ini("my_logofolder"))
        if my_logofolder[-1:] == "\\":
            my_logofolder = r'{}'.format(my_logofolder[:-1])
        my_token_xapi = get_from_ini("my_token_xapi")
        my_user_image_location = get_from_ini("my_user_image_location")
        my_local_domain_toignore = get_from_ini("my_local_domain_toignore")
        logo_start = get_from_ini("logo_start")
        logo_end  = get_from_ini("logo_end")
        scale_logo = get_from_ini("scale_logo")
        my_fontsize = int(get_from_ini("my_fontsize"))
        my_fontcolor = get_from_ini("my_fontcolor")
        my_fontfile = get_from_ini("my_fontfile")
    except Exception as e:  # Error: keys missing from .ini file
        print(f"\n**ERROR** reading settings file.\n    ERROR: {e} ")
        beep(3)
        exit()
else: # ----------- CONFIG FILE: CREATE new config file because it does not exist
    try:
        config = configparser.ConfigParser(allow_no_value=True)
        config.add_section('Settings')
        config.set('Settings', 'endpoint_ip  ', '_VIDEO_UNIT_IP_ADDRESS_')
        config.set('Settings', '; ---- IP address of your video unit (has to be accessible by this computer)')
        config.set('Settings', 'my_inputfile ', '_BACKGROUND_IMAGE_FILENAME_')
        config.set('Settings', '; ---- Base image of your virtual background')
        config.set('Settings', 'my_logofolder', '')
        config.set('Settings', '; ---- foldername where downloaded images are cached. Empty: current folder')
        config.set('Settings', 'my_token_xapi', '_YOUR_VIDEO_TOKEN_')
        config.set('Settings', '; ---- Token to access your video endpoint. See docs for explanation')
        config.set('Settings', 'my_user_image_location  ', 'User3')
        config.set('Settings', '; ---- Slot name for your virtual background: user1, user2 or user3')
        config.set('Settings', 'my_local_domain_toignore', '')
        config.set('Settings', '; ---- When checking active call participants, ignore users from this domain')
        config.set('Settings', ';      You want your CUSTOMER logo, not yours. Allowed: comma separated list')
        config.set('Settings', 'logo_start  ', '_LOGO_START_XxY_')
        config.set('Settings', 'logo_end    ', '_LOGO_END_XxY_')
        config.set('Settings', '; ---- START and END coordinates of area where logo and text can be placed in (XxY)')
        config.set('Settings', 'scale_logo  ', 'True')
        config.set('Settings', '; ---- Increase your logo size to fit your defined area? Default: True')
        config.set('Settings', 'my_fontsize ', '36')
        config.set('Settings', '; ---- The max font size when embedding text in your virtual background')
        config.set('Settings', 'my_fontcolor', 'yellow')
        config.set('Settings', '; ---- Font color when you embed text on your virtual background (text or #hex)')
        config.set('Settings', 'my_fontfile ', '')
        config.set('Settings', '; ---- Font file used when embedding text in your virtual background (empty=Arial)')
        with open('./' + configFile, 'w') as configfile:
            config.write(configfile)
        print(f"\n*NOTE* configuration .ini file does not exist\n  ---> open the generated .ini file to configure this script\n")
        exit()
    except Exception as e:  # Error creating config file
        print(f"\n**ERROR** creating config file.\n    ERROR: {e} ")
        beep(3)
        exit()


emaildomains = ["yahoo.com", "hotmail.com", "aol.com", "hotmail.co.uk", "hotmail.fr", "msn.com", "yahoo.fr", "wanadoo.fr", "orange.fr", "comcast.net", "yahoo.co.uk", "yahoo.com.br", "yahoo.co.in", "live.com", "rediffmail.com", "free.fr", "gmx.de", "web.de", "yandex.ru", "ymail.com", "libero.it", "outlook.com", "uol.com.br", "bol.com.br", "mail.ru", "cox.net", "hotmail.it", "sbcglobal.net", "sfr.fr", "live.fr", "verizon.net", "live.co.uk", "googlemail.com", "yahoo.es", "ig.com.br", "live.nl", "bigpond.com", "terra.com.br", "yahoo.it", "neuf.fr", "yahoo.de", "alice.it", "rocketmail.com", "att.net", "laposte.net", "facebook.com", "bellsouth.net", "yahoo.in", "hotmail.es", "charter.net", "yahoo.ca", "yahoo.com.au", "rambler.ru", "hotmail.de", "tiscali.it", "shaw.ca", "yahoo.co.jp", "sky.com", "earthlink.net", "optonline.net", "freenet.de", "t-online.de", "aliceadsl.fr", "virgilio.it", "home.nl", "qq.com", "telenet.be", "me.com", "yahoo.com.ar", "tiscali.co.uk", "yahoo.com.mx", "voila.fr", "gmx.net", "mail.com", "planet.nl", "tin.it", "live.it", "ntlworld.com", "arcor.de", "yahoo.co.id", "frontiernet.net", "hetnet.nl", "live.com.au", "yahoo.com.sg", "zonnet.nl", "club-internet.fr", "juno.com", "optusnet.com.au", "blueyonder.co.uk", "bluewin.ch", "skynet.be", "sympatico.ca", "windstream.net", "mac.com", "centurytel.net", "chello.nl", "live.ca", "aim.com", "bigpond.net.au"]
images = ['jpg','png','jpeg']
headers = {
  'Authorization': 'Basic ' + my_token_xapi,
  'Content-Type': 'text/xml'
}
if my_local_domain_toignore != "":
    for items in my_local_domain_toignore.split(","):
        emaildomains.append(items.strip())
# convert easy to see/write variables to what I need.
startX, startY = int(logo_start.split("x")[0]), int(logo_start.split("x")[1])
endX, endY = int(logo_end.split("x")[0]), int(logo_end.split("x")[1])
if endY < startY or endX < startX:
    print(f"\n **ERROR** EndX({endX}) should be > StartX({startX}) and\n           EndY({endY}) should be > StartY({startY}) \n")
    exit()
max_w = endX - startX
max_h = endY - startY
middle_x = int(startX + (endX - startX)/2)
middle_y = int(startY + (endY - startY)/2)


def help_text():
    help_text = """
 Webex Virtual Background logo insertion \n
____________________________________DJ Uittenbogaard_(""" + myVersion + """)__

Options: (replace uppercase text)
  DOMAIN/EMAIL           - add logo to background in userX
  FILE_NAME/URL          - add logo to background in userX
  clear                  - remove logo
  user1/2/3              - switch to background user1/2/3
  user1/2/3 FILE_NAME/URL - upload background to user1/2/3
  text YOUR_TEXT         - add text to background in userX
  text TEXT##ON##NEWLINE - add multiline text to background
_______________________________________________________________\n\n"""
    help_text = help_text.replace("userX",my_user_image_location)
    print(help_text)
    exit()


# ___ check if a file exists
def check_files(filename):
    try:
        filesize = os.path.getsize(str(filename))
        return True
    except:
        return False


# ___ read email addresses from an active call, return most common domain
def read_allparticipants():
    getparticipant_payload = "<Command><Conference><ParticipantList><Search></Search></ParticipantList></Conference></Command>"
    participant_xml = xapiCall(headers,getparticipant_payload, endpoint_ip)
    if "not found" in participant_xml:
        print(f"\n*NOTE* No active call\n")
        beep(3)
        exit()
    if "error" in participant_xml.lower():
        print(f"\n**ERROR** Getting participant details. \n           Message: {participant_xml}\n")
        beep(3)
        exit()
    userdomain_array = dict()
    tree = ET.fromstring(participant_xml)
    for elem in tree.iter():
        if elem.tag == "Email":
            userEmail = elem.text
            if userEmail is None:
                print("     -- user email: no email found. Is this a Webex meeting?")
                continue
            userDomain = userEmail.split("@")[1]
            print(f"     -- user email: {userEmail} ---- domain: {userDomain}")
            if userDomain not in emaildomains:
                if userDomain not in userdomain_array:
                    userdomain_array[userDomain] = 1
                else:
                    userdomain_array[userDomain] += 1
    if len(userdomain_array) == 0:
        print("\n     **ERROR** read_allparticipants: no external users found. - stopping\n")
        beep(3)
        exit()
    else:
        top_domain = max(userdomain_array, key=userdomain_array.get)
    return top_domain


# ___ send (x)API call to video device
def xapiCall(headers,payload,endpointip):
    conn = http.client.HTTPSConnection(endpointip, context = ssl._create_unverified_context(), timeout=20)
    try:
        conn.request("POST", "/putxml", payload, headers)
        res = conn.getresponse()
    except Exception as e:
        print(f"\n**ERROR** connecting to video device ({endpointip}).\n          Message: {e}\n")
        beep(3)
        exit()
    if res.status == 200:
        data = res.read().decode("utf-8")
        if "error" in data.lower():
            data = "**ERROR** xapiCall: " + data.split("status=")[1].split("/>")[0]
            #print(f"\n**ERROR**: {data}")
    else:
        data = "**ERROR** xapiCall: status: " + str(res.status) + "  -- reason: " + str(res.reason)
    return data


# ___ if there is no locally cached logo file: download it
def download_logo(logofile,logocommand):
    logofile_exists = check_files(my_logofolder + "/" + logofile)
    if logofile_exists:             # --- use local file (exists)
        print(f"     LOCAL FILE EXISTS. Using '{logofile}' (download_logo)")
        return_filename = logofile
    elif logocommand != "":        # --- command NOT EMPTY = image URL
        print(f"     DOWNLOAD IMAGE: {logofile} (download_logo)")
        try:
            r = requests.get(logocommand, stream=True)
        except:
            print(f"\n**ERROR** downloading image {logofile} - code: {r.status_code}")
            beep(3)
            exit()
        if r.status_code == 200:
            r.raw.decode_content = True
            with open(my_logofolder + "/" + logofile, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
            return_filename = logofile
        else:
            print(f"\n**ERROR** download_logo RESULT: {r.status_code} (download_logo)\n")
            beep(3)
            exit()
    elif logocommand == "" and not logofile_exists: # --- file does not exist + no image URL
        print(f"\n**ERROR** local file does not exist: '{my_logofolder}/{logofile}' (download_logo)\n")
        beep(3)
        exit()
    else:
        return_filename = logofile
    return return_filename


def filename_clean(filename):
    invalid = '<>:"/\|?* '
    for char in invalid:
        filename = filename.replace(char, '-')
    return filename


# ___ check what should be done and how. RETURNS: logo filename
def get_logo(logo_info):
    userX_present = any(x in logo_info.lower() for x in ["user1", "user2", "user3"])
    if '@' in logo_info:  # ---- received email address with domain ------------
        customer_domain = logo_info.split('@')[-1]
        print(f"     '@' in parameter: {customer_domain} (get_logo)")
        if not "." in customer_domain:
            print(f"\n**ERROR** customer domain doesn't contain a '.':  {customer_domain}\n")
            beep(3)
            exit()
        getlogo_command = "https://logo.clearbit.com/www." + customer_domain
        customer_domain += ".png"
    elif 'http' in logo_info:   # ---- received URL to image -------------------
        if userX_present:
            logo_info = my_commandline.split(" ")[1]    # URL
            print(f"     NEW_BACKGROUND url: {logo_info}")
        my_image_name = str(logo_info.rsplit('/', 1)[-1])
        if '.' not in my_image_name:
            my_image_name += ".jpg"
        my_image_extension = my_image_name.rsplit('.',1)[1].lower()
        my_image_name = filename_clean(my_image_name)
        getlogo_command = logo_info
        customer_domain = my_image_name
    elif logo_info.split('.')[-1].lower() in images: #  LOCAL image ------------
        if userX_present:
            logo_info = my_commandline.split(" ")[1]
            print(f"     NEW background: {logo_info} (get_logo)")
        print(f"     LOCAL image: {my_logofolder}/{logo_info} (get_logo)")
        getlogo_command = ""
        customer_domain = logo_info
    elif "text" in logo_info: # ---- Add text instead of logo ------------------
        customer_domain = "text"
        getlogo_command = "text"
    else:    # ---- received just a domain name --------------------------------
        if not "." in logo_info:
            print(f"\n**ERROR** customer domain doesn't contain a dot:  '{logo_info}'\n")
            beep(3)
            exit()
        customer_domain = logo_info + ".png"
        print(f"     DOMAIN NAME only: {logo_info} (get_logo)")
        customer_domain = customer_domain.replace("www.","")
        getlogo_command = "https://logo.clearbit.com/www." + customer_domain.rsplit(".",1)[0]
    # NOW _download_ the actual file and return the downloaded filename
    if customer_domain != "text":
        return_filename = my_logofolder + "/" + download_logo(customer_domain, getlogo_command)
    else:
        return_filename = "text"
    return return_filename


def image_to_b64(base64object,new_logo):
    my_image_extension = new_logo.rsplit('.',1)[1].lower()
    if my_image_extension != "png":
        my_image_extension = "jpeg"  # (not 'jpg') needed by base64 encoder
    buffer = BytesIO()
    base64object.convert('RGB')
    base64object.save(buffer,format=my_image_extension)
    myimage = buffer.getvalue()
    myimage_b64 = str(base64.b64encode(myimage))[2:][:-1]
    return myimage_b64


# resize logo - RETURNS: image object + image destination resolution
def resizeLogo(imLogo, max_w, max_h,scale_logo):
    imLogo_x, imLogo_y = imLogo.size
    pctLogo_x = max_w / imLogo_x    # width compared to max withd (x)
    pctLogo_y = max_h / imLogo_y    # height compared to max height (y)
    oneIsSmaller = pctLogo_x < 1 or pctLogo_y < 1    # width OR  height bigger  than max
    bothAreBigger = pctLogo_x > 1 and pctLogo_y > 1  # width AND height smaller than max
    if scale_logo and ( (oneIsSmaller) or (bothAreBigger) ):
        if pctLogo_x > pctLogo_y:   # scale down by factor of Y
            new_width  = imLogo_x * pctLogo_y
            new_height = imLogo_y * pctLogo_y
        else:                       # scale down by factor of X
            new_width  = imLogo_x * pctLogo_x
            new_height = imLogo_y * pctLogo_x
        imLogoResized = imLogo.resize((int(new_width),int(new_height)), Image.NEAREST)
        newstart_x = middle_x - int(imLogoResized.width/2)
        newstart_y = middle_y - int(imLogoResized.height/2)
        imLogo = imLogoResized
    else:
        newstart_x = middle_x - int(imLogo_x/2)
        newstart_y = middle_y - int(imLogo_y/2)
    return imLogo, newstart_x, newstart_y


# ADD TEXT to image - returns image object
def addText(imBackground,msg,my_font,my_fontsize):
    msg = msg.replace("##","\n")
    # calculate size of text (to place it in the right location)
    text_width, text_height = my_font.getsize_multiline(msg)
    if text_width > max_w:
        while text_width > max_w:
            my_fontsize -= 1
            my_font = ImageFont.truetype(my_fontfile, my_fontsize)
            text_width, text_height = my_font.getsize_multiline(msg)
        print(f"     NOTE: Font-size changed to {my_fontsize} to fit in the max space")
    elif text_height > max_h:
        while text_height > max_h:
            my_fontsize -= 1
            my_font = ImageFont.truetype(my_fontfile, my_fontsize)
            text_width, text_height = my_font.getsize_multiline(msg)
        print(f"     NOTE: Font-size changed to {my_fontsize} to fit in the max space")
    if my_fontsize < 16:
        print(f"     Calculated font size {my_fontsize} smaller than minimum, change to: {min_fontsize}")
        my_font = ImageFont.truetype(my_fontfile, min_fontsize)
    draw = ImageDraw.Draw(imBackground)       # prepare for adding text
    newstart_x = middle_x - (text_width/2)    # calculate 'centered' position of text
    newstart_y = middle_y - (text_height/2)
    draw.multiline_text((newstart_x,newstart_y), str(msg), font=my_font, fill=my_fontcolor)
    return imBackground


# ---------------------------------------------------------------------------------
#      _____ _______       _____ _______
#     / ____|__   __|/\   |  __ \__   __|
#    | (___    | |  /  \  | |__) | | |
#     \___ \   | | / /\ \ |  _  /  | |
#     ____) |  | |/ ____ \| | \ \  | |
#    |_____/   |_/_/    \_\_|  \_\ |_| http://www.network-science.de/ascii/ 'big'
#
# ---------------------------------------------------------------------------------
# _______1____ READ COMMAND LINE
if len(sys.argv) > 1:
    my_commandline = ' '.join(sys.argv[1:])
    if my_commandline.split(" ")[0].lower() in ["help"]:
        help_text()
    else:
        print("\n\n________________________________________(" + myVersion + ")___")
    if len(my_commandline) > 45:
        print(f"1___ Argument:\n     {my_commandline}")
    else:
        print(f"1___ Argument: {my_commandline}")
else:
    my_commandline = ""
if not check_files(my_inputfile):
    print(f"\n**ERROR** background image file '{my_inputfile}' cannot be found\n")
    beep(3)
    exit()
if my_commandline.split(" ")[0] == "text":
    if not check_files(my_fontfile):   # --- if font-file doesn't exist, use default
        if my_fontfile == "":
            print(f"     *NOTE* font file not configured, using Arial.ttf")
        else:
            print(f"     *NOTE* font file '{my_fontfile}' cannot be found, using {my_fontfile}")
        if os.name == 'nt':
            my_fontfile = "arial.ttf"
        else:
            my_fontfile = "Arial.ttf"
if my_logofolder == "":
    my_logofolder = "."
elif not check_files(my_logofolder):
    try:
        os.mkdir(my_logofolder)
        print(f"     **NOTE: imagecache folder '{my_logofolder}' does not exist. Creating it.")
    except Exception as e:
        print(f"\n**ERROR** creating imagecache folder: \nError message:\n{e}\n")
        beep(3)
        exit()


# _______2____ PROCESS COMMAND LINE
merge_image = False
commandline_count = len(my_commandline.split(" "))
commandline_part1 = my_commandline.split(" ")[0]
if commandline_count == 2:
    commandline_part2 = my_commandline.split(" ")[1]
elif commandline_count > 2:  # text with spaces -> combine
    commandline_part2 = ' '.join(my_commandline.split(" ")[1:])
if my_commandline == "":
    # --- Read participant list from device
    print("2___ GOING TO READ PARTICIPANTS!  my_commandline is EMPTY ")
    top_participant = read_allparticipants()
    new_logo = get_logo(top_participant)
    imLogo = Image.open(new_logo)
    imLogo, newstart_x, newstart_y = resizeLogo(imLogo, max_w, max_h,scale_logo)
    merge_image = True
elif commandline_part1 == "clear":
    # --- Clear logo from background
    print("2___ Removing logo from background")
    imBackground = Image.open(my_inputfile)
    new_logo = my_inputfile
elif commandline_count == 1 and commandline_part1.lower() in ["user1", "user2", "user3"]:
    # --- SWITCH to user1/2/3
    my_user_image_location = commandline_part1
    print(f"2___ Switching to {my_user_image_location}\n\n\n")
    payl_switchbg = "<Command><Cameras><Background><Set><Image>" + my_user_image_location + "</Image><Mode>Image</Mode></Set></Background></Cameras></Command>"
    xapiresult = xapiCall(headers,payl_switchbg, endpoint_ip)
    if "**ERROR**" in xapiresult:
        print(f"\n**ERROR** Can't switch to new background\n{xapiresult}\n")
    beep(1)
    exit()
elif commandline_count > 1 and commandline_part1.lower() in ["user1", "user2", "user3"]:
    # --- NEW virtual background to device
    print("2___ Download new background - no logos")
    image_destination = commandline_part1  # User1/2/3
    image_location = commandline_part2     # Image
    my_user_image_location = image_destination
    if len(image_location) > 45:
        print(f"     Image (for '{image_destination}'):\n     {image_location}")
    else:
        print(f"     Image (for '{image_destination}'):   {image_location}")
    new_logo = get_logo(image_location)
    imBackground = Image.open(new_logo)
elif commandline_part1 == "text":
    # --- ADD TEXT instead of logo
    print("2___ Text: embedding text in background")
    my_font = ImageFont.truetype(my_fontfile, my_fontsize)
    my_text = commandline_part2
    imBackground = Image.open(my_inputfile)
    imBackground = addText(imBackground,my_text,my_font,my_fontsize)
    new_logo = my_inputfile
else:  # --- Email, domain or URL
    print("2___ Preparing logo download")
    new_logo = get_logo(my_commandline)
    imLogo = Image.open(new_logo)
    imLogo, newstart_x, newstart_y = resizeLogo(imLogo, max_w, max_h,scale_logo)
    merge_image = True


#if my_commandline != 'clear' and 'user' not in my_commandline.lower() and 'text' not in my_commandline:
if merge_image:
    imBackground = Image.open(my_inputfile)
    inputSize_x, inputSize_y = imBackground.size
    if startX > inputSize_x or endX > inputSize_x or startY > inputSize_y or endY > inputSize_y:
        print(f"\n**ERROR** Start/End coordinates of logo must be within the base image.\n          Image resolution = {inputSize_x}x{inputSize_y}, logo start {logo_start}, logo end {logo_end}\n")
        exit()
    back_im = imBackground.copy()
    back_im.paste(imLogo, (newstart_x, newstart_y))   # X,Y - from top-left corner
    # SAVE result
    back_im64 = image_to_b64(back_im,new_logo)
    back_im.convert('RGB').save(my_logofolder + "/_result.jpg")
else:  # --- clear / text / newbackground
    back_im64 = image_to_b64(imBackground,new_logo)
    imBackground.convert('RGB').save(my_logofolder + "/_result.jpg")


# _______3____ PREPARE BACKGROUND FOR UPLOAD
print("3___ PREPARE background upload")
payload = "<Command><Cameras><Background><Upload><Image>" + my_user_image_location + "</Image><body>xxx</body></Upload></Background></Cameras></Command>"
payload = payload.replace("xxx", back_im64)

# _______4____ UPLOAD BACKGROUND
print("4___ UPLOADING background to video device @ " + endpoint_ip + ")")
xapiresult = xapiCall(headers,payload, endpoint_ip)
if "**ERROR**" in xapiresult:
    print(f"\n**ERROR** Can't add new background:\n {xapiresult}\n")

# _______5a____ SWITCH TO BLUR
print(f"5___ Switch to Blur and then back to {my_user_image_location} to make changes visible.")
payl_switchbg = "<Command><Cameras><Background><Set><Mode>BlurMonochrome</Mode></Set></Background></Cameras></Command>"
xapiresult = xapiCall(headers,payl_switchbg, endpoint_ip)
if "**ERROR**" in xapiresult:
    print(f"\n**ERROR** Can't switch to blur:\n {xapiresult}\n")

# _______5b____ SWITCH TO NEW BACKGROUND
payl_switchbg = "<Command><Cameras><Background><Set><Image>" + my_user_image_location + "</Image><Mode>Image</Mode></Set></Background></Cameras></Command>"
xapiresult = xapiCall(headers,payl_switchbg, endpoint_ip)
if "**ERROR**" in xapiresult:
    print(f"\n**ERROR** Can't switch to new background\n{xapiresult}\n")

print("____ finished ___________________________________\n")
beep(1)

