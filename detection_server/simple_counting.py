from ultralytics import YOLO
import cv2
import time
import numpy as np
from datetime import datetime
import csv
import os

class SimpleObjectCounter:
    def __init__(self, model_path="model.pt", camera_source=0):
        print("Initializing Simple Object Counter...")
        
        # Load YOLO model
        self.model = YOLO(model_path)
        print(f"Model loaded: {model_path}")
        
        # Camera settings
        self.camera_source = camera_source
        self.cap = None
        
        # Detection settings
        self.confidence_threshold = 0.6
        self.line_position = 0.5  # Posisi garis (0.5 = tengah frame)
        
        # Counting variables
        self.ripe_count = 0
        self.unripe_count = 0
        self.previous_objects = set()
        
        # Anti-duplicate detection
        self.recently_counted_objects = {}
        self.frame_count = 0
        self.cooldown_frames = 30
        self.tracking_distance = 80
        self.crossing_tolerance = 5
        
        # Performance metrics
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0
        self.inference_times = []
        self.frame_delays = []
        self.last_frame_time = time.time()
        
        # Display settings
        self.show_metrics = True
        
        # CSV logging
        self.csv_filename = f"counting_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.detection_log = []
        self.session_start_time = datetime.now()
        self.last_save_time = time.time()
        self.auto_save_interval = 30  # Save every 30 seconds
        
        # Timer settings
        self.session_duration = 300  # 5 minutes in seconds
        self.start_time = time.time()
        
    def initialize_camera(self):
        """Initialize camera with optimal settings"""
        print(f"Opening camera source: {self.camera_source}")
        
        self.cap = cv2.VideoCapture(self.camera_source)
        if not self.cap.isOpened():
            print(f"Error: Cannot open camera {self.camera_source}")
            return False
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        # Get actual camera properties
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        print(f"Camera initialized: {width}x{height} @ {fps} FPS")
        return True
    
    def initialize_csv(self):
        """Initialize CSV file with headers"""
        try:
            # Create results directory if it doesn't exist
            results_dir = "counting_results"
            os.makedirs(results_dir, exist_ok=True)
            
            # Full path for CSV file
            self.csv_filepath = os.path.join(results_dir, self.csv_filename)
            
            # Write header
            with open(self.csv_filepath, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([
                    'Timestamp',
                    'Elapsed_Time_Seconds', 
                    'Frame_Number',
                    'Ripe_Count',
                    'Unripe_Count',
                    'Total_Count',
                    'Current_FPS',
                    'Inference_Time_ms',
                    'Avg_Inference_Time_ms',
                    'Frame_Delay_ms',
                    'Avg_Frame_Delay_ms',
                    'Detection_Event',
                    'Object_Class',
                    'Confidence'
                ])
            
            print(f"CSV file initialized: {self.csv_filepath}")
            return True
            
        except Exception as e:
            print(f"Error initializing CSV: {e}")
            return False
    
    def log_detection_event(self, object_class, confidence):
        """Log a detection event"""
        current_time = datetime.now()
        elapsed_seconds = (current_time - self.session_start_time).total_seconds()
        
        # Calculate averages
        avg_inference = np.mean(self.inference_times) if self.inference_times else 0
        avg_delay = np.mean(self.frame_delays) * 1000 if self.frame_delays else 0
        current_inference = self.inference_times[-1] if self.inference_times else 0
        current_delay = self.frame_delays[-1] * 1000 if self.frame_delays else 0
        
        detection_data = {
            'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'elapsed_seconds': round(elapsed_seconds, 3),
            'frame_number': self.frame_count,
            'ripe_count': self.ripe_count,
            'unripe_count': self.unripe_count,
            'total_count': self.ripe_count + self.unripe_count,
            'current_fps': round(self.current_fps, 2),
            'inference_time': round(current_inference, 2),
            'avg_inference_time': round(avg_inference, 2),
            'frame_delay': round(current_delay, 2),
            'avg_frame_delay': round(avg_delay, 2),
            'detection_event': 'COUNT',
            'object_class': 'Ripe' if object_class == 0 else 'Unripe',
            'confidence': round(confidence, 3)
        }
        
        self.detection_log.append(detection_data)
    
    def log_frame_data(self):
        """Log regular frame data (every few frames for performance tracking)"""
        if self.frame_count % 30 == 0:  # Log every 30 frames
            current_time = datetime.now()
            elapsed_seconds = (current_time - self.session_start_time).total_seconds()
            
            # Calculate averages
            avg_inference = np.mean(self.inference_times) if self.inference_times else 0
            avg_delay = np.mean(self.frame_delays) * 1000 if self.frame_delays else 0
            current_inference = self.inference_times[-1] if self.inference_times else 0
            current_delay = self.frame_delays[-1] * 1000 if self.frame_delays else 0
            
            frame_data = {
                'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'elapsed_seconds': round(elapsed_seconds, 3),
                'frame_number': self.frame_count,
                'ripe_count': self.ripe_count,
                'unripe_count': self.unripe_count,
                'total_count': self.ripe_count + self.unripe_count,
                'current_fps': round(self.current_fps, 2),
                'inference_time': round(current_inference, 2),
                'avg_inference_time': round(avg_inference, 2),
                'frame_delay': round(current_delay, 2),
                'avg_frame_delay': round(avg_delay, 2),
                'detection_event': 'FRAME',
                'object_class': '',
                'confidence': 0
            }
            
            self.detection_log.append(frame_data)
    
    def save_to_csv(self, force_save=False):
        """Save detection log to CSV file"""
        current_time = time.time()
        
        # Auto-save every interval or force save
        if force_save or (current_time - self.last_save_time > self.auto_save_interval):
            try:
                if self.detection_log:
                    # Append new data to CSV
                    with open(self.csv_filepath, 'a', newline='', encoding='utf-8') as file:
                        writer = csv.writer(file)
                        for data in self.detection_log:
                            writer.writerow([
                                data['timestamp'],
                                data['elapsed_seconds'],
                                data['frame_number'],
                                data['ripe_count'],
                                data['unripe_count'],
                                data['total_count'],
                                data['current_fps'],
                                data['inference_time'],
                                data['avg_inference_time'],
                                data['frame_delay'],
                                data['avg_frame_delay'],
                                data['detection_event'],
                                data['object_class'],
                                data['confidence']
                            ])
                    
                    # Clear log after saving
                    saved_count = len(self.detection_log)
                    self.detection_log = []
                    self.last_save_time = current_time
                    
                    if force_save:
                        print(f"Final data saved to CSV: {saved_count} records")
                    else:
                        print(f"Auto-saved to CSV: {saved_count} records")
                        
            except Exception as e:
                print(f"Error saving to CSV: {e}")
    
    def create_summary_csv(self):
        """Create a summary CSV with final statistics"""
        try:
            summary_filename = f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            summary_filepath = os.path.join("counting_results", summary_filename)
            
            session_duration = (datetime.now() - self.session_start_time).total_seconds()
            avg_inference = np.mean(self.inference_times) if self.inference_times else 0
            avg_delay = np.mean(self.frame_delays) * 1000 if self.frame_delays else 0
            
            with open(summary_filepath, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['Metric', 'Value'])
                writer.writerow(['Session Start', self.session_start_time.strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow(['Session End', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow(['Total Duration (seconds)', round(session_duration, 2)])
                writer.writerow(['Total Frames Processed', self.frame_count])
                writer.writerow(['Final Ripe Count', self.ripe_count])
                writer.writerow(['Final Unripe Count', self.unripe_count])
                writer.writerow(['Total Objects Counted', self.ripe_count + self.unripe_count])
                writer.writerow(['Average FPS', round(self.current_fps, 2)])
                writer.writerow(['Average Inference Time (ms)', round(avg_inference, 2)])
                writer.writerow(['Average Frame Delay (ms)', round(avg_delay, 2)])
                
                if self.inference_times:
                    writer.writerow(['Min Inference Time (ms)', round(np.min(self.inference_times), 2)])
                    writer.writerow(['Max Inference Time (ms)', round(np.max(self.inference_times), 2)])
                
                if self.frame_delays:
                    writer.writerow(['Min Frame Delay (ms)', round(np.min(self.frame_delays) * 1000, 2)])
                    writer.writerow(['Max Frame Delay (ms)', round(np.max(self.frame_delays) * 1000, 2)])
            
            print(f"Summary saved: {summary_filepath}")
            
        except Exception as e:
            print(f"Error creating summary CSV: {e}")
    
    def calculate_fps(self):
        """Calculate real-time FPS"""
        self.fps_counter += 1
        current_time = time.time()
        
        # Calculate frame delay
        frame_delay = current_time - self.last_frame_time
        self.frame_delays.append(frame_delay)
        self.last_frame_time = current_time
        
        # Keep only last 30 frame delays for average
        if len(self.frame_delays) > 30:
            self.frame_delays.pop(0)
        
        # Update FPS every second
        if current_time - self.fps_start_time >= 1.0:
            self.current_fps = self.fps_counter / (current_time - self.fps_start_time)
            self.fps_counter = 0
            self.fps_start_time = current_time
    
    def process_detection(self, frame):
        """Process object detection on frame"""
        # Start inference timing
        inference_start = time.time()
        
        # Run YOLO detection
        results = self.model(frame, verbose=False)
        
        # Calculate inference time
        inference_time = time.time() - inference_start
        self.inference_times.append(inference_time * 1000)  # Convert to milliseconds
        
        # Keep only last 30 inference times for average
        if len(self.inference_times) > 30:
            self.inference_times.pop(0)
        
        return results, inference_time * 1000
    
    def count_objects(self, results, frame_height):
        """Count objects crossing the detection line"""
        line_y = int(frame_height * self.line_position)
        current_objects = set()
        detections = []
        
        if len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                cls = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                
                # Filter by confidence threshold
                if conf < self.confidence_threshold:
                    continue
                
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                
                # Create object ID for tracking
                region_x = int(center_x // self.tracking_distance) * self.tracking_distance
                obj_id = f"{cls}_{region_x}_{int(center_y)}"
                current_objects.add(obj_id)
                
                # Check if object is crossing the line
                if obj_id not in self.previous_objects:
                    if center_y > line_y - self.crossing_tolerance and center_y < line_y + self.crossing_tolerance:
                        # Create signature to prevent duplicate counting
                        signature = f"{cls}_{region_x}_{line_y}"
                        
                        # Only count if not recently counted
                        if signature not in self.recently_counted_objects:
                            if cls == 0:  # Ripe
                                self.ripe_count += 1
                                print(f"COUNTED: Ripe - Total: {self.ripe_count}")
                                # Log detection event to CSV
                                self.log_detection_event(cls, conf)
                            elif cls == 1:  # Unripe
                                self.unripe_count += 1
                                print(f"COUNTED: Unripe - Total: {self.unripe_count}")
                                # Log detection event to CSV
                                self.log_detection_event(cls, conf)
                            
                            # Mark as recently counted
                            self.recently_counted_objects[signature] = self.frame_count
                
                # Store detection for drawing
                detections.append({
                    'bbox': (int(x1), int(y1), int(x2), int(y2)),
                    'class': cls,
                    'confidence': conf,
                    'center': (int(center_x), int(center_y))
                })
        
        self.previous_objects = current_objects
        return detections, line_y
    
    def draw_results(self, frame, detections, line_y, inference_time):
        """Draw detection results and metrics on frame"""
        height, width = frame.shape[:2]
        
        # Draw detection line
        cv2.line(frame, (0, line_y), (width, line_y), (0, 255, 0), 2)
        
        # Draw detections
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            cls = det['class']
            conf = det['confidence']
            
            # Color and label
            color = (0, 255, 0) if cls == 0 else (0, 0, 255)
            class_name = "Ripe" if cls == 0 else "Unripe"
            label = f"{class_name} {conf:.2f}"
            
            # Draw bounding box and label
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Draw counters
        counter_text = f"Ripe: {self.ripe_count}  Unripe: {self.unripe_count}"
        cv2.putText(frame, counter_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Draw line position
        cv2.putText(frame, f"Line Y: {line_y}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Draw timer countdown
        remaining_time = self.get_remaining_time()
        time_text = f"Time: {self.format_time(remaining_time)}"
        color = (0, 255, 255) if remaining_time > 60 else (0, 0, 255)  # Yellow if >1min, Red if <1min
        cv2.putText(frame, time_text, (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
        # Draw performance metrics if enabled
        if self.show_metrics:
            y_offset = 120  # Adjusted for timer display
            
            # Current FPS
            cv2.putText(frame, f"FPS: {self.current_fps:.1f}", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            y_offset += 25
            
            # Current inference time
            cv2.putText(frame, f"Inference: {inference_time:.1f}ms", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            y_offset += 25
            
            # Average inference time
            if self.inference_times:
                avg_inference = np.mean(self.inference_times)
                cv2.putText(frame, f"Avg Inference: {avg_inference:.1f}ms", (10, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                y_offset += 25
            
            # Average frame delay
            if self.frame_delays:
                avg_delay = np.mean(self.frame_delays) * 1000  # Convert to ms
                cv2.putText(frame, f"Frame Delay: {avg_delay:.1f}ms", (10, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                y_offset += 25
            
            # Frame count
            cv2.putText(frame, f"Frame: {self.frame_count}", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    
    def cleanup_old_objects(self):
        """Remove old objects from tracking"""
        if self.frame_count % 100 == 0:  # Cleanup every 100 frames
            old_objects = []
            for obj_id, frame_counted in self.recently_counted_objects.items():
                if self.frame_count - frame_counted > self.cooldown_frames:
                    old_objects.append(obj_id)
            
            for obj_id in old_objects:
                del self.recently_counted_objects[obj_id]
    
    def check_timer(self):
        """Check if session time has expired"""
        elapsed_time = time.time() - self.start_time
        return elapsed_time >= self.session_duration
    
    def get_remaining_time(self):
        """Get remaining time in seconds"""
        elapsed_time = time.time() - self.start_time
        remaining = max(0, self.session_duration - elapsed_time)
        return remaining
    
    def format_time(self, seconds):
        """Format seconds to MM:SS format"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def print_statistics(self):
        """Print current statistics"""
        print("\n" + "="*50)
        print("OBJECT COUNTING STATISTICS")
        print("="*50)
        print(f"Ripe Count: {self.ripe_count}")
        print(f"Unripe Count: {self.unripe_count}")
        print(f"Total Count: {self.ripe_count + self.unripe_count}")
        print(f"Current FPS: {self.current_fps:.2f}")
        
        if self.inference_times:
            avg_inference = np.mean(self.inference_times)
            min_inference = np.min(self.inference_times)
            max_inference = np.max(self.inference_times)
            print(f"Inference Time - Avg: {avg_inference:.2f}ms, Min: {min_inference:.2f}ms, Max: {max_inference:.2f}ms")
        
        if self.frame_delays:
            avg_delay = np.mean(self.frame_delays) * 1000
            min_delay = np.min(self.frame_delays) * 1000
            max_delay = np.max(self.frame_delays) * 1000
            print(f"Frame Delay - Avg: {avg_delay:.2f}ms, Min: {min_delay:.2f}ms, Max: {max_delay:.2f}ms")
        
        print(f"Total Frames Processed: {self.frame_count}")
        print(f"Session Duration: 5 minutes")
        print(f"Remaining Time: {self.format_time(self.get_remaining_time())}")
        print(f"CSV File: {self.csv_filename}")
        print(f"Pending CSV Records: {len(self.detection_log)}")
        print("="*50)
    
    def run(self):
        """Main detection loop"""
        if not self.initialize_camera():
            return
        
        # Initialize CSV logging
        if not self.initialize_csv():
            print("Warning: CSV logging disabled due to initialization error")
        
        print("\nStarting object counting...")
        print("Controls:")
        print("  'q' - Quit")
        print("  's' - Show/Hide statistics")
        print("  'm' - Toggle metrics display")
        print("  'r' - Reset counters")
        print("  'c' - Save current data to CSV")
        print("  SPACE - Print current statistics")
        print(f"\nSession Duration: 5 minutes")
        print(f"Results will be auto-saved to: {self.csv_filename}")
        print("Press any key to start...")
        
        # Create window
        cv2.namedWindow('Simple Object Counter', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Simple Object Counter', 800, 600)
        
        try:
            while True:
                self.frame_count += 1
                
                # Check if session time has expired
                if self.check_timer():
                    print("\n⏰ Session time expired (5 minutes completed)")
                    break
                
                # Read frame
                ret, frame = self.cap.read()
                if not ret:
                    print("Error: Cannot read frame")
                    break
                
                # Flip frame horizontally (optional)
                frame = cv2.flip(frame, 1)
                
                # Calculate FPS
                self.calculate_fps()
                
                # Process detection
                results, inference_time = self.process_detection(frame)
                
                # Count objects
                detections, line_y = self.count_objects(results, frame.shape[0])
                
                # Draw results
                self.draw_results(frame, detections, line_y, inference_time)
                
                # Cleanup old objects
                self.cleanup_old_objects()
                
                # Log frame data periodically
                self.log_frame_data()
                
                # Auto-save to CSV
                self.save_to_csv()
                
                # Check for time warnings
                remaining_time = self.get_remaining_time()
                if remaining_time <= 60 and remaining_time > 55:  # Warning at 1 minute left
                    print("⚠️ Warning: 1 minute remaining!")
                elif remaining_time <= 30 and remaining_time > 25:  # Warning at 30 seconds left
                    print("⚠️ Warning: 30 seconds remaining!")
                elif remaining_time <= 10 and remaining_time > 5:  # Warning at 10 seconds left
                    print("⚠️ Warning: 10 seconds remaining!")
                
                # Display frame
                cv2.imshow('Simple Object Counter', frame)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    self.print_statistics()
                elif key == ord('m'):
                    self.show_metrics = not self.show_metrics
                    print(f"Metrics display: {'ON' if self.show_metrics else 'OFF'}")
                elif key == ord('r'):
                    self.ripe_count = 0
                    self.unripe_count = 0
                    self.recently_counted_objects = {}
                    print("Counters reset!")
                elif key == ord('c'):
                    self.save_to_csv(force_save=True)
                elif key == ord(' '):
                    self.print_statistics()
                
                # Small delay to prevent high CPU usage
                time.sleep(0.001)
                
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        
        finally:
            # Final save to CSV
            self.save_to_csv(force_save=True)
            
            # Create summary CSV
            self.create_summary_csv()
            
            # Print final statistics
            self.print_statistics()
            
            # Cleanup
            if self.cap:
                self.cap.release()
            cv2.destroyAllWindows()
            print("Simple Object Counter stopped.")
            print(f"Results saved to: {self.csv_filepath}")

def main():
    """Main function"""
    print("Simple Object Counter v1.0")
    print("="*30)
    
    # Configuration
    model_path = "model.pt"  # Path to your YOLO model
    camera_source = 0        # Camera index (0 for default webcam)
    
    # Create and run counter
    counter = SimpleObjectCounter(model_path, camera_source)
    counter.run()

if __name__ == "__main__":
    main()
