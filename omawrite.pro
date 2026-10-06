QT += core gui widgets printsupport qml quick quickcontrols2 quickdialogs2 dbus network

CONFIG += c++17 release
TARGET = omawrite
TEMPLATE = app

HEADERS += \
    src/backend.h \
    src/codelexer.h \
    src/markdownhighlighter.h \
    src/router.h \
    src/systemtheme.h \
    src/vaults.h

SOURCES += \
    src/main.cpp \
    src/backend.cpp \
    src/codelexer.cpp \
    src/markdownhighlighter.cpp \
    src/router.cpp \
    src/systemtheme.cpp \
    src/vaults.cpp

RESOURCES += src/resources.qrc

macx {
    ICON = macos/omawrite.icns
    QMAKE_TARGET_BUNDLE_PREFIX = dev.omacom
}
