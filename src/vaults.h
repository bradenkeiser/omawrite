#pragma once

#include "router.h"

#include <QJsonObject>
#include <QList>
#include <QString>

// Joplin through its local Data API (the Web Clipper service). The token comes
// from OMAWRITE_JOPLIN_TOKEN, else the macOS Keychain item "omawrite-joplin"
// (account "joplin"), else `secret-tool lookup service omawrite-joplin`.
class JoplinClient {
public:
    bool folders(QList<Router::Folder> *out);
    QString createFolder(const QString &title, const QString &parentId);
    // Returns the id of the note with this title in the folder, or empty.
    QString findNote(const QString &folderId, const QString &title);
    bool noteExists(const QString &id);
    QString createNote(const QString &folderId, const QString &title, const QString &body);
    bool updateNote(const QString &id, const QString &folderId, const QString &title,
                    const QString &body);
    QString error() const { return m_error; }

private:
    bool request(const QByteArray &verb, const QString &path, const QJsonObject &body,
                 QJsonObject *reply, int *status = nullptr);
    QString token();

    QString m_token;
    QString m_error;
};

// An Obsidian vault is a folder of Markdown files. The vault is the
// "obsidian/vault" setting, else the open (or most recent) vault Obsidian lists.
class ObsidianVault {
public:
    QString root();
    bool folders(QList<Router::Folder> *out);
    QString createFolder(const QString &title, const QString &parentId);
    // Writes <folder>/<title>.md and returns its absolute path. Refuses to
    // replace a file other than `previousPath`, which is removed after a move.
    QString saveNote(const QString &folderId, const QString &title, const QString &body,
                     const QString &previousPath);
    QString error() const { return m_error; }

    static QString fileNameForTitle(const QString &title);

private:
    QString m_root;
    QString m_error;
};
