set glue=C:\Python26\python.exe ..\communications\ctipmain.py

start "T1 glue" %glue% -a 10.1.1.11 -n COMT1
start "T2 glue" %glue% -a 10.1.1.12 -n COMT2
start "telemetry glue" %glue% -a 10.1.1.20 -n COMIP

start "Flight code" FlightCode-01.exe