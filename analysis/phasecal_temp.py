import Release
import sys
Release.analysis.phasecalibrator.run(sys.argv[1], map(int,sys.argv[2:]), True)