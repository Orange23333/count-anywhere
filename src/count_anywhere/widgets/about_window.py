from typing import Callable

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from count_anywhere.libs.data_bindings import bind_translated_text
from count_anywhere.libs.i18n import Translator

class AboutWindow(QWidget):
    def __init__(
            self,
            version: str,
            tr: Translator,
            on_closed_handler: Callable[[QWidget], None] | None = None,
            parent = None
    ) -> None:
        super().__init__(parent)

        self.__version = version
        self.__tr = tr
        self.__on_closed_handler = on_closed_handler

        self.__data_binding_removers = []

        self.__data_binding_removers.append(
            bind_translated_text(
                self.__tr,
                'about',
                self,
                lambda w, t: w.setWindowTitle(t)
            )
        )
        self.setFixedSize(480, 270)

        self.__layout = QVBoxLayout()
        self.__layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.__title = QLabel('app.name')
        self.__data_binding_removers.append(
            bind_translated_text(
                self.__tr,
                'app.name',
                self.__title,
                lambda w, t: w.setText(t)
            )
        )
        self.__title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.__title.setFixedSize(QSize(self.width(), 48))
        self.__title.setStyleSheet('font-size: 45px; font-weight: bold;')
        self.__title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.__layout.addWidget(self.__title)

        self.__version = QLabel('version_with_value')
        self.__data_binding_removers.append(
            bind_translated_text(
                self.__tr,
                'version_with_value',
                self.__version,
                lambda w, t: w.setText(t),
                version = version
            )
        )
        self.__version.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.__version.setFixedSize(QSize(self.width(), 24))
        self.__version.setStyleSheet('font-size: 18px;')
        self.__version.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.__layout.addWidget(self.__version)

        self.__authors = QLabel('authors_with_value')
        class Authors:
            def __init__(self, tr: Translator) -> None:
                self.__tr = tr

            def __str__(self) -> str:
                return self.__tr('app.authors')
        self.__data_binding_removers.append(
            bind_translated_text(
                self.__tr,
                'authors_with_value',
                self.__authors,
                lambda w, t: w.setText(t),
                authors = Authors(self.__tr)
            )
        )
        self.__authors.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.__authors.setStyleSheet('font-size: 18px;')
        self.__authors.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.__layout.addWidget(self.__authors)

        self.__references = None  # Reversed field.

        self.setLayout(self.__layout)

    def __del__(self) -> None:
        for remover in self.__data_binding_removers:
            remover()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.__on_closed_handler is not None:
            self.__on_closed_handler(self)
