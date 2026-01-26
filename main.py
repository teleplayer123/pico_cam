import board
import busio
import displayio
from adafruit_ov7670 import OV7670
import sdcardio
import storage
from adafruit_st7735r import ST7735R
import struct
import time


# Helper Functions

def save_bmp_from_bitmap(
    filename,
    bitmap
):
    width = bitmap.width
    height = bitmap.height
    row_raw = width * 2
    row_padded = (row_raw + 3) & ~3
    pixel_data_size = row_padded * height
    header_size = 14 + 40 + 12
    file_size = header_size + pixel_data_size

    with open(filename, "wb") as f:
        # BMP HEADER
        f.write(b"BM")
        f.write(struct.pack("<IHHI",
            file_size, 0, 0, header_size
        ))

        # DIB HEADER
        f.write(struct.pack("<IIIHHIIIIII",
            40, width, height, 1, 16, 3,
            pixel_data_size, 2835, 2835, 0, 0
        ))

        # RGB565 MASKS
        f.write(struct.pack("<III",
            0xF800, 0x07E0, 0x001F
        ))

        # PIXELS (bottom-up)
        for y in range(height - 1, -1, -1):
            for x in range(width):
                pixel = bitmap[x, y]   # 0–65535
                f.write(bytes((
                    pixel & 0xFF,
                    (pixel >> 8) & 0xFF
                )))
            f.write(b"\x00" * (row_padded - row_raw))

# SD card pins
sd_mosi_pin = board.GP19
sd_miso_pin = board.GP16
clk_pin = board.GP18
sd_cs_pin = board.GP17

capture_file = "/sd/frame{}.bmp"

# Setup sd card 
spi = busio.SPI(clk_pin, MOSI=sd_mosi_pin, MISO=sd_miso_pin)
sdcard = sdcardio.SDCard(spi, sd_cs_pin, baudrate=1000000)
vfs = storage.VfsFat(sdcard)
storage.mount(vfs, "/sd")

#Setting up the TFT LCD display
mosi_pin = board.GP11
clk_pin = board.GP10
reset_pin = board.GP26
cs_pin = board.GP28
dc_pin = board.GP27

displayio.release_displays()
spi = busio.SPI(clock=clk_pin, MOSI=mosi_pin)
display_bus = displayio.FourWire(spi, command=dc_pin, chip_select=cs_pin, reset=reset_pin)
display = ST7735R(display_bus, width=128, height=160, bgr=True)
group = displayio.Group(scale=2)
display.root_group.append(group)

cam_width = 80
cam_height = 60
cam_size = 3 #80x60 resolution

camera_image = displayio.Bitmap(cam_width, cam_height, 65536)
camera_image_tile = displayio.TileGrid(
    camera_image ,
    pixel_shader=displayio.ColorConverter(
        input_colorspace=displayio.Colorspace.RGB565_SWAPPED
    ),
    x=0,
    y=0,
)
group.append(camera_image_tile)
camera_image_tile.transpose_xy=True

# Setup up the camera
cam_bus = busio.I2C(board.GP21, board.GP20)

cam = OV7670(
    cam_bus,
    data_pins=[
        board.GP0,
        board.GP1,
        board.GP2,
        board.GP3,
        board.GP4,
        board.GP5,
        board.GP6,
        board.GP7,
    ],
    clock=board.GP8,
    vsync=board.GP13,
    href=board.GP12,
    mclk=board.GP9,
    shutdown=board.GP15,
    reset=board.GP14,
)
cam.size =  cam_size
cam.flip_y = True

#display.auto_refresh = False
img_idx = 0
while True:
    cam.capture(camera_image)
    time.sleep(0.5)
    camera_image.dirty()
    save_bmp_from_bitmap(capture_file.format(img_idx), camera_image)
    # with open(capture_file.format(img_idx), "wb") as fh:
    #     fh.write(camera_image)
    img_idx += 1
    display.refresh()