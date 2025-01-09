import hid

VENDOR = 13651
PRODUCT = 45057

devices = hid.enumerate()

print("usage_page usage interface_number bus_type")
while True:
    for device in devices:
        if (device['vendor_id']==VENDOR) and (device['product_id']==PRODUCT): #  and (device["usage_page"]==1) and (device["usage"]==0):
            # print(device)
            try:
                dev = hid.device()
                dev.open_path(device['path'])
                dev.set_nonblocking(True)
                data = dev.read(1)
                print(data, end="")
            except:
                print("Fail", end="")
