import streamlit as st
import cv2
import numpy as np
import time

# Optional: If you have a deepfake detection model, load it here.
# For demonstration, we use a placeholder function.

def is_deepfake(frame: np.ndarray) -> bool:
    """Placeholder deepfake detection.
    Replace this with a real model inference.
    Returns True if the frame is detected as a deepfake.
    """
    # Dummy logic: randomly flag frames as deepfake for demo purposes.
    # In production, replace with model inference.
    return False

# Streamlit UI
st.title("Real‑Time Video Deepfake Detector")

# Video capture from webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    st.error("Cannot access webcam")
    st.stop()

# Create a placeholder for the video frame
frame_placeholder = st.empty()

# Create a status text
status_text = st.empty()

# Main loop
while True:
    ret, frame = cap.read()
    if not ret:
        st.warning("Failed to read frame from webcam")
        break

    # Convert BGR to RGB for display
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Detect deepfake (placeholder)
    deepfake = is_deepfake(rgb_frame)

    # Overlay status on frame
    overlay = rgb_frame.copy()
    if deepfake:
        cv2.putText(overlay, "DEEPFAKE DETECTED", (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 0, 255), 2, cv2.LINE_AA)
    else:
        cv2.putText(overlay, "REAL", (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 255, 0), 2, cv2.LINE_AA)

    # Display frame
    frame_placeholder.image(overlay, channels="RGB")

    # Update status text
    status_text.text(f"Deepfake: {deepfake}")

    # Break loop if user stops the app
    if st.button("Stop"):
        break

cap.release()
st.success("Video stream ended")
