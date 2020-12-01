# Data_Aquisition

These codes are for the implementation of experimental research efforts by Zach Quintanilla.

## import_packages.txt
This imports the relevent packages that you may need to install on a new Raspberry Pi in order to perform the codes within this Repository.

## DataAquisition5.py
This is the most used program designed to monitor the spontaneous imbibition of a fluid into a vaccumed shale sample with a Raspberry Pi monitoring and 
recording the scale mass as recorded by a Sartorious scale, the ambient temperature and humidity in the room, and the temperature of the fluid that the shale is immersed in. 
This also has the capability to send regular reports through email to update on the status of the experiment. 

## DataAquisitionAlt.py
Very similar to DataAquisition5 except that it is formated to work for a different Sartorius scale.

## DataAquisition_TempControl.py
This is for monitoring and controling the temperature of an experiment within a specified temperature range by contorlling a IoT relay that provides power to the heat source. 
The temperature is monitored by an RTD temperature sensor and Adafruit MAX 31865 Temperature Sensor Amplifier.This also has the capability to send regular reports through email 
to update on the status of the experiment. 

## RemoteCam.py
This is for using a camera to remotely record a video of the experimental set up and send the recording through email. This is useful for monitoring a long term experiment 
when the experimental setup is offsite.
