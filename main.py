import cv2
from cvzone.HandTrackingModule import HandDetector
from time import sleep
import numpy as np
import cvzone
from pynput.keyboard import Controller, Key


class Button():
    def __init__(self, pos, text, size=[85, 85]):
        self.pos = pos
        self.size = size
        self.text = text


def drawAll(img, buttonList):
    for button in buttonList:
        x, y = button.pos
        w, h = button.size
        cvzone.cornerRect(img, (button.pos[0], button.pos[1], button.size[0], button.size[1]),
                          20, rt=0)
        cv2.rectangle(img, button.pos, (x + w, y + h), (255, 0, 255), cv2.FILLED)
        cv2.putText(img, button.text, (x + 20, y + 65),
                    cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)
    return img


def main():
    # Open webcam
    cap = cv2.VideoCapture(0)
    cap.set(3, 1280)
    cap.set(4, 720)

    # Hand detector
    detector = HandDetector(detectionCon=0.8, maxHands=2)

    # Keyboard layout including Backspace
    keys = [
        ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
        ["A", "S", "D", "F", "G", "H", "J", "K", "L", ";"],
        ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "/"],
        ["SPACE", "BACKSPACE"]
    ]

    # Create button list
    buttonList = []
    for i in range(len(keys)):
        for j, key in enumerate(keys[i]):
            if key == "SPACE":
                buttonList.append(Button([50, 400], key, [600, 85]))
            elif key == "BACKSPACE":
                buttonList.append(Button([100 * 9 + 50, 100 * 3 + 50], key, [600, 85]))  # Position for Backspace
            else:
                buttonList.append(Button([100 * j + 50, 100 * i + 50], key))

    # Virtual keyboard controller
    keyboard = Controller()
    finalText = ""

    # Typing state tracking
    lastTypedKey = None
    typingCooldown = 0

    while True:
        # Read frame from webcam
        success, img = cap.read()
        img = cv2.flip(img, 1)  # Flip the image horizontally

        if not success:
            print("Failed to capture frame")
            break

        # Detect hands
        hands, img = detector.findHands(img, draw=True)

        # Draw keyboard buttons
        img = drawAll(img, buttonList)

        # Decrement typing cooldown
        if typingCooldown > 0:
            typingCooldown -= 1

        # Process hand interactions
        if hands:
            # Check each hand
            for hand in hands:
                lmList = hand['lmList']

                if lmList:
                    # Get index and middle finger tip coordinates
                    index_tip = lmList[8][:2]
                    middle_tip = lmList[12][:2]

                    # Check for button interaction
                    for button in buttonList:
                        bx, by = button.pos
                        bw, bh = button.size

                        # Check if fingers are over the button
                        if bx < index_tip[0] < bx + bw and by < index_tip[1] < by + bh:
                            # Highlight button when hovering
                            cv2.rectangle(img, (bx - 5, by - 5), (bx + bw + 5, by + bh + 5),
                                          (175, 0, 175), cv2.FILLED)
                            cv2.putText(img, button.text, (bx + 20, by + 65),
                                        cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)

                            # Enhanced typing detection
                            # Check distance between index and middle fingers
                            l = detector.findDistance(lmList[8][:2], lmList[12][:2], img)[0]

                            # More flexible pinch detection
                            if l < 30 and typingCooldown == 0:
                                # Special handling for space key
                                if button.text == "SPACE":
                                    keyboard.press(Key.space)
                                    finalText += " "
                                elif button.text == "BACKSPACE":
                                    if finalText:  # Only delete if there's text
                                        finalText = finalText[:-1]  # Remove the last character
                                    keyboard.press(Key.backspace)  # Simulate backspace press
                                else:
                                    keyboard.press(button.text)
                                    finalText += button.text

                                cv2.rectangle(img, button.pos, (bx + bw, by + bh),
                                              (0, 255, 0), cv2.FILLED)
                                cv2.putText(img, button.text, (bx + 20, by + 65),
                                            cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)

                                # Set cooldown to prevent rapid typing
                                typingCooldown = 10
                                lastTypedKey = button.text

        # Display typed text
        cv2.rectangle(img, (50, 530), (1000, 630), (175, 0, 175), cv2.FILLED)
        cv2.putText(img, finalText, (60, 600),
                    cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 3)

        # Show the image
        cv2.imshow("Virtual Hand Keyboard", img)

        # Exit condition
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('c'):
            # Clear text when 'c' is pressed
            finalText = ""

    # Clean up
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
