PyView
======

This repository contains a range of helper classes and functions to simplify scientific data acquisition and visualization using Python.
I used these classes during my PhD thesis for acquiring and analyzing data in a high-frequency, low-temperature experiment involving superconducting qubits.

##Overview

The repository is organized in the following way:

* *config* contains configration scripts and settings.
* *doc* contains the (still incomplete) documentation of the project.
* *gui* contains all GUI classes, most notably the code IDE and graphical data manager classes.
* *helpers* contains various helper classes, e.g. for remote code execution as well as data & instrument management.
* *lib* contains various library classes, most notably the *Datacube* class which acts as a universal data container.
* *scripts* contains various setup and example scripts.
* *server* contains server scripts that implement a fully transparent remote control scheme for measurement instruments over the network using Python.
* *test* contains various test scripts. 

##Usage

The package is designed to be modular, so you can use most of the components individually. Check out the *scripts* directory for some examples.

##Further information

This code is currently unmaintained. For further information on this code and my PhD work, check out my personal website (http://www.andreas-dewes.de/en/publications).
