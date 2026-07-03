import requests
import time
import os
import getpass

# whether or not to use ntfy's public server, if not use ntfyUrl
pub = False
ntfyUrl = "http://rpi-node:8070/gasPrice"

uname = getpass.getuser()

fn = "/home/" + uname + "/gas-shit/currPrice"
fn2 = "/home/" + uname + "/gas-shit/raiseTime"
rows = []

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


# boilerplate merge sort
# this is here because I originally intended to compare multiple locations
def merge(arr, l, m, r):
    n1 = m - l + 1
    n2 = r - m

    L = [0] * n1
    R = [0] * n2

    for i in range(n1):
        L[i] = arr[l + i]
    for j in range(n2):
        R[j] = arr[m + 1 + j]

    i = j = 0
    k = l

    while i < n1 and j < n2:
        if L[i] <= R[j]:
            arr[k] = L[i]
            i += 1
        else:
            arr[k] = R[j]
            j += 1
        k += 1

    while i < n1:
        arr[k] = L[i]
        i += 1
        k += 1

    while j < n2:
        arr[k] = R[j]
        j += 1
        k += 1

def mergeSort(arr, l, r):
    if l < r:
        m = l + (r - l) // 2
        mergeSort(arr, l, m)
        mergeSort(arr, m + 1, r)
        merge(arr, l, m, r)

# send notification
def notify (msg):
    if pub == True:
        requests.post("https://ntfy.sh/gasPrice", data=msg.encode(encoding='utf-8'))
    else:
        requests.post(ntfyUrl, data=msg.encode(encoding='utf-8'))
# grab stores around area
stores = requests.get("https://api.kwiktrip.com/api/stores/nearby", params=params).json()["stores"]

# grab gas prices from stores
for p in stores:
    store = p['id']

    storedata = requests.get(f"https://api.kwiktrip.com/api/location/store/information/{store}").json()

    fuel = storedata['fuel']

    rows.append([p['name'], fuel[0]['type'], fuel[0]['currentPrice']])

# put prices in array to sort
if lim > 1:
    price = []
    for i in rows:
        price.append(i[2])

    mergeSort(price, 0, len(price) - 1)
    lowPrice = price[0]
else:
    lowPrice = rows[0][2]

# read current price from file and convert to float
f1 = open(fn, "r")
currPrice = f1.read()
f1.close()
currPrice = float(currPrice)

# core logic, checks if the lowest price is higher or lower, notifies if lower, sets a time 24hrs in the future if higher, notifies if price is higher and the 24hr time has passed, does nothing if price is the same
if lowPrice < currPrice:
    f1 = open(fn, "w")
    f1.write(str(lowPrice))
    f1.close()
    notify("lower price to: $" + str(lowPrice))
    if os.path.exists(fn2):
        os.remove(fn2)
elif lowPrice > currPrice:
    if os.path.exists(fn2):
        f2 = open(fn2, "r")
        raiseTime = f2.read()
        f2.close()
        raiseTime = float(raiseTime)
        if raiseTime < time.time():
            notify("raise price to: $" + str(lowPrice))
            f1 = open(fn, "w")
            f1.write(str(lowPrice))
            f1.close()
            os.remove(fn2)
    else:
        f2 = open(fn2, "w")
        f2.write(str(time.time() + raiseFuture))
        f2.close()
        notify("price raised to $" + str(lowPrice) + ", wait 24 hours")
