from pathlib import Path
from typing import Optional
import configparser
import os

class ConfigLoader:
    def __init__(self) -> None:
        self._config: configparser.ConfigParser = configparser.ConfigParser()
        self._config_path: Optional[Path] = self._find_ini()
        if self._config_path:
            self._config.read(self._config_path)



    # ── private helpers ─────────────────────────────────────────
    def _find_ini(self) -> Optional[Path]:
        """Return first existing config.ini path, or None."""
        candidates = [
            Path(os.getenv("CONFIG_INI_PATH", "")),
            Path(__file__).resolve().parent.parent / "config.ini",            # src/config.ini
            Path(__file__).resolve().parent.parent / "config" / "config.ini",# src/config/config.ini ← your actual file
            Path(__file__).resolve().parent / "config.ini",                  # src/services/config.ini
            Path(__file__).resolve().parent / "config" / "config.ini",
        ]
        for p in candidates:
            if p and p.is_file():
                return p
        return None


    # ── public API ──────────────────────────────────────────────
    def get(
        self,
        section: str,
        key: str,
        env: Optional[str] = None,
        default: Optional[str] = None,
    ) -> Optional[str]:
        for sec in self._config.sections():
            if sec.lower() == section.lower() and key in self._config[sec]:
                return self._config[sec][key]
        return os.getenv(env or "", default)


# instantiate a shared loader so every import re-uses it
config_loader = ConfigLoader()
