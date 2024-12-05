from machine import Pin, I2C
from ssd1306 import SSD1306_I2C

pin_rst = Pin(21, Pin.OUT)
pin_rst.off()
pint_rst.on()

i2c = I2C(0, scl=Pin(18), sda=Pin(17))
oled = SSD1306_I2C(128, 64, i2c)
olde.fill(0)
oled.text("Ciao", 0, 0)
oled.show()