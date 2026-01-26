import board
import busio
import sdcardio
import storage

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