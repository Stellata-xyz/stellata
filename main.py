import logging
import time
import threading

from indi.client.indiclient import IndiClient
from indi.INDI import INDI
from indi.client.indievent import IndiEvent, IndiEventType

# INDI settings
host = 'localhost'
port = 7624
driver_name = "Telescope Simulator"

# logging default (stderr)
logging.basicConfig(format='%(asctime)s: %(name)-8s %(levelname)-8s %(message)s', level=logging.INFO)
logger = logging.getLogger('indiclient')

client = IndiClient(host=host, port=port, logger=logger)
if not client.connect():
    # logger.warning('INDI server not reachable')
    logging.error("FAILED")
    logging.error("No indiserver running on " + client.getHost() + ":" + str(client.getPort()))
    # sys.exit(1)

logging.debug(client.getHost(), client.getPort())

# Geographic location
#latitude = '59:51:05.0'
#longitude = '17:37:30.0'


# Script settings
update_delay = 1  # delay in s between updates

DEVICE_NAME = driver_name
client.wait_device(DEVICE_NAME, connect=False)
device_telescope = client.devices[DEVICE_NAME]
logging.debug(DEVICE_NAME, 'is here', [p for p in client.devices[DEVICE_NAME].properties.keys()])
telescope_connect = device_telescope.getSwitch("CONNECTION")
while not (telescope_connect):
    time.sleep(0.5)
    telescope_connect = device_telescope.getSwitch("CONNECTION")

# if the telescope device is not connected, we do connect it
# Not wirking yet

# We want to set the ON_COORD_SET switch to engage tracking after goto
# device.getSwitch is a helper to retrieve a property vector
logging.info("Set tracking mode ... ")
telescope_on_coord_set = device_telescope.getSwitch("ON_COORD_SET")

while not (telescope_on_coord_set):
    time.sleep(0.5)
    telescope_on_coord_set = device_telescope.getSwitch("ON_COORD_SET")

# the order below is defined in the property vector, look at the standard Properties page
# or enumerate them in the Python shell when you're developing your program
telescope_on_coord_set.vp['TRACK'].s = INDI.ISState.ISS_ON  # TRACK
telescope_on_coord_set.vp['SLEW'].s = INDI.ISState.ISS_OFF # SLEW
telescope_on_coord_set.vp['SYNC'].s = INDI.ISState.ISS_OFF  # SYNC
client.send_new_property(telescope_on_coord_set)

# Now let's make a goto to vega
# Beware that ra/dec are in decimal hours/degrees
vega = {'ra': (144.8958 * 24.0) / 360.0, 'dec': 15.2300}

telescope_on_coord_set = device_telescope.getSwitch("ON_COORD_SET")
logging.info(f"Telescope Slew Status: {telescope_on_coord_set.vp['SLEW'].s}")


telescope_radec = device_telescope.getNumber("EQUATORIAL_EOD_COORD")
logging.info(f"Telescope Slew Status: {telescope_on_coord_set.vp['SLEW'].s}")

while not (telescope_radec):
    time.sleep(0.5)
    telescope_radec = device_telescope.getNumber("EQUATORIAL_EOD_COORD")
logging.info(f"Telescope Slew Status: {telescope_on_coord_set.vp['SLEW'].s}")

telescope_radec.vp['RA'].value = vega['ra']
telescope_radec.vp['DEC'].value = vega['dec']
logging.info(f"RA={telescope_radec.vp['RA'].value}")
logging.info(f"DEC={telescope_radec.vp['DEC'].value}")
client.send_new_property(telescope_radec)
logging.debug(f"Telescope RA/DEC Status: {telescope_radec.s}")

while telescope_radec.s == INDI.IPState.IPS_BUSY:
    logging.info("Scope Moving ", telescope_radec[0].value, telescope_radec[1].value)
    time.sleep(2)

print('TEST')
ccd = 'CCD Simulator'
device_ccd=client.devices[ccd]
while not device_ccd:
    time.sleep(0.5)
    device_ccd = client.getDevice(ccd)

print("TEST2")
ccd_connect = device_ccd.getSwitch("CONNECTION")
print(ccd_connect)
while not ccd_connect:
    time.sleep(0.5)
    ccd_connect = device_ccd.getSwitch("CONNECTION")

ccd_active_devices = device_ccd.getText("ACTIVE_DEVICES")
logging.info(f"ACTIVE Devices: {ccd_active_devices}")
while not (ccd_active_devices):
    time.sleep(0.5)
    ccd_active_devices = device_ccd.getText("ACTIVE_DEVICES")

ccd_exposure = device_ccd.getNumber("CCD_EXPOSURE")
logging.info(f"CCD Exposure: {ccd_exposure}")
while not ccd_exposure:
    time.sleep(0.5)
    ccd_exposure = device_ccd.getNumber("CCD_EXPOSURE")


client.send_new_property(ccd_active_devices)


client.set_blob_mode(INDI.BLOBHandling.B_ALSO, device_ccd, None)

indi_event=IndiEvent(None, device=device_ccd, value=None)


ccd_ccd1 = device_ccd.getBLOB("CCD1")
while not ccd_ccd1:
    logging.info("NOT CCD1")
    time.sleep(0.5)
    ccd_ccd1 = device_ccd.getBLOB("CCD1")

exposures = [1.0, 5.0, 6.0, 7.0, 10.0]
blobEvent = threading.Event()
blobEvent.clear()
i = 0


ccd_exposure.vp['CCD_EXPOSURE_VALUE'].value = exposures[i]

client.send_new_property(ccd_exposure)
while i < len(exposures):
    # wait for the ith exposure
    # blobEvent.wait()
    # we can start immediately the next one
    if i + 1 < len(exposures):
        ccd_exposure.vp['CCD_EXPOSURE_VALUE'].value = exposures[i + 1]
        blobEvent.clear()
        client.send_new_property(ccd_exposure)
    # and meanwhile process the received one
        blob = ccd_ccd1.vp['CCD1']
        logging.info(f"name: {blob.name} size: {blob.size} format: {blob.format}")
        # pyindi-client adds a getblobdata() method to IBLOB item
        # for accessing the contents of the blob, which is a bytearray in Python
        fits = blob.blob
        logging.info(f"fits data type: {type(fits)}")
        # here you may use astropy.io.fits to access the fits data
        # and perform some computations while the ccd is exposing
        # but this is outside the scope of this tutorial
    i += 1
