import os
import subprocess
import ConfigParser

parser = ConfigParser.ConfigParser()
parser.read('ground.cfg')

hs_dest = parser.get('telemetry', 'HighSpeedDestination')
ls_dest = parser.get('telemetry', 'LowSpeedDestination')
hs_comports = [s.strip() for s in parser.get('telemetry', 'HighSpeedComports').split(',')]
ls_comport = parser.get('telemetry', 'LowSpeedComport')
hs_baud = parser.getint('telemetry', 'HighSpeedBaud')
ls_baud = parser.getint('telemetry', 'LowSpeedBaud')

subprocess.call('start "Fast telemetry glue" python "{program}" --name={comport}'\
                    .format( program=os.path.join('..','communications','ctipmain.py'),
                             comport=hs_comports[0] ),
                shell=True)
subprocess.call('start "Fast telemetry" telemetry.exe "{dest}" {comport} {baud}'\
                    .format( dest=hs_dest, comport=hs_comports[1], baud=hs_baud ),
                shell=True)

subprocess.call('start "Slow telemetry" telemetry.exe "{dest}" {comport} {baud}'\
                    .format( dest=ls_dest, comport=ls_comport, baud=ls_baud ),
                shell=True)

subprocess.call('start "Groundstation" "{program}"'\
                    .format( program=os.path.join('groundstation','run.py') ),
                shell=True)
