"""
TExt Based Automation is a simple script to allow
adding of text menus and tasks to create a simple automation application
"""
import os
import sys
import getpass
import logging
import datetime
import ssh_helper
from crypto_helper import CryptoHelper

#Const varibles
TASKS_PATH = "tasks/"
MENUS_PATH = "menus/"
SCRIPTS_PATH = "scripts/"
LOGS_PATH = "logs/"
MIN_LENGTH_LOCK_PASSWORD = 4 #The minumum length of the lock password.
MAIN_LOGGER_NAME = 'teba'
DEVICE_LOGGER_NAME = MAIN_LOGGER_NAME+'.device'
MASTER_MENU_FILE = 'teba_menu.txt'
MAIN_HEADER = """\
____  ____  ____    __   
(_  _)( ___)(  _ \  /__\  
  )(   )__)  ) _ < /(__)\ 
 (__) (____)(____/(__)(__)"""

def main():
	"""Starting the program !!!"""
	#Define cerdentials -> Can be removed ?
	"""lockPassword = None
	SSH_user = None
	SSH_password = None
	"""

	## Logging ##
	#Setting the loggers format
	formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(funcName)s:%(message)s')
	#Define and initialize the logers, one loger for main program , and one for connections and tasks.
	logger_main = setup_logger(MAIN_LOGGER_NAME, LOGS_PATH+'teba.log', formatter, logging.DEBUG)
	logger_device = setup_logger(DEVICE_LOGGER_NAME, LOGS_PATH+'device.log', formatter, logging.DEBUG)

	try:
		#This is the main menu file
		main_menu_file = open(MENUS_PATH+MASTER_MENU_FILE, 'r')
		print_space("Starting , please initialize your password.")
		creds = initialize_passwords()
		#Run main menu.
		tasks = parse_file(main_menu_file)
		menu_run(tasks, creds)
	except Exception as e:
		print("A critical error has occurred which the script is unable to handle. Sorry :(")

def change_filename(loggername, filename):
	"""Fucntion to change the log file name."""
	formatter = ''
	log = logging.getLogger(loggername)
	for hdlr in log.handlers[:]:
		formatter = hdlr.formatter
		log.removeHandler(hdlr)
	handler = logging.FileHandler(filename)
	handler.setFormatter(formatter)
	log.addHandler(handler)

def setup_logger(name, log_file, formatter, level=logging.DEBUG):
	"""Function to initialize the logers"""
	handler = logging.FileHandler(log_file)
	handler.setFormatter(formatter)
	logger = logging.getLogger(name)
	logger.setLevel(level)
	logger.addHandler(handler)

	return logger

def pause(message="Press the <ENTER> key to continue..."):
	"""Function to pause with a message"""
	_ = input(message)

def check_creds(temp_lock_password, lock_password):
	"""Function to verify lock password."""
	#We keep the lock Password as double hash string.
	try:
		if CryptoHelper.hash(temp_lock_password, 2) == lock_password:
			logging.getLogger(MAIN_LOGGER_NAME).info("Lock password successful")
			return True
		else:
			logging.getLogger(MAIN_LOGGER_NAME).warning("Wrong lock password")
			return False
	except Exception as e:
		logging.getLogger(MAIN_LOGGER_NAME).critical("Unable to hash received lock password, error : {} ".format(str(e)))
		return False

def print_space(mstr):
	"""Function to print a space with a title"""
	print("\n\n*****{}*****\n\n".format(mstr.strip()))

def generate_tasks(task):
	"""Function to generate task array from task file."""
	task_array = []
	try:
		#open task file
		taskfile = open(TASKS_PATH+task, 'r')
		for line in taskfile:
			line = line.strip()
			logging.getLogger(MAIN_LOGGER_NAME).debug("Working on line : {}".format(line))
			if line.startswith('#') or line == '\n' or line == '':	#This is a remark , or empty line ..
				continue
			if line.startswith('<'):
				#This is a new device , setting a new device array.
				device = []
				logging.getLogger(MAIN_LOGGER_NAME).debug("Adding new device with IP of {}".format(line[1:]))
				device.append(line[1:])
				continue
			if line.startswith('>'):
				#This is the end of the device, add the array to the main task array
				task_array.append(device)
				continue
			else:
				#This is a command
				logging.getLogger(MAIN_LOGGER_NAME).debug("Adding new command to the array {}".format(line))
				device.append(line)
				continue
	except Exception as e:
		logging.getLogger(MAIN_LOGGER_NAME).critical("Unable to create task array from file. error: {} ".format(str(e)))
	return task_array

def task_run(task, creds):
	"""Function to run task"""
	#First we check if we need to run another menu , if so , no need to check password.
	if task[3].rstrip() == 'menu':
		logging.getLogger(MAIN_LOGGER_NAME).debug("Task was set to Menu {}".format(task[2]))
		#Set the menu file
		menu_file = open(MENUS_PATH+task[2], 'r')
		tasks = parse_file(menu_file)
		menu_run(tasks, creds, False)
		return True

	#Now, lets check if this is a script that we like to run.
	if task[3].rstrip() == 'script':
		logging.getLogger(MAIN_LOGGER_NAME).debug("Task was set to Script {}".format(SCRIPTS_PATH+task[2]))
		#Show message to user
		pause("Execute script : {}".format(task[2]))
		#We need to remove the .py from the name of the script and then import it.
		__import__(task[2][:-3])
		logging.getLogger(MAIN_LOGGER_NAME).info("Script {} completed".format(task[2]))
		#Pause to see output
		pause()
		return True

	#If we dont run script or another menu, we need to "unlock" the script.
	index = 0 # this is the index of the number of attempts
	temp_lock_password = getpass.getpass("Please enter lock password:")
	while not check_creds(temp_lock_password, creds[0]):
		index += 1 #Error with lock password
		if index > 2:
			logging.getLogger(MAIN_LOGGER_NAME).critical("To many failed attempts for lock password")
			logging.getLogger(MAIN_LOGGER_NAME).critical("Exit script")
			sys.exit() #Exit script !!
		temp_lock_password = getpass.getpass("Error, Please enter lock password:")

	#Rung task :
	if task[3].rstrip().lower() == 'device':
		#lockpassword is ok , we can start with the task.
		logging.getLogger(MAIN_LOGGER_NAME).info("Open Device connection using User {} and filename {}".format(creds[1], task[2]))

		#Open the command file and read it into array
		task_array = generate_tasks(task[2])

		logging.getLogger(MAIN_LOGGER_NAME).debug("The task that we need to run is : {}".format(task[3]))
		logging.getLogger(MAIN_LOGGER_NAME).debug("Task was set to Device")
		logging.getLogger(MAIN_LOGGER_NAME).debug("Decrypt Password")
		temp_ssh_password = CryptoHelper.decrypt(CryptoHelper.hash(temp_lock_password), creds[2])

		#Setting new log file:
		change_filename(DEVICE_LOGGER_NAME, LOGS_PATH+datetime.datetime.now().strftime("%Y%m%d%H%M%S_")+creds[1]+".log")

		#Run task
		try:
			if ssh_helper.run_task_array(task_array, creds[1], temp_ssh_password, DEVICE_LOGGER_NAME):
				pause("{} Completed successful".format(task[2]))
			else:
				pause("Something is wrong , please check logs")
		except Exception as e:
			pause("Received error while running task. Error is {}".format(str(e)))
			logging.getLogger(MAIN_LOGGER_NAME).critical("Received exception while running task : {}".format(str(e)))
		finally:
			#Remove Password
			temp_ssh_password = CryptoHelper.hash(task[3])
			temp_ssh_password = None
			logging.getLogger(MAIN_LOGGER_NAME).debug("Done with tasks")

def menu_run(tasks, creds, rootmenu=True):
	"""Function to run the menu (set rootmenu to False if you are not running a root menu)"""
	ans = True
	index = 1
	while ans:
		#Clear the screen (support for linux and windows - thanks to tutorialspoint.com)
		# for mac and linux(here, os.name is 'posix')
		if os.name == 'posix':
			_ = os.system('clear')
		else:
		# for windows platfrom
			_ = os.system('cls')
		print(MAIN_HEADER)
		#print_space("Main Menu")
		for task in tasks:
			logging.getLogger(MAIN_LOGGER_NAME).info("{}) {}".format(task[0], task[1]))
			print("{}) {}".format(task[0], task[1]))
			index += 1
		#User can press E to Exit or to go back to previous menu.
		print("E) Exit")
		ans = input("Run Task: ")
		if ans in ('E', 'e'):
			if rootmenu:
				print("\n\n\nGood Bye ...")
			ans = False
			break
		try:
			#Getting the user input and calling the function to run the task.
			task_int = int(ans)
			#Checking to see that we dont have negative numbers or zero to avoid runnig wrong task - like task [-1]
			if task_int < 1:
				continue
			task = (tasks[task_int-1])
			print_space(task[1])
			_ = task_run(task, creds)
		except SystemExit as e:
			#This is for exit nicely in case we need.
			logging.getLogger(MAIN_LOGGER_NAME).info("SystemExit exception was raised : {}".format(str(e)))
			raise
		except Exception as e:
			ans = True
			logging.getLogger(MAIN_LOGGER_NAME).debug("Unable to run task - exception : {}".format(str(e)))
			continue
	return True

def parse_file(menu_file):
	"""Function to parse the menu file."""
	#Start the parsing
	logging.getLogger(MAIN_LOGGER_NAME).info("parse_file")
	tasks = []
	for line in menu_file:
		if line.startswith('#') or line == '\n':	#This is a remark , or empty line
			continue
		else:	#Else , this is another command, add it to commands
			tasks.append(line.split(','))
			continue
	return tasks

def initialize_passwords():
	"""Function to initialize the credentials and return them."""
	#creds[0] = lockpassword , creds[1] = username , creds[2] = password (encrypted)
	creds = []
	try:
		logging.getLogger(MAIN_LOGGER_NAME).info("Initialize credentials")
		#Make sure lock password is more then MIN_LENGTH_LOCK_PASSWORD chars
		while True:
			temp_lock_password = getpass.getpass("Please enter lock password:(needs to be {} chars or more)".format(MIN_LENGTH_LOCK_PASSWORD))
			if len(temp_lock_password) > MIN_LENGTH_LOCK_PASSWORD:
				break
		#Hash the lock password.
		creds.append(CryptoHelper.hash(temp_lock_password, 2))

		#Ask for username :
		creds.append(input("Username: "))

		#We encrypt the password using the hash of the lockPassword
		temp_ssh_password = getpass.getpass("Password: ")
		creds.append(CryptoHelper.encrypt(CryptoHelper.hash(temp_lock_password), temp_ssh_password))

		#Remove temp Passwords
		temp_ssh_password = CryptoHelper.hash(str(datetime.datetime.now()))
		temp_ssh_password = None
	except Exception as e:
		logging.getLogger(MAIN_LOGGER_NAME).critical("Opps , unable to initialize passwords. Error: {}".format(str(e)))
		raise e
	return creds

if __name__ == "__main__":
	main()
