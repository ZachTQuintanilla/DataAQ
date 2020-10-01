from picamera import PiCamera
from time import sleep
from email.message import EmailMessage
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email.mime.application
from email import encoders
import email.encoders
import getpass
import sys
import smtplib
from string import Template
import os


class RemoteCam():
    def __init__(self, filename = 'video.h264'):
        self.filename = filename
        try:
            self.Check_Cred()
        except:
            self.My_Email = input('Please provide the sending email address:\n')
            self.Pass = getpass.getpass(prompt='Please provide the sending email password:\n')
            self.Check_Login()
    def Check_Cred(self):
        with open('Credentials', mode='r') as info:
            for line in info:
                self.My_Email=line.split()[0]
                self.Pass=line.split()[1]
        self.Check_Login()      
    def Check_Login(self):
        try:
            server=smtplib.SMTP('smtp.gmail.com', 587, timeout=300)
            server.starttls()
            server.login(self.My_Email, self.Pass)
            server.quit()
            print('Login to email server successful!')
        except:
            print('Login to email server failed! Please enter the correct credientials.')
            sys.exit()      
    def get_contacts(self,file):
        names=[]
        emails=[]
        with open(file, mode='r') as contacts:
            for a_contact in contacts:
                names.append(a_contact.split()[0])
                emails.append(a_contact.split()[1])
        return names, emails

    def read_template(self, file):
        with open(file, 'r') as template_file:
            template_file_content = template_file.read()
        return Template(template_file_content)
    def send_email(self):
        
        names,emails = self.get_contacts('lab_contacts.txt')
        message_template = self.read_template('Video_Message.txt')

        server=smtplib.SMTP('smtp.gmail.com', 587, timeout=300)
        server.starttls()
        server.login(self.My_Email, self.Pass)

        for name, email in zip(names, emails):
            #msg = EmailMessage()
            msg = MIMEMultipart()
            message = message_template.substitute(PERSON_NAME=name.title())
            msg['From'] = self.My_Email
            msg['To']= email
            msg['Subject'] = 'Remote Video'
            msg.attach(MIMEText(message))
            
            
            part = MIMEBase("application", "octet-stream")
            part.set_payload(open(self.filename, "rb").read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="video.mp4"')
            msg.attach(part)                 

            server.send_message(msg)
            del msg
        print(f'Email(s) sent!')   
    def CameraRecord(self):
        print('Recording Video!')
        camera = PiCamera()
        camera.resolution = (640,480)
        camera.start_recording(self.filename)
        camera.wait_recording(30)
        camera.stop_recording()
        
        os.system("MP4Box -add " + self.filename + " " + 'video.mp4') # tutorial for install to make this conversion possible at: http://raspi.tv/2013/another-way-to-convert-raspberry-pi-camera-h264-output-to-mp4
        os.system("rm " + self.filename) # delete h264 file
        self.filename = 'video.mp4'
    def Execute(self):
        self.CameraRecord()
        self.send_email()
        os.system("rm " + self.filename)

if __name__ == '__main__':
    RemoteCam().Execute()
    
    
