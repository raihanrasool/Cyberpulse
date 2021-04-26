from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.util import irange
from mininet.node import Controller, OVSKernelSwitch, RemoteController
import logging
import time
import json
import re
import csv
import datetime
report_interval=10
infile="server_report.csv"
def GetRole(hostip, traffic_config):
    if (hostip == traffic_config["iperf_server"]):
        return "server"
    for h in traffic_config["iperf_client"]:
        if (h["host_ip"] == hostip):
            return "client"


def ProcessIperfReport(range_start,range_end):
    ret_end = range_start
    tx_sum=0.0
    rate_sum=0.0
    time=0
#print ( range_start, range_end)
    with open(infile) as f:
        for line in f:
            data = line.strip().split(',')
            if (9== len(data)):
                #TCP
                interval = data[6]
                ints = interval.split('-')
                start=ints[0]
                end=ints[1]
                if((float(start)>=float(range_start)) and
                   (float(end) <=float(range_end))
                   ):
                    tx =  float(data[7])
                    tx_sum = tx_sum+tx
                    rate = float(data[8])
                    rate_sum = rate_sum + rate
                    time = data[0]
                    ret_end = end
    return ret_end,tx_sum/(1024*1024), rate_sum/(1024*1024)


def ParsePingFull( pingOutput ):
    errorTuple = ( 0, 0, 0, 0)
    r = r'rtt min/avg/max/mdev = '
    r += r'(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+) ms'
    m = re.search( r, pingOutput )
    if m is None:
        print ("error")
        return errorTuple
    rttmin = float( m.group( 1 ) )
    rttavg = float( m.group( 2 ) )
    rttmax = float( m.group( 3 ) )
    rttdev = float( m.group( 4 ) )
    return rttmin, rttavg, rttmax, rttdev

def WriteGraphFile(data):
        output_file = open('traffic_data.csv', 'w')
        keys = data[0].keys()
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)


def Traffic(cip, cport, traffic_config):

    hostPerSwitch = traffic_config['host_per_switch']
    totalSwitch = traffic_config['switch_count']
    bwval= traffic_config['link_capacity_in_Mbit']
    linkopts = dict(bw=bwval, delay='0ms', loss=0, max_queue_size=10, use_htb=True,jitter=0,max_latency=0)
    logging.debug("Creating mininet")
    net = Mininet(None,host=CPULimitedHost, link=TCLink,build=False,autoSetMacs=True)
    totalHost=totalSwitch*hostPerSwitch
    c0 = net.addController('c0', controller=RemoteController,ip=cip,port=cport)
    for sn in range (1, totalSwitch+1):
        switch =  net.addSwitch("s{}".format(sn))
        for hn in range (1,hostPerSwitch+1):
            host = net.addHost( "h{}s{}".format(hn,sn), cls=CPULimitedHost, cpu=100/totalHost )
            net.addLink(switch, host, **linkopts)

    for snsrc in range (1, totalSwitch+1):
        src = "s{}".format(snsrc)
        for sndst in range (1, totalSwitch+1):
            dst = "s{}".format(sndst)
            if src !=dst:
                net.addLink(src,dst, **linkopts)
    net.build()
    for controller in net.controllers:
        controller.start()

    for switch in net.switches:
        switch.start( net.controllers )
    net.pingAll()
    hosts = net.hosts
#CLI(net)
    #start iperf  traffic
    serverip = traffic_config["iperf_server"] 
    duration =  traffic_config["traffic_duration_min"] * 60 
    for host in hosts:
        role = GetRole(host.IP(), traffic_config)
        if (GetRole(host.IP(), traffic_config) == "server"):
            cmd='/usr/bin/iperf -i  {} -y C -f m -s -B  {}  > {} &'.format(report_interval,host.IP(),infile)
            host.cmd( cmd)
            logging.debug('Starting iperf server in {}'.format(serverip))
        if (GetRole(host.IP(), traffic_config) == "client"):
            cmd='/usr/bin/iperf -c {} -B {} -t {} -f m &'.format(serverip,  host.IP(), duration)
            logging.debug('Starting iperf client in in {} for duration {} sec'.format(host.IP(),duration ))
            host.cmd( cmd)
    
    starttime = datetime.datetime.now()
    data_list = []
    range_start=0
    while True:
        range_end= float(range_start) + float(report_interval)
        range_start_new,tx,rate = ProcessIperfReport(range_start,range_end)
        endtime = datetime.datetime.now()
        if (range_start_new != range_start):
            range_start = range_start_new
            result = hosts[-1].cmd('ping -c 10', hosts[0].IP())
            rttmin, rttavg, rttmax, rttdev = ParsePingFull(result)
            logging.debug('Ping average delay result {} ms'.format(rttavg))
            elem = {
                 "Time":endtime.strftime("%Y-%m-%d %H:%M:%S"),
                 "RttAvg":rttavg,
                 "Input_load":tx,
                 "Throughput":rate
             }
            data_list.append(elem)
            WriteGraphFile(data_list)
        elapsed = endtime - starttime
        if (elapsed.total_seconds()>duration):
            logging.debug('elapsed time {} sec.Exiting traffic generation '.format(duration))
            break;
        time.sleep(2)
               
    net.stop()

if __name__ == '__main__':
    logging.basicConfig(filename='traffic.log',
        filemode='w',
        format='%(levelname)-8s:%(asctime)12s:%(funcName)12s: line %(lineno)3d : %(message)s',
        datefmt='%H:%M:%S',
        level=logging.DEBUG)
    json_data=open("config.json").read()
    data = json.loads(json_data)
    setLogLevel('info')
    Traffic(data['controller']['controller_ip'],
           int( data['controller']['controller_openflow_port']),
           data['traffic_config']
           )
