from dataclasses import dataclass


@dataclass
class BuildConfig:
    PKGUTILS_VERSION = 10000
    PKGUTILS_VERSION_STR = "1.0.0"
    REQUEST_VERSION = 1
    REQUEST_VERSION_STR = "V1"
    REQUEST_ENCRYPTED = False
