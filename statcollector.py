import requests
import json
import sys
import logging
from pprint import pprint
import time
import csv
import datetime
from sklearn.metrics import accuracy_score, fbeta_score
from sklearn.externals import joblib
#from Traffic_classification import *
import numpy as np
"""
	Load the model and evaluate the performance.
"""


def load_model(model_path):
    '''
    inputs:
       - molde_path: the path of the saved model (pickle). 
       Example call: clf = joblib.load('path_of_the_pickle_file.pkl') 
                    model_predictions = clf.predict(X_test)
                    accuracy_score(y_test, model_predictions)
                    fbeta_score(y_test, model_predictions)
    '''
    clf = joblib.load(model_path)
    return clf


def predict(model, instance):
    """
    Predicts single data instance.

    Parameters
    ----------
    model : pickle object
        The trained model.
    instance : array
        Holds the dta observation.

    Return:
        Returns the classification output, along with the confidence level.
    """
    prediction = model.predict(instance)
    confidence = model.predict_proba(instance)
    return [prediction, np.max(confidence)]


class StatCollector:
    def __init__(self, interval, duration, controllerIP, controllerPort,
                 flooding_threshold_byteCount, full_bw, serverip,clients,
                 important_links, ml_config):
        self.interval = interval
        self.duration = 60 * duration
        self.controllerIP = controllerIP
        self.controllerPort = controllerPort
        self.urlbase = 'http://' + controllerIP + ':' + controllerPort
        self.headers = {'Accept': 'application/json'}
        self.auth = ('', '')
        self.switch_list = []
        self.graph_data_list = []
        self.oldvalue = {}
        self.flows = {}
        self.serverip = serverip
        self.attack_node = 0
        self.detection_time = 0
        self.attack_nodes_count =  len(clients)
        self.IsFlooding = False
        self.shouldcontinue = True
        self.flooding_threshold_byteCount = flooding_threshold_byteCount
        self.readings = {}
        self.reading_iteration = 0
        self.ml_model = ml_config['model_name']
        self.confidence_level = int(ml_config['confidence_level'])
        self.action = ml_config['action']
        self.importants_links_list = []
        item = {
            'switch_id': important_links['switch_id'],
            'port_number': important_links['port_number']
        }
        self.importants_links_list.append(item)
        self.readings['Node'] = 1
        self.readings['total_bytes'] = 0
        self.readings['total_bytes_imp'] = 0
        self.readings['Used_Bandwidth'] = 0
        self.readings['Utilised_Bandwidth_Rate'] = 0
        self.readings['Packet_Drop_Rate'] = 0

        self.readings['Link_Capacity'] = full_bw
        self.readings['Percentage_Of_Lost_Packet_Rate'] = 0
        self.readings['Percentage_Of_Lost_Byte_Rate'] = 0
        self.readings['Packet_Received_Rate'] = 0
        self.readings['Lost_Bandwidth'] = 0
        self.readings['Packet_Size_Byte'] = 0
        self.readings['Packet_Received'] = 0
        self.readings['Packet_Lost'] = 0
        self.readings['Transmitted_Byte'] = 0
        self.readings['Flood_Status'] = 0
        self.readings['Important_link_BW'] = 0

    def GetSwitchList(self):
        # Get all the switches connected to the controller
        #and save them for later use
        url = self.urlbase + '/wm/core/controller/switches/json'
        response = requests.get(url, headers=self.headers, auth=self.auth)
        items = response.json()
        try:
            for i in items:
                self.switch_list.append(i['switchDPID'])
        except (ValueError, KeyError, TypeError):
            logging.debug("JSON format error")

    def GetFlowID(self, sw, flow):
        return str(sw) + "_" + str(flow["match"])

    def IsFlowToServer(self, flow):
        if (('ipv4_dst' in flow) and (flow['ipv4_dst'] == self.serverip)):
            return True
        return False

    def GetNodeID(self, flow):
        srcip = flow['ipv4_src']
        v = srcip.split('.')
        return v[3]

    def ReadFlows(self):
        url = self.urlbase + '/wm/core/switch/all/flow/json'
        response = requests.get(url, headers=self.headers, auth=self.auth)
        items = response.json()
        for sw in self.switch_list:
            if sw in items:
                it = items[sw]['flows']
                for index in range(0, len(it)):
                    f = items[sw]['flows'][index]
                    Class = 0
                    if (int(f['byteCount']) > self.flooding_threshold_byteCount):
                        Class = 1
                    if (f["match"] and self.IsFlowToServer(f['match']) == True):
                        id = self.GetFlowID(sw, f)
                        self.readings['Node'] = self.GetNodeID(f['match'])
                        self.readings['Flood_Status'] = Class
                        self.ApplyML(sw, f)
        #print (self.flows)

    def ReadPacketStats(self):
        # This function reads BW for a particular switch
        elapsed = self.curtime - self.oldvalue['last_time']
        diff = elapsed.total_seconds()
        firstime = False
        if (diff == 0):
            firstime = True
        url = self.urlbase + '/wm/core/switch/all/port/json'
        response = requests.get(url, headers=self.headers, auth=self.auth)
        items = response.json()
        allportstat = []
        for sw in self.switch_list:
            if sw in items:
                for index in range(0, len(items[sw]['port_reply'][0]['port'])):
                    it = items[sw]['port_reply'][0]['port'][index]
                    allportstat.append(it)
        txp_pkt = sum(float(item["transmitPackets"]) for item in allportstat)

        rxp_pkt = sum(float(item["receivePackets"]) for item in allportstat)
        tx_pkt = txp_pkt
        rx_pkt = rxp_pkt
        packetLost = tx_pkt - rx_pkt
        txb_byte = sum(float(item["transmitBytes"]) for item in allportstat)
        rxb_byte = sum(float(item["receiveBytes"]) for item in allportstat)

        total_bytes = txb_byte + rxb_byte
        cur_total_bytes = total_bytes - self.readings['total_bytes']
        avgMbps = 0
        div = len(allportstat) * 1024.0 * 128 * diff
        if (div > 0):
            avgMbps = cur_total_bytes / div
#print("total_bytes:", total_bytes, "cur_total_bytes",
#                 cur_total_bytes, " avgMbps ", avgMbps, " diff ", diff)
        self.readings['Used_Bandwidth'] = avgMbps
        self.readings[
            'Utilised_Bandwidth_Rate'] = avgMbps / self.readings['Link_Capacity']
        self.readings[
            'Lost_Bandwidth'] = self.readings['Link_Capacity'] - self.readings['Used_Bandwidth']
        self.readings['total_bytes'] = total_bytes

        byteLost = txb_byte - rxb_byte
        self.readings['packetLost'] = 0
        self.readings['packetSize'] = 0
        self.readings['packetReceived'] = 0
        self.readings['packetReceivedRate'] = 0
        self.readings['Packet Drop Rate'] = 0
        self.readings['lostByteRate'] = 0
        curtime = self.curtime
        if firstime == False:
            try:
                self.readings[
                    'Packet_Lost'] = packetLost - self.oldvalue['packetLost']
                self.readings[
                    'Packet_Received'] = rxp_pkt - self.oldvalue['rx_pkt']

                if (diff > 0):
                    self.readings['Packet_Received_Rate'] = (
                        rxp_pkt - self.oldvalue['rx_pkt']) / diff

                diff = (tx_pkt - self.oldvalue['tx_pkt'])
                if (diff > 0):
                    self.readings[
                        'Packet_Drop_Rate'] = self.readings['packetLost'] / diff
                self.readings[
                    'Percentage_Of_Lost_Packet_Rate'] = 100 * self.readings['Packet_Drop_Rate']
                diff = (txb_byte - self.oldvalue['txb_byte'])
                self.readings['Transmitted_Byte'] = diff
                if (diff > 0):
                    self.readings['Percentage_Of_Lost_Byte_Rate'] = 100 * (
                        byteLost - self.oldvalue['byteLost']) / diff
                if (rx_pkt > 0):
                    self.readings['Packet_Size_Byte'] = (rxb_byte / rx_pkt)
            except Exception as exception:
                print(exception)
                pass

        self.oldvalue['packetLost'] = packetLost
        self.oldvalue['tx_pkt'] = tx_pkt
        self.oldvalue['rx_pkt'] = rx_pkt
        self.oldvalue['txb_byte'] = txb_byte
        self.oldvalue['byteLost'] = byteLost

        important_port_stat = []
        for sw in self.switch_list:
            if (self.IsImportantSwitch(sw) == True):
                if sw in items:
                    for index in range(0, len(items[sw]['port_reply'][0]['port'])):
                        it = items[sw]['port_reply'][0]['port'][index]
                        if (it['portNumber'] != 'local') and (self.IsImportantPort(
                                int(it['portNumber'])) == True):
                            important_port_stat.append(it)
# print ("imp ",important_port_stat)
        txb_byte_imp = sum(
            float(item["transmitBytes"]) for item in important_port_stat)
        rxb_byte_imp = sum(
            float(item["receiveBytes"]) for item in important_port_stat)

        total_bytes_imp = txb_byte_imp + rxb_byte_imp
        #       cur_total_bytes_imp = total_bytes_imp
        cur_total_bytes_imp = total_bytes_imp - self.readings['total_bytes_imp']
        avgMbps = 0
        div = len(important_port_stat) * 1024.0 * 128 * diff
        if (div > 0):
            avgMbps = cur_total_bytes_imp / div
# print("imp total_bytes:", total_bytes_imp, "cur_total_bytes", cur_total_bytes_imp," avgMbps ", avgMbps, " diff ", diff)
        self.readings['total_bytes_imp'] = total_bytes_imp
        self.readings['Important_link_BW'] = avgMbps


#print(self.readings)

    def IsImportantSwitch(self, sw):
        for item in self.importants_links_list:
            if (item['switch_id'] == sw):
                return True
        return False

    def IsImportantPort(self, port):
        for item in self.importants_links_list:
            if (item['port_number'] == port):
                return True
        return False

    def UnclockAll(self):
        url = self.urlbase + '/wm/staticflowpusher/clear/all/json'
        response = requests.get(url, headers=self.headers, auth=self.auth)

    def BlockHost(self, sw, flow):
        url = self.urlbase + '/wm/staticflowpusher/json'
        rule = {
            'switch': sw,
            "name": "flow1",
            "cookie": "0",
            "priority": "32768",
            "active": "true",
            "src-ip": flow['ipv4_src'],
            "dst-ip": flow["ipv4_dst"],
            "action": ""
        }
        body = json.dumps(rule)
        response = requests.post(
            url, headers=self.headers, auth=self.auth, data=body)

    def ReadBW(self, sw):
        # This function reads BW for a particular switch
        url = self.urlbase + '/wm/statistics/bandwidth/' + sw + '/all/json'
        response = requests.get(url, headers=self.headers, auth=self.auth)
        data = response.json()
        #print(data)
        rx = sum(float(item["bits-per-second-rx"]) for item in data)
        tx = sum(float(item["bits-per-second-tx"]) for item in data)
        bps = rx + tx
        print("Switch: ", sw, ", bandwidth in bps: ", bps, ", in Mbps:",
              bps / (1024.0 * 128))
        return bps

    def ReadBWs(self):
        # This function reads BW for all switches using ReadBW
        totbps = 0
        for sw in self.switch_list:
            totbps = totbps + self.ReadBW(sw)
        logging.debug(
            'For all Switches total bandwidth in bps: {}, in Mbps:{}'.format(
                totbps, totbps / (1024.0 * 128)))
        avgbps = totbps
        if (len(self.switch_list)) > 0:
            avgbps = totbps / len(self.switch_list)
            avgMbps = totbps / (1024.0 * 128)
            logging.debug(
                'For all Switches average bandwidth in bps: {}, in Mbps:{}'.
                format(avgbps, avgMbps))
        self.readings['Used_Bandwidth'] = avgMbps
        self.readings[
            'Utilised_Bandwidth_Rate'] = avgMbps / self.readings['Link_Capacity']
        self.readings[
            'Lost_Bandwidth'] = self.readings['Link_Capacity'] - self.readings['Used_Bandwidth']
        print("Used_Bandwidth ", self.readings['Used_Bandwidth'], " Lost ",
              self.readings['Lost_Bandwidth'])

    def Graph(self):
        elem = {
            'Iteration':
            self.reading_iteration,
            "Time":
            self.curtime.strftime("%Y-%m-%d %H:%M:%S"),
            "FloodingRate":
            self.readings['Important_link_BW'],
            'Packet_Drop_Rate':
            self.readings['Packet_Drop_Rate'],
            'Used_Bandwidth':
            self.readings['Used_Bandwidth'],
            'Bandwidth_Saturation':
            100 * self.readings['Used_Bandwidth'] /
            self.readings['Link_Capacity'],
            'Transmitted_Byte':
            self.readings['Transmitted_Byte'],
            'No_of_Attacker': self.attack_node,
            'Detection_Time': self.detection_time 
        }
        self.graph_data_list.append(elem)
        self.WriteGraphFile()

    def ApplyML(self, sw, flow):
        test_d = np.array([
            self.readings['Node'], self.readings['Utilised_Bandwidth_Rate'],
            self.readings['Packet_Drop_Rate'], self.readings['Link_Capacity'],
            self.readings['Percentage_Of_Lost_Packet_Rate'],
            self.readings['Percentage_Of_Lost_Byte_Rate'],
            self.readings['Packet_Received_Rate'],
            self.readings['Used_Bandwidth'], self.readings['Lost_Bandwidth'],
            self.readings['Packet_Size_Byte'],
            self.readings['Packet_Received'], self.readings['Packet_Lost'],
            self.readings['Transmitted_Byte'], self.readings['Flood_Status']
        ])
        scaled_obs = self.scaler.transform(test_d.reshape(1, -1))
        #['Utilised Bandwith Rate','Packet Drop Rate','Link_Capacity','Percentage_Of_Lost_Packet_Rate','Percentage_Of_Lost_Byte_Rate','Packet Received  Rate','Used_Bandwidth','Lost_Bandwidth','Packet Size_Byte','Packet_Received','Packet_lost','Transmitted_Byte','Flood Status']
        # The observation needs to be of type array
        prediction, confidence = predict(self.loaded_model,
                                         scaled_obs.reshape(1, -1))
        logging.debug('Classification prediction: {}, confidence: {}'.format(
            prediction, confidence))
        conf_percent = confidence * 100
        if (conf_percent > self.confidence_level):
            elapsed = self.curtime -  self.start_time  
            diff = elapsed.total_seconds()
            self.detection_time = diff
            self.attack_node = self.attack_node +1
            logging.debug(
                'Applying action {} with confidence level {} source IP {}'.
                format(self.action, conf_percent, flow['match']['ipv4_src']))
            if (self.action == "drop_host"):
                self.BlockHost(sw, flow['match'])

    def WriteGraphFile(self):
        output_file = open('graph_data.csv', 'w')
        keys = self.graph_data_list[0].keys()
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(self.graph_data_list)

    def StatLoop(self):
        self.curtime = datetime.datetime.now()
        self.start_time = self.curtime
        self.last_time = self.curtime
        self.oldvalue['start_time'] = self.curtime
        self.oldvalue['last_time'] = self.curtime
        logging.debug('Loading Model {} '.format(self.ml_model))
        self.loaded_model = load_model(self.ml_model)
        self.scaler = joblib.load("scaler.save")
        while self.shouldcontinue == True:
            try:
                #reset the readings
                #get  Utilized Bandwidth

                if (self.reading_iteration > 0):
                    self.oldvalue['last_time'] = self.curtime
                    self.curtime = datetime.datetime.now()
                self.reading_iteration = self.reading_iteration + 1
                #self.ReadBWs()
                #get all flow and its class
                #get all pakcet stats like Packet Size, Packets Received, Packets Loss,Packets Received Rate,Lost Byte Rate,Packet Drop Rate
                self.ReadPacketStats()
                self.ReadFlows()
                self.Graph()
                time.sleep(self.interval)
                program_elapsed = self.curtime - self.start_time
                if (program_elapsed.total_seconds() > self.duration):
                    self.WriteGraphFile()
                    self.UnclockAll()
                    break
            except KeyboardInterrupt:
                logging.debug('Keyboard exception received. Exiting.')
                exit()

logging.basicConfig(
    filename='statcollector.log',
    filemode='w',
    format=
    '%(levelname)-8s:%(asctime)12s:%(funcName)12s: line %(lineno)3d : %(message)s',
    datefmt='%H:%M:%S',
    level=logging.DEBUG)
json_data = open("config.json").read()
data = json.loads(json_data)
statc = StatCollector(
    int(data['stat_collector_config']['collection_interval_sec']),
    int(data['stat_collector_config']['programme_duration_min']),
    data['controller']['controller_ip'],
    data['controller']['controller_rest_port'],
    data['stat_collector_config']['flooding_threshold_byteCount'],
    data['traffic_config']['link_capacity_in_Mbit'],
    data['traffic_config']['iperf_server'], 
    data['traffic_config']['iperf_client'], 
    data['important_link'],
    data['machine_learning_config'])

statc.GetSwitchList()
statc.StatLoop()
