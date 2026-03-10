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

# Herz zeichnen
for row_index, row in enumerate(heart):
    for col_index, pixel in enumerate(row):
        if pixel == 1:
            x = col_index * 10 + 20
            y = row_index * 10 + 20
            display.rectangle(filled=True, x1=x, y1=y, x2=x+9, y2=y+9)

# Anzeigen
display.update()

# 5 Sekunden warten
time.sleep(5) 
