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
import adafruit_max31855
import adafruit_max31865
import Adafruit_DHT as dht
import board
import busio
import digitalio
import os.path
import re
from string import Template
from email.message import EmailMessage
from email.mime.image import MIMEImage




class DataAQ():
    
    def __init__(self, filename='abc.csv', email = 'Y', salinity = 30):
        self.filename = filename
        self.name=self.filename.split('.')[0]
        self.email = email
        if self.email == 'Y':
            try:
                self.Check_Cred()
            except:
                self.My_Email = input('Please provide the sending email address:\n')
                self.Pass = getpass.getpass(prompt='Please provide the sending email password:\n')
                self.Check_Login()
        else:
            print('Email Capability Disabled!')
                
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
  
    def Sartorius_init(self,COM):
        #Initialize Sartorius Scale
        ser = serial.Serial(port = '/dev/ttyUSB0', baudrate = 9600, parity = serial.PARITY_ODD, stopbits = serial.STOPBITS_ONE, bytesize = serial.EIGHTBITS, timeout = None)
        self.ser = ser
    
    def K_type_init(self):
        #Inititalize K Thermocouple
        spi = busio.SPI(board.SCK, MOSI = board.MOSI, MISO = board.MISO)
        cs = digitalio.DigitalInOut(board.D24)
        ksensor = adafruit_max31855.MAX31855(spi,cs)
        return ksensor
       
    def RTD_init(self):
        #Initalize RTP100 sensor to GPIO5
        spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
        cs = digitalio.DigitalInOut(board.D5)
        rtdsensor = adafruit_max31865.MAX31865(spi,cs, wires = 4)
        return rtdsensor
        
    def Scale_Value(self):
        self.ser.write(b"\x1bP\r\n")     
        weight = self.ser.readline() 
        self.ser.write(b"\x1bP\r\n")     
        weight = self.ser.readline() 
        weight=re.findall("\d+\.\d+",str(weight))
        weight = float(weight[0]) 
        return weight
        
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
    
    def send_email(self,wchange):
        
        names,emails = self.get_contacts('lab_contacts.txt')
        message_template = self.read_template('Regular_Message.txt')

        server=smtplib.SMTP('smtp.gmail.com', 587, timeout=300)
        server.starttls()
        server.login(self.My_Email, self.Pass)

        for name, email in zip(names, emails):
            self.simple_plot()
            msg = EmailMessage()
            message = message_template.substitute(PERSON_NAME=name.title(),WEIGHT_CHANGE=wchange)
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
        plottime, real_weight, plottemp, adj_weight = np.loadtxt(self.filename,skiprows=3,delimiter=',', usecols=(1,2,3,6)).T
        fig, ax = plt.subplots(figsize=(8,6), dpi=80)
        ax.plot(plottime,real_weight,'b-',label='Recorded_Weight')
        ax.plot(plottime,adj_weight,'g--',label='Temp Corrected Weight')
        ax.set_ylabel('Weight(g)',fontsize=10)
        ax.set_xlabel('Time (hours)',fontsize = 10)
        
        ax2 = ax.twinx()
        ax2.set_ylabel('Temperature (C)')
        ax2.plot(plottime,plottemp,'r')
        
        ax.legend()
        plt.title(self.name,fontsize = 18)
        if os.path.isfile(f'{self.name}.pdf'):
            os.remove(f'{self.name}.pdf')
        plt.savefig(f'{self.name}.pdf')
        plt.close()
    
    def Density_Calc(self,temp):
        if self.salinity == 'C12':
            a = -.731*10**-3
            b = -.32*10**-6
            TrueDens = .75 + a*(temp-20) + b/2*(temp-20)**2       
        else:
            CleanDens = 1000 * (1 - (temp + 288.9414) / (508929.2 * (temp + 68.12963)) * (temp - 3.9863) ** 2)
            A = 0.824493 - 0.0040899 * temp + 0.000076438 * temp ** 2 - 0.00000082467 * temp ** 3 + 0.0000000053675 * temp ** 4
            B = -0.005724 + 0.00010227 * temp - 0.0000016546 * temp ** 2
            C = 0.00048314
            TrueDens = (CleanDens + A * self.salinity + B * self.salinity ** (3 / 2) + C * self.salinity ** 2) / 1000
        return TrueDens
        
    def Temp_Correction(self,temp,RefD,raw_weight):
        TrueDens = self.Density_Calc(temp)
        TrueWeight = raw_weight + (TrueDens-RefD)*self.Vs
        return TrueWeight
    
    def Error(self,temp, RefD, raw_weight):
        #Error Calculation for RTD Sensor
        Temp_Error = (.15 + temp*.002)
        High_Temp = temp + Temp_Error
        Low_Temp = temp - Temp_Error
        High_Weight_Error = self.Temp_Correction(High_Temp,RefD,raw_weight)
        Low_Weight_Error = self.Temp_Correction(Low_Temp,RefD,raw_weight)
        return High_Weight_Error, Low_Weight_Error
    def Collect(self,starttime,refD,rtdsensor,writer):
            timestamp = datetime.datetime.now().replace(microsecond=0)
            relativetime = (timestamp-starttime)/datetime.timedelta(hours=1)
            weight = self.Scale_Value()
            while weight<10:
                print('Scale Error = Value Too Small')
                weight = self.Scale_Value()
            Liq_Temperature = rtdsensor.temperature 
            #Liq_Temperature = ksensor.temperature
            #print(f'Ktype Sensor is {ksensor.temperature}')
            Humidity, Air_Temperature = dht.read_retry(dht.DHT22, 4)
            AdjWeight=self.Temp_Correction(Liq_Temperature,refD,weight)
            PlusError, MinusError = self.Error(Liq_Temperature, refD, weight)
            writer.writerow([timestamp,format(relativetime,'.4f'),format(weight,'.4f'),format(Liq_Temperature,'.4f'),format(Air_Temperature,'.4f'), format(Humidity,'.2f'), format(AdjWeight,'.4f'), format(PlusError,'.4f'), format(MinusError,'.4f')])
            
    def Aquire(self):    
        count = 0
        ecount = 0
        plt.show(block=True)
        rtdsensor=self.RTD_init()
        #ksensor = self.K_type_init()
        self.Sartorius_init('/dev/ttyUSB0')  
        if os.path.isfile(self.filename):
            answer = input('File already exists! Would you like to append to the exsisting file? (Y/N) \n')
            if answer == 'Y':
                wfile=open(f'{self.filename}', mode='a+')
                writer = csv.writer(wfile, lineterminator = '\n')  
                variable_line=linecache.getline(self.filename, 2).split(',')
                if variable_line[1]!= 'C12':
                    self.salinity = float(variable_line[1])
                else:
                    self.salinity = 'C12'
                self.Vs=float(variable_line[3])
                starttime=datetime.datetime.strptime(variable_line[5], '%Y-%m-%d %H:%M:%S')
                initialweight = float(variable_line[7])
                refD=self.Density_Calc(float(variable_line[9]))
                print('Appending to existing Datafile!')
            else:
                sys.exit('Answer was not Y! Cancel DataAQ()')
        else:    
            
            self.salinity = (input('Please provide salinity of the brine (mg/L):\n'))
            if self.salinity != 'C12':
                self.salinity = float(self.salinity)
            self.Vs = float(input('Please provide an estimate for the total solid volume submerged (cm^3):\n'))
            
            BEGIN = input('Data Aquisition armed press enter when ready!') 
            
            wfile=open(f'{self.filename}', mode='a+')
            writer = csv.writer(wfile, lineterminator = '\n')
            writer.writerow([f'Experiment: {self.name}'])
            initial_temp=rtdsensor.temperature
            refD=self.Density_Calc(initial_temp)
            starttime=datetime.datetime.now().replace(microsecond=0)
            initialweight=self.Scale_Value()
            while initialweight<10:
                print('Scale Error = Value Too Small')
                initialweight = self.Scale_Value()
            writer.writerow(['Brine_Salinity/C12',self.salinity,'Vs',self.Vs,'StartTime',starttime,'InitialWeight',initialweight,'Initial_Temp',initial_temp])
            writer.writerow(['Time','Relative Time (Hours)','Weight (g)','Liq Temperature (C)','Air Temperature (C)','Humidity','Temp Adjusted Weight (g)', '(+)Error from RTD sensor (g)','(-)Error from RTD sensor (g)','Comments'])
            print('Initial Data Recorded! Starting DataAQ!')
            #collect data every 5 sec for first 10 min
            for i in range(1,120):
                self.Collect(starttime,refD,rtdsensor,writer)
                time.sleep(5)
            print('Early Time Data Collection Complete!')
        #collect data every min after first 10 min or appending
        while True: 
            self.Collect(starttime,refD,rtdsensor,writer)
            time.sleep(60)
            count+=1
            ecount+=1
            #log every 30 min count==120,60,40,30    
            if count==60:
                wfile.close()
                #email every 4 hrs ecount==960,480,320,240
                print(f'DATA LOGGED @ {datetime.datetime.now().replace(microsecond=0)}!')
                if ecount >= 240 and self.email == 'Y':
                    try:
                        self.send_email(format(weight-initialweight,'.4f'))
                        initialweight=self.Scale_Value()
                        ecount = 0
                    except:
                        print('Email(s) not sent! Still recording data!')
                        self.simple_plot()
                else:
                    self.simple_plot()
                wfile=open(f'{self.filename}', mode='a+')
                writer = csv.writer(wfile, lineterminator = '\n')
                count=0
            
if __name__ == '__main__':
    try:
        print('Program for Spontaneous Imbibtion Experiments\nThis program is for use with a Sartorius Scale and RTD temperature sensor and/or K-type thermocouple.\nEmail updates will be sent every 4 hours from an email the users specifies\n')
        filename=input('Please type destination filename with .csv \n')
        if filename[-4:]=='.csv':
            Experiment=DataAQ(filename,email = 'N')
            Experiment.Aquire()
        else:
            print('You did not add ".csv" to the end of the file!')
    except KeyboardInterrupt:
        print('Data Aquisition Complete!')
        plt.show(block=False)
        wfile=open(filename, mode='a+')
        wfile.close()
        final=input('Is this experiment complete? (Y/N)')    
        if final == 'Y':   
            Experiment.send_final_email()
            print('Experiment Complete!')
        else:
            print('Data Aquisition has been paused!')


