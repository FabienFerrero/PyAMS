# PyAMS version 2021
Python Antenna Measurement System is an open source framework for antenna measurement using ATS800B system

Version 1.0.1, November, 2021

Author: Omar Bouchenak Khelladi, Fabien Ferrero and Lionel Tombakdjian

ATS800B is provided by Rohde & Scharz company   
https://www.rohde-schwarz.com/de/produkt/ats800b-produkt-startseite_63493-642314.html?change_c=true

# ATS800B

The ATS800B system is based on a compact antenna test range (CATR) using a paraboloid reflector with a dualpolarization feed antenna placed at its single focal point to
transform a spherical wavefront into a planar wave distribution and vice versa.
With the compact dimension, the measurement system can stand on a bench lab bench, enabling radiation measurement at millimeter waves in a user-friendly environment.
The compact range has been designed for optimal operation in the 20-50GHz bands.
A rotational stage from PI motor is available to rotate the Antenna Under Test (AUT) during measurement.
The reflector source is a dual-port wideband Vivaldi that can capture two orthogonal polarizations simultaneously.
One objective of this repo will be to provide know-how to extend the capabilities of the actual system.

<img src="https://raw.githubusercontent.com/FabienFerrero/PyAMS/main/Documents/pictures/schematic_tx.png">

# Measurement Equipments for antenna measurement

The optimal equipment to measure antenna with AT800B is a Vector Network Analyser. We are using a two ports ZNA67 with external connector option.

In order to measure the two components of the radiating wave using the two-feed of the recflector source, two different configurations must be use for AUT transmission or reception mode.

<img src="https://github.com/FabienFerrero/PyAMS/blob/main/Documents/pictures/test_bench.png">


# How to install

PyAMS will require several Python lib :
- RsInstrument
- time
- matplotlib
- random
- pipython

# REFERENCES

ATS800B, accessed June, 2020. [Online].Available:
https://www.rohde-schwarz.com/us/product/ats800bproductstartpage.html.
