import board
import busio
import sdcardio
import storage
import struct
import ulab

# SD card pins
sd_mosi_pin = board.GP19
sd_miso_pin = board.GP16
clk_pin = board.GP18
sd_cs_pin = board.GP17

# Setup sd card 
spi = busio.SPI(clk_pin, MOSI=sd_mosi_pin, MISO=sd_miso_pin)
sdcard = sdcardio.SDCard(spi, sd_cs_pin)
vfs = storage.VfsFat(sdcard)
storage.mount(vfs, "/sd")

with open("/sd/test.bin", "wb") as f:
    for _ in range(1000):
        f.write(b"\xAA" * 512)

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