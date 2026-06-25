from typing import override

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QContextMenuEvent, QCursor, QKeyEvent, QMouseEvent, QPainter, QPaintEvent, QPixmap, QScreen
from PySide6.QtWidgets import QApplication, QLabel, QMenu, QWidget, QGridLayout

import any_singleton.singletons as sgt

from count_anywhere import sgt_dns
from count_anywhere.libs.markers import CountMarker, Group, Marker, ReferenceMarker
from count_anywhere.libs.collections import Space


class MarkerWidget(QWidget):
    def __init__(
            self,
            parent: QWidget | None = None,
            data: Marker | None = None
    ) -> None:
        super().__init__(parent)

        if data is None:
            raise ValueError('`data` must be provided.')
        self.data: Marker = data
        self.sync_from_data()

        self.style = 'o'

    def sync_from_data(self) -> None:
        self.move(QPoint(self.data.x, self.data.y))


# TODO: 不时向temp文件写入当前demarker以免丢失，或者直接设计自动保存。

class MarkerView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.markers: Space = Space(2)

    def add_marker(self, marker: Marker) -> None:
        self.markers.add()

    def select_item_by_position(self, position: QPoint, /) -> None:
        pass

    @override
    def paintEvent(self, event: QPaintEvent, /) -> None:
        painter = QPainter(self)

    @override
    def mousePressEvent(self, event: QMouseEvent, /) -> None:
        pass

    @override
    def mouseDoubleClickEvent(self, event: QMouseEvent, /) -> None:
        pass

    @override
    def mouseMoveEvent(self, event: QMouseEvent, /) -> None:
        pass

    @override
    def mouseReleaseEvent(self, event: QMouseEvent, /) -> None:
        pass

    def contextMenuEvent(self, event: QContextMenuEvent, /) -> None:
        menu = QMenu()


class MarkerEditor(QWidget):
    def __init__(
            self,
            parent: QWidget | None = None,
            screen: QScreen | None = None,
            picture: QPixmap | None = None
    ) -> None:
        super().__init__(parent)

        config = sgt._get_singleton(sgt_dns.CONFIG)

        self.__count_i = 0
        self.__default_group = Group(
            name = '@default_group'
        )
        self.__default_reference_marker = ReferenceMarker(
            name = '@default_reference_marker',
            parent = self.__default_group,
            position = (0, 0),
            rotation = 0.0
        )

        window_flag = (
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint
        )
        if not config['debug']:
            window_flag |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlag(window_flag)
        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )
        self.setStyleSheet("""
            border: 1px solid #EE0000;
            border-radius: 1px;
        """)
        self.showFullScreen()

        if screen is None:
            screen = QApplication.primaryScreen()
        self.setScreen(screen)

        self.__layout = QGridLayout()
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.__edit_area = QLabel()
        if picture is not None:
            self.__edit_area.setPixmap(picture)
        else:
            self.__edit_area.setStyleSheet("""
                /*background: transparent;*/
                background-color: rgba(255, 255, 255, 1%);
            """)
        self.__edit_area.setFixedSize(screen.availableSize())
        self.__layout.addWidget(self.__edit_area)

        self.setLayout(self.__layout)

    def _create_marker(
            self,
            pos: Marker.Position,
            group: Group = None,
            ref: ReferenceMarker = None
    ) -> Marker:
        if group is None:
            group = self.__default_group
        if ref is None:
            ref = self.__default_reference_marker

        self.__count_i += 1

        return CountMarker(
            name = 'count_' + str(self.__count_i),
            parent = group,
            position = pos,
            refers_to = ref
        )

    @override
    def mousePressEvent(self, event: QMouseEvent, /) -> None:
        event.ignore()

    @override
    def mouseReleaseEvent(self, event: QMouseEvent, /) -> None:
        event.ignore()

    @override
    def mouseMoveEvent(self, event: QMouseEvent, /) -> None:
        event.ignore()

    @override
    def mouseDoubleClickEvent(self, event: QMouseEvent, /) -> None:
        event.ignore()

    @override
    def keyPressEvent(self, event: QKeyEvent, /) -> None:
        print(f'Got mod={event.modifiers()} key={event.key()} (vk.mod={event.nativeModifiers()} vk={event.nativeVirtualKey()}).')

        if not event.isAutoRepeat():
            match event.key():
                case Qt.Key.Key_Escape:
                    self.close()
                    event.accept()
                case _:
                    if event.modifiers() == Qt.KeyboardModifier.NoModifier and event.key() == Qt.Key.Key_Space:
                        cursor_pos = self.mapFromGlobal(QCursor.pos())
                        if self.rect().contains(cursor_pos):
                            new_marker_model = self._create_marker((cursor_pos.x(), cursor_pos.y()))
                            new_marker_view = MarkerWidget(data=new_marker_model)
                            self.__layout.addWidget(new_marker_view)
                            准备开始设计绘制事件

                        event.accept()

        event.ignore()

    @override
    def keyReleaseEvent(self, event: QKeyEvent, /) -> None:
        event.ignore()