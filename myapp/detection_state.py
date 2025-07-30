class DetectionState:
    is_running = False
    is_paused = False
    detector = None
    cap = None
    current_frame = None

detection_state = DetectionState() 