from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.switch import Switch
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, Rectangle
import cv2
import numpy as np
from chessboard_processor import process_frame, initialize_model
from chess_engine import ChessEngineManager
from chess_com_api import ChessComAPI
import threading
import queue
import time

# Set window size and color scheme
Window.size = (1200, 800)
PRIMARY_COLOR = get_color_from_hex('#2C3E50')
SECONDARY_COLOR = get_color_from_hex('#ECF0F1')
ACCENT_COLOR = get_color_from_hex('#3498DB')

class ModernButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = ACCENT_COLOR
        self.color = (1, 1, 1, 1)
        self.font_size = dp(16)
        self.size_hint = (0.8, None)
        self.height = dp(50)
        self.pos_hint = {'center_x': 0.5}

class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.canvas.before.add(Color(*PRIMARY_COLOR))
        self.canvas.before.add(Rectangle(pos=self.pos, size=self.size))
        
        layout = BoxLayout(orientation='vertical', spacing=dp(20), padding=dp(40))
        
        # Title with modern styling
        title = Label(
            text='Chess Vision Assistant',
            font_size=dp(32),
            color=SECONDARY_COLOR,
            size_hint_y=0.3
        )
        
        # Modern buttons
        live_btn = ModernButton(
            text='Live Feed Monitoring',
            on_press=self.switch_to_live
        )
        
        offline_btn = ModernButton(
            text='Offline to Online',
            on_press=self.switch_to_offline
        )
        
        layout.add_widget(title)
        layout.add_widget(live_btn)
        layout.add_widget(offline_btn)
        self.add_widget(layout)
    
    def switch_to_live(self, instance):
        self.manager.current = 'live'
    
    def switch_to_offline(self, instance):
        self.manager.current = 'offline'

class LiveFeedScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_fen = None
        self.model = None
        self.capture = None
        self.chess_engine = ChessEngineManager()
        self.frame_queue = queue.Queue(maxsize=2)
        self.processing_thread = None
        self.is_running = False
        self.last_processed_time = 0
        self.processing_interval = 0.5  # Process every 0.5 seconds
        
        # Main layout
        main_layout = BoxLayout(orientation='horizontal', spacing=dp(20), padding=dp(20))
        
        # Left panel - Camera feed
        left_panel = BoxLayout(orientation='vertical', size_hint_x=0.6)
        
        # Status bar
        status_bar = BoxLayout(size_hint_y=0.1)
        self.error_label = Label(
            text='',
            color=(1, 0, 0, 1),
            size_hint_x=0.7
        )
        self.status_label = Label(
            text='',
            color=SECONDARY_COLOR,
            size_hint_x=0.3
        )
        status_bar.add_widget(self.error_label)
        status_bar.add_widget(self.status_label)
        
        # Camera feed with border
        camera_container = BoxLayout(
            orientation='vertical',
            size_hint_y=0.8,
            padding=dp(2)
        )
        with camera_container.canvas.before:
            Color(*ACCENT_COLOR)
            self.camera_border = Rectangle(pos=camera_container.pos, size=camera_container.size)
        self.img = Image(size_hint=(1, 1))
        camera_container.add_widget(self.img)
        
        # Controls
        controls = BoxLayout(
            orientation='horizontal',
            size_hint_y=0.1,
            spacing=dp(10)
        )
        
        back_btn = ModernButton(
            text='Back',
            size_hint_x=0.3,
            on_press=self.go_back
        )
        
        switch_layout = BoxLayout(orientation='horizontal', size_hint_x=0.7)
        switch_label = Label(
            text='Suggest Moves',
            color=SECONDARY_COLOR,
            size_hint_x=0.7
        )
        self.suggest_moves = Switch(active=True, size_hint_x=0.3)
        self.suggest_moves.bind(active=self.on_suggest_moves_change)
        switch_layout.add_widget(switch_label)
        switch_layout.add_widget(self.suggest_moves)
        
        controls.add_widget(back_btn)
        controls.add_widget(switch_layout)
        
        left_panel.add_widget(status_bar)
        left_panel.add_widget(camera_container)
        left_panel.add_widget(controls)
        
        # Right panel - Chess board
        right_panel = BoxLayout(orientation='vertical', size_hint_x=0.4)
        
        # FEN display
        self.fen_label = Label(
            text='FEN: ',
            color=SECONDARY_COLOR,
            size_hint_y=0.1
        )
        
        # Digital board
        board_container = BoxLayout(
            orientation='vertical',
            size_hint_y=0.9,
            padding=dp(2)
        )
        with board_container.canvas.before:
            Color(*ACCENT_COLOR)
            self.board_border = Rectangle(pos=board_container.pos, size=board_container.size)
        self.digital_board = Image(size_hint=(1, 1))
        board_container.add_widget(self.digital_board)
        
        right_panel.add_widget(self.fen_label)
        right_panel.add_widget(board_container)
        
        main_layout.add_widget(left_panel)
        main_layout.add_widget(right_panel)
        self.add_widget(main_layout)

    def on_enter(self):
        try:
            self.status_label.text = "Initializing..."
            self.model = initialize_model()
            self.capture = cv2.VideoCapture(0)
            
            # Set camera properties for better quality
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.capture.set(cv2.CAP_PROP_FPS, 30)
            self.capture.set(cv2.CAP_PROP_AUTOFOCUS, 1)
            self.capture.set(cv2.CAP_PROP_BRIGHTNESS, 128)
            self.capture.set(cv2.CAP_PROP_CONTRAST, 128)
            
            if not self.capture.isOpened():
                raise Exception("Could not open camera")
            
            self.is_running = True
            self.processing_thread = threading.Thread(target=self.process_frames)
            self.processing_thread.start()
            
            self.status_label.text = ""
            # Update display at 60 FPS for smooth video
            Clock.schedule_interval(self.update_display, 1.0 / 60.0)
            
        except Exception as e:
            self.error_label.text = str(e)
    
    def on_leave(self):
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join()
        Clock.unschedule(self.update_display)
        if self.capture:
            self.capture.release()
    
    def process_frames(self):
        """Process frames for chess detection in a separate thread"""
        while self.is_running:
            try:
                current_time = time.time()
                if current_time - self.last_processed_time >= self.processing_interval:
                    ret, frame = self.capture.read()
                    if not ret:
                        continue
                    
                    # Process frame for chess detection
                    processed_frame, fen = process_frame(frame, self.model)
                    
                    # Update queue with new frame and FEN
                    if not self.frame_queue.full():
                        self.frame_queue.put((processed_frame, fen))
                    
                    self.last_processed_time = current_time
                
                # Small sleep to prevent CPU overuse
                time.sleep(0.01)
                    
            except Exception as e:
                print(f"Error in processing thread: {e}")
    
    def update_display(self, dt):
        """Update the display with the latest frame"""
        try:
            ret, frame = self.capture.read()
            if not ret:
                return
            
            # Update video feed with smooth frame
            display_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            buf = cv2.flip(display_frame, 0)
            texture = Texture.create(
                size=(display_frame.shape[1], display_frame.shape[0]),
                colorfmt='rgb'
            )
            texture.blit_buffer(buf.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
            self.img.texture = texture
            
            # Check for new processed frame and FEN
            if not self.frame_queue.empty():
                processed_frame, fen = self.frame_queue.get()
                
                # Update FEN and digital board
                if fen and fen != self.current_fen:
                    self.fen_label.text = f'FEN: {fen}'
                    self.current_fen = fen
                    
                    # Update chess engine position
                    if self.chess_engine.update_position(fen):
                        # Get best move if suggestions are enabled
                        if self.suggest_moves.active:
                            best_move = self.chess_engine.get_best_move()
                            if best_move:
                                self.chess_engine.last_move = best_move
                        
                        # Render and display the board
                        board_img = self.chess_engine.render_board()
                        if board_img is not None:
                            # Convert BGR to RGB for Kivy
                            board_img = cv2.cvtColor(board_img, cv2.COLOR_BGR2RGB)
                            # Create texture
                            board_texture = Texture.create(
                                size=(board_img.shape[1], board_img.shape[0]),
                                colorfmt='rgb'
                            )
                            board_texture.blit_buffer(board_img.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
                            self.digital_board.texture = board_texture
                            self.status_label.text = "Board updated"
                        else:
                            self.error_label.text = "Failed to render board"
                    else:
                        self.error_label.text = "Invalid FEN position"
                
        except Exception as e:
            self.error_label.text = str(e)
            print(f"Error in update_display: {e}")
    
    def on_suggest_moves_change(self, instance, value):
        if not value:
            self.chess_engine.last_move = None
            # Re-render board without move highlight
            if self.current_fen:
                self.update_display(0)  # Force update with current FEN
    
    def go_back(self, instance):
        self.manager.current = 'home'

class OfflineScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=dp(20), padding=dp(40))
        
        # Status labels
        self.error_label = Label(
            text='',
            color=(1, 0, 0, 1),
            size_hint_y=0.1
        )
        self.status_label = Label(
            text='',
            color=SECONDARY_COLOR,
            size_hint_y=0.1
        )
        
        # Modern buttons
        camera_btn = ModernButton(
            text='Take Photo',
            on_press=self.take_photo
        )
        
        gallery_btn = ModernButton(
            text='Choose from Gallery',
            on_press=self.choose_from_gallery
        )
        
        back_btn = ModernButton(
            text='Back',
            on_press=self.go_back
        )
        
        layout.add_widget(self.error_label)
        layout.add_widget(self.status_label)
        layout.add_widget(camera_btn)
        layout.add_widget(gallery_btn)
        layout.add_widget(back_btn)
        self.add_widget(layout)
    
    def take_photo(self, instance):
        try:
            self.status_label.text = "Opening camera..."
            self.error_label.text = ""
            
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                raise Exception("Could not open camera")
            
            ret, frame = cap.read()
            if not ret:
                raise Exception("Could not capture image")
            
            cv2.imwrite('capture.jpg', frame)
            self.status_label.text = "Processing image..."
            
            self.process_image('capture.jpg')
            
        except Exception as e:
            self.error_label.text = str(e)
            self.status_label.text = ""
        finally:
            cap.release()
    
    def choose_from_gallery(self, instance):
        try:
            from plyer import filechooser
            
            self.status_label.text = "Select an image..."
            self.error_label.text = ""
            
            path = filechooser.open_file(
                title="Pick a chess image..",
                filters=[("Images", "*.jpg", "*.png")]
            )
            
            if path:
                self.status_label.text = "Processing image..."
                self.process_image(path[0])
            else:
                self.status_label.text = ""
                
        except Exception as e:
            self.error_label.text = str(e)
            self.status_label.text = ""
    
    def process_image(self, image_path):
        try:
            frame = cv2.imread(image_path)
            if frame is None:
                raise Exception("Could not load image")
            
            if not hasattr(self, 'model'):
                self.model = initialize_model()
            
            processed_frame, fen = process_frame(frame, self.model)
            
            if fen:
                self.status_label.text = "Opening in chess.com..."
                if ChessComAPI.open_analysis(fen):
                    self.status_label.text = f"Opened in chess.com"
                else:
                    raise Exception("Failed to open chess.com analysis")
            else:
                raise Exception("Could not detect chess position")
            
        except Exception as e:
            self.error_label.text = str(e)
            self.status_label.text = ""
    
    def go_back(self, instance):
        self.manager.current = 'home'

class ChessApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(LiveFeedScreen(name='live'))
        sm.add_widget(OfflineScreen(name='offline'))
        return sm

if __name__ == '__main__':
    ChessApp().run()
