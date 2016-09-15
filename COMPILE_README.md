# Overview

Hello, brave user! To start, make sure that you've at least glanced at the README.md for a general overview of how this project is structured.

Continuing on, make sure you've run install_dependencies.sh. Of course, this assumes that you have apt-get installed. If not, you can just read through the file and manually install all the dependencies you see in that file.

Also included in install_dependencies.sh are all of the python dependencies you need to run both the LCD Char screen and the webserver. We're using Python 2.7 here, so make sure it's the correct version, and you have the standard library installed for it (it should have come with the normal installation).

In each of the c_files/ directories in both receiver_files/ and sender_files/ there is a Makefile for their respective programs. It comes with a bunch of error flags enabled, and uses gcc by default, as well as linking to the required libraries.

Once you have everything installed, you should just be able to run the programs and have them work! However, do make sure that you run them with the correct permissions (probably as the superuser, i.e. sudo), because we will be binding to interfaces (eth0), and that will likely require special permissions.

