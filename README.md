# teba
TEBA - TExt Based Automation - is a tool to create automation menu app using simple text files. 

The app use text files for menus and tasks to be run. Menus files can holds reference to different tasks , or to other menus and have sub menus. 

The tasks file can hold many different devices and for each device a group of commands. 

The conneciton is made using SSH with a user name and password. The credentials are inputed at the start of the script togther with a lock password. Just like an app on your phone, this app can run in the background and no one will be able to run commands without enter the lock password. 

The lock password keep the application safe from miss using , but also keep the user credentials safe. 

The user password is encrypted using the lock password, and the lock password is NEVER saved , so without it , no one can run commands and can not recover the SSH password. 

The menu files are simple text file using the following template: 
ID,Title,Command File Name,type
Where: 
ID = The id of the command 
Title = The text that wil be shown in the menu 
Command File Name = The filename that this command is poting to 
Type = The type of the command (menu / device)  
For example: 
1,Test command,test_command.txt,device 
This is a command of ID 1 , with the title "Test command" . When the user will chooce 1 at the menu, it will load the file test_command.txt and will execute it (since the type is device) 
You can use # to indicate a comment.

The task files are also a text file using the following template: 
<device
command
command
?command
!command
>

For example: 
<192.168.1.1
ls -la
?ping 8.8.8.8
!ifconfig 
>

Commands should be between < and > where the first is the hostname/IP of the device.
A command line that starts with ! will be printed out to the user. 
A command line that starts with ? will be printed out to the user with a Y/N question asking the user if he would like to continue. 
You can have multipe devices in the same task file, as long as you keep the structure of the file. 

Another typr of command , can be script. You can run other python scripts from inside the application. The script will be loaded using the import command , make sure you allow it. 

You should have 3 folders: 
menus - to hold the menus files.
scripts - to hold the external scripts you would like to use. 
tasks - to hold the tasks files. 

Anoher folder is logs, which will hold the logs. 
Main log is - teba.log 
But for each task there will be an additional log. 

You MUST have the main menu inside the menu folder with the filename - teba_menu.txt - this is the main menu.
