#!/usr/bin/env python3

import subprocess

subprocess.call(['sudo', 'systemctl', 'stop', 'brickman'])

"""
Tetris für LEGO EV3 mit ev3dev2
Display: 178x128 Pixel (Schwarz/Weiß)
Steuerung: EV3-Buttons
  Links/Rechts  → Block bewegen
  Oben          → Block drehen
  Unten         → Block schneller fallen
  Enter         → Hard Drop (sofort fallen)
  Backspace     → Spiel beenden
"""

import time
import random
from ev3dev2.display import Display
from ev3dev2.button import Button
from ev3dev2.sound import Sound
from PIL import ImageDraw, ImageFont

# ─────────────────────────────────────────
# KONSTANTEN
# ─────────────────────────────────────────
BLOCK   = 10          # Pixel pro Zelle
COLS    = 10          # Spielfeld-Breite
ROWS    = 12          # Spielfeld-Höhe
OFFSET_X = 4          # Spielfeld links
OFFSET_Y = 4          # Spielfeld oben

SCREEN_W = 178
SCREEN_H = 128

# Tetromino-Formen (jede Rotation als Liste von (Zeile, Spalte))
TETROMINOES = {
    'I': [
        [(0,0),(0,1),(0,2),(0,3)],
        [(0,0),(1,0),(2,0),(3,0)],
    ],
    'O': [
        [(0,0),(0,1),(1,0),(1,1)],
    ],
    'T': [
        [(0,1),(1,0),(1,1),(1,2)],
        [(0,0),(1,0),(2,0),(1,1)],  # falsche Klammer korrigiert
        [(0,0),(0,1),(0,2),(1,1)],
        [(0,1),(1,1),(2,1),(1,0)],
    ],
    'S': [
        [(0,1),(0,2),(1,0),(1,1)],
        [(0,0),(1,0),(1,1),(2,1)],
    ],
    'Z': [
        [(0,0),(0,1),(1,1),(1,2)],
        [(0,1),(1,0),(1,1),(2,0)],
    ],
    'J': [
        [(0,0),(1,0),(1,1),(1,2)],
        [(0,0),(0,1),(1,0),(2,0)],
        [(0,0),(0,1),(0,2),(1,2)],
        [(0,1),(1,1),(2,0),(2,1)],
    ],
    'L': [
        [(0,2),(1,0),(1,1),(1,2)],
        [(0,0),(1,0),(2,0),(2,1)],
        [(0,0),(0,1),(0,2),(1,0)],
        [(0,0),(0,1),(1,1),(2,1)],
    ],
}

PIECE_NAMES = list(TETROMINOES.keys())


# ─────────────────────────────────────────
# SPIELFELD
# ─────────────────────────────────────────
def empty_board():
    return [[0] * COLS for _ in range(ROWS)]


def is_valid(board, shape, row, col):
    """Prüft ob eine Position gültig ist."""
    for (dr, dc) in shape:
        r, c = row + dr, col + dc
        if r < 0 or r >= ROWS or c < 0 or c >= COLS:
            return False
        if board[r][c]:
            return False
    return True


def place_piece(board, shape, row, col):
    """Setzt einen Block fest ins Spielfeld."""
    for (dr, dc) in shape:
        board[row + dr][col + dc] = 1


def clear_lines(board):
    """Löscht volle Zeilen und gibt Anzahl zurück."""
    new_board = [row for row in board if not all(row)]
    cleared = ROWS - len(new_board)
    for _ in range(cleared):
        new_board.insert(0, [0] * COLS)
    return new_board, cleared


# ─────────────────────────────────────────
# ZEICHNEN
# ─────────────────────────────────────────
def draw_game(screen, board, shape, row, col, score, level, next_name):
    draw = ImageDraw.Draw(screen.image)

    # Hintergrund löschen
    draw.rectangle([0, 0, SCREEN_W - 1, SCREEN_H - 1], fill='white')

    # Spielfeld-Rand
    field_w = COLS * BLOCK
    field_h = ROWS * BLOCK
    draw.rectangle(
        [OFFSET_X - 1, OFFSET_Y - 1,
         OFFSET_X + field_w, OFFSET_Y + field_h],
        outline='black'
    )

    # Gesetzten Blöcke zeichnen
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c]:
                x = OFFSET_X + c * BLOCK
                y = OFFSET_Y + r * BLOCK
                draw.rectangle([x, y, x + BLOCK - 2, y + BLOCK - 2], fill='black')

    # Aktuellen Block zeichnen
    for (dr, dc) in shape:
        r2, c2 = row + dr, col + dc
        if 0 <= r2 < ROWS and 0 <= c2 < COLS:
            x = OFFSET_X + c2 * BLOCK
            y = OFFSET_Y + r2 * BLOCK
            draw.rectangle([x, y, x + BLOCK - 2, y + BLOCK - 2], fill='black')

    # Trennlinie
    side_x = OFFSET_X + field_w + 4
    draw.line([side_x, 0, side_x, SCREEN_H], fill='black')

    # Score & Level
    info_x = side_x + 4
    draw.text((info_x, 4),  "Score", fill='black')
    draw.text((info_x, 14), str(score), fill='black')
    draw.text((info_x, 30), "Lvl", fill='black')
    draw.text((info_x, 40), str(level), fill='black')

    # Nächster Block (Vorschau)
    draw.text((info_x, 56), "Next", fill='black')
    next_shape = TETROMINOES[next_name][0]
    for (dr, dc) in next_shape:
        px = info_x + dc * 7
        py = 68 + dr * 7
        draw.rectangle([px, py, px + 5, py + 5], fill='black')

    screen.update()


def draw_screen(screen, text_lines):
    """Zeigt einen einfachen Text-Bildschirm (Game Over / Start)."""
    draw = ImageDraw.Draw(screen.image)
    draw.rectangle([0, 0, SCREEN_W - 1, SCREEN_H - 1], fill='white')
    y = 20
    for line in text_lines:
        draw.text((20, y), line, fill='black')
        y += 16
    screen.update()


# ─────────────────────────────────────────
# HAUPTSPIEL
# ─────────────────────────────────────────
def run_game(screen, btn, sound):
    board = empty_board()
    score = 0
    level = 1
    lines_total = 0

    def new_piece():
        name = random.choice(PIECE_NAMES)
        return name, 0, TETROMINOES[name], 0, COLS // 2 - 2

    cur_name, rot_idx, shapes, cur_row, cur_col = new_piece()
    cur_shape = shapes[rot_idx]
    next_name = random.choice(PIECE_NAMES)

    fall_interval = 0.8  # Sekunden pro Schritt
    last_fall = time.time()

    running = True
    while running:
        now = time.time()

        # ── INPUT ──────────────────────────
        if btn.left:
            if is_valid(board, cur_shape, cur_row, cur_col - 1):
                cur_col -= 1
            time.sleep(0.02)

        elif btn.right:
            if is_valid(board, cur_shape, cur_row, cur_col + 1):
                cur_col += 1
            time.sleep(0.02)

        elif btn.up:
            # Drehen
            new_rot = (rot_idx + 1) % len(shapes)
            new_shape = shapes[new_rot]
            if is_valid(board, new_shape, cur_row, cur_col):
                rot_idx = new_rot
                cur_shape = new_shape
            time.sleep(0.02)

        elif btn.down:
            # Schnell fallen
            if is_valid(board, cur_shape, cur_row + 1, cur_col):
                cur_row += 1
                last_fall = now
            time.sleep(0.01)

        elif btn.enter:
            # Hard Drop
            while is_valid(board, cur_shape, cur_row + 1, cur_col):
                cur_row += 1
            last_fall = 0  # sofort platzieren

        elif btn.backspace:
            running = False
            break

        # ── AUTOMATISCHES FALLEN ───────────
        if now - last_fall >= fall_interval:
            if is_valid(board, cur_shape, cur_row + 1, cur_col):
                cur_row += 1
            else:
                # Block setzen
                place_piece(board, cur_shape, cur_row, cur_col)
                board, cleared = clear_lines(board)

                if cleared:
                    lines_total += cleared
                    score += [0, 100, 300, 500, 800][cleared] * level
                    level = lines_total // 10 + 1
                    fall_interval = max(0.1, 0.8 - (level - 1) * 0.07)
                    sound.beep()

                # Neues Stück
                cur_name = next_name
                shapes = TETROMINOES[cur_name]
                rot_idx = 0
                cur_shape = shapes[0]
                cur_row = 0
                cur_col = COLS // 2 - 2
                next_name = random.choice(PIECE_NAMES)

                # Game Over prüfen
                if not is_valid(board, cur_shape, cur_row, cur_col):
                    running = False

            last_fall = now

        # ── ZEICHNEN ───────────────────────
        draw_game(screen, board, cur_shape, cur_row, cur_col,
                  score, level, next_name)

    return score


# ─────────────────────────────────────────
# EINSTIEGSPUNKT
# ─────────────────────────────────────────
def main():
    screen = Display()
    btn    = Button()
    sound  = Sound()

    while True:
        # Startbildschirm
        draw_screen(screen, [
            "  TETRIS",
            "",
            "Enter = Start",
            "Back  = Beenden",
        ])

        # Warten auf Enter oder Backspace
        while True:
            if btn.enter:
                break
            if btn.backspace:
                draw_screen(screen, ["  Tschuess!"])
                time.sleep(1)
                return
            time.sleep(0.02)

        time.sleep(0.02)  # Entprellung

        final_score = run_game(screen, btn, sound)

        # Game-Over-Bildschirm
        draw_screen(screen, [
            "  GAME OVER",
            "",
            "  Score: " + str(final_score),
            "",
            "Enter = Nochmal",
            "Back  = Beenden",
        ])

        # Warten auf Eingabe
        while True:
            if btn.enter:
                break
            if btn.backspace:
                return
              subprocess.call(['sudo', 'systemcl', 'start', 'brickman'])
            time.sleep(0.02)

        time.sleep(0.02)


if __name__ == '__main__':
    main()
