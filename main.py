#!C:\Users\User\Desktop\virtual_painter-main\venv\Scripts\python.exe
from handTracker import *
import cv2
import numpy as np
import random

def detect_shape(points):
    if len(points) < 5:  # Require at least 5 points for reliable shape detection
        return None  # Not enough points to determine a shape

    pts = np.array(points)
    distances = [np.linalg.norm(pts[i] - pts[i-1]) for i in range(1, len(pts))]
    avg_distance = np.mean(distances)
    variance = np.var(distances)

    if variance < avg_distance * 0.1:
        return 'Circle'

    if len(points) >= 4:
        lengths = [np.linalg.norm(pts[i] - pts[(i + 1) % len(pts)]) for i in range(len(pts))]
        width, height = lengths[0], lengths[1]
        aspect_ratio = max(width, height) / min(width, height)

        if aspect_ratio < 1.1:
            return 'Square'
        else:
            return 'Rectangle'

    if len(points) >= 3:
        return 'Triangle'
    
    return None

class ColorRect():
    def __init__(self, x, y, w, h, color, text='', alpha=0.5):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color
        self.text = text
        self.alpha = alpha
        
    def drawRect(self, img, text_color=(255, 255, 255), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.8, thickness=2):
        alpha = self.alpha
        bg_rec = img[self.y:self.y + self.h, self.x:self.x + self.w]
        colored_rect = np.ones(bg_rec.shape, dtype=np.uint8)
        colored_rect[:] = self.color
        res = cv2.addWeighted(bg_rec, alpha, colored_rect, 1 - alpha, 1.0)
        
        img[self.y:self.y + self.h, self.x:self.x + self.w] = res
        text_size = cv2.getTextSize(self.text, fontFace, fontScale, thickness)
        text_pos = (int(self.x + self.w / 2 - text_size[0][0] / 2), int(self.y + self.h / 2 + text_size[0][1] / 2))
        cv2.putText(img, self.text, text_pos, fontFace, fontScale, text_color, thickness)

    def isOver(self, x, y):
        return (self.x + self.w > x > self.x) and (self.y + self.h > y > self.y)

detector = HandTracker(detectionCon=0.8)
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)
canvas = np.zeros((720, 1280, 3), np.uint8)

px, py = 0, 0
color = (255, 0, 0)
brushSize = 5
eraserSize = 20

colorsBtn = ColorRect(200, 0, 100, 100, (120, 255, 0), 'Colors')

colors = [
    ColorRect(300, 0, 100, 100, (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))),
    ColorRect(400, 0, 100, 100, (0, 0, 255)),
    ColorRect(500, 0, 100, 100, (255, 0, 0)),
    ColorRect(600, 0, 100, 100, (0, 255, 0)),
    ColorRect(700, 0, 100, 100, (0, 255, 255)),
    ColorRect(800, 0, 100, 100, (0, 0, 0), "Eraser")
]

clear = ColorRect(900, 0, 100, 100, (100, 100, 100), "Clear")

pens = [ColorRect(1100, 50 + 100 * i, 100, 100, (50, 50, 50), str(penSize)) for i, penSize in enumerate(range(5, 25, 5))]
penBtn = ColorRect(1100, 0, 100, 50, color, 'Pen')

boardBtn = ColorRect(50, 0, 100, 100, (255, 255, 0), 'Board')
whiteBoard = ColorRect(50, 120, 1020, 580, (255, 255, 255), alpha=0.6)

coolingCounter = 20
hideBoard = True
hideColors = True
hidePenSizes = True

drawing_points = []  # Initialize the drawing_points list

while True:
    if coolingCounter:
        coolingCounter -= 1

    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.resize(frame, (1280, 720))
    frame = cv2.flip(frame, 1)

    detector.findHands(frame)
    positions = detector.getPostion(frame, draw=False)
    upFingers = detector.getUpFingers(frame)

    if upFingers:
        x, y = positions[8][0], positions[8][1]
        
        # Check for five fingers up to clear the canvas
        if upFingers.count(1) == 5:
            canvas = np.zeros((720, 1280, 3), np.uint8)  # Clear the canvas

        if upFingers[1] and not whiteBoard.isOver(x, y):
            px, py = 0, 0

            if not hidePenSizes:
                for pen in pens:
                    if pen.isOver(x, y):
                        brushSize = int(pen.text)
                        pen.alpha = 0
                    else:
                        pen.alpha = 0.5

            if not hideColors:
                for cb in colors:
                    if cb.isOver(x, y):
                        color = cb.color
                        cb.alpha = 0
                    else:
                        cb.alpha = 0.5

                if clear.isOver(x, y):
                    clear.alpha = 0
                    canvas = np.zeros((720, 1280, 3), np.uint8)
                else:
                    clear.alpha = 0.5
            
            if colorsBtn.isOver(x, y) and not coolingCounter:
                coolingCounter = 10
                colorsBtn.alpha = 0
                hideColors = not hideColors
                colorsBtn.text = 'Colors' if hideColors else 'Hide'
            else:
                colorsBtn.alpha = 0.5
            
            if penBtn.isOver(x, y) and not coolingCounter:
                coolingCounter = 10
                penBtn.alpha = 0
                hidePenSizes = not hidePenSizes
                penBtn.text = 'Pen' if hidePenSizes else 'Hide'
            else:
                penBtn.alpha = 0.5

            if boardBtn.isOver(x, y) and not coolingCounter:
                coolingCounter = 10
                boardBtn.alpha = 0
                hideBoard = not hideBoard
                boardBtn.text = 'Board' if hideBoard else 'Hide'
            else:
                boardBtn.alpha = 0.5

        elif upFingers[1] and not upFingers[2]:
            if whiteBoard.isOver(x, y) and not hideBoard:
                # Collect points for shape detection
                drawing_points.append((x, y))

                # Draw on canvas
                if px == 0 and py == 0:
                    px, py = positions[8]
                
                if color == (0, 0, 0):
                    cv2.line(canvas, (px, py), positions[8], color, eraserSize)
                else:
                    cv2.line(canvas, (px, py), positions[8], color, brushSize)
                
                # Update the last positions
                px, py = positions[8]

                # If enough points are collected, detect the shape
                if len(drawing_points) >= 5:  # Adjust this as necessary
                    detected_shape = detect_shape(drawing_points)
                    
                    if detected_shape:
                        # Draw the detected shape
                        if detected_shape == 'Circle':
                            cv2.circle(canvas, (x, y), brushSize, color, -1)
                        elif detected_shape == 'Square':
                            # Draw square at detected position
                            square_size = brushSize * 2
                            cv2.rectangle(canvas, (x - square_size // 2, y - square_size // 2), 
                                          (x + square_size // 2, y + square_size // 2), color, -1)
                        elif detected_shape == 'Triangle':
                            pts = np.array([[x, y - brushSize], [x - brushSize, y + brushSize], [x + brushSize, y + brushSize]], np.int32)
                            cv2.fillPoly(canvas, [pts], color)

                        # Clear points after drawing shape
                        drawing_points.clear()

        elif upFingers.count(1) == 3:  # Check for three fingers up
            square_size = brushSize * 50  # Increase size for better visibility
            cv2.rectangle(canvas, 
                  (x - square_size // 2, y - square_size // 2), 
                  (x + square_size // 2, y + square_size // 2), 
                  color, 2)  # Set thickness to 2 for border

        else:
            px, py = 0, 0
        
    # Draw UI elements
    colorsBtn.drawRect(frame)
    cv2.rectangle(frame, (colorsBtn.x, colorsBtn.y), (colorsBtn.x + colorsBtn.w, colorsBtn.y + colorsBtn.h), (255, 255, 255), 2)

    boardBtn.drawRect(frame)
    cv2.rectangle(frame, (boardBtn.x, boardBtn.y), (boardBtn.x + boardBtn.w, boardBtn.y + boardBtn.h), (255, 255, 255), 2)

    if not hideBoard:       
        whiteBoard.drawRect(frame)
        canvasGray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
        _, imgInv = cv2.threshold(canvasGray, 20, 255, cv2.THRESH_BINARY_INV)
        imgInv = cv2.cvtColor(imgInv, cv2.COLOR_GRAY2BGR)
        frame = cv2.bitwise_and(frame, imgInv)
        frame = cv2.bitwise_or(frame, canvas)

    if not hideColors:
        for c in colors:
            c.drawRect(frame)
            cv2.rectangle(frame, (c.x, c.y), (c.x + c.w, c.y + c.h), (255, 255, 255), 2)

        clear.drawRect(frame)
        cv2.rectangle(frame, (clear.x, clear.y), (clear.x + clear.w, clear.y + clear.h), (255, 255, 255), 2)

    penBtn.color = color
    penBtn.drawRect(frame)
    cv2.rectangle(frame, (penBtn.x, penBtn.y), (penBtn.x + penBtn.w, penBtn.y + penBtn.h), (255, 255, 255), 2)
    
    if not hidePenSizes:
        for pen in pens:
            pen.drawRect(frame)
            cv2.rectangle(frame, (pen.x, pen.y), (pen.x + pen.w, pen.y + pen.h), (255, 255, 255), 2)

    cv2.imshow('video', frame)
    k = cv2.waitKey(1)
    if k == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
