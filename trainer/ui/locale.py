"""Interface language: Ukrainian default, English via compiled .qm.

The translator must be installed on the QApplication *before* any widget
is built — `tr()` resolves at call time, so widgets created earlier keep
the old language. Switching language therefore takes effect on next launch;
the menu action says so honestly instead of pretending.

Persistence: `view/language` in pytrainer.ini (`uk` default). `--lang en`
on the command line overrides for one run (screenshots, checks).
"""

from __future__ import annotations

from ..paths import app_folder, resource

SETTINGS_GROUP = "view/language"
DEFAULT = "uk"
ENGLISH = "en"

_QM_NAME = "pytrainer_en.qm"


def settings_path_default():
    return app_folder() / "pytrainer.ini"


def current_language(settings=None) -> str:
    """Saved language, `uk` unless settings say `en` (or garbage)."""
    if settings is None:
        return DEFAULT
    return ENGLISH if str(settings.value(SETTINGS_GROUP, DEFAULT)) == ENGLISH else DEFAULT


def set_language(settings, lang: str) -> None:
    if settings is not None:
        settings.setValue(SETTINGS_GROUP, ENGLISH if lang == ENGLISH else DEFAULT)


def install_language(app, lang: str):
    """Installs the English translator on the app; None for Ukrainian.

    The reference is kept on the app object — a garbage-collected
    QTranslator silently stops translating.
    """
    previous = getattr(app, "_pytrainer_translator", None)
    if previous is not None:
        app.removeTranslator(previous)
        app._pytrainer_translator = None
    if lang != ENGLISH:
        return None
    from PySide6.QtCore import QTranslator

    qm = resource("i18n", _QM_NAME)
    translator = QTranslator(app)
    if qm.exists() and translator.load(str(qm)):
        app.installTranslator(translator)
        app._pytrainer_translator = translator
        return translator
    return None
