from typing import override

from PySide6.QtCore import Property, Qt, QPoint
from PySide6.QtGui import QBrush, QContextMenuEvent, QCursor, QKeyEvent, QMouseEvent, QPainter, QPaintEvent, QPen, QPixmap, QScreen
from PySide6.QtWidgets import QApplication, QFrame, QLabel, QMainWindow, QMenu, QWidget, QGridLayout

import any_singleton.singletons as sgt

from count_anywhere import sgt_dns
from count_anywhere.libs.markers import CountMarker, Group, Marker, ReferenceMarker
from count_anywhere.libs.collections import Space


class MarkerWidget(QWidget):
    MARKER_RADIUS = 6

    def __init__(
            self,
            parent: QWidget | None = None,
            data: Marker | None = None
    ) -> None:
        super().__init__(parent)

        if data is None:
            raise ValueError('`data` must be provided.')
        self.data: Marker = data

        self.style = 'o'

        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setFixedSize(self.MARKER_RADIUS * 2 + 2, self.MARKER_RADIUS * 2 + 2)
        self.sync_from_data()

    def __del__(self) -> None:
        pass

    def sync_from_data(self) -> None:
        self.move(QPoint(self.data.x - self.MARKER_RADIUS, self.data.y - self.MARKER_RADIUS))

    @override
    def paintEvent(self, event: QPaintEvent, /) -> None:
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setPen(QPen(Qt.GlobalColor.red, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(self.rect().center(), self.MARKER_RADIUS, self.MARKER_RADIUS)
        painter.end()


# TODO: 不时向temp文件写入当前marker以免丢失，或者直接设计自动保存。

class MarkerView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.marker_space: Space = Space(2)

    def add_marker(self, marker: Marker) -> None:
        self.marker_space.add([marker.position[0], marker.position[1]], marker)
        MarkerWidget(parent=self, data=marker).show()

    def select_item_by_position(self, position: QPoint, /) -> None:
        pass

    @override
    def paintEvent(self, event: QPaintEvent, /) -> None:
        super().paintEvent(event)

    @override
    def mousePressEvent(self, event: QMouseEvent, /) -> None:
        super().mousePressEvent(event)

    @override
    def mouseDoubleClickEvent(self, event: QMouseEvent, /) -> None:
        super().mouseDoubleClickEvent(event)

    @override
    def mouseMoveEvent(self, event: QMouseEvent, /) -> None:
        super().mouseMoveEvent(event)

    @override
    def mouseReleaseEvent(self, event: QMouseEvent, /) -> None:
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event: QContextMenuEvent, /) -> None:
        super().contextMenuEvent(event)


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
        #self.setAttribute(
        #    Qt.WidgetAttribute.WA_TranslucentBackground |
        #    Qt.WidgetAttribute.WA_TransparentForMouseEvents
        #)
        self.setStyleSheet("""
            border: 1px solid #EE0000;
            border-radius: 1px;
        """)
        self.showFullScreen()

        if screen is None:
            screen = QApplication.primaryScreen()
        self.setScreen(screen)
        self.setFixedSize(screen.availableSize())

        self.__layout = QGridLayout()
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.__edit_area = QLabel()
        if picture is not None:
            self.__edit_area.setPixmap(picture)
        else:
            self.__edit_area.setStyleSheet("""
                /*background: transparent;*/
                background-color: rgba(255, 255, 255, 50%);
            """)
        self.__edit_area.setMargin(0)
        self.__edit_area.setFixedSize(self.rect().size())
        self.__layout.addWidget(self.__edit_area, 0, 0)

        self.__marker_view = MarkerView()
        self.__edit_area.setMargin(0)
        self.__edit_area.setFixedSize(self.rect().size())
        self.__marker_view.raise_()
        self.__layout.addWidget(self.__marker_view, 0, 0)

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
        super().mousePressEvent(event)

    @override
    def mouseReleaseEvent(self, event: QMouseEvent, /) -> None:
        super().mouseReleaseEvent(event)

    @override
    def mouseMoveEvent(self, event: QMouseEvent, /) -> None:
        super().mouseMoveEvent(event)

    @override
    def mouseDoubleClickEvent(self, event: QMouseEvent, /) -> None:
        super().mouseDoubleClickEvent(event)

    @override
    def keyPressEvent(self, event: QKeyEvent, /) -> None:
        print(f'Got mod={event.modifiers()} key={event.key()} (vk.mod={event.nativeModifiers()} vk={event.nativeVirtualKey()}).')

        has_held = False
        def hold() -> None:
            nonlocal has_held
            has_held = True

        if not event.isAutoRepeat():
            MODIFIERS_MASK = (
                Qt.KeyboardModifier.ControlModifier |
                Qt.KeyboardModifier.AltModifier |
                Qt.KeyboardModifier.ShiftModifier |
                Qt.KeyboardModifier.MetaModifier
            )
            modifiers = event.modifiers() & MODIFIERS_MASK
            key = event.key()

            match modifiers:
                case Qt.KeyboardModifier.NoModifier:
                    match key:
                        case Qt.Key.Key_Escape:
                            # close()
                            self.close()
                            hold()
                        case Qt.Key.Key_Space:
                            # add_marker_at_cursor()
                            cursor_pos = self.mapFromGlobal(QCursor.pos())
                            if self.rect().contains(cursor_pos):
                                new_marker_model = self._create_marker((cursor_pos.x(), cursor_pos.y()))
                                self.__marker_view.add_marker(new_marker_model)

                                hold()
                        case _:
                            pass
                case Qt.KeyboardModifier.ControlModifier:
                    match key:
                        case Qt.Key.Key_Z:
                            # undo()
                            raise NotImplementedError()
                        case _:
                            pass
                case _:
                    pass

        if has_held:
            event.accept()
        else:
            event.ignore()

    @override
    def keyReleaseEvent(self, event: QKeyEvent, /) -> None:
        super().keyReleaseEvent(event)