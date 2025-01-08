import threading
import pystray
from pystray import Icon as icon, Menu as menu, MenuItem as item
from PIL import Image, ImageDraw, ImageFont
import time
from cuesdk import CueSdk, CorsairDeviceFilter, CorsairDeviceType, CorsairError, CorsairDevicePropertyId

def create_image(image, level):
    draw = ImageDraw.Draw(image)
    draw.rectangle((22, 80, 22+(level*2), 175), fill=(0, 128, 0))
    font = ImageFont.truetype('font.ttf', size=120)
    if len(str(level)) == 3:
        coord = (25, 45)
    elif len(str(level)) == 2:
        coord = (52, 45)
    else:
        coord = (90, 45)
    draw.text(coord, str(level), fill='white', font=font)   
    return image

def none():
    pass

def create_or_update_battery_icons(icons, image, disconnected, battery_levels):
    updated_icons = {}
    for device, level in battery_levels:
        if level is None:
            img = disconnected
            title = f"{device}\n연결 해제됨"
        else:
            img = create_image(image.copy(), level)
            title = f"{device}\n배터리 잔량: {level}%"
        if device in icons:
            icons[device].icon = img
            icons[device].title = title
            icons[device].menu = menu(
                item(text=f'{device}', action=none),
                item(text=f'배터리 잔량: {level}%' if level is not None else '연결 해제됨', action=none)
            )
            updated_icons[device] = icons[device]
        else:
            icon_obj = pystray.Icon(
                name=device,
                title=title,
                icon=img,
                menu=menu(
                    item(text=f'{device}', action=none),
                    item(text=f'배터리 잔량: {level}%' if level is not None else '연결 해제됨', action=none)
                )
            )
            icon_obj.run_detached()
            updated_icons[device] = icon_obj
    return updated_icons

def update_battery_levels(sdk, image, disconnected):
    icons = {}
    while True:
        battery_levels = []
        devices, err = sdk.get_devices(CorsairDeviceFilter(device_type_mask=CorsairDeviceType.CDT_All))
        if err == CorsairError.CE_Success and devices:
            for d in devices:
                device, err = sdk.get_device_info(d.device_id)
                if device:
                    battery_level = None
                    battery, err = sdk.read_device_property(d.device_id, CorsairDevicePropertyId.CDPI_BatteryLevel)
                    if err == CorsairError.CE_Success and battery:
                        battery_level = battery.value
                    battery_levels.append((device.model, battery_level))
        icons = create_or_update_battery_icons(icons, image, disconnected, battery_levels)
        time.sleep(3)

if __name__ == "__main__":
    image = Image.open('battery.png')
    disconnected = Image.open('disconnected.png')
    sdk = CueSdk()

    def on_state_changed(evt):
        print(evt.state)

    err = sdk.connect(on_state_changed)
    details, err = sdk.get_session_details()
    print(details)
    
    battery_thread = threading.Thread(target=update_battery_levels, args=(sdk, image, disconnected))
    battery_thread.start()
    while True:
        time.sleep(3)
