#!/usr/bin/env python
# coding: utf-8


import serial
import numpy as np
import matplotlib.pyplot as plt
import linecache
import datetime
import csv
import time
import smtplib
import sys
import getpass

import RPi.GPIO as GPIO

import adafruit_max31865
import Adafruit_DHT as dht
import board
import busio
import digitalio
import os.path
from string import Template
from email.message import EmailMessage
from email.mime.image import MIMEImage




class DataAQ():
    
    def __init__(self, filename='abc.csv',control = 'Y'):
        self.filename = filename
        self.name=self.filename.split('.')[0]
        self.control = control
        self.My_Email = input('Please provide the sending email address:\n')
        self.Pass = getpass.getpass(prompt='Please provide the sending email password:\n')
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

    
       
    def RTD_init(self):
        #Initalize RTP100 sensor to GPIO5
        spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
        cs = digitalio.DigitalInOut(board.D5)
        rtdsensor = adafruit_max31865.MAX31865(spi,cs, wires = 4)
        return rtdsensor
      
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
        message_template = self.read_template('Temp_Message.txt')

        server=smtplib.SMTP('smtp.gmail.com', 587, timeout=300)
        server.starttls()
        server.login(self.My_Email, self.Pass)

        for name, email in zip(names, emails):
            self.simple_plot()
            msg = EmailMessage()
            message = message_template.substitute(PERSON_NAME=name.title())
            msg['From'] = self.My_Email
            msg['To']= email
            msg['Subject'] = self.name
            msg.set_content(message)
            msg.add_attachment(open(self.filename, 'r').read(), filename = self.filename)
            
            pdfopen=open(f'{self.name}.pdf','rb').read()
            image=MIMEImage(pdfopen, _subtype='pdf', name=os.path.basename(f'{self.name}.pdf'))
            msg.attach(image) 
            server.send_message(msg)
            del msg
        print(f'Email(s) sent! Data Aquisition in progress @ {datetime.datetime.now()}!')    
        
    def send_final_email(self):
        names,emails = self.get_contacts('lab_contacts.txt')
        message_template = self.read_template('Final_Message.txt')

        server=smtplib.SMTP('smtp.gmail.com', 587, timeout=300)
        server.starttls()
        server.login(self.My_Email, self.Pass)

        for name, email in zip(names, emails):
            self.simple_plot()
            msg = EmailMessage()
            message = message_template.substitute(PERSON_NAME=name.title())
            msg['From'] = self.My_Email
            msg['To']= email
            msg['Subject'] = self.name
            msg.set_content(message)
            msg.add_attachment(open(self.filename, 'r').read(), filename = self.filename)
            
            pdfopen=open(f'{self.name}.pdf','rb').read()
            image=MIMEImage(pdfopen, _subtype='pdf', name=os.path.basename(f'{self.name}.pdf'))
            msg.attach(image) 
            server.send_message(msg)
            del msg
        print(f'Final Email(s) Sent!')    
        server.quit()    
        
    def simple_plot(self):
        plottime, RTD_Temp, Ambient_Temp = np.loadtxt(self.filename,skiprows=3,delimiter=',', usecols=(1,2,3)).T
        fig, ax = plt.subplots(figsize=(8,6), dpi=80)
        ax.plot(plottime,RTD_Temp,'b-',label='RTD_Temperature')
        ax.plot(plottime,Ambient_Temp,'g--',label='Ambient_Temperature')
        ax.set_ylabel('Temperature(C)',fontsize=10)
        ax.set_xlabel('Time (hours)',fontsize = 10)
        ax.legend()
        plt.title(self.name,fontsize = 18)
        if os.path.isfile(f'{self.name}.pdf'):
            os.remove(f'{self.name}.pdf')
        plt.savefig(f'{self.name}.pdf')
        plt.close()
       
    def Aquire(self):    
        count = 0
        ecount = 0
        plt.show(block=True)
        rtdsensor=self.RTD_init()
        GPIO.setup(25,GPIO.OUT)
        if os.path.isfile(self.filename):
            answer = input('File already exists! Would you like to append to the exsisting file? (Y/N) \n')
            if answer == 'Y':
                wfile=open(f'{self.filename}', mode='a+')
                writer = csv.writer(wfile, lineterminator = '\n')  
                data_line=linecache.getline(f'{self.filename}',4).split(',')
                starttime=datetime.datetime.strptime(data_line[0], '%Y-%m-%d %H:%M:%S')
            else:
                sys.exit('Answer was not Y! Cancel DataAQ()')
        else:    
            starttime=datetime.datetime.now().replace(microsecond=0)
            wfile=open(f'{self.filename}', mode='a+')
            writer = csv.writer(wfile, lineterminator = '\n')
            writer.writerow([f'Experiment: {self.name}'])
            writer.writerow(['Time','Relative Time (Hours)','RTD Temperature (C)','Air Temperature (C)','Comments'])
        print('Data Aquisition in progress!') 
        while True: 
            timestamp = datetime.datetime.now().replace(microsecond=0)
            relativetime = format((timestamp-starttime)/datetime.timedelta(hours=1),'.2f')
            RTD_Temperature = format(rtdsensor.temperature,'.4f')
            Humidity, Air_Temperature = dht.read_retry(dht.DHT22, 4)
            Air_Temperature = format(Air_Temperature,'.2f')
            Humidity = format(Humidity,'.2f')
            writer.writerow([timestamp,relativetime,RTD_Temperature,Air_Temperature, Humidity])
            #needs to be 15,30,45,60 sec interval)
            #while loop used to control a relay switch to halogen lights
            print(f'RTD_Temperature is:{RTD_Temperature}   Ambient_Temperature is:{Air_Temperature}')
            if self.control == 'Y':
                control_counter = 0
                while control_counter<60:
                    time.sleep(1)
                    control_counter+=1
                    temp_check =rtdsensor.temperature
                    if temp_check>36:
                        GPIO.output(25,False)
                        print('Lights Off')
                    elif temp_check<35.25:
                        GPIO.output(25,True)
                        print('Lights On')
            else:
                time.sleep(60)
                
            count+=1
            ecount+=1
            #log every 30 min count==120,60,40,30    
            if count==30:
                wfile.close()
                #email every 4 hrs ecount==960,480,320,240
                print(f'DATA LOGGED @ {datetime.datetime.now().replace(microsecond=0)}!')
                if ecount >= 240:
                    try:
                        self.send_email()
                        ecount = 0
                    except:
                        print('Email(s) not sent! Still recording data!')                
                wfile=open(f'{self.filename}', mode='a+')
                writer = csv.writer(wfile, lineterminator = '\n')
                count=0
            
if __name__ == '__main__':
    try:
        print('Program for Temperature Monitoring and/or Control using a Datalogger.com\nrelay switch to activate halogen lights.\nEmail updates will be sent every 4 hours from an email the users specifies\n')
        filename=input('Please type destination filename with .csv \n')
        if filename[-4:]=='.csv':
            Experiment=DataAQ(filename,control = 'N')
            Experiment.Aquire()
        else:
            print('You did not add ".csv" to the end of the file!')
    except KeyboardInterrupt:
        print('Data Aquisition Complete!')
        plt.show(block=False)
        wfile=open(filename, mode='a+')
        wfile.close()
        GPIO.output(25,False)
        final=input('Is this experiment complete? (Y/N)')    
        if final == 'Y':   
            Experiment.send_final_email()
            print('Experiment Complete!')
        else:
            print('Data Aquisition has been paused!')

