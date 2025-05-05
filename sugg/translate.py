# sugg/translate.py
import requests
from PySide6.QtCore import QObject, QRunnable, Signal, QThreadPool, QSettings
from lg import logger


def translate_text(text: str, target_lang: str) -> str:
    """
    Call Google Translate API to translate from English to target_lang.
    """
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "en",
        "tl": target_lang,
        "dt": "t",
        "q": text,
    }
    logger.info(f'sending translation request: {params}')
    r = requests.get(url, params=params, timeout=5)
    r.raise_for_status()
    data = r.json()
    logger.info(f'result: {data}')
    return "".join(chunk[0] for chunk in data[0])


def _safe_emit(signal, *args):
    """
    Emit Qt signal safely, ignoring if the target has been deleted.
    """
    try:
        logger.info(f'emitting signal:{signal!r}')
        signal.emit(*args)
        logger.info(f'signal:{signal!r} emitted!')
    except RuntimeError:
        logger.warning("Signal source has been deleted; skipping emit.")


class Suggestor(QObject):
    clearSignal = Signal()
    addSignal   = Signal(str)


suggestor = Suggestor()


class TranslateTask(QRunnable):
    def __init__(self, text: str, target: str):
        super().__init__()
        self.text = text
        self.target = target

    def run(self):
        try:
            result = translate_text(self.text, self.target)
        except Exception as e:
            result = f"Error: {e}"  # ensure result always defined
        _safe_emit(suggestor.clearSignal)
        _safe_emit(suggestor.addSignal, result)


def translate_suggestion(msgid: str):
    """
    Launch a TranslateTask to fetch suggestions asynchronously.
    """
    settings = QSettings("POEditor", "Settings")
    target = settings.value("targetLanguage", "vi")
    task = TranslateTask(msgid, target)
    QThreadPool.globalInstance().start(task)
