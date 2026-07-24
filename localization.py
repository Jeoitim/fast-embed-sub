"""Qt translation loading and presentation helpers.

Application translations live in ``i18n/*.ts`` and are compiled to ``.qm``
files for runtime use.  This module deliberately contains no locale-specific
translation dictionary.
"""

from __future__ import annotations

import html
import os
import sys
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QLocale, QObject, QTranslator, Signal


SUPPORTED_LANGUAGES = {"en": "en_US", "zh": "zh_CN"}


def application_dir() -> Path:
    """Return the source or frozen application directory."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


class TranslationManager(QObject):
    """Own the active QTranslator and switch application language at runtime."""

    language_changed = Signal(str)

    def __init__(self, app, language: str = "zh"):
        super().__init__(app)
        self._app = app
        self._translator: QTranslator | None = None
        self._language = ""
        if not self.set_language(language):
            self.set_language("en")

    @property
    def language(self) -> str:
        return self._language

    def set_language(self, language: str) -> bool:
        language = language if language in SUPPORTED_LANGUAGES else "zh"
        if language == self._language:
            return True

        translator = None
        if language != "en":
            translator = QTranslator(self)
            qm_path = application_dir() / "i18n" / f"fast_embed_sub_{SUPPORTED_LANGUAGES[language]}.qm"
            if not translator.load(os.fspath(qm_path)):
                translator.deleteLater()
                return False

        self._language = language
        old_translator = self._translator
        self._translator = translator
        if old_translator is not None:
            self._app.removeTranslator(old_translator)
            old_translator.deleteLater()
        if translator is not None:
            self._app.installTranslator(translator)

        QLocale.setDefault(QLocale(SUPPORTED_LANGUAGES[language]))
        self.language_changed.emit(language)
        return True


def translate_log_event(event, **param_overrides) -> str:
    """Translate a structured engine log event at presentation time."""
    messages = {
        "warn_no_ffmpeg": QCoreApplication.translate(
            "TranscodeLog",
            "<b>[Warning]</b> ffmpeg.exe was not detected in the components directory or PATH. Encoding tasks will not work.",
        ),
        "sys_vs_registered": QCoreApplication.translate(
            "TranscodeLog",
            "[System] Registered the portable VapourSynth Python runtime mapping.",
        ),
        "queue_task_added": QCoreApplication.translate(
            "TranscodeLog", "<b>[Queue]</b> Task added: {video} ({preset})"
        ),
        "task_start": QCoreApplication.translate(
            "TranscodeLog", "<b>[{video}]</b> Encoding started..."
        ),
        "task_cmd": QCoreApplication.translate("TranscodeLog", "<b>[{video}]</b> Command: {cmd}"),
        "sys_vs_loaded": QCoreApplication.translate(
            "TranscodeLog", "[System] Loaded portable VapourSynth runtime: {dir}"
        ),
        "queue_finished": QCoreApplication.translate(
            "TranscodeLog", "<b>[Queue]</b> All tasks completed"
        ),
        "sys_cleaned_temp": QCoreApplication.translate(
            "TranscodeLog", "[System] Removed temporary Vpy file: {filename}"
        ),
        "queue_cleared": QCoreApplication.translate(
            "TranscodeLog", "<b>[Queue]</b> Task queue cleared"
        ),
        "task_deleted_unfinished": QCoreApplication.translate(
            "TranscodeLog", "<b>[{video}]</b> Removed incomplete file: {filename}"
        ),
        "task_delete_failed": QCoreApplication.translate(
            "TranscodeLog", "<b>[{video}]</b> Failed to remove file: {error}"
        ),
        "task_cancelled": QCoreApplication.translate(
            "TranscodeLog", "<b>[{video}]</b> Task cancelled"
        ),
        "task_success": QCoreApplication.translate(
            "TranscodeLog", "<b>[{video}]</b> Encoding completed"
        ),
        "task_failed": QCoreApplication.translate(
            "TranscodeLog", "<b>[{video}]</b> Encoding failed (exit code: {exit_code})"
        ),
    }

    if not event.translatable:
        return html.escape(event.message_key)

    message = messages.get(event.message_key, event.message_key)
    params = {**event.params, **param_overrides}
    safe_params = {key: html.escape(str(value)) for key, value in params.items()}
    try:
        return message.format(**safe_params)
    except (KeyError, ValueError):
        return message


def translate_engine_error(error) -> str:
    """Translate a structured EngineError without coupling the engine to Qt text."""
    messages = {
        "preset_vpy_syntax_error": QCoreApplication.translate(
            "EngineError",
            "The compiled Vpy script for preset [{preset}] contains a syntax error.\n"
            "Error: {error} (line {line})\n"
            "Code: {code}",
        ),
        "preset_not_found": QCoreApplication.translate("EngineError", "Preset not found: {preset}"),
        "unsupported_placeholder": QCoreApplication.translate(
            "EngineError", "Unsupported placeholder: {placeholder}"
        ),
    }
    message_key = getattr(error, "message_key", None)
    if message_key not in messages:
        return str(error)
    params = getattr(error, "params", {})
    try:
        return messages[message_key].format(**params)
    except (KeyError, ValueError):
        return messages[message_key]
