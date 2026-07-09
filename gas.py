import requests
import time
import os
import getpass

# whether or not to use ntfy's public server, if not use ntfyUrl
pub = True 
ntfyUrl = "http://rpi-node:8070/gasPrice"

#file names
uname = getpass.getuser()

unleadPriceFn = "/home/" + uname + "/gas-shit/currPriceUnlead"
unleadTimeFn = "/home/" + uname + "/gas-shit/raiseTimeUnlead"
dieselPriceFn = "/home/" + uname + "/gas-shit/currPriceDiesel"
dieselTimeFn = "/home/" + uname + "/gas-shit/raiseTimeDiesel"

# time to wait to raise price in seconds
raiseFuture = 86400

lat = 44.512947
long = -87.960007
lim = 1

# params to grab local stores
params = {
    'latitude': lat,
    'longitude': long,
    'limit': lim
}

def fileCheck (fn):
    # make sure curr price exists and has correct data
    if os.path.exists(fn):
        f1 = open(fn, "r")
        read = f1.read()
        f1.close()
        try:
            read = float(read)
        except:
            f1 = open(fn, "w")
            f1.write(str(999))
            f1.close()
    else:
        f1 = open(fn, "w")
        f1.write(str(999))
        f1.close()

fileCheck(unleadPriceFn)
fileCheck(dieselPriceFn)

# send notification
def notify (msg):
    if pub == True:
        requests.post("https://ntfy.sh/gasPrice", data=msg.encode(encoding='utf-8'))
    else:
        requests.post(ntfyUrl, data=msg.encode(encoding='utf-8'))

# grab store
stores = requests.get("https://api.kwiktrip.com/api/stores/nearby", params=params).json()["stores"]

# grab gas prices from store
store = stores[0]['id']

storedata = requests.get(f"https://api.kwiktrip.com/api/location/store/information/{store}").json()

fuel = storedata['fuel']
    
prices = [fuel[0]['currentPrice'], fuel[4]['currentPrice']]

def priceCheck (priceFn, timeFn, lowPrice, name):
    # grab current price from file and conver to float
    f1 = open(priceFn, "r")
    currPrice = f1.read()
    f1.close()
    currPrice = float(currPrice)
    
    # core logic, checks if the lowest price is higher or lower, notifies if lower, sets a time 24hrs in the future if higher, notifies if price is higher and the 24hr time has passed, does nothing if price is the same
    
    if lowPrice < currPrice:
        f1 = open(priceFn, "w")
        f1.write(str(lowPrice))
        f1.close()
        notify("lower " + name + " price: $" + str(lowPrice))
        if os.path.exists(timeFn):
            os.remove(timeFn)
    elif lowPrice > currPrice:
        if os.path.exists(timeFn):
            f2 = open(timeFn, "r")
            raiseTime = f2.read()
            f2.close()
            raiseTime = float(raiseTime)
            if raiseTime < time.time():
                notify("raise " + name + " price: $" + str(lowPrice))
                f1 = open(priceFn, "w")
                f1.write(str(lowPrice))
                f1.close()
                os.remove(timeFn)
        else:
            f2 = open(timeFn, "w")
            f2.write(str(time.time() + raiseFuture))
            f2.close()
            notify(name + " price raised to $" + str(lowPrice) + ", wait 24 hours")

priceCheck(unleadPriceFn, unleadTimeFn, prices[0], "unleaded")

priceCheck(dieselPriceFn, dieselTimeFn, prices[1], "diesel")
