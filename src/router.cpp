#include "router.h"

#include <QRegularExpression>

namespace Router {

namespace {

// Can `abbreviation` be spelled by taking a non-empty prefix of some words, in
// order? With `anchored`, the first word taken must be the first word.
bool wordPrefixMatch(const QString &abbreviation, const QStringList &words,
                     int word, bool anchored) {
    if (abbreviation.isEmpty())
        return true;
    for (int i = word; i < words.size(); ++i) {
        const QString &candidate = words.at(i);
        const int limit = qMin(candidate.length(), abbreviation.length());
        for (int length = limit; length > 0; --length) {
            if (candidate.left(length) == abbreviation.left(length)
                    && wordPrefixMatch(abbreviation.mid(length), words, i + 1, false))
                return true;
        }
        if (anchored)
            return false;
    }
    return false;
}

bool isSubsequence(const QString &abbreviation, const QString &name) {
    int at = 0;
    for (const QChar c : name) {
        if (at < abbreviation.length() && abbreviation.at(at) == c)
            ++at;
    }
    return at == abbreviation.length();
}

} // namespace

bool Resolution::createsFolders() const {
    for (const Step &step : steps) {
        if (step.id.isEmpty())
            return true;
    }
    return false;
}

QStringList Resolution::titles() const {
    QStringList result;
    for (const Step &step : steps)
        result.append(step.title);
    return result;
}

QString appName(App app) {
    switch (app) {
    case App::Joplin:
        return QStringLiteral("Joplin");
    case App::Obsidian:
        return QStringLiteral("Obsidian");
    case App::None:
        break;
    }
    return {};
}

Header parseHeader(const QString &firstLine) {
    static const QRegularExpression headerRe(
        QStringLiteral("^\\s*(jop|obs)(?:\\s*[-/]\\s*|\\s+|$)(.*)$"),
        QRegularExpression::CaseInsensitiveOption);
    const QRegularExpressionMatch match = headerRe.match(firstLine);
    if (!match.hasMatch())
        return {};

    Header header;
    header.app = match.captured(1).toLower() == QStringLiteral("jop") ? App::Joplin
                                                                      : App::Obsidian;
    QString rest = match.captured(2).trimmed();

    static const QRegularExpression titleRe(QStringLiteral("\\[([^\\]]*)\\]\\s*$"));
    const QRegularExpressionMatch title = titleRe.match(rest);
    if (title.hasMatch()) {
        header.title = title.captured(1).trimmed();
        rest = rest.left(title.capturedStart(0));
    }

    static const QRegularExpression separatorRe(QStringLiteral("[\\s/-]+"));
    header.parts = rest.split(separatorRe, Qt::SkipEmptyParts);
    return header;
}

QString bodyWithoutHeader(const QString &text) {
    const int newline = text.indexOf(QLatin1Char('\n'));
    if (newline < 0)
        return {};
    QString body = text.mid(newline + 1);
    if (body.startsWith(QLatin1Char('\n')))
        body.remove(0, 1);
    return body;
}

QString noteTitle(const Header &header, const QString &body) {
    if (!header.title.isEmpty())
        return header.title;
    static const QRegularExpression headingRe(QStringLiteral("^#{1,6}\\s+(.+?)\\s*#*\\s*$"),
                                              QRegularExpression::MultilineOption);
    const QRegularExpressionMatch heading = headingRe.match(body);
    return heading.hasMatch() ? heading.captured(1) : QString();
}

int matchTier(const QString &abbreviation, const QString &name) {
    const QString a = abbreviation.toLower();
    const QString n = name.toLower();
    if (a.isEmpty())
        return 0;
    if (a == n)
        return 1;
    if (n.startsWith(a))
        return 2;
    static const QRegularExpression wordRe(QStringLiteral("[\\s_.-]+"));
    const QStringList words = n.split(wordRe, Qt::SkipEmptyParts);
    if (wordPrefixMatch(a, words, 0, true))
        return 3;
    if (wordPrefixMatch(a, words, 0, false))
        return 4;
    if (isSubsequence(a, n))
        return 5;
    return 0;
}

Resolution resolve(const QStringList &parts, const QList<Folder> &folders,
                   const QHash<QString, QString> &aliases) {
    Resolution resolution;
    QString parentId;
    bool creating = false;
    QString where = QStringLiteral("the top level");

    for (const QString &part : parts) {
        QList<Folder> children;
        if (!creating) {
            for (const Folder &folder : folders) {
                if (folder.parentId == parentId)
                    children.append(folder);
            }
        }

        if (part.startsWith(QLatin1Char('+'))) {
            const QString title = part.mid(1);
            if (title.isEmpty()) {
                resolution.error = QStringLiteral("Write a name after +");
                return resolution;
            }
            Step step{QString(), title};
            for (const Folder &child : children) {
                if (child.title.compare(title, Qt::CaseInsensitive) == 0)
                    step = {child.id, child.title};
            }
            creating = step.id.isEmpty();
            resolution.steps.append(step);
            parentId = step.id;
            where = step.title;
            continue;
        }

        if (creating) {
            resolution.error = QStringLiteral("'%1' is inside a new folder; mark it +%1 to create it")
                                   .arg(part);
            return resolution;
        }

        const QString alias = aliases.value(part.toLower());
        int bestTier = 0;
        QList<Folder> best;
        for (const Folder &child : children) {
            const int tier = alias.isEmpty() ? matchTier(part, child.title)
                : (child.title.compare(alias, Qt::CaseInsensitive) == 0 ? 1 : 0);
            if (tier == 0)
                continue;
            if (bestTier == 0 || tier < bestTier) {
                bestTier = tier;
                best = {child};
            } else if (tier == bestTier) {
                best.append(child);
            }
        }

        if (best.isEmpty()) {
            resolution.error = QStringLiteral("Nothing matches '%1' in %2 (write +%1 to create it)")
                                   .arg(part, where);
            return resolution;
        }
        if (best.size() > 1) {
            QStringList names;
            for (const Folder &folder : best)
                names.append(folder.title);
            if (names.size() > 3)
                names = names.mid(0, 3) << QStringLiteral("%1 more").arg(best.size() - 3);
            resolution.error = QStringLiteral("'%1' could be %2; type more")
                                   .arg(part, names.join(QStringLiteral(" or ")));
            return resolution;
        }

        resolution.steps.append({best.first().id, best.first().title});
        parentId = best.first().id;
        where = best.first().title;
    }

    resolution.ok = true;
    return resolution;
}

} // namespace Router
