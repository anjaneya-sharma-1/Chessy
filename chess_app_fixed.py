from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.switch import Switch
from kivy.clock import Clock
from kivy.graphics.texture import Texture
import cv2
import numpy as np
from chessboard_processor import process_frame, initialize_model
from chess_engine import ChessEngineManager
from chess_com_api import ChessComAPI

class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=10, padding=20)
        
        # Title
        title = Label(
            text='Chess Vision Assistant',
            font_size='24sp',
            size_hint_y=0.2
        )
        
        # Buttons
        live_btn = Button(
            text='Live Feed Monitoring',
            size_hint=(0.8, 0.2),
            pos_hint={'center_x': 0.5}
        )
        live_btn.bind(on_press=self.switch_to_live)
        
        offline_btn = Button(
            text='Offline to Online',
            size_hint=(0.8, 0.2),
            pos_hint={'center_x': 0.5}
        )
        offline_btn.bind(on_press=self.switch_to_offline)
        
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
        
        # Create a layout
        layout = BoxLayout(orientation='vertical')
        
        # Add error label
        self.error_label = Label(text='', color=(1, 0, 0, 1))
        layout.add_widget(self.error_label)
        
        # Add loading label
        self.loading_label = Label(text='', color=(0, 1, 0, 1))
        layout.add_widget(self.loading_label)
        
        # Add back button
        back_btn = Button(text='Back', size_hint=(1, 0.1))
        back_btn.bind(on_press=self.go_back)
        layout.add_widget(back_btn)
        
        # Add camera feed
        self.img = Image(size_hint=(1, 0.6))
        layout.add_widget(self.img)
        
        # Add FEN label
        self.fen_label = Label(text='FEN: ', size_hint=(1, 0.1))
        layout.add_widget(self.fen_label)
        
        # Add move suggestion switch
        switch_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        switch_label = Label(text='Suggest Moves: ')
        self.suggest_moves = Switch(active=True)
        self.suggest_moves.bind(active=self.on_suggest_moves_change)
        switch_layout.add_widget(switch_label)
        switch_layout.add_widget(self.suggest_moves)
        layout.add_widget(switch_layout)
        
        # Add digital board
        self.digital_board = Image(size_hint=(1, 0.6))
        layout.add_widget(self.digital_board)
        
        self.add_widget(layout)

    def on_enter(self):
        try:
            self.loading_label.text = "Initializing..."
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
            
            self.loading_label.text = ""
            Clock.schedule_interval(self.update, 1.0 / 30.0)  # 30 FPS
        except Exception as e:
            self.error_label.text = str(e)
    
    def on_leave(self):
        Clock.unschedule(self.update)
        if self.capture:
            self.capture.release()
    
    def on_suggest_moves_change(self, instance, value):
        if not value:  # If suggestions turned off
            self.chess_engine.last_best_move = None
            self.update_digital_board(self.current_fen)

    def update_digital_board(self, fen=None):
        """Update the digital board display"""
        if fen and fen != self.current_fen:
            self.current_fen = fen
            if self.chess_engine.update_position(fen):
                # Get and show best move if suggestions are enabled
                if self.suggest_moves.active:
                    best_move = self.chess_engine.get_best_move()
                    if best_move:
                        self.chess_engine.last_best_move = best_move
                
                # Render and display the board
                board_img = self.chess_engine.render_board()
                board_texture = Texture.create(size=(board_img.shape[1], board_img.shape[0]), colorfmt='bgr')
                board_texture.blit_buffer(board_img.tobytes(), colorfmt='bgr', bufferfmt='ubyte')
                self.digital_board.texture = board_texture

    def update(self, dt):
        try:
            ret, frame = self.capture.read()
            if not ret:
                raise Exception("Could not read from camera")

            # Create a clean copy for display
            display_frame = frame.copy()
            
            # Process frame for chess detection (original frame)
            processed_frame, fen = process_frame(frame, self.model)
            
            # Update video feed with chess detection results
            # Convert from BGR to RGB for Kivy
            display_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            
            # Create texture
            buf = cv2.flip(display_frame, 0)  # Flip vertically for Kivy
            texture = Texture.create(
                size=(display_frame.shape[1], display_frame.shape[0]), 
                colorfmt='rgb')
            texture.blit_buffer(buf.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
            self.img.texture = texture
            
            # Update FEN and digital board
            if fen:
                self.fen_label.text = f'FEN: {fen}'
                self.update_digital_board(fen)
                
        except Exception as e:
            self.error_label.text = str(e)
    
    def go_back(self, instance):
        self.manager.current = 'home'

class OfflineScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=10, padding=20)
        
        # Status labels
        self.error_label = Label(
            text='',
            color=(1, 0, 0, 1),  # Red color
            size_hint_y=0.1
        )
        self.status_label = Label(
            text='',
            size_hint_y=0.1
        )
        
        # Image selection buttons
        camera_btn = Button(
            text='Take Photo',
            size_hint=(0.8, 0.2),
            pos_hint={'center_x': 0.5}
        )
        camera_btn.bind(on_press=self.take_photo)
        
        gallery_btn = Button(
            text='Choose from Gallery',
            size_hint=(0.8, 0.2),
            pos_hint={'center_x': 0.5}
        )
        gallery_btn.bind(on_press=self.choose_from_gallery)
        
        back_btn = Button(
            text='Back',
            size_hint=(0.8, 0.1),
            pos_hint={'center_x': 0.5}
        )
        back_btn.bind(on_press=self.go_back)
        
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
            
            # Initialize camera
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                raise Exception("Could not open camera")
            
            # Capture frame
            ret, frame = cap.read()
            if not ret:
                raise Exception("Could not capture image")
            
            # Save the captured image
            cv2.imwrite('capture.jpg', frame)
            self.status_label.text = "Processing image..."
            
            # Process the image
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
            
            # Open file chooser
            path = filechooser.open_file(
                title="Pick a chess image..",
                filters=[("Images", "*.jpg", "*.png")]
            )
            
            if path:
                self.status_label.text = "Processing image..."
                # Process the selected image
                self.process_image(path[0])
            else:
                self.status_label.text = ""
                
        except Exception as e:
            self.error_label.text = str(e)
            self.status_label.text = ""
    
    def process_image(self, image_path):
        try:
            # Load and process image
            frame = cv2.imread(image_path)
            if frame is None:
                raise Exception("Could not load image")
            
            # Initialize YOLO model if not already done
            if not hasattr(self, 'model'):
                self.model = initialize_model()
            
            # Process frame and get FEN
            processed_frame, fen = process_frame(frame, self.model)
            
            if fen:
                self.status_label.text = "Opening in chess.com..."
                # Open position in chess.com
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
