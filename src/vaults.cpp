#include "vaults.h"

#include <QDir>
#include <QDirIterator>
#include <QEventLoop>
#include <QFile>
#include <QFileInfo>
#include <QJsonArray>
#include <QJsonDocument>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QNetworkRequest>
#include <QProcess>
#include <QRegularExpression>
#include <QSaveFile>
#include <QSettings>
#include <QTimer>
#include <QUrlQuery>

namespace {

const char joplinBaseUrl[] = "http://localhost:41184";
const int joplinTimeoutMs = 4000;

QString commandOutput(const QString &program, const QStringList &arguments) {
    QProcess process;
    process.start(program, arguments);
    if (!process.waitForFinished(3000) || process.exitCode() != 0)
        return {};
    return QString::fromUtf8(process.readAllStandardOutput()).trimmed();
}

} // namespace

QString JoplinClient::token() {
    if (!m_token.isEmpty())
        return m_token;
    m_token = qEnvironmentVariable("OMAWRITE_JOPLIN_TOKEN");
#ifdef Q_OS_MACOS
    if (m_token.isEmpty())
        m_token = commandOutput(QStringLiteral("security"),
                                {QStringLiteral("find-generic-password"), QStringLiteral("-a"),
                                 QStringLiteral("joplin"), QStringLiteral("-s"),
                                 QStringLiteral("omawrite-joplin"), QStringLiteral("-w")});
#else
    if (m_token.isEmpty())
        m_token = commandOutput(QStringLiteral("secret-tool"),
                                {QStringLiteral("lookup"), QStringLiteral("service"),
                                 QStringLiteral("omawrite-joplin")});
#endif
    return m_token;
}

bool JoplinClient::request(const QByteArray &verb, const QString &path,
                           const QJsonObject &body, QJsonObject *reply, int *status) {
    m_error.clear();
    const QString key = token();
    if (key.isEmpty()) {
        m_error = QStringLiteral("No Joplin token (Keychain item omawrite-joplin)");
        return false;
    }

    QUrl url(QString::fromLatin1(joplinBaseUrl) + path);
    QUrlQuery query(url);
    query.addQueryItem(QStringLiteral("token"), key);
    url.setQuery(query);

    QNetworkRequest networkRequest(url);
    networkRequest.setHeader(QNetworkRequest::ContentTypeHeader,
                             QStringLiteral("application/json"));
    networkRequest.setTransferTimeout(joplinTimeoutMs);

    // A blocking call keeps saving simple; the API is local and answers in
    // milliseconds, and the transfer timeout bounds a stalled Joplin.
    QNetworkAccessManager manager;
    const QByteArray payload = body.isEmpty() ? QByteArray()
                                              : QJsonDocument(body).toJson(QJsonDocument::Compact);
    QNetworkReply *networkReply = manager.sendCustomRequest(networkRequest, verb, payload);
    QEventLoop loop;
    QObject::connect(networkReply, &QNetworkReply::finished, &loop, &QEventLoop::quit);
    loop.exec(QEventLoop::ExcludeUserInputEvents);

    const int code = networkReply->attribute(QNetworkRequest::HttpStatusCodeAttribute).toInt();
    const QByteArray data = networkReply->readAll();
    const QNetworkReply::NetworkError networkError = networkReply->error();
    networkReply->deleteLater();
    if (status)
        *status = code;

    if (code == 0) {
        m_error = QStringLiteral("Joplin isn't reachable; is it running with the Web Clipper on?");
        return false;
    }
    if (networkError != QNetworkReply::NoError || code >= 400) {
        m_error = code == 403 ? QStringLiteral("Joplin rejected the token")
                              : QStringLiteral("Joplin error %1").arg(code);
        return false;
    }
    if (reply)
        *reply = QJsonDocument::fromJson(data).object();
    return true;
}

bool JoplinClient::folders(QList<Router::Folder> *out) {
    out->clear();
    for (int page = 1;; ++page) {
        QJsonObject reply;
        if (!request("GET", QStringLiteral("/folders?fields=id,title,parent_id&limit=100&page=%1")
                                .arg(page), {}, &reply))
            return false;
        for (const QJsonValue &value : reply.value(QStringLiteral("items")).toArray()) {
            const QJsonObject folder = value.toObject();
            out->append({folder.value(QStringLiteral("id")).toString(),
                         folder.value(QStringLiteral("title")).toString(),
                         folder.value(QStringLiteral("parent_id")).toString()});
        }
        if (!reply.value(QStringLiteral("has_more")).toBool())
            return true;
    }
}

QString JoplinClient::createFolder(const QString &title, const QString &parentId) {
    QJsonObject reply;
    if (!request("POST", QStringLiteral("/folders"),
                 {{QStringLiteral("title"), title}, {QStringLiteral("parent_id"), parentId}},
                 &reply))
        return {};
    return reply.value(QStringLiteral("id")).toString();
}

QString JoplinClient::findNote(const QString &folderId, const QString &title) {
    for (int page = 1;; ++page) {
        QJsonObject reply;
        if (!request("GET", QStringLiteral("/folders/%1/notes?fields=id,title&limit=100&page=%2")
                                .arg(folderId).arg(page), {}, &reply))
            return {};
        for (const QJsonValue &value : reply.value(QStringLiteral("items")).toArray()) {
            const QJsonObject note = value.toObject();
            if (note.value(QStringLiteral("title")).toString().compare(title, Qt::CaseInsensitive) == 0)
                return note.value(QStringLiteral("id")).toString();
        }
        if (!reply.value(QStringLiteral("has_more")).toBool())
            return {};
    }
}

bool JoplinClient::noteExists(const QString &id) {
    int status = 0;
    if (request("GET", QStringLiteral("/notes/%1?fields=id").arg(id), {}, nullptr, &status))
        return true;
    if (status == 404)
        m_error.clear();
    return false;
}

QString JoplinClient::createNote(const QString &folderId, const QString &title,
                                 const QString &body) {
    QJsonObject reply;
    if (!request("POST", QStringLiteral("/notes"),
                 {{QStringLiteral("title"), title}, {QStringLiteral("body"), body},
                  {QStringLiteral("parent_id"), folderId}},
                 &reply))
        return {};
    return reply.value(QStringLiteral("id")).toString();
}

bool JoplinClient::updateNote(const QString &id, const QString &folderId, const QString &title,
                              const QString &body) {
    return request("PUT", QStringLiteral("/notes/%1").arg(id),
                   {{QStringLiteral("title"), title}, {QStringLiteral("body"), body},
                    {QStringLiteral("parent_id"), folderId}},
                   nullptr);
}

QString ObsidianVault::root() {
    if (!m_root.isEmpty())
        return m_root;

    m_root = QSettings().value(QStringLiteral("obsidian/vault")).toString();
    if (!m_root.isEmpty())
        return m_root;

#ifdef Q_OS_MACOS
    const QString config = QDir::homePath()
        + QStringLiteral("/Library/Application Support/obsidian/obsidian.json");
#else
    const QString config = QDir::homePath() + QStringLiteral("/.config/obsidian/obsidian.json");
#endif
    QFile file(config);
    if (!file.open(QIODevice::ReadOnly))
        return {};
    const QJsonObject vaults =
        QJsonDocument::fromJson(file.readAll()).object().value(QStringLiteral("vaults")).toObject();
    double newest = -1;
    for (const QJsonValue &value : vaults) {
        const QJsonObject vault = value.toObject();
        const double rank = vault.value(QStringLiteral("open")).toBool()
            ? 1e300 : vault.value(QStringLiteral("ts")).toDouble();
        if (rank > newest) {
            newest = rank;
            m_root = vault.value(QStringLiteral("path")).toString();
        }
    }
    return m_root;
}

bool ObsidianVault::folders(QList<Router::Folder> *out) {
    out->clear();
    const QString vault = root();
    if (vault.isEmpty() || !QFileInfo(vault).isDir()) {
        m_error = QStringLiteral("No Obsidian vault found (set obsidian/vault)");
        return false;
    }

    // The iterator still descends into hidden folders, so drop anything under
    // .obsidian, .trash, .git and the like here.
    const QDir base(vault);
    QDirIterator it(vault, QDir::Dirs | QDir::NoDotAndDotDot, QDirIterator::Subdirectories);
    while (it.hasNext()) {
        const QString relative = base.relativeFilePath(it.next());
        if (relative.startsWith(QLatin1Char('.')) || relative.contains(QStringLiteral("/.")))
            continue;
        const int slash = relative.lastIndexOf(QLatin1Char('/'));
        out->append({relative, relative.mid(slash + 1),
                     slash < 0 ? QString() : relative.left(slash)});
    }
    return true;
}

QString ObsidianVault::createFolder(const QString &title, const QString &parentId) {
    const QString relative = parentId.isEmpty() ? title : parentId + QLatin1Char('/') + title;
    if (!QDir(root()).mkpath(relative)) {
        m_error = QStringLiteral("Could not create folder %1").arg(relative);
        return {};
    }
    return relative;
}

QString ObsidianVault::fileNameForTitle(const QString &title) {
    static const QRegularExpression unsafeRe(QStringLiteral("[\\\\/:*?\"<>|#^\\[\\]]"));
    QString name = title;
    name.replace(unsafeRe, QStringLiteral(" "));
    name = name.simplified();
    return name + QStringLiteral(".md");
}

QString ObsidianVault::saveNote(const QString &folderId, const QString &title,
                                const QString &body, const QString &previousPath) {
    const QString path = QDir(root()).filePath(
        (folderId.isEmpty() ? QString() : folderId + QLatin1Char('/')) + fileNameForTitle(title));
    const QString cleanPrevious = previousPath.isEmpty() ? QString()
                                                         : QDir::cleanPath(previousPath);
    if (QFileInfo::exists(path) && QDir::cleanPath(path) != cleanPrevious) {
        m_error = QStringLiteral("%1 already exists; change the title")
                      .arg(fileNameForTitle(title));
        return {};
    }

    QSaveFile file(path);
    if (!file.open(QIODevice::WriteOnly | QIODevice::Text)) {
        m_error = QStringLiteral("Could not write %1").arg(path);
        return {};
    }
    file.write(body.toUtf8());
    if (!file.commit()) {
        m_error = QStringLiteral("Could not write %1").arg(path);
        return {};
    }

    if (!cleanPrevious.isEmpty() && cleanPrevious != QDir::cleanPath(path))
        QFile::remove(cleanPrevious);
    return path;
}
