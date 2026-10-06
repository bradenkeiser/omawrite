#pragma once

#include <QHash>
#include <QList>
#include <QString>
#include <QStringList>

// Routes a document to a Joplin notebook or an Obsidian folder from a header on
// its first line, e.g. "jop - mus - pol" or "obs - aidea - [VPC notes]".
namespace Router {

enum class App { None, Joplin, Obsidian };

struct Header {
    App app = App::None;
    QStringList parts; // abbreviated folder path, outermost first; "+name" creates
                       // (split on - or /, else on spaces when neither is used)
    QString title;     // from a trailing [bracketed title], may be empty
};

struct Folder {
    QString id;       // Joplin folder id, or vault-relative path for Obsidian
    QString title;
    QString parentId; // empty for top-level folders
};

struct Step {
    QString id; // empty when the folder must be created
    QString title;
};

struct Resolution {
    bool ok = false;
    QString error;
    QList<Step> steps;
    QString title; // a trailing part that was taken as the note title
    bool createsFolders() const;
    QStringList titles() const;
};

QString appName(App app);

// Parses the first line of the document. Anything that is not a header yields
// App::None, so ordinary documents are untouched.
Header parseHeader(const QString &firstLine);

// The document text with the header line (and one blank line after it) removed.
QString bodyWithoutHeader(const QString &text);

// Title from the header, else the first "# heading" of the body, else empty.
QString noteTitle(const Header &header, const QString &body);

// 0 means no match; lower is a better match.
int matchTier(const QString &abbreviation, const QString &name);

// Resolves each part against the children of the previous one. Aliases map an
// abbreviation (lowercase) to an exact folder title. With `lastMayBeTitle`, a
// final part containing a space or matching no folder becomes the title.
Resolution resolve(const QStringList &parts, const QList<Folder> &folders,
                   const QHash<QString, QString> &aliases = {}, bool lastMayBeTitle = false);

} // namespace Router
