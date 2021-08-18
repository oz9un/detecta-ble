# Author Özgün Kültekin
# BLE Scanner

import argparse, os, time
from bluepy.btle import *
from pyfiglet import Figlet
from collections import defaultdict

# Global variables:
ADVERTISING_MACS = defaultdict(dict)
RSSI = defaultdict(dict)
SHOW_RSSI = False
SHOW_ADV = False
FILE_WRITE = ""


# Default Delegate function to automatically process received adv packets.
class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    #Override the handleDiscovery method, thus we can keep statistics.
    def handleDiscovery(self, scanEntry, isNewDev, isNewData):
        # This function called when advertising data is received from an LE device.
        if isNewDev:
            if SHOW_ADV:
                print("New advertising device found!: ", scanEntry.addr)
            ADVERTISING_MACS[scanEntry.addr] = 0

        ADVERTISING_MACS[scanEntry.addr] += 1
        
        RSSI[scanEntry.addr] = scanEntry.rssi
        if SHOW_RSSI:
            print(RSSI)


# Where magic happens.
def BLEScanner(scanTime, interface):
    scanner = Scanner(1).withDelegate(ScanDelegate())
    devices = scanner.scan(scanTime)

    for dev in devices:
        print('------------------------------------------------')
        print("Device Address -> " + dev.addr)
        print("RSSI -> " + str(dev.rssi))
        if dev.connectable:
            try:
                p1 = Peripheral(dev.addr, iface=interface)
                services = p1.getServices()
                if len(services) > 0:
                    print("\nSERVICES FOUND!")
                    for serv in list(services):
                        print("Service UUID -> ", serv.uuid)
                        characteristics = serv.getCharacteristics()
                        if len(characteristics) > 0:
                            print("\nCharacteristics:")
                            for char in characteristics:
                                print("Characteristic UUID -> ", char.uuid)
                                print("Characteristic Properties -> ", char.propertiesToString())

            except:
                pass
        print('------------------------------------------------\n\n')

        print('--------------------ADVERTISING COUNTS--------------------')
        for adv in ADVERTISING_MACS.keys():
            print(adv + "  ->  " + str(ADVERTISING_MACS[adv]))
        print('----------------------------------------------------------')

    if FILE_WRITE != "":
        fileOperations()


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
    parser.add_argument("-t", "--scan_time", default=10, help="Indicates the scanning time.")
    parser.add_argument("-iface", "--interface", default=1, required=True, help="Set your bluetooth dongle iface. E.g: for hci1, type 1")
    parser.add_argument("-adv", '--show_adv', action='store_true', default=False)
    parser.add_argument("-rssi", '--show_rssi', action='store_true', default=False)
    parser.add_argument("-w", "--write_folder", default="")

    args = vars(parser.parse_args())

    SHOW_ADV = args['show_adv']
    SHOW_RSSI = args['show_rssi']
    FILE_WRITE = args['write_folder']

    f = Figlet(font='slant')
    print(f.renderText('DETECTA_BLE'))
    time.sleep(2)
    
    BLEScanner(args['scan_time'], args['interface'])
