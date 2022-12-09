TransporterPAL is a tool to predict natural product transporters by interconneting data from the STITCH, STRING and UniProt databases. 

The file TransporterPAL_commandline.py can be executed on the commandline as:
python3 TransporterPAL_commandline.py

The libraries asyncio, aiohttp, sys, requests, csv, json and time need to be imported. 
Save a copy of species.v11.5.txt on your drive

Also ensure to enter input on the following lines before execution of TransporterPAL_commandline.py:
Line #26 insert contact email for good API usage
Line #29 insert your path to species.v11.5.txt
Line #38 Enter your substrate
Line #39 Enter your organism

