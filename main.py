import board
import busio
import displayio
from adafruit_ov7670 import OV7670
import sdcardio
import storage
from adafruit_st7735r import ST7735R
from adafruit_bitmapsaver import save_pixels
import ulab
import struct
import gc

# SD card pins
sd_mosi_pin = board.GP19
sd_miso_pin = board.GP16
clk_pin = board.GP18
sd_cs_pin = board.GP17

capture_file = "/sd/frame{}.bmp"

# Setup sd card 
spi = busio.SPI(clk_pin, MOSI=sd_mosi_pin, MISO=sd_miso_pin)
sdcard = sdcardio.SDCard(spi, sd_cs_pin)
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
shader = displayio.ColorConverter(input_colorspace=displayio.Colorspace.RGB565_SWAPPED)
camera_image_tile = displayio.TileGrid(
    camera_image,
    pixel_shader=shader,
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

def rbg565_to_bgr(color):
    blue = (color << 3) & 0x00F8
    green = (color >> 3) & 0x00FC
    red = (color >> 8) & 0x00F8
    return [red, green, blue]

def convert_bitmap(bm):
    colors = ulab.numpy.zeros(bm.width * bm.height * 3, dtype=ulab.numpy.uint8)
    width = bm.width
    height = bm.height
    for x in range(width):
        for y in range(height):
            # The color value is the pixel value at (x, y)
            color_value = bm[x, y]
            colors[y * width + x] = rbg565_to_bgr(color_value)
    return colors

def save_as_bmp(filename, width, height, rgb_data):
    # Each row must be padded to a multiple of 4 bytes
    row_size = (width * 3 + 3) & ~3
    padding = row_size - width * 3
    pixel_array = b''

    # BMP stores pixels bottom-up, so we reverse the rows
    for y in range(height - 1, -1, -1):
        row = b''
        for x in range(width):
            i = (y * width + x) * 3
            r, g, b = rgb_data[i:i+3]
            row += bytes([b, g, r])  # BMP uses BGR
        row += b'\x00' * padding
        pixel_array += row

    # File header (14 bytes)
    file_size = 14 + 40 + len(pixel_array)
    bmp_header = b'BM' + struct.pack('<IHHI', file_size, 0, 0, 54)

    # DIB header (40 bytes)
    dib_header = struct.pack('<IIIHHIIIIII',
        40, width, height, 1, 24, 0,
        len(pixel_array), 2835, 2835, 0, 0
    )

    with open(filename, 'wb') as f:
        f.write(bmp_header)
        f.write(dib_header)
        f.write(pixel_array)

display.auto_refresh = False
img_idx = 0
while True:
    cam.capture(camera_image)
    filename = capture_file.format(img_idx)
    save_pixels(filename, camera_image, shader)
    img_idx += 1
    print("Saved Image {}".format(img_idx))
    gc.collect()

# while True:
#     cam.capture(camera_image)
#     camera_image.dirty()
#     display.refresh(minimum_frames_per_second=0)
#     w = camera_image.width
#     h = camera_image.height
#     data = convert_bitmap(camera_image)
#     filename = capture_file.format(img_idx)
#     save_as_bmp(filename, w, h, data)
#     print("Saved Image {}".format(img_idx))
#     img_idx += 1
#     gc.collect()