# Import required libraries
import cv2                  # OpenCV for image processing and computer vision
from cvzone.HandTrackingModule import HandDetector  # For hand detection and tracking
from time import sleep     # For adding delays when needed
import numpy as np         # For numerical operations and array handling
import cvzone             # Additional computer vision utilities
from pynput.keyboard import Controller, Key  # For simulating keyboard inputs
from pynput.mouse import Button as MouseButton, Controller as MouseController  # For mouse control
import webbrowser         # For opening web browser
import os                 # For operating system operations
import psutil            # For process and system monitoring

# Define Button class for creating virtual keyboard buttons
class Button():
    def __init__(self, pos, text, size=[85, 85]):
        """
        Initialize Button object
        :param pos: List of [x, y] coordinates for button position
        :param text: Text to display on button
        :param size: List of [width, height] for button size, default is [85, 85]
        """
        self.pos = pos      # Position coordinates [x, y]
        self.size = size    # Button dimensions [width, height]
        self.text = text    # Text to display on button

# Function to draw all buttons on the virtual keyboard
def drawAll(img, buttonList):
    """
    Draw all buttons on the image
    :param img: Images to draw buttons on
    :param buttonList: List of Button objects to draw
    :return: Image with buttons drawn
    """
    for button in buttonList:
        x, y = button.pos
        w, h = button.size
        # Draw button border with rounded corners
        cvzone.cornerRect(img, (button.pos[0], button.pos[1], button.size[0], button.size[1]),
                          20, rt=0)
        # Fill button with purple color
        cv2.rectangle(img, button.pos, (x + w, y + h), (255, 0, 255), cv2.FILLED)
        # Add white text to button
        cv2.putText(img, button.text, (x + 20, y + 65),
                    cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)
    return img

# Function to close Microsoft Edge browser
def close_edge():
    """
    Find and close all Microsoft Edge processes
    """
    for proc in psutil.process_iter(['name']):
        try:
            # Check for both possible Edge process names
            if proc.info['name'].lower() in ['msedge.exe', 'microsoftedge.exe']:
                proc.kill()  # Terminate the process
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass  # Handle any process access errors

def main():
    """
    Main function running the virtual hand control system
    """
    # Initialize video capture from default camera (0)
    cap = cv2.VideoCapture(0)
    cap.set(3, 1280)  # Set capture width
    cap.set(4, 720)   # Set capture height

    # Initialize mode tracker (0 = keyboard mode, 1 = YouTube/mouse mode)
    youtube = 0

    # Initialize input controllers
    keyboard = Controller()  # For keyboard simulation
    mouse = MouseController()  # For mouse simulation

    # Initialize hand detector with high confidence threshold
    # maxHands=2 allows detection of both hands for gestures
    detector = HandDetector(detectionCon=0.8, maxHands=2)

    # Define screen dimensions for mouse mapping
    SCREEN_WIDTH = 1920
    SCREEN_HEIGHT = 1080

    # Define keyboard layout in rows
    keys = [
        ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
        ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
        ["A", "S", "D", "F", "G", "H", "J", "K", "L", ";"],
        ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "/"],
        ["SPACE", "BACKSPACE", "YOUTUBE"]  # Special function keys
    ]

    # Create button objects for each key
    buttonList = []
    for i in range(len(keys)):
        for j, key in enumerate(keys[i]):
            # Special sizing for function keys
            if key == "SPACE":
                buttonList.append(Button([50, 450], key, [250, 85]))  # Wider space bar
            elif key == "BACKSPACE":
                buttonList.append(Button([350, 450], key, [400, 84]))  # Wide backspace
            elif key == "YOUTUBE":
                buttonList.append(Button([850, 450], key, [400, 85]))  # Wide YouTube button
            else:
                # Regular keys with standard spacing
                buttonList.append(Button([100 * j + 50, 100 * i + 50], key))

    # Initialize tracking variables
    finalText = ""          # Store typed text
    typingCooldown = 0      # Prevent rapid repeated typing
    clickCooldown = 0       # Prevent rapid repeated clicking
    prev_hand_y = None      # Track previous hand position for scrolling
    scroll_sensitivity = 0.2 # Adjust scroll speed
    two_hands_cooldown = 0  # Prevent rapid mode switching

    # Main program loop
    while True:
        # Capture and prepare frame
        success, img = cap.read()
        img = cv2.flip(img, 1)  # Mirror image for natural interaction

        if not success:
            print("Failed to capture frame")
            break

        # Detect hands in frame
        hands, img = detector.findHands(img, draw=True)

        if youtube == 1:  # YouTube/Edge Mode
            # Check for two-hand gesture to exit YouTube mode
            if len(hands) == 2 and two_hands_cooldown == 0:
                hand1 = hands[0]
                hand2 = hands[1]

                # Helper function to check if palm is facing up
                def is_palm_up(hand):
                    lmList = hand['lmList']
                    # Check if index and middle fingers are up
                    return (lmList[8][1] < lmList[5][1] and  # Index finger up
                            lmList[12][1] < lmList[9][1])    # Middle finger up

                # If both palms are up, exit YouTube mode
                if is_palm_up(hand1) and is_palm_up(hand2):
                    close_edge()
                    youtube = 0  # Switch back to keyboard mode
                    finalText = ""  # Reset text
                    two_hands_cooldown = 20  # Set cooldown

            # Manage cooldown timer
            if two_hands_cooldown > 0:
                two_hands_cooldown -= 1

            # Handle mouse control in YouTube mode
            if hands:
                for hand in hands:
                    lmList = hand['lmList']
                    if lmList:
                        # Map hand coordinates to screen coordinates
                        index_x, index_y = lmList[8][:2]
                        screen_x = np.interp(index_x, [0, 1280], [0, SCREEN_WIDTH])
                        screen_y = np.interp(index_y, [0, 720], [0, SCREEN_HEIGHT])
                        mouse.position = (screen_x, screen_y)

                        # Handle mouse clicking
                        if clickCooldown == 0:
                            # Measure distance between index and middle finger
                            l = detector.findDistance(lmList[8][:2], lmList[12][:2], img)[0]
                            if l < 30:  # If fingers are close, click
                                mouse.click(MouseButton.left)
                                clickCooldown = 10

                        # Handle scrolling gesture
                        palm_y = lmList[0][1]
                        if prev_hand_y is not None:
                            y_movement = prev_hand_y - palm_y
                            # Check if middle and ring fingers are up
                            middle_up = lmList[12][1] < lmList[9][1]
                            ring_up = lmList[16][1] < lmList[13][1]

                            # Scroll if both fingers are up and hand moves
                            if middle_up and ring_up:
                                if abs(y_movement) > 2:
                                    scroll_amount = int(y_movement * scroll_sensitivity)
                                    mouse.scroll(0, scroll_amount)

                        prev_hand_y = palm_y

            # Manage click cooldown
            if clickCooldown > 0:
                clickCooldown -= 1

            # Display YouTube mode instructions
            cv2.putText(img, "Mouse Control Mode", (50, 50),
                        cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
            cv2.putText(img, "Show both palms to close Edge", (50, 100),
                        cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
            cv2.putText(img, "Hold up middle + ring fingers to scroll", (50, 150),
                        cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)

        else:  # Keyboard Mode
            # Draw virtual keyboard
            img = drawAll(img, buttonList)

            # Manage typing cooldown
            if typingCooldown > 0:
                typingCooldown -= 1

            # Handle keyboard interactions
            if hands:
                for hand in hands:
                    lmList = hand['lmList']
                    if lmList:
                        # Get finger positions
                        index_tip = lmList[8][:2]
                        middle_tip = lmList[12][:2]
                        ring_tip = lmList[16][:2]

                        # Check each button for interaction
                        for button in buttonList:
                            bx, by = button.pos
                            bw, bh = button.size

                            # If index finger is over button
                            if bx < index_tip[0] < bx + bw and by < index_tip[1] < by + bh:
                                # Highlight button
                                cv2.rectangle(img, (bx - 5, by - 5), (bx + bw + 5, by + bh + 5),
                                              (175, 0, 175), cv2.FILLED)
                                cv2.putText(img, button.text, (bx + 20, by + 65),
                                            cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)

                                # Check for clicking gesture
                                l = detector.findDistance(lmList[8][:2], lmList[12][:2], img)[0]

                                # If clicking gesture detected and cooldown is over
                                if l < 30 and typingCooldown == 0:
                                    # Handle special buttons
                                    if button.text == "SPACE":
                                        keyboard.press(Key.space)
                                        finalText += " "
                                    elif button.text == "BACKSPACE":
                                        if finalText:
                                            finalText = finalText[:-1]
                                        keyboard.press(Key.backspace)
                                    elif button.text == "YOUTUBE":
                                        webbrowser.open('https://www.youtube.com')
                                        youtube = 1  # Switch to YouTube mode
                                    else:
                                        # Handle regular keys
                                        keyboard.press(button.text)
                                        finalText += button.text

                                    # Visual feedback for button press
                                    cv2.rectangle(img, button.pos, (bx + bw, by + bh),
                                                  (0, 255, 0), cv2.FILLED)
                                    cv2.putText(img, button.text, (bx + 20, by + 65),
                                                cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)
                                    typingCooldown = 10

            # Display typed text
            cv2.rectangle(img, (50, 580), (1000, 680), (175, 0, 175), cv2.FILLED)
            cv2.putText(img, finalText, (60, 650),
                        cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 3)

        # Display the image
        cv2.imshow("Virtual Hand Control", img)

        # Check for 'q' key press to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Clean up
    cap.release()
    cv2.destroyAllWindows()

# Entry point of the program
if __name__ == "__main__":
    main()