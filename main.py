import board
import busio
import displayio
from adafruit_ov7670 import OV7670
import sdcardio
import storage
from adafruit_st7735r import ST7735R
import ulab
import struct

# SD card pins
sd_mosi_pin = board.GP19
sd_miso_pin = board.GP16
clk_pin = board.GP18
sd_cs_pin = board.GP17

capture_file = "/sd/frame{}.jpg"

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
camera_image_tile = displayio.TileGrid(
    camera_image ,
    pixel_shader=displayio.ColorConverter(input_colorspace=displayio.Colorspace.RGB565_SWAPPED),
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

def create_palette(bm):
    colors = []
    for x in range(bm.width):
        for y in range(bm.height):
            # The color value is the pixel value at (x, y)
            color_value = bm[x, y]
            colors.append(color_value)
    palette = displayio.Palette(len(colors))
    for i, color in enumerate(colors):
        palette[i] = color
    return palette

def save_as_bmp(filename, width, height, pixel_data):
    with open(filename, 'wb') as fh:
        # BMP Header
        fh.write(b'BM')
        file_size = 54 + len(pixel_data)
        fh.write(struct.pack('<IHHI', file_size, 0, 0, 54))
        
        # DIB Header
        fh.write(struct.pack('<IiiHHIIiiII',
            40, width, height, 1, 24, 0,
            len(pixel_data), 2835, 2835, 0, 0
        ))
        
        # Pixel Data (BGR format)
        fh.write(pixel_data)

display.auto_refresh = False
img_idx = 0
while True:
    cam.capture(camera_image)
    camera_image.dirty()
    display.refresh(minimum_frames_per_second=0)
    # palette = create_palette(camera_image)
    # buffer = ulab.numpy.frombuffer(camera_image)
    filename = capture_file.format(img_idx)
    save_as_bmp(filename, camera_image.width, camera_image.height, camera_image)
    print("Saved Image {}".format(img_idx))
    img_idx += 1    