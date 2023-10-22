import os, sys, pathlib
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QFormLayout, QLayout, QMenuBar,\
    QLineEdit, QLabel, QWidget, QDialog, QVBoxLayout, QHBoxLayout, QFileDialog, QSizePolicy
from PySide6.QtGui import QPainter, QPixmap, QIcon, QIntValidator, QScreen
from PySide6.QtCore import Qt, QPoint, QSize, QRect, QLine
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from video_logic import skew_map, save_map, get_map, crop_img
from loadlabel import loading
import config as cf


class MainWindow(QMainWindow):
    def __init__(self, app_: QApplication):
        super().__init__()
        self.app = app_
        self.__window_init()

        self.setCentralWidget(MenuWidget(self))

    def __window_init(self) -> None:
        self.setWindowTitle(cf.MAIN_WINDOW_TITLE)
        self.setMinimumSize(cf.MAIN_WINDOW_MINIMUM_SIZE)
        # self.setWindowIcon(QIcon(cf.ICON_WINDOW_PATH))

    def run(self) -> None:
        self.show()

    def exit(self) -> None:
        self.app.exit()


class SettingsDialog(QDialog):
    def __init__(self, parent_: QWidget = None):
        super().__init__(parent_)

        self.thickness = cf.DEFAULT_THICKNESS
        self.frame_frequency = cf.DEFAULT_FRAME_FREQUENCY
        self.skew_effect = cf.DEFAULT_SKEW_EFFECT

        self.thickness_editor = QLineEdit(self)
        self.frame_frequency_editor = QLineEdit(self)
        self.skew_effect_editor = QLineEdit(self)
        self._editors_init()

        self.ok_btn = QPushButton("Oк", self)
        self.ok_btn.clicked.connect(self.close)

        self._widgets_to_layout()

    def _editors_init(self) -> None:
        self.thickness_editor.setAlignment(Qt.AlignLeft)
        self.thickness_editor.setValidator(QIntValidator())
        self.thickness_editor.setText(str(self.thickness))
        self.thickness_editor.textChanged.connect(self.thickness_edit_action)

        self.frame_frequency_editor.setAlignment(Qt.AlignLeft)
        self.frame_frequency_editor.setValidator(QIntValidator())
        self.frame_frequency_editor.setText(str(self.frame_frequency))
        self.frame_frequency_editor.textChanged.connect(self.frame_frequency_edit_action)

        self.skew_effect_editor.setAlignment(Qt.AlignLeft)
        self.skew_effect_editor.setValidator(QIntValidator())
        self.skew_effect_editor.setText(str(self.skew_effect))
        self.skew_effect_editor.textChanged.connect(self.skew_effect_edit_action)

    def _widgets_to_layout(self) -> None:
        layout = QFormLayout()
        layout.addRow("Параметры вырезки", None)
        layout.addRow("Толщина вырезки: ", self.thickness_editor)
        layout.addRow("Частота кадров: ", self.frame_frequency_editor)
        layout.addRow("Эффект искажения: ", self.skew_effect_editor)
        layout.addRow("Параметры стабилизации", None)
        layout.addRow("Параметры выискивания", None)
        layout.addWidget(self.ok_btn)
        self.setLayout(layout)

    def thickness_edit_action(self, text_: str) -> None:
        self.thickness = 0 if len(text_) <= 0 or text_.find('-') != -1 else int(text_)
        if self.thickness > 20:
            self.thickness = 20
        self.thickness_editor.setText(str(self.thickness))

    def frame_frequency_edit_action(self, text_: str) -> None:
        self.frame_frequency = 0 if len(text_) <= 0 or text_.find('-') != -1 else int(text_)
        if self.frame_frequency > 20:
            self.frame_frequency = 20
        self.frame_frequency_editor.setText(str(self.frame_frequency))

    def skew_effect_edit_action(self, text_: str) -> None:
        self.skew_effect = 0 if len(text_) <= 0 or text_.find('-') != -1 else int(text_)
        if self.skew_effect > 50:
            self.skew_effect = 50
        self.skew_effect_editor.setText(str(self.skew_effect))

    def run(self) -> None:
        self.exec()


class PaintTube(QWidget):
    def __init__(self, parent_: QWidget = None):
        super().__init__(parent_)

    def connect_img(self, img_) -> None:
        pass

    def set_active(self, is_active_: bool = True) -> False:
        self.setVisible(is_active_)


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        FigureCanvasQTAgg.__init__(self, self.fig)
        FigureCanvasQTAgg.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvasQTAgg.updateGeometry(self)


class MatGraphWidget(QWidget):
    def __init__(self, parent: QWidget = None):
        QWidget.__init__(self, parent)
        self.is_set_img = False
        self.canvas = MplCanvas()
        self.vbl = QVBoxLayout()
        self.vbl.addWidget(self.canvas)
        self.setLayout(self.vbl)

    def set_img(self, img):
        self.is_set_img = True
        self.canvas.ax.imshow(img)
        # self.canvas.ax.legend()
        self.canvas.draw()

    def clear(self):
        self.is_set_img = False
        self.canvas.ax.clear()
        self.canvas.axes_init()


def select_path_to_files(filter_str_: str, parent_: QWidget = None, **kwargs) -> list:
    file_dialog = QFileDialog(parent_)
    file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
    file_dialog.setNameFilter(filter_str_)
    if 'dir' in kwargs:
        file_dialog.setDirectory(kwargs['dir'])
    if not file_dialog.exec():
        return list()
    return file_dialog.selectedFiles()


def select_path_to_one_file(filter_str_: str, parent_: QWidget = None, **kwargs) -> str:
    if 'dir' in kwargs:
        return QFileDialog.getOpenFileName(parent_, "Выбрать файл", dir=kwargs['dir'], filter=filter_str_)[0]
    return QFileDialog.getOpenFileName(parent_,  "Выбрать файл", filter=filter_str_)[0]


class MenuWidget(QWidget):
    counter = 0

    def __init__(self, main_window_):
        super().__init__()
        self.main_window = main_window_
        self.settings_dialog = SettingsDialog(self)
        self.map_label = QLabel(self)
        self.map_label.setVisible(False)
        self.paint_map = PaintTube(self)
        self.paint_map.set_active(False)
        self.map_widget = MatGraphWidget(self)
        self.map_widget.setVisible(False)
        self.img = None

        self.menu_bar = QMenuBar(self)
        self.menu_bar.addAction("Выбрать видео").triggered.connect(self.select_video_action)
        self.menu_bar.addAction("Сохранить как").triggered.connect(self.save_action)
        self.menu_bar.addAction("Настройки").triggered.connect(self.settings_dialog.run)
        self.menu_bar.addAction("&Выйти", "Shift+Esc").triggered.connect(self.exit_action)

    def _widgets_to_layout(self) -> None:
        layout = QHBoxLayout()
        layout.addWidget(self.map_widget)
        # layout.addWidget(self.map_label)
        layout.addWidget(self.paint_map)
        self.setLayout(layout)

    def _save_by_path(self, path_: str, type_: str) -> None:
        if self.map_widget is not None and self.map_widget.is_set_img:
            QScreen.grabWindow(self.main_window.app.primaryScreen(),
                               self.map_widget.winId()).save(path_, type_)

    def save_action(self) -> None:
        filename = QFileDialog.getSaveFileName(self, filter="PNG files (*.png) ;; JPG files (*.jpg; *.jpeg)")
        self._save_by_path(filename[0], filename[0].split('.')[-1].lower())

    def select_video_action(self) -> None:
        path = select_path_to_one_file('MP4 files (*.mp4)', self)
        self.compute_video(path)

    @loading('show_results')
    def compute_video(self, path) -> None:
        self.img = get_map(path, self.settings_dialog.thickness, self.settings_dialog.frame_frequency)
        self.img = skew_map(self.img, self.settings_dialog.skew_effect)

    def show_results(self):
        if self.img is None:
            return
        self.map_widget.set_img(self.img)
        self.map_widget.setVisible(True)
        self.paint_map.set_active(True)

    def exit_action(self) -> None:
        self.main_window.exit()


def window_main() -> None:
    app = QApplication()
    main_window = MainWindow(app)
    main_window.run()
    app.exec()
