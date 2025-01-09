import pywinusb.hid as hid

def print_data(data):
        print(f"Received data: {data}")

# Enumerate HID devices
all_devices = hid.HidDeviceFilter().get_devices()
keyboards = [dev for dev in all_devices if "FootSwitch" in dev.product_name]

print("Detected keyboards:")
for keyboard in keyboards:
    print(f"Device: {keyboard.product_name}")
    #print(keyboard.get_input_report_descriptors())
    keyboard.open()
    for report in keyboard.find_output_reports():
        print(report)

print("Opening specific keyboard")
# Open a specific keyboard
if keyboards:
    dev = keyboards[0]  # Replace with the appropriate device
    # o = dev.open()
    dev.set_raw_data_handler(print_data)
    print(f"Listening to input from: {dev.product_name}")
                                        
    # Keep the script running
    input("Press Enter to exit...\n")
    dev.close()

