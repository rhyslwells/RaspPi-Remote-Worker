We will need to conside the enviorment set up of the repo on the raspberry pi.
Will we use UV?
How will I connect to the raspberry pi to set up the repo, and how will I manage the copy of the repo on the raspberry pi going forward. Ie git pull, then uv sync any new dependancies, the repo moving forward? Probablly doing this throguh the terminal.

---
WE will need to understand the documenttion for controlpanel and runner.
---

We will need to understand how to added new scripts to the control panel. It would be good if all i needed to do was add a new row in the Config sheet, and then add the script to the scripts folder, and then it would be ready to run. I will need to understand how the control panel reads the config sheet, and how it manages the scripts.

----

Prime hunter setup with paramters in Config control panel.

IN prime hunter we will need parameters to be injected to the script when it runs, 

Script Name	Status	Last Used	Details	Priority	Parameter-1	Parameter-2	Parameter-3
runner.py	IDLE		Ready           	5			
test_connection.py	SUCCESS	2026-03-13 11:47:35	Connection test successful	5			
prime_hunter.py	SUCCESS		parameter1 is the lowest integer, and the second is the larger integer.		0	100	

I would also like to modify the control panel to accept the possibility thbat more parameter columns are added
----