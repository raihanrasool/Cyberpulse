
#rm traffic_data.csv graph_data.csv server_report.csv
#touch traffic_data.csv graph_data.csv server_report.csv
echo "Clearing current mininet config status"
sudo mn -c
echo "Running traffic"
sudo python traffic.py&
sleep 15
echo "Running stat collector"
python FloodingRate.py&
python BWSaturation.py&
python Delay.py&
python Throughput.py&
python DropRate.py&
python Attack.py&
#python3.6 statcollector.py
/home/ali/anaconda3/bin/python3.6  statcollector.py
