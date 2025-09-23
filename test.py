import board
import busio
import sdcardio
import storage
import digitalio
import time
from adafruit_ov7670 import OV7670
from adafruit_bitmapsaver import save_pixels

# --- SD Card Setup ---
try:
    print("Setting up SD card...")
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    cs = digitalio.DigitalInOut(board.D5)  # Replace with your SD_CS pin
    sdcard = sdcardio.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")
    print("SD card mounted at /sd")
except OSError as e:
    print("Error mounting SD card:", e)
    while True:
        pass # Halt the program if the SD card fails

# --- OV7670 Camera Setup ---
print("Setting up camera...")
i2c = busio.I2C(board.SCL, board.SDA) # Replace with your I2C pins
cam = OV7670(
    i2c,
    data_pins=[
        board.PCC_D0, board.PCC_D1, board.PCC_D2, board.PCC_D3,
        board.PCC_D4, board.PCC_D5, board.PCC_D6, board.PCC_D7
    ], # Replace with your data pins
    clock=board.PCC_CLK, vsync=board.PCC_DEN1, href=board.PCC_DEN2,
    reset=board.D38, shutdown=board.D39 # Replace with your control pins
)

# Set the desired image size and format
cam.size = OV7670.SIZE_DIV16 # Example: 40x30 pixels
cam.colorspace = OV7670.COLORSPACE_RGB565
cam.flip_y = True # Adjust if your image is upside down

width = cam.width
height = cam.height

# --- Capture and Save Image ---
try:
    # Create a buffer to hold the image data
    buffer = bytearray(width * height * 2) # RGB565 uses 2 bytes per pixel
    
    # Capture the image
    print("Capturing image...")
    cam.capture(buffer)

    # Save the image to the SD card
    filename = f"/sd/capture_{time.monotonic()}.bmp"
    print(f"Saving image to {filename}...")

    # The save_pixels function from adafruit_bitmapsaver is used here.
    # It requires displayio to create a bitmap object from the buffer.
    from displayio import Bitmap, Palette
    
    # The OV7670 produces RGB565, which can be directly converted to a Bitmap
    # for saving. The color palette is not used here for 16-bit color.
    bitmap = Bitmap(width, height, 65535, buffer=buffer)
    palette = Palette(65536)
    
    with open(filename, "wb") as f:
        save_pixels(f, bitmap, palette)

    print("Image saved successfully!")

except Exception as e:
    print("An error occurred during capture or save:", e)

