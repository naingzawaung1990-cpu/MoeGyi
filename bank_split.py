import pygame
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
from ultralytics import YOLO
import time
from pathlib import Path
import numpy as np
import sys
import os
import threading
import queue
from collections import deque

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class YoloApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)
        self.window.geometry("1300x800")
        self.window.resizable(False, False)
        self.window.configure(bg="#0f0c96")

        self.cap = None
        self.video_loaded = False
        self.display_width = 1000
        self.display_height = 600
        
        # --- Split screen: left half = main, right half = top=phone, bottom=wallet ---
        self.half_width = self.display_width // 2   # 500
        self.half_height = self.display_height // 2 # 300 (each for phone/wallet)
        
        # --- Threading & Queue ---
        self.frame_queue = deque(maxlen=2)
        self.result_queue = queue.Queue(maxsize=2)
        self.running = False
        self.capture_thread = None
        self.process_thread = None
        
        # --- Performance Monitoring ---
        self.fps = 0
        self.inference_time = 0
        self.last_time = time.time()
        self.frame_count = 0
        self.latency = 0
        self.current_resolution = (0, 0)
        self.processed_frames = 0
        
        # --- Configurations ---
        self.model_path = resource_path(r"C:\Users\Admin\Desktop\BBANK\save3_yolo26m.pt")
        self.alarm_path = resource_path(r"C:\Users\Admin\Desktop\BBANK\alarm.mp3")
        
        self.class_colors = {
            'PISTOL': (0, 0, 255),
            'Rifle': (255, 0, 0),
            'No gun_phone': (0, 255, 0),
            'No gun_wallet': (0, 255, 255)
        }

        self.display_thresholds = {
            'PISTOL': 0.85,
            'Rifle': 0.75,
            'No gun_phone': 0.75,
            'No gun_wallet': 0.75
        }
        
        self.alarm_thresholds = {
            'PISTOL': 0.85,
            'Rifle': 0.75
        }
        
        self.alarm_trigger_classes = ['PISTOL', 'Rifle']
        self.alarm_frame_count = 0
        self.frames_threshold = 5
        self.display_classes = ['No gun_phone', 'No gun_wallet', 'PISTOL', 'Rifle']
        
        self.detection_imgsz = 1280
        self.confidence_threshold = 0.25
        
        self.frame_skip_counter = 0
        self.frame_skip_interval = 1
        self.prev_frame = None
        self.prev_frame_size = None
        self.motion_threshold = 3000
        self.min_motion_area = 500
        
        self.video_mode = False
        self.video_fps = 0
        self.video_frame_count = 0
        
        # Crop padding for phone/wallet boxes
        self.crop_padding = 25
        
        if not Path(self.model_path).exists():
            messagebox.showerror("Error", f"Model file not found at: {self.model_path}")
            self.window.destroy()
            return

        try:
            pygame.mixer.init()
            print("Loading YOLO model...")
            self.detection_model = YOLO(self.model_path)
            self.class_names = self.detection_model.names
            print(f"Model loaded. Classes: {list(self.class_names.values())}")
            print("Warming up model...")
            dummy_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
            _ = self.detection_model(dummy_frame, verbose=False, imgsz=1280)
            print("Model ready!")
        except Exception as e:
            messagebox.showerror("Error", f"Initialization Error: {str(e)}")
            self.window.destroy()
            return
        
        self.update_id = None
        self.setup_ui()
        print("Application initialized successfully!")

    def setup_ui(self):
        tk.Label(self.window, text="Automatic Gun Detection System",
                 bg="#3834f0", fg="#E5F902", font=("Arial", 24, "bold"),
                 anchor="center", width=100, height=2).pack(side=tk.TOP, fill=tk.X)

        self.middle_frame = tk.Frame(self.window, bg="#0f0c96")
        self.middle_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.left_frame = tk.Frame(self.middle_frame, bg="#0f0c96")
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.button_frame = tk.Frame(self.left_frame, bg="#0f0c96")
        self.button_frame.pack(side=tk.LEFT, padx=5, pady=10, anchor="n")

        btn_style = {"font": ("Arial", 12, "bold"), "width": 7, "height": 2}
        tk.Button(self.button_frame, text="VIDEO", bg="#aeb1b0", command=self.browse_video, **btn_style).grid(row=0, column=1, pady=5)
        tk.Button(self.button_frame, text="WEB", bg="#37fab9", command=self.use_webcam, **btn_style).grid(row=1, column=0, pady=5, padx=5)
        tk.Button(self.button_frame, text="STOP", bg="#e1f00b", command=self.stop_capture, **btn_style).grid(row=1, column=1, pady=5, padx=5)
        tk.Button(self.button_frame, text="CCTV", bg="#05f521", command=self.use_cctv, **btn_style).grid(row=1, column=2, pady=5, padx=5)
        tk.Button(self.button_frame, text="PERF", bg="#fc9d00", command=self.show_performance, **btn_style).grid(row=2, column=0, pady=5)
        tk.Button(self.button_frame, text="QUIT", bg="#fc3f00", command=self.quit_app, **btn_style).grid(row=2, column=1, pady=5)
        tk.Button(self.button_frame, text="LOW", bg="#9d03fc", command=self.set_low_latency, **btn_style).grid(row=2, column=2, pady=5)

        self.video_container = tk.Frame(self.left_frame, bg="black", width=self.display_width, height=self.display_height)
        self.video_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.video_container.pack_propagate(False)

        self.video_label = tk.Label(self.video_container, bg="black")
        self.video_label.pack(fill=tk.BOTH, expand=True)

        self.resolution_label = tk.Label(self.video_container, 
                                         text="Res: 0x0",
                                         bg="black", fg="white", 
                                         font=("Arial", 10, "bold"))
        self.resolution_label.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)
        
        self.status_label = tk.Label(self.left_frame, text="Status: Ready | FPS: 0 | Inf: 0ms", 
                                     bg="#0f0c96", fg="white", font=("Arial", 12, "bold"))
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
        self.perf_label = tk.Label(self.left_frame, text="Latency: 0ms | Frame: 0", 
                                   bg="#0f0c96", fg="yellow", font=("Arial", 10))
        self.perf_label.pack(side=tk.BOTTOM, fill=tk.X)

    def update_resolution_display(self):
        width, height = self.current_resolution
        if width > 0 and height > 0:
            self.resolution_label.config(text=f"Res: {width}x{height}")
            if width >= 2560 or height >= 1440:
                self.resolution_label.config(fg="#00FF00")
            elif width >= 1920 or height >= 1080:
                self.resolution_label.config(fg="#FFFF00")
            else:
                self.resolution_label.config(fg="#FFA500")
        else:
            self.resolution_label.config(text="Res: 0x0", fg="white")

    def set_low_latency(self):
        if self.cap:
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.cap.set(cv2.CAP_PROP_FPS, 25)
            messagebox.showinfo("Info", "Low latency mode activated!")

    def extract_crop(self, frame, xyxy, padding=25):
        """Extract cropped region from frame with padding. Returns None if invalid."""
        h, w = frame.shape[:2]
        x1, y1, x2, y2 = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(w, x2 + padding)
        y2 = min(h, y2 + padding)
        if x2 <= x1 or y2 <= y1:
            return None
        return frame[y1:y2, x1:x2].copy()

    def extract_phone_wallet_crops(self, results, frame):
        """Get first No gun_phone and No gun_wallet crop from results. Returns (phone_crop, wallet_crop)."""
        phone_crop = None
        wallet_crop = None
        for result in results:
            for box in result.boxes:
                name = self.class_names[int(box.cls)]
                conf = float(box.conf)
                thresh = self.display_thresholds.get(name, 0.5)
                if conf < thresh:
                    continue
                if name == 'No gun_phone' and phone_crop is None:
                    phone_crop = self.extract_crop(frame, box.xyxy.cpu().numpy().flatten())
                elif name == 'No gun_wallet' and wallet_crop is None:
                    wallet_crop = self.extract_crop(frame, box.xyxy.cpu().numpy().flatten())
                if phone_crop is not None and wallet_crop is not None:
                    return (phone_crop, wallet_crop)
        return (phone_crop, wallet_crop)

    def build_split_display(self, main_frame, phone_crop, wallet_crop):
        """Build 1000x600 image: left half = main video, right top = phone, right bottom = wallet."""
        composite = np.zeros((self.display_height, self.display_width, 3), dtype=np.uint8)
        composite[:] = (30, 30, 30)
        
        # Left half: main video (scale to fit 500x600, keep aspect ratio)
        h, w = main_frame.shape[:2]
        left_w, left_h = self.half_width, self.display_height
        scale = min(left_w / w, left_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        resized_main = cv2.resize(main_frame, (new_w, new_h))
        x0 = (left_w - new_w) // 2
        y0 = (left_h - new_h) // 2
        composite[0:left_h, 0:left_w][y0:y0+new_h, x0:x0+new_w] = resized_main
        
        # Right half: top = phone (500x300), bottom = wallet (500x300)
        slot_w, slot_h = self.half_width, self.half_height
        base_x = self.half_width
        
        # Top slot: Phone
        if phone_crop is not None and phone_crop.size > 0:
            ph, pw = phone_crop.shape[:2]
            r = min(slot_w / pw, slot_h / ph)
            nw, nh = int(pw * r), int(ph * r)
            small = cv2.resize(phone_crop, (nw, nh))
            sx = (slot_w - nw) // 2
            sy = (slot_h - nh) // 2
            composite[0:slot_h, base_x:base_x+slot_w][sy:sy+nh, sx:sx+nw] = small
            cv2.putText(composite, "PHONE", (base_x + 10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(composite, "PHONE -", (base_x + 10, slot_h//2 + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (120, 120, 120), 2)
        
        # Bottom slot: Wallet / QR
        if wallet_crop is not None and wallet_crop.size > 0:
            wh, ww = wallet_crop.shape[:2]
            r = min(slot_w / ww, slot_h / wh)
            nw, nh = int(ww * r), int(wh * r)
            small = cv2.resize(wallet_crop, (nw, nh))
            sx = (slot_w - nw) // 2
            sy = (slot_h - nh) // 2
            composite[slot_h:self.display_height, base_x:base_x+slot_w][sy:sy+nh, sx:sx+nw] = small
            cv2.putText(composite, "WALLET/QR", (base_x + 10, slot_h + 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        else:
            cv2.putText(composite, "WALLET/QR -", (base_x + 10, slot_h + slot_h//2 + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (120, 120, 120), 2)
        
        # Separator line between left and right
        cv2.line(composite, (self.half_width, 0), (self.half_width, self.display_height), (80, 80, 80), 2)
        cv2.line(composite, (self.half_width, self.half_height), (self.display_width, self.half_height), (80, 80, 80), 2)
        
        return composite

    def capture_frames(self):
        print("Capture thread started")
        frame_interval = 0
        last_capture_time = time.time()
        while self.running:
            if self.cap and self.cap.isOpened():
                try:
                    if self.video_mode and self.video_fps > 0:
                        current_time = time.time()
                        elapsed = current_time - last_capture_time
                        frame_interval = 1.0 / self.video_fps
                        if elapsed < frame_interval:
                            time.sleep(frame_interval - elapsed)
                        last_capture_time = time.time()
                    ret, frame = self.cap.read()
                    if ret:
                        if self.video_mode:
                            self.video_frame_count += 1
                        if len(self.frame_queue) >= 2:
                            self.frame_queue.popleft()
                        self.frame_queue.append(frame)
                        h, w = frame.shape[:2]
                        self.current_resolution = (w, h)
                    else:
                        if self.video_mode:
                            print(f"Video ended. Total frames: {self.video_frame_count}")
                            self.stop_capture()
                        time.sleep(0.001)
                except Exception as e:
                    print(f"Capture error: {e}")
                    time.sleep(0.01)
            else:
                time.sleep(0.01)
        print("Capture thread stopped")

    def process_frames(self):
        print("Processing thread started")
        processed_count = 0
        while self.running:
            if self.frame_queue:
                try:
                    frame = self.frame_queue.popleft()
                    current_h, current_w = frame.shape[:2]
                    self.current_resolution = (current_w, current_h)
                    
                    if self.video_mode:
                        start_inf = time.time()
                        results = self.detection_model(frame, conf=self.confidence_threshold,
                                                      imgsz=self.detection_imgsz, half=True,
                                                      verbose=False, max_det=10)
                        self.inference_time = (time.time() - start_inf) * 1000
                    else:
                        motion_detected = self.check_motion(frame)
                        if not motion_detected:
                            self.frame_skip_counter += 1
                            if self.frame_skip_counter % self.frame_skip_interval != 0:
                                continue
                        start_inf = time.time()
                        results = self.detection_model(frame, conf=self.confidence_threshold,
                                                      imgsz=self.detection_imgsz, half=True,
                                                      verbose=False, max_det=10)
                        self.inference_time = (time.time() - start_inf) * 1000
                    
                    detected_alarm = False
                    for result in results:
                        for box in result.boxes:
                            name = self.class_names[int(box.cls)]
                            conf = float(box.conf)
                            if name in self.alarm_trigger_classes:
                                alarm_thresh = self.alarm_thresholds.get(name)
                                if alarm_thresh and conf >= alarm_thresh:
                                    detected_alarm = True
                                    break
                        if detected_alarm:
                            break
                    
                    annotated_frame = self.custom_plot(results, frame.copy())
                    annotated_frame = self.add_resolution_overlay(annotated_frame)
                    phone_crop, wallet_crop = self.extract_phone_wallet_crops(results, frame)
                    
                    processed_count += 1
                    self.processed_frames = processed_count
                    
                    if self.result_queue.qsize() < 2:
                        self.result_queue.put((annotated_frame, phone_crop, wallet_crop, detected_alarm,
                                             self.inference_time, processed_count))
                    else:
                        try:
                            self.result_queue.get_nowait()
                            self.result_queue.put((annotated_frame, phone_crop, wallet_crop, detected_alarm,
                                                 self.inference_time, processed_count))
                        except Exception:
                            pass
                except IndexError:
                    pass
                except Exception as e:
                    print(f"Processing error: {e}")
                    continue
            time.sleep(0.001)
        print("Processing thread stopped")

    def add_resolution_overlay(self, frame):
        width, height = self.current_resolution
        if width > 0 and height > 0:
            overlay = frame.copy()
            text = f"{width}x{height}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 1.0
            thickness = 2
            (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
            text_x = frame.shape[1] - text_width - 20
            text_y = frame.shape[0] - 20
            cv2.rectangle(overlay, (text_x - 10, text_y - text_height - 10),
                         (text_x + text_width + 10, text_y + 10), (0, 0, 0), -1)
            alpha = 0.6
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
            cv2.putText(frame, text, (text_x, text_y), font, font_scale, (255, 255, 255), thickness)
        return frame

    def check_motion(self, frame):
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if self.prev_frame is None:
                self.prev_frame = gray
                self.prev_frame_size = gray.shape
                return True
            if gray.shape != self.prev_frame.shape:
                self.prev_frame = cv2.resize(self.prev_frame, (gray.shape[1], gray.shape[0]))
                self.prev_frame_size = gray.shape
            gray_blur = cv2.GaussianBlur(gray, (21, 21), 0)
            prev_blur = cv2.GaussianBlur(self.prev_frame, (21, 21), 0)
            frame_diff = cv2.absdiff(prev_blur, gray_blur)
            _, thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
            thresh = cv2.dilate(thresh, None, iterations=2)
            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            motion_detected = False
            for contour in contours:
                if cv2.contourArea(contour) > self.min_motion_area:
                    motion_detected = True
                    break
            self.prev_frame = gray
            self.prev_frame_size = gray.shape
            return motion_detected
        except Exception as e:
            print(f"Motion detection error: {e}")
            self.prev_frame = None
            self.prev_frame_size = None
            return True

    def update_frame(self):
        if not self.running:
            return
        current_time = time.time()
        self.frame_count += 1
        if current_time - self.last_time >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_time = current_time
        
        if not self.result_queue.empty():
            try:
                annotated_frame, phone_crop, wallet_crop, detected_alarm, inf_time, processed_count = self.result_queue.get()
                self.latency = (time.time() - current_time) * 1000
                self.update_resolution_display()
                
                if detected_alarm:
                    self.alarm_frame_count += 1
                    if self.alarm_frame_count >= self.frames_threshold:
                        if not pygame.mixer.music.get_busy():
                            try:
                                pygame.mixer.music.load(self.alarm_path)
                                pygame.mixer.music.play()
                            except Exception:
                                pass
                        self.status_label.config(text=f"⚠️ GUN DETECTED! ⚠️ | FPS: {self.fps}", fg="red")
                else:
                    self.alarm_frame_count = 0
                    self.status_label.config(text=f"Status: Monitoring | FPS: {self.fps} | Inf: {inf_time:.0f}ms", fg="green")
                
                self.perf_label.config(text=f"Latency: {self.latency:.0f}ms | Frame: {processed_count}")
                
                # Split screen: left = main, right = phone (top) + wallet (bottom)
                display_frame = self.build_split_display(annotated_frame, phone_crop, wallet_crop)
                
                rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb_frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
                self.video_label.image = imgtk
            except Exception as e:
                print(f"Display error: {e}")
        
        self.update_id = self.window.after(10, self.update_frame)

    def start_threads(self):
        self.running = True
        self.capture_thread = threading.Thread(target=self.capture_frames, daemon=True)
        self.process_thread = threading.Thread(target=self.process_frames, daemon=True)
        self.capture_thread.start()
        self.process_thread.start()
        print("Threads started successfully")

    def stop_capture(self):
        print("Stopping capture...")
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=1)
        if self.process_thread:
            self.process_thread.join(timeout=1)
        if self.cap:
            self.cap.release()
        self.cap = None
        self.video_loaded = False
        self.video_mode = False
        if self.update_id:
            self.window.after_cancel(self.update_id)
        pygame.mixer.music.stop()
        self.clear_display()
        self.frame_queue.clear()
        while not self.result_queue.empty():
            try:
                self.result_queue.get_nowait()
            except Exception:
                break
        print("Capture stopped")

    def clear_display(self):
        black_img = Image.new('RGB', (self.display_width, self.display_height), color='black')
        black_tk = ImageTk.PhotoImage(black_img)
        self.video_label.configure(image=black_tk)
        self.video_label.image = black_tk
        self.current_resolution = (0, 0)
        self.update_resolution_display()
        self.status_label.config(text="Status: Stopped", fg="white")
        self.perf_label.config(text="Latency: 0ms | Frame: 0")

    def browse_video(self):
        self.stop_capture()
        path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv")])
        if path:
            self.cap = cv2.VideoCapture(path)
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.video_fps = self.cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            print(f"Video Info: {width}x{height}, FPS: {self.video_fps}, Total frames: {total_frames}")
            self.video_mode = True
            self.video_frame_count = 0
            self.frame_skip_interval = 1
            self.current_resolution = (width, height)
            self.video_loaded = True
            self.start_threads()
            self.update_frame()
            self.status_label.config(text=f"Video: {os.path.basename(path)} | FPS: {self.video_fps:.1f}", fg="cyan")

    def use_webcam(self):
        self.stop_capture()
        self.video_mode = False
        self.frame_skip_interval = 3
        self.cap = cv2.VideoCapture(0)
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.current_resolution = (width, height)
            self.video_loaded = True
            self.start_threads()
            self.update_frame()
            self.status_label.config(text="Webcam Active", fg="cyan")

    def use_cctv(self):
        self.stop_capture()
        self.video_mode = False
        self.frame_skip_interval = 3
        rtsp_url = "rtsp://admin:admin123456789@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0&tcp"
        self.cap = cv2.VideoCapture(rtsp_url)
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.current_resolution = (width, height)
            print(f"CCTV connected: {width}x{height} @ {fps}fps")
            self.video_loaded = True
            self.start_threads()
            self.update_frame()
            self.status_label.config(text=f"CCTV: {width}x{height} @ {fps:.1f}fps", fg="cyan")
        else:
            messagebox.showerror("Error", "Cannot connect to CCTV!")

    def custom_plot(self, results, img):
        for result in results:
            for box in result.boxes:
                name = self.class_names[int(box.cls)]
                conf = float(box.conf)
                if name not in self.display_classes:
                    continue
                display_thresh = self.display_thresholds.get(name, 0.5)
                if conf >= display_thresh:
                    color = self.class_colors.get(name, (255, 255, 255))
                    xyxy = box.xyxy.cpu().numpy().flatten().astype(int)
                    cv2.rectangle(img, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), color, 2)
                    label = f"{name} {conf:.2f}"
                    cv2.putText(img, label, (xyxy[0], xyxy[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        return img

    def show_performance(self):
        width, height = self.current_resolution
        stats = f"""
        Performance Statistics:
        -----------------------
        Current FPS: {self.fps}
        Inference Time: {self.inference_time:.0f}ms
        Total Latency: {self.latency:.0f}ms
        Frame Queue Size: {len(self.frame_queue)}
        Alarm Count: {self.alarm_frame_count}
        Video Mode: {self.video_mode}
        Video FPS: {self.video_fps:.1f}
        Processed Frames: {self.processed_frames}
        Current Resolution: {width}x{height}
        Display: {self.display_width}x{self.display_height} (Split: Left=Main, Right=Phone+Wallet)
        """
        messagebox.showinfo("Performance Info", stats)

    def quit_app(self):
        self.stop_capture()
        pygame.mixer.quit()
        self.window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = YoloApp(root, "GUN DETECTION - SPLIT: PHONE | WALLET/QR")
    root.mainloop()
