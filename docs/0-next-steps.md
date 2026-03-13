The notes here will need to be integrated respectively to the other docs, or if they are stand alone put iinto their own file.

---

We will need to conside the enviorment set up of the repo on the raspberry pi.
Will we use UV?
How will I connect to the raspberry pi to set up the repo, and how will I manage the copy of the repo on the raspberry pi going forward. Ie git pull, then uv sync any new dependancies, the repo moving forward? Probablly doing this throguh the terminal.


---

Config Class
- for the google sheet actiing as a config 
   we will need a python class here, that can be imported into respective scripts, so that they know when to run, ect.
   - Later we will need to consider multi processing.
   - if a script complete i would like the config sheet status to change respectively. 
   - Current options are "IDLE", "START", "RUNNING", "SUCCESS", "FAILED"
   - scripts\test_connection.py will need to be updated with respect to the new class, removing any uncessary code.
   - Part of the class should be to log the the status's like in scripts\test_connection.py to the Log sheet. So that this tracks any scripts that get run. 
   - We will need a readme file in C:\Users\RhysL\Desktop\RaspPi-Remote-Worker\docs\scripts to be generated.


---

We will need to understand the need for ├── runner.py              # Main polling and execution loop


