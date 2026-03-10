from ev3dev2.display import Display
import time

display = Display()

# Herz-Muster aus Pixeln (5x5 Grid)
heart = [
    [0, 1, 0, 1, 0],
    [1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1],
    [0, 1, 1, 1, 0],
    [0, 0, 1, 0, 0],
]

# Display leeren
display.clear()

# Herz zeichnen - jeden Pixel einzeln als kleines Quadrat
for row_index, row in enumerate(heart):
    for col_index, pixel in enumerate(row):
        if pixel == 1:
            for dx in range(10):
                for dy in range(10):
                    x = col_index * 10 + 20 + dx
                    y = row_index * 10 + 20 + dy
                    display.draw.point((x, y))

# Anzeigen
display.update()

# 5 Sekunden warten
time.sleep(5)
