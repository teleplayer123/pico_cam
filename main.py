import board
import busio
import displayio
from adafruit_ov7670 import OV7670
import sdcardio
import storage
from adafruit_st7735r import ST7735R
import struct


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

def save_bmp_rgb565(filename, width, height, framebuf):
    row_size = (width * 2 + 3) & ~3
    pixel_array_size = row_size * height
    header_size = 14 + 40 + 12
    file_size = header_size + pixel_array_size
    with open(filename, "wb") as f:
        # BMP HEADER
        f.write(b'BM')
        f.write(struct.pack('<IHHI', file_size, 0, 0, header_size))
        # DIB HEADER (BITMAPINFOHEADER) 
        f.write(struct.pack('<IIIHHIIIIII',
            40,
            width,
            height,
            1,
            16,
            3,                 # BI_BITFIELDS
            pixel_array_size,
            2835,
            2835,
            0,
            0
        ))
        # COLOR MASKS
        f.write(struct.pack('<III',
            0xF800,  # Red
            0x07E0,  # Green
            0x001F   # Blue
        ))
        # PIXEL DATA (BOTTOM-UP)
        for y in range(height - 1, -1, -1):
            row_start = y * width * 2
            row = framebuf[row_start:row_start + width * 2]
            f.write(row)
            f.write(b'\x00' * (row_size - width * 2))    

display.auto_refresh = False
img_idx = 0
while True:
    cam.capture(camera_image)
    camera_image.dirty()
    display.refresh(minimum_frames_per_second=0)
    save_bmp_rgb565(capture_file.format(img_idx), cam.width, cam.height, cam.buffer)
    # with open(capture_file.format(img_idx), "wb") as fh:
    #     fh.write(camera_image)
    img_idx += 1


