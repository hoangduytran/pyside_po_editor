# main_utils/main_button_enum.py

from enum import Enum

class ButtonEnum(Enum):
    EXPLORER       = ("\U0001F4C2", "Explorer")
    SEARCH         = ("\U0001F50D", "Search")
    SOURCE_CONTROL = ("\U0001F500", "Source Control")
    RUN            = ("\u25B6", "Run")
    EXTENSIONS     = ("\U0001F4E6", "Extensions")

    @property
    def icon(self):
        return self.value[0]

    @property
    def tooltip(self):
        return self.value[1]
