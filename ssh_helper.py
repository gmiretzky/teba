"""
This module provide the SSH frameworks to access the devices.
Also provide a class to hold device details and info.
"""
import time
import getpass
import logging
import paramiko

def run_task_array(task_array, ssh_user, ssh_password, loggername):
	"""This function is the main function that is called. It will run the task array (commands)"""
	result = True
	if not task_array:
		return False
	#For each device , do the follow:
	for device in task_array:
		#Log
		logging.getLogger(loggername).info("Connecting to {}".format(device[0]))
		logging.getLogger(loggername.split('.')[0]).info("Connecting to {}".format(device[0]))

		#Create a new device and login
		temp_device = Device(ssh_user, ssh_password, device[0], loggername)
		logging.getLogger(loggername).debug("temp_device created")
		connected = temp_device.connect_to_device()
		if connected == 1:
			#Unable to connect to the device due to wrong password (in case of multiple device creds). Lets make 1 more attempt to connect before giving up.
			temp_login_password = getpass.getpass("We were unable to connect to device {} can be wrong password . Please enter password again :".format(device[0]))
			temp_device = Device(ssh_user, temp_login_password, device[0], loggername)
			del temp_login_password
			connected = temp_device.connect_to_device()
		if connected != 10:
			#If we are unable to connect to the device , there is some sort of an issue and we will stop the execution of the script
			#Before we doing that , we need to make sure that we finished , we will change the False to break , and add result for the return data
			logging.getLogger(loggername).critical("Unable to connect to {}".format(device[0]))
			result = False
			break
		#Run the tasks
		try:
			temp_device.execute(device[1:])
		except Exception as e:
			logging.getLogger(loggername).critical("Exception was raised: {}".format(str(e)))
			return False
		#Check that we finished successfuly :
		if not temp_device.ready:
			logging.getLogger(loggername.split('.')[0]).critical("Somthing went wrong and device is not ready once task is complete")
			#Also here , we will stop the execution of the script, changing result to False and breaking the loop.
			result = False
			break
		#Now we need to close the connection
		temp_device.client.close()

		#once we finished with everything, we need to destroy the temp_device object
		#Check if there was any error and we break the loop ? If so , we need to manually close the client.
		if not result:
			temp_device.client.close()
		del temp_device
		return result

class Device:
	"""Class to provide device information, and SSH access."""
	ScreenOUTPUT = False
	username = None
	password = None
	sleepTimeCommand = 0.2
	sleepTimeBanner = 1
	maxIterations = 500
	bufferSize = 4096
	device_ip = None
	port = 22
	client = None
	ready = True
	shell = None
	loggername = None

	def __init__(self, username, password, ip, loggername):
		"""Create a new device using IP and credentials."""
		self.loggername = loggername
		self.username = username
		self.password = password
		self.device_ip = ip
		self.ready = True
		#Create a temp log file

		try:
			self.client = paramiko.SSHClient()
			self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		except Exception as e:
			logging.getLogger(self.loggername.split('.')[0]).critical("Failed to initialize F5Execute "+str(e))
			self.ready = False

	def __del__(self):
		"""Done with this device, lets free and remove what we can."""
		logging.getLogger(self.loggername.split('.')[0]).debug("Deleting Device Instance - {}".format(self.device_ip))
		self.client.close()
		del self.client
		self.username = None
		self.password = None
		self.ready = None
		self.shell = None
		self.loggername = None
		self.device_ip = None

	def connect_to_device(self):
		"""
		This function connect to the device.
		We will return error 1 - in case of bad password / authentication
		Error 2 - in case of "Unable to connect to port 22"
		Error 3 - for unknown error .
		10 - in case of success .
		"""
		#Add log to file..
		logging.getLogger(self.loggername).info("Connecting to device: "+ self.device_ip+"\n")
		#Connect to device.
		try:
			self.client.connect(self.device_ip, self.port, self.username, self.password)
			self.shell = self.client.invoke_shell()
			output = self.get_response()
			logging.getLogger(self.loggername).info(output)
			time.sleep(self.sleepTimeCommand)
			logging.getLogger(self.loggername).info("Connected to device: "+ self.device_ip)
			self.ready = True
			return 10
		except Exception as e:
			logging.getLogger(self.loggername.split('.')[0]).critical("Failed to connect to device : "+ self.device_ip +" "+str(e))
			self.ready = False
			#check to see which error message to return
			if str(e).find("Authentication failed") > -1:
				logging.getLogger(self.loggername).critical("Failed to connect to device : Wrong password")
				return 1
			if str(e).find("Unable to connect to port") > -1:
				logging.getLogger(self.loggername).critical("Failed to connect to device : Unable to connect to port")
				return 2
			return 3

	def execute(self, task):
		"""This function read the commands file , and for each device , connects to it and run the commands."""
		logging.getLogger(self.loggername.split('.')[0]).debug("this is some information i get {}".format(task))
		#Get array of commands and run them.
		try:
			for command in task:
				logging.getLogger(self.loggername).debug("This is the command i get : {}".format(command))
				logging.getLogger(self.loggername).info("sending command: " + command + '\n')
				#Check if this is a continue command :
				logging.getLogger(self.loggername).debug("Check to see if command {} is starting with command char ".format(command))
				logging.getLogger(self.loggername).debug("First char is {}".format(command[0]))
				if command[0] == '!':
					#This is a message that should be printed to the user
					logging.getLogger(self.loggername).debug("Showing message to the user")
					logging.getLogger(self.loggername).info("Message is {}".format(command[1:]))
					print(command[1:])
				if command[0] == '?':
					#This is a yes/no command
					logging.getLogger(self.loggername).info("Need to run Y/N function .. ")
					logging.getLogger(self.loggername).info("Command is {}".format(command[1:]))
					out = self.run_command(command[1:]+'\n')
					logging.getLogger(self.loggername).debug("Done running , the output is : {}".format(out))
					print(out)
					logging.getLogger(self.loggername).info("output string  : " + out + '\n')
					if not self.YNRun():
						print("Exit the task  .. ")
						#Need to raise except to break from the loop .. Also , keep throuing it in the parent function !!
						logging.getLogger(self.loggername).error("User select to stop the run ")
						raise AttributeError("User cancel the operation.")
						break
				else:
					out = self.run_command(command+'\n')
					if self.ScreenOUTPUT:
						print(out)
					logging.getLogger(self.loggername).info("output string  : " + out + '\n')

		except AttributeError as e:
			self.ready = False
			raise
		except Exception as e:
			logging.getLogger(self.loggername).critical("Error sending command to Device : {} ".format(str(e)))
			self.ready = False

	def YNRun(self):
		"""Function to ask confirmation [Except Y only all others are No]"""
		logging.getLogger(self.loggername).debug("Inside YN function")
		if input("Continue [Y/N] ? ") == "Y":
			return True
		return False

	def get_response(self):
		"""Function for waiting and receive SSH output."""
		count = 0
		recv_len = 1
		output = ""
		data = bytearray()
		while recv_len:
			time.sleep(self.sleepTimeCommand)
			if self.shell.recv_ready():
				data = self.shell.recv(self.bufferSize)
				recv_len = len(data)
				output += data.decode("utf-8")
			if recv_len < self.bufferSize and (">" in data.decode("utf-8") or "$" in data.decode("utf-8") or "#" in data.decode("utf-8")) and not "##" in data.decode("utf-8"):
				break
			if count == self.maxIterations:
				print("!!!!!!!!!To many iterations for reading output!!!!!!!!!")
				print("out is : " + output)
				logging.getLogger(self.loggername.split('.')[0]).critical("!!!!!!!!!To many iterations for reading output!!!!!!!!!\n")
				break
			count += 1
		return output

	def run_command(self, com):
		"""Fucntion for executing a SSH command."""
		self.shell.send(com)
		out = self.get_response()
		return out
