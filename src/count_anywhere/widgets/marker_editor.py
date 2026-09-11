from __future__ import annotations
from dataclasses import dataclass
import math
from typing import override

from PySide6.QtCore import (
    QPoint,
    Qt,
    Signal
)
from PySide6.QtGui import (
    QBrush,
    QContextMenuEvent,
    QColor,
    QCursor,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPen,
    QPixmap,
    QScreen
)
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QLabel,
    QMenu,
    QSizePolicy,
    QWidget
)

import any_singleton.singletons as sgt

from count_anywhere import sgt_dns
from count_anywhere.libs.collections import Space
from count_anywhere.libs.markers import (
    CountMarker, Group, Marker, ReferenceMarker
)


# UI Framework:
# MarkerEditor provides window and surrounding functions.
# MarkerView is used to contain the Marker/MarkerWidget and render them.
# MarkerWidget is a view of one Marker.


@dataclass
class MarkerStyle:
    radius: int
    thickness: float

    @property
    def side_length(self) -> float:
        return (self.radius + self.thickness) * 2


class MarkerWidget(QWidget):
    def __init__(
            self,
            parent: QWidget | None = None,
            data: Marker | None = None,
            marker_style: MarkerStyle | None = None
    ) -> None:
        super().__init__(parent)

        if data is None:
            raise ValueError('`data` must be provided.')
        self._data: Marker = data

        if marker_style is None:
            self.__marker_style: MarkerStyle = MarkerStyle(
                radius=6,
                thickness=2.0
            )
        else:
            self.__marker_style: MarkerStyle = marker_style

        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self._update()

    def sync_from_data(self) -> None:
        self.move(QPoint(
            self._data.x - self.__marker_style.radius,
            self._data.y - self.__marker_style.radius
        ))

    def _update(self) -> None:
        self.sync_from_data()
        l = int(math.ceil(self.__marker_style.side_length))
        self.setFixedSize(l, l)
        self.update()

    @property
    def marker_style(self) -> MarkerStyle:
        return self.__marker_style

    @marker_style.setter
    def marker_style(self, value: MarkerStyle) -> None:
        self.__marker_style = value

    @override
    def paintEvent(self, event: QPaintEvent, /) -> None:
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setPen(QPen(Qt.GlobalColor.red, self.__marker_style.thickness))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(
            self.rect().center(), self.__marker_style.radius, self.__marker_style.radius
        )
        painter.end()


# TODO: 不时向temp文件写入当前marker以免丢失，或者直接设计自动保存。

class MarkerView(QWidget):
    marker_clicked = Signal(QPoint)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._data: Space = Space(2)
        self.__widgets: dict[int, MarkerWidget] = {}

        self.__cursor_pos: QPoint = QPoint(-1, -1)
        self.__preview_marker: MarkerWidget | None = None
        self.__preview_marker.marker_style = MarkerStyle(
            radius=6,
            thickness=2.0
        )
        self.__preview_removing: bool = False

        self.setMouseTracking(True)  # ?

    #def __len__(self) -> int:
    #    return len(self.__widgets)

    def add_marker(self, marker: Marker) -> int:
        marker_id = self._data.add(
            [marker.position[0], marker.position[1]], marker
        )

        widget = MarkerWidget(
            parent=self,
            data=marker,
            marker_style=MarkerStyle(
                radius=self.__preview_marker.marker_style.radius,
                thickness=self.__preview_marker.marker_style.thickness
            )
        )
        widget.show()

        self.__widgets[marker_id] = widget
        return marker_id

    @staticmethod
    def __normalize_position(position: Marker.Position | QPoint) -> tuple[int, int]:
        if isinstance(position, QPoint):
            return position.x(), position.y()
        return position

    def move_marker(self, marker_id: int, new_position: Marker.Position | QPoint) -> None:
        x, y = MarkerView.__normalize_position(new_position)

        raise NotImplementedError()  # TODO: Implement it.

    def remove_marker(self, marker_id: int) -> None:
        widget = self.__widgets.pop(marker_id, None)
        if widget is not None:
            self._data.remove(marker_id, [widget._data.x, widget._data.y])  # TODO: 确保所有（坐标）变动都被及时更正，以免无法索引。
            widget.deleteLater()

    def find_nearest_marker(self, position: Marker.Position | QPoint, tolerance: float, /) -> tuple[int, Marker] | None:
        x, y = MarkerView.__normalize_position(position)

        boundary = [
            x - tolerance, y - tolerance,
            x + tolerance, y + tolerance
        ]

        results = self._data.nearest(boundary, num_results=1)
        results = list(results)
        if len(results) == 0:
            return None

        result = results[0]
        return result.object.id, result.object

    def _update(self) -> None:
        l = (self.__preview_style.radius + self.__preview_style.thickness) * 2
        l = int(math.ceil(l))
        self.setFixedSize(l, l)

        for mid, w in self.__widgets.items():
            w._update()

    def update_preview(self, position: QPoint) -> None:
        """
        Update the preview marker.
        """
        HEREEEEEEEEEEEEE
        self.__cursor_pos = position
        self.__preview_removing = self.find_marker_at(position, self.__preview_radius + 2) is not None
        self.update()

    @override
    def paintEvent(self, event: QPaintEvent, /) -> None:
        super().paintEvent(event)

        position = self.__cursor_pos
        if position.x() < 0:
            return

        painter = QPainter(self)
        if self.__preview_removing:
            painter.setPen(QPen(QColor(255, 0, 0, 200), 2))
            painter.setBrush(QColor(255, 0, 0, 90))
        else:
            painter.setPen(QPen(QColor(0, 120, 255, 180), 2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(position, self.__preview_radius, self.__preview_radius)
        painter.end()

    @override
    def mouseMoveEvent(self, event: QMouseEvent, /) -> None:
        super().mouseMoveEvent(event)
        self.update_preview(event.position().toPoint())

    @override
    def mousePressEvent(self, event: QMouseEvent, /) -> None:
        super().mousePressEvent(event)

        if event.button() == Qt.MouseButton.LeftButton:
            self.marker_clicked.emit(event.position().toPoint())
            event.accept()


class MarkerEditor(QWidget):
    def __init__(
            self,
            parent: QWidget | None = None,
            screen: QScreen | None = None,
            picture: QPixmap | None = None
    ) -> None:
        self.__cfg = sgt._get_singleton(sgt_dns.CONFIG)

        super().__init__(parent)

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
        self.__history: list[int] = []

        window_flag = (
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint
        )
        if not self.__cfg['debug']:
            window_flag |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlag(window_flag)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet("""
            border: 1px solid #EE0000;
            border-radius: 1px;
        """)

        if screen is None:
            screen = QApplication.primaryScreen()
        self.setScreen(screen)
        self.setGeometry(screen.availableGeometry())

        self.__layout = QGridLayout()
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setSpacing(0)
        self.__layout.setAlignment(Qt.AlignmentFlag.AlignTop)


        self.__edit_area = QLabel()
        if picture is not None:
            self.__edit_area.setPixmap(picture)
        else:
            self.__edit_area.setStyleSheet("""
                background-color: rgba(255, 255, 255, 50%);
            """)
        self.__edit_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.__layout.addWidget(self.__edit_area, 0, 0)

        self.__marker_view = MarkerView()
        self.__marker_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.__marker_view.marker_clicked.connect(self._on_marker_view_clicked)
        self.__layout.addWidget(self.__marker_view, 0, 0)
        self.__marker_view.raise_()

        self.setLayout(self.__layout)

        # TODO: count label 因为某种原因会开始不刷新
        self.__count_label = QLabel(self)
        self.__count_label.setStyleSheet("""
            background-color: rgba(0, 0, 0, 80%);
            color: white;
            font-size: 20px;
            padding: 4px 8px;
        """)
        self.__count_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.__count_label.move(8, 8)
        self.__count_label.raise_()
        self.update_count()

        self.show()
        self.activateWindow()
        self.setFocus()

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

    def _add_marker_at(self, pos: QPoint) -> None:
        marker_id = self.__marker_view.add_marker(self._create_marker((pos.x(), pos.y())))
        self.__history.append(marker_id)
        self.update_count()

    def _remove_marker(self, marker_id: int) -> None:
        self.__marker_view.remove_marker(marker_id)
        if marker_id in self.__history:
            self.__history.remove(marker_id)
        self.update_count()

    def toggle_marker_at(self, pos: QPoint) -> None:
        found = self.__marker_view.find_marker_at(pos, self.__marker_view.preview_radius + 2)
        if found is None:
            self._add_marker_at(pos)
        else:
            self._remove_marker(found[1])

    def undo(self) -> None:
        if not self.__history:
            return
        marker_id = self.__history.pop()
        self.__marker_view.remove_marker(marker_id)
        self.update_count()

    def update_count(self) -> None:
        self.__count_label.setText(str(len(self.__marker_view)))

    def _on_marker_view_clicked(self, pos: QPoint) -> None:
        self.toggle_marker_at(pos)

    @override
    def keyPressEvent(self, event: QKeyEvent, /) -> None:
        if self.__cfg['debug']:
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
                            pos = self.__marker_view.mapFromGlobal(QCursor.pos())
                            if self.__marker_view.rect().contains(pos):
                                self.toggle_marker_at(pos)
                            hold()
                        case _:
                            pass
                case Qt.KeyboardModifier.ControlModifier:
                    match key:
                        case Qt.Key.Key_Z:
                            # undo()
                            self.undo()
                            hold()
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
