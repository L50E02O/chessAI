from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior

from src.ocr.board_detection import detect_board_from_image
from src.engine.stockfish_engine import get_best_move_for_fen

KV = '''
<RootWidget>:
    orientation: 'vertical'
    padding: 12
    spacing: 12

    BoxLayout:
        size_hint_y: None
        height: '40dp'
        spacing: 8

        Button:
            text: 'Select image'
            on_release: root.open_file_chooser()

        Button:
            text: 'Analyze'
            on_release: root.analyze_image()
            id: analyze_btn

    Label:
        text: root.image_path or 'No image selected'
        size_hint_y: None
        height: '30dp'

    Label:
        text: 'FEN:\\n' + (root.fen or '')
        size_hint_y: None
        height: '80dp'
        halign: 'left'
        valign: 'top'
        text_size: self.width, None

    Label:
        text: 'Best move: ' + (root.best_move or '---')
        size_hint_y: None
        height: '40dp'
'''


class LabelButton(ButtonBehavior, Label):
    """Small helper combining label look with button behavior."""
    pass


class RootWidget(BoxLayout):
    image_path = StringProperty('')
    fen = StringProperty('')
    best_move = StringProperty('')

    def open_file_chooser(self):
        from kivy.uix.filechooser import FileChooserListView
        content = BoxLayout(orientation='vertical')
        fc = FileChooserListView(filters=['*.png', '*.jpg', '*.jpeg'], size_hint_y=0.9)
        content.add_widget(fc)
        btns = BoxLayout(size_hint_y=0.1)

        def select(*args):
            if fc.selection:
                self.image_path = fc.selection[0]
                popup.dismiss()

        select_btn = LabelButton(text='Select')
        select_btn.bind(on_release=select)
        cancel_btn = LabelButton(text='Cancel')
        cancel_btn.bind(on_release=lambda *a: popup.dismiss())
        btns.add_widget(select_btn)
        btns.add_widget(cancel_btn)
        content.add_widget(btns)
        popup = Popup(title='Choose image', content=content, size_hint=(0.9, 0.9))
        popup.open()

    def analyze_image(self):
        if not self.image_path:
            Popup(title='Error', content=Label(text='Select an image first'), size_hint=(0.6,0.4)).open()
            return
        # detect board and get FEN
        fen = detect_board_from_image(self.image_path)
        self.fen = fen or 'Not detected'
        # get best move
        if fen:
            move = get_best_move_for_fen(fen)
            self.best_move = move or 'Not available'
        else:
            self.best_move = 'Not available'


class MobileApp(App):
    def build(self):
        Builder.load_string(KV)
        return RootWidget()


if __name__ == '__main__':
    MobileApp().run()
