# Author Özgün Kültekin
# BLE Scanner

import argparse, os, time, json
from bluepy.btle import *
from pyfiglet import Figlet
from collections import defaultdict
from prettytable import PrettyTable

# Global variables:
ADVERTISING_MACS = defaultdict(int)
ALL_DETAILS = {}
RSSI = defaultdict(int)
SHOW_RSSI = False
SHOW_ADV = False
JSON_WRITE = False
FILE_WRITE = ""


# Default Delegate function to automatically process received adv packets.
class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    # Override the handleDiscovery method, thus we can keep statistics.
    def handleDiscovery(self, scanEntry, isNewDev, isNewData):
        # This function called when advertising data is received from an LE device.
        if isNewDev:
            if SHOW_ADV:
                print("New advertising device found!: ", scanEntry.addr)
            ADVERTISING_MACS[scanEntry.addr] = 0
            ALL_DETAILS[scanEntry.addr] = {}

        ADVERTISING_MACS[scanEntry.addr] += 1
        RSSI[scanEntry.addr] = scanEntry.rssi

        if SHOW_RSSI:
            for key in RSSI:
                print(key + " -> " + str(RSSI[key]))

    # Override the handleNotification method, it is called when a notification or indication is received from a connected Peripheral object.
    # But this function will be mostly unnecessary, because detecta_ble will be used for scanning purposes.
    def handleNotification(self, cHandle, data):
        print("Notification received")
        print("chandle -> " + cHandle)
        print(binascii.b2a_hex(data))


def serviceExtractor(services, addr):
    if len(services) > 0:
        print("\nSERVICES FOUND!")
        for serv in list(services):
            ALL_DETAILS[addr][str(serv.uuid)] = {}
            print("Service UUID -> ", serv.uuid)
            characteristics = serv.getCharacteristics()
            charsExtractor(characteristics, addr, serv.uuid)    
    else:
        print("No service detected for this device.")                


def charsExtractor(characteristics, addr, service_uuid):
    if len(characteristics) > 0:
        print("\nCharacteristics:")
        for char in characteristics:
            charPropParser(char.properties)
            ALL_DETAILS[addr][str(service_uuid)][str(char.uuid)] = charPropParser(char.properties)
            print("Characteristic UUID -> ", char.uuid)
            print("Characteristic Properties -> ", char.propertiesToString())
    else:
        print("No characteristic detected for this service.")


def charPropParser(properties):
    # BLE GATT CHARACTERISTIC PROPERTIES BIT VALUES:
    bit_values = {
        1: "BROADCAST",
        2: "READ",
        4: "WRITE WITHOUT RESPONSE",
        8: "WRITE",
        16: "NOTIFY",
        32: "INDICATE",
        64: "WRITE WITH SIGNATURE",
        128: "HAS EXTENDED PROPERTIES",
        256: "WRITE WITH SIGNATURE AND MITM PROTECTION"
    }

    detected_properties = []
    current_value = properties
    check = 256
    while(current_value != 0):
        if(current_value >= check):
            current_value -= check
            detected_properties.append(bit_values[check])
        check /= 2
    return detected_properties


# Where magic happens.
def BLEScanner(scanTime, interface):
    scanner = Scanner(interface).withDelegate(ScanDelegate())
    devices = scanner.scan(int(scanTime))

    for dev in devices:
        print('------------------------------------------------')
        print("Device Address -> " + dev.addr)
        print("RSSI -> " + str(dev.rssi))
        if dev.connectable:
            try:
                p1 = Peripheral(dev.addr, iface=interface)
                services = p1.getServices()
                serviceExtractor(services, dev.addr)
            except:
                pass
        print('------------------------------------------------\n\n')

    print('--------------------ADVERTISING COUNTS--------------------')
    for adv in ADVERTISING_MACS.keys():
        print(adv + "  ->  " + str(ADVERTISING_MACS[adv]))
    print('----------------------------------------------------------')

    if FILE_WRITE != "":
        fileOperations()
    if JSON_WRITE:
        timestr = time.strftime("%Y%m%d-%H%M%S")
        json_output = open(timestr+".json", 'w')
        json_output.write(json.dumps(ALL_DETAILS, indent=4))
        json_output.close()

# If -w parameter is specified, create statistics files in target folder
def fileOperations():
    if not os.path.exists(FILE_WRITE):
        os.makedirs(FILE_WRITE)
    
    adv_statistics = open(FILE_WRITE + "/adv_statistics.txt", "w")
    rssi_file = open(FILE_WRITE + "/rssi_list.txt", "w")

    for adv in ADVERTISING_MACS.keys():
        adv_statistics.write(adv + "  ->  " + str(ADVERTISING_MACS[adv]))
        adv_statistics.write('\n')

    for rssi in RSSI.keys():
        rssi_file.write(adv + "  ->  " + str(RSSI[rssi]))
        rssi_file.write('\n')

    adv_statistics.close()
    rssi_file.close()



if __name__ == '__main__':
    # Get user parameters:
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--scan_time", default=10, help="Scanning time for surrounding BLE devices (seconds) (default=10)")
    parser.add_argument("-iface", "--interface", default=1, required=True, help="Set your bluetooth dongle iface (hciX). E.g: for hci1, type 1")
    parser.add_argument("-adv", '--show_adv', action='store_true', default=False, help="Show real-time advertisement packets while detecta-ble is scanning.")
    parser.add_argument("-rssi", '--show_rssi', action='store_true', default=False, help="Enable showing real-time rssi values of advertisement packets while detecta-ble is scanning.")
    parser.add_argument("-w", "--write_folder", default="", help="Name of the folder if you want to keep statistics for 'advertisement packet counts per device' and 'latest rssi values of devices'")
    parser.add_argument("-json", "--json", action='store_true', default=False, help="Save output in json format")

    args = vars(parser.parse_args())
    
    SHOW_ADV = args['show_adv']
    SHOW_RSSI = args['show_rssi']
    FILE_WRITE = args['write_folder']
    JSON_WRITE = args['json']


    f = Figlet(font='slant')
    print(f.renderText('DETECTA - BLE'))
    time.sleep(2)
    
    BLEScanner(args['scan_time'], args['interface'])