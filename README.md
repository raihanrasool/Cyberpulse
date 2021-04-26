### How do I get set up and run? ###
Assuming OS Ubuntu 16.04
Install required packages by following instruction from
https://floodlight.atlassian.net/wiki/spaces/floodlightcontroller/pages/1343544/Installation+Guide
Install Java 8 using  Instruction from http://www.webupd8.org/2012/09/install-oracle-java-8-in-ubuntu-via-ppa.html
Install Anaconda from https://repo.anaconda.com/archive/Anaconda3-5.2.0-Linux-x86_64.sh

sudo apt-get install build-essential ant maven python-dev 
If you want to test via mininet
sudo apt-get install mininet 
### Quick help ###
Installing floodlight from code
Download: https://github.com/floodlight/floodlight/archive/v1.2.zip
Unzip: v1.2.zip 

Make Changes:
 file src/main/resources/floodlightdefault.properties set
 
 net.floodlightcontroller.statistics.StatisticsCollector.enable=TRUE
 net.floodlightcontroller.statistics.StatisticsCollector.collectionIntervalPortStatsSeconds=5
Compile: 
 cd floodlight-1.2; make
Initilize:
 sudo rm -rf /var/lib/floodlight/

Run:
cd floodlight-1.2; 
sudo java -jar target/floodlight.jar 

Run project
unzip mlsdn.zip
cd mlsdn
./run.sh
check status 
tail -f Statcollector.log


