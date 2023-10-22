import os, sys, pathlib
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QFormLayout, QLayout, QMenuBar,\
    QLineEdit, QLabel, QWidget, QDialog, QVBoxLayout, QHBoxLayout, QFileDialog, QSizePolicy, QCheckBox
from PySide6.QtGui import QPainter, QPixmap, QIcon, QIntValidator, QScreen, QPen, QBrush, QColor
from PySide6.QtCore import Qt, QPoint, QSize, QRect, QLine
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from video_logic import skew_map, save_map, get_map, crop_img, dust_selection
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
        # self.show()
        self.showMaximized()

    def exit(self) -> None:
        self.app.exit()


class SettingsDialog(QDialog):
    def __init__(self, parent_: QWidget = None):
        super().__init__(parent_)
        self.setWindowTitle("Настройки")

        self.thickness = cf.DEFAULT_THICKNESS
        self.frame_frequency = cf.DEFAULT_FRAME_FREQUENCY
        self.skew_effect = cf.DEFAULT_SKEW_EFFECT

        self.is_stabilization = False

        self.is_dust_selection = True
        self.dust_min_area = 50
        self.dust_thresh = 200

        self.thickness_editor = QLineEdit(self)
        self.frame_frequency_editor = QLineEdit(self)
        self.skew_effect_editor = QLineEdit(self)
        self.stabilization_editor = QCheckBox("Применить стабилизацию", self)
        self.dust_selection_editor = QCheckBox("Отображать контуры пыли", self)
        self.dust_min_editor = QLineEdit(self)
        self.dust_thresh_editor = QLineEdit(self)
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

        self.stabilization_editor.setChecked(self.is_stabilization)
        self.stabilization_editor.stateChanged.connect(self.stabilization_edit_action)

        self.dust_selection_editor.setChecked(self.is_dust_selection)
        self.dust_selection_editor.stateChanged.connect(self.dust_selection_edit_action)

        self.dust_min_editor.setAlignment(Qt.AlignLeft)
        self.dust_min_editor.setValidator(QIntValidator())
        self.dust_min_editor.setText(str(self.dust_min_area))
        self.dust_min_editor.textChanged.connect(self.dust_min_area_edit_action)

        self.dust_thresh_editor.setAlignment(Qt.AlignLeft)
        self.dust_thresh_editor.setValidator(QIntValidator())
        self.dust_thresh_editor.setText(str(self.dust_thresh))
        self.dust_thresh_editor.textChanged.connect(self.dust_thresh_edit_action)

    def _widgets_to_layout(self) -> None:
        layout = QFormLayout()
        layout.addRow("Параметры вырезки", None)
        layout.addRow("Толщина вырезки: ", self.thickness_editor)
        layout.addRow("Частота кадров: ", self.frame_frequency_editor)
        layout.addRow("Эффект искажения: ", self.skew_effect_editor)
        layout.addRow("Параметры стабилизации", None)
        layout.addWidget(self.stabilization_editor)
        layout.addRow("Параметры выискивания", None)
        layout.addWidget(self.dust_selection_editor)
        layout.addRow("Минимальная площадь пыли", self.dust_min_editor)
        layout.addRow("Яркость выискиваемой пыли", self.dust_thresh_editor)
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

    def stabilization_edit_action(self, state_):
        self.is_stabilization = state_

    def dust_selection_edit_action(self, state_):
        self.is_dust_selection = state_

    def dust_min_area_edit_action(self, text_: str) -> None:
        self.dust_min_area = 10 if len(text_) <= 0 or text_.find('-') != -1 or int(text_) < 10 else int(text_)
        if self.dust_min_area > 10:
            self.dust_min_area = 10
        self.dust_min_editor.setText(str(self.dust_min_area))

    def dust_thresh_edit_action(self, text_: str) -> None:
        self.dust_thresh = 150 if len(text_) <= 0 or text_.find('-') != -1 or int(text_) < 150 else int(text_)
        if self.dust_thresh > 255:
            self.dust_thresh = 255
        self.dust_thresh_editor.setText(str(self.dust_thresh))

    def run(self) -> None:
        self.exec()


class TubePainter(QPainter):
    def __init__(self, parent_: QWidget):
        super().__init__(parent_)
        self.rect_size = QSize(400, 510)
        self.pen = QPen()
        self.pen.setStyle(Qt.SolidLine)
        self.pen.setWidth(2)

        self.position = QPoint(750, 80)

    def draw_all(self, circle_d=20):
        self.setPen(self.pen)
        self.draw_sides(circle_d)
        self.draw_circles(circle_d)

    def draw_sides(self, circle_d):
        length = circle_d * 25 // 20
        self.draw_line(QPoint(0, 0), QPoint(self.rect_size.width(), 0))
        self.draw_line(QPoint(0, self.rect_size.height()),
                       QPoint(self.rect_size.width(), self.rect_size.height()))
        for y in range(0, self.rect_size.height(), circle_d + length):
            if y + length > self.rect_size.height():
                length = self.rect_size.height() - y
            self.draw_line(QPoint(0, y), QPoint(0, y + length))
            self.draw_line(QPoint(self.rect_size.width(), y), QPoint(self.rect_size.width(), y + length))

    def draw_line(self, pos1: QPoint, pos2: QPoint):
        line = QLine(pos1 + self.position, pos2 + self.position)
        self.drawLine(line)

    def draw_circles(self, circle_d):
        brush_circle = QBrush(QColor(240, 240, 240))
        length = circle_d * 25 // 20
        for y in range(length + circle_d // 2, self.rect_size.height(), circle_d + length):
            self.drawEllipse(QPoint(0, y) + self.position, circle_d, circle_d // 2)
            self.drawEllipse(QPoint(self.rect_size.width(), y) + self.position, circle_d, circle_d // 2)
            self.fillRect(QRect(QPoint(- 2 - circle_d, y - circle_d // 2 - 2) + self.position,
                                QSize(circle_d, circle_d + 2 * 2)), brush_circle)
            self.fillRect(QRect(QPoint(self.rect_size.width() + 2, y - circle_d // 2 - 2) + self.position,
                                QSize(circle_d, circle_d + 2 * 2)), brush_circle)


class PaintTube(QWidget):
    def __init__(self, parent_: QWidget = None):
        super().__init__(parent_)
        self.setMinimumSize(2000, 1000)
        self.img = None

    def paintEvent(self, event_) -> None:
        painter = TubePainter(self)
        painter.draw_all()

    def connect_img(self, img_) -> None:
        self.img = img_

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
        if self.settings_dialog.is_dust_selection:
            self.img = dust_selection(self.img, self.settings_dialog.dust_thresh,
                                      self.settings_dialog.dust_min_area)

    def show_results(self):
        if self.img is None:
            return
        self.map_widget.set_img(self.img)
        self.map_widget.setVisible(True)
        self.paint_map.set_active(True)
        self.paint_map.update()

    def exit_action(self) -> None:
        self.main_window.exit()


def window_main() -> None:
    app = QApplication()
    main_window = MainWindow(app)
    main_window.run()
    app.exec()
