#include <QtTest>
#include <QFont>
#include <QQmlComponent>
#include <QQmlContext>
#include <QQmlEngine>
#include <QQuickStyle>

#include "backend.h"
#include "markdownhighlighter.h"
#include "router.h"
#include "codelexer.h"

class OmawriteTest : public QObject {
    Q_OBJECT

private slots:
    void initTestCase() {
        QVERIFY(m_settingsDirectory.isValid());
        QQuickStyle::setStyle(QStringLiteral("Material"));
        QSettings::setDefaultFormat(QSettings::IniFormat);
        QSettings::setPath(QSettings::IniFormat, QSettings::UserScope,
                           m_settingsDirectory.path());
    }

    void countsWords() {
        QCOMPARE(Backend::countWords(QStringLiteral("one two-three don't 42")), 4);
        QCOMPARE(Backend::countWords(QStringLiteral("你好 世界")), 2);
        QCOMPARE(Backend::countWords(QString()), 0);
    }

    void normalizesLinks() {
        QCOMPARE(Backend::normalizedLinkUrl(QStringLiteral("www.example.com/path")),
                 QStringLiteral("https://www.example.com/path"));
        QCOMPARE(Backend::normalizedLinkUrl(QStringLiteral("mailto:writer@example.com")),
                 QStringLiteral("mailto:writer@example.com"));
        QVERIFY(Backend::normalizedLinkUrl(QStringLiteral("example.com")).isEmpty());
        QVERIFY(Backend::normalizedLinkUrl(QStringLiteral("file:///tmp/private")).isEmpty());
    }

    void suggestsSafeNames() {
        QCOMPARE(Backend::suggestedFileName(QStringLiteral("My first draft\nBody")),
                 QStringLiteral("My first draft.md"));
        QCOMPARE(Backend::suggestedFileName(QStringLiteral("A/B")), QStringLiteral("A-B.md"));
        QCOMPARE(Backend::suggestedFileName(QString()), QStringLiteral("Untitled.md"));
        QCOMPARE(Backend::suggestedFileName(QStringLiteral("Already.md")),
                 QStringLiteral("Already.md"));
    }

    void keepsNotoFromCrowdingTheFontList() {
        const QStringList fonts = Backend::selectableFontFamilies({
            QStringLiteral("Noto Sans Devanagari"), QStringLiteral("Liberation Serif"),
            QStringLiteral("Noto Serif"), QStringLiteral("Noto Sans Tamil UI"),
            QStringLiteral("adwaita Sans"), QStringLiteral("IBM Plex Mono"),
            QStringLiteral("Noto Sans"), QStringLiteral("Noto Sans Mono"),
            QStringLiteral("Liberation Serif"), QStringLiteral("Monospace"),
            QStringLiteral("Standard Symbols PS"), QStringLiteral("D050000L"),
            QStringLiteral("Noto Color Emoji"), QStringLiteral("Nimbus Sans [UKWN]"),
            QStringLiteral("Nimbus Sans [URW ]")});
        QCOMPARE(fonts, QStringList({QStringLiteral("IBM Plex Mono"),
                                     QStringLiteral("adwaita Sans"),
                                     QStringLiteral("Liberation Serif"),
                                     QStringLiteral("Nimbus Sans"),
                                     QStringLiteral("Noto Sans"),
                                     QStringLiteral("Noto Sans Mono"),
                                     QStringLiteral("Noto Serif")}));
    }

    void remembersEditorFont() {
        const QString installed = Backend().availableFonts().value(1);
        QVERIFY(!installed.isEmpty());

        {
            Backend backend;
            QCOMPARE(backend.editorFont(), Backend::defaultEditorFont());
            QSignalSpy fontSpy(&backend, &Backend::editorFontChanged);
            backend.setEditorFont(installed);
            QCOMPARE(fontSpy.count(), 1);
        }

        QCOMPARE(Backend().editorFont(), installed);

        // A remembered font that has since been uninstalled falls back.
        QSettings().setValue(QStringLiteral("editor/font"), QStringLiteral("No Such Font"));
        QCOMPARE(Backend().editorFont(), Backend::defaultEditorFont());
        QSettings().remove(QStringLiteral("editor/font"));
    }

    void findsInlineMarkdownRanges() {
        const auto markup = MarkdownHighlighter::inlineMarkup(
            QStringLiteral("**bold** and *italic* and [site](https://example.com)"));
        QCOMPARE(markup.size(), 3);
        QCOMPARE(markup.at(0).content.start, 2);
        QCOMPARE(markup.at(0).content.length, 4);
        QCOMPARE(markup.at(2).content.length, 4);
        QCOMPARE(markup.at(2).markers[0].length, 1);
    }

    void leavesIntrawordUnderscoresLiteral() {
        QVERIFY(MarkdownHighlighter::inlineMarkup(QStringLiteral(
            "sudo cp ./$n-userdata_customizations.sh && dcv_host/userdata_x.sh")).isEmpty());
        QVERIFY(MarkdownHighlighter::inlineMarkup(QStringLiteral("a_b_c and x__y__z")).isEmpty());
        QVERIFY(MarkdownHighlighter::inlineMarkup(QStringLiteral("2 * 3 * 4")).isEmpty());

        const auto markup = MarkdownHighlighter::inlineMarkup(
            QStringLiteral("_italic_ and __bold__ and snake_case"));
        QCOMPARE(markup.size(), 2);
        QCOMPARE(markup.at(0).kind, MarkdownHighlighter::InlineKind::Bold);
        QCOMPARE(markup.at(1).kind, MarkdownHighlighter::InlineKind::Italic);
        QCOMPARE(markup.at(1).content.start, 1);
    }

    void ignoresMarkupInsideInlineCode() {
        QVERIFY(MarkdownHighlighter::inlineMarkup(QStringLiteral("run `*glob* _x_` now")).isEmpty());
        QCOMPARE(MarkdownHighlighter::inlineMarkup(QStringLiteral("`code` and *em*")).size(), 1);
    }

    void tracksFencedCodeBlocks() {
        QTextDocument document;
        MarkdownHighlighter highlighter(&document);
        document.setPlainText(QStringLiteral(
            "intro *em*\n```bash\nmv a_b.sh *x*\n```\nafter *em*"));
        highlighter.rehighlight();
        QList<int> states;
        for (QTextBlock block = document.begin(); block.isValid(); block = block.next())
            states.append(block.userState());
        QCOMPARE(states.size(), 5);
        QCOMPARE(states.at(0), 0);
        QVERIFY(MarkdownHighlighter::isCodeBlockState(states.at(1)));
        QCOMPARE(states.at(2), states.at(1));
        QCOMPARE(states.at(3), 0);
        QCOMPARE(states.at(4), 0);
    }

    static QList<Router::Folder> joplinTree() {
        // Mirrors the real notebook tree the router was designed against.
        const auto f = [](const char *id, const char *parent) {
            const QString path = QString::fromLatin1(id);
            return Router::Folder{path, path.section(QLatin1Char('/'), -1),
                                  QString::fromLatin1(parent)};
        };
        return {f("homelab", ""), f("homelab/elec_eng", "homelab"),
                f("homelab/homelab_stuff", "homelab"), f("homelab/truenas", "homelab"),
                f("homelab/network_monitoring", "homelab"), f("homelab/networking", "homelab"),
                f("homelab/networking/truenas", "homelab/networking"),
                f("homelab/reinstall_reconfigure_meshagent", "homelab"),
                f("homelab/home_assistant", "homelab"), f("homelab/iot", "homelab"),
                f("musings", ""), f("musings/polished", "musings"),
                f("musings/scribblings", "musings"), f("cheffing", ""), f("games", ""),
                f("tunestolearn", ""), f("AWS_IDEA", ""), f("Claude_AWS_IDEA", ""),
                f("aws", "")};
    }

    void parsesRoutingHeaders() {
        Router::Header header = Router::parseHeader(QStringLiteral("jop - hl - eng"));
        QCOMPARE(header.app, Router::App::Joplin);
        QCOMPARE(header.parts, (QStringList{QStringLiteral("hl"), QStringLiteral("eng")}));
        QVERIFY(header.title.isEmpty());

        header = Router::parseHeader(QStringLiteral("obs - aidea - [VPC peering notes]"));
        QCOMPARE(header.app, Router::App::Obsidian);
        QCOMPARE(header.parts, QStringList{QStringLiteral("aidea")});
        QCOMPARE(header.title, QStringLiteral("VPC peering notes"));

        QCOMPARE(Router::parseHeader(QStringLiteral("JOP mus/pol")).parts.size(), 2);
        QCOMPARE(Router::parseHeader(QStringLiteral("# jop notes")).app, Router::App::None);
        QCOMPARE(Router::parseHeader(QStringLiteral("jopling along")).app, Router::App::None);
        QCOMPARE(Router::parseHeader(QStringLiteral("obstacles")).app, Router::App::None);

        QCOMPARE(Router::bodyWithoutHeader(QStringLiteral("jop - mus\n\n# Title\nbody")),
                 QStringLiteral("# Title\nbody"));
        QCOMPARE(Router::noteTitle({}, QStringLiteral("text\n## My heading ##\n")),
                 QStringLiteral("My heading"));
    }

    void resolvesAbbreviatedFolders() {
        const auto titles = [](const QString &header) {
            const Router::Resolution resolution =
                Router::resolve(Router::parseHeader(header).parts, joplinTree());
            return resolution.ok ? resolution.titles().join(QLatin1Char('/'))
                                 : QStringLiteral("ERROR ") + resolution.error;
        };
        QCOMPARE(titles(QStringLiteral("jop - hl - eng")), QStringLiteral("homelab/elec_eng"));
        QCOMPARE(titles(QStringLiteral("jop - mus - pol")), QStringLiteral("musings/polished"));
        QCOMPARE(titles(QStringLiteral("obs - aidea")), QStringLiteral("AWS_IDEA"));
        QCOMPARE(titles(QStringLiteral("obs - aws")), QStringLiteral("aws"));
        QCOMPARE(titles(QStringLiteral("jop - hl - networking - tn")),
                 QStringLiteral("homelab/networking/truenas"));
        QVERIFY(titles(QStringLiteral("jop - hl - tn")).startsWith(QStringLiteral("ERROR")));
        QVERIFY(titles(QStringLiteral("jop - hl - net")).contains(QStringLiteral("type more")));
        QVERIFY(titles(QStringLiteral("jop - hl - zzz")).contains(QStringLiteral("+zzz")));

        const Router::Resolution created = Router::resolve(
            {QStringLiteral("hl"), QStringLiteral("+eng2"), QStringLiteral("+deep")}, joplinTree());
        QVERIFY(created.ok);
        QVERIFY(created.createsFolders());
        QVERIFY(created.steps.at(1).id.isEmpty());
        QVERIFY(!Router::resolve({QStringLiteral("+new"), QStringLiteral("x")}, joplinTree()).ok);

        // An existing folder named with + is reused, not duplicated.
        QCOMPARE(Router::resolve({QStringLiteral("+musings")}, joplinTree()).steps.at(0).id,
                 QStringLiteral("musings"));

        const QHash<QString, QString> aliases{{QStringLiteral("songs"), QStringLiteral("tunestolearn")}};
        QCOMPARE(Router::resolve({QStringLiteral("songs")}, joplinTree(), aliases).titles(),
                 QStringList{QStringLiteral("tunestolearn")});
    }

    void takesTrailingPartAsTitle() {
        const auto route = [](const QString &line) {
            const Router::Header header = Router::parseHeader(line);
            const Router::Resolution r =
                Router::resolve(header.parts, joplinTree(), {}, header.title.isEmpty());
            return r.ok ? r.titles().join(QLatin1Char('/')) + QStringLiteral(" | ") + r.title
                        : QStringLiteral("ERROR ") + r.error;
        };
        QCOMPARE(route(QStringLiteral("obs - aidea - vscode implementation")),
                 QStringLiteral("AWS_IDEA | vscode implementation"));
        QCOMPARE(route(QStringLiteral("jop - mus - pol - Chapter one")),
                 QStringLiteral("musings/polished | Chapter one"));
        QCOMPARE(route(QStringLiteral("jop - hl - zzz")), QStringLiteral("homelab | zzz"));
        QCOMPARE(route(QStringLiteral("jop hl eng")), QStringLiteral("homelab/elec_eng | "));
        // A bracketed title means every other part must be a folder.
        QVERIFY(route(QStringLiteral("jop - hl - zzz - [T]")).startsWith(QStringLiteral("ERROR")));
        // Ambiguity is still refused rather than read as a title.
        QVERIFY(route(QStringLiteral("jop - hl - net")).startsWith(QStringLiteral("ERROR")));
    }

    void lexesFencedCodeLanguages() {
        using namespace CodeLexer;
        const auto kinds = [](Language language, const QString &line) {
            QStringList out;
            for (const Token &token : lex(language, line))
                out.append(QString::number(int(token.kind)) + QLatin1Char(':')
                           + line.mid(token.start, token.length));
            return out.join(QLatin1Char(' '));
        };
        QCOMPARE(languageForName(QStringLiteral("bash")), Language::Shell);
        QCOMPARE(languageForName(QStringLiteral("nope")), Language::Plain);
        QCOMPARE(kinds(Language::Shell, QStringLiteral("check=\"my_name\" # note")),
                 QStringLiteral("4:check 1:\"my_name\" 2:# note"));
        QCOMPARE(kinds(Language::Shell, QStringLiteral("echo $check ${HOME} 42")),
                 QStringLiteral("0:echo 4:$check 4:${HOME} 3:42"));
        QCOMPARE(kinds(Language::Shell, QStringLiteral("for n in a_b; do")),
                 QStringLiteral("0:for 0:in 0:do"));
        QCOMPARE(kinds(Language::Json, QStringLiteral("{\"a\": true, \"b\": \"x\"}")),
                 QStringLiteral("5:\"a\" 0:true 5:\"b\" 1:\"x\""));
        QCOMPARE(kinds(Language::Yaml, QStringLiteral("  name: web # c")),
                 QStringLiteral("5:name 2:# c"));
        QCOMPARE(kinds(Language::Python, QStringLiteral("def f(x): return 'a#b'")),
                 QStringLiteral("0:def 0:return 1:'a#b'"));
    }

    void loadsCurrentOmarchyTheme() {
        QTemporaryDir homeDirectory;
        QVERIFY(homeDirectory.isValid());

        const QByteArray originalHome = qgetenv("HOME");
        struct HomeRestorer {
            QByteArray value;
            ~HomeRestorer() { qputenv("HOME", value); }
        } restoreHome{originalHome};
        QVERIFY(qputenv("HOME", homeDirectory.path().toUtf8()));

        const QString themeDirectory = homeDirectory.path()
            + QStringLiteral("/.local/state/omarchy/current/theme");
        QVERIFY(QDir().mkpath(themeDirectory));

        QFile colorsFile(themeDirectory + QStringLiteral("/colors.toml"));
        QVERIFY(colorsFile.open(QIODevice::WriteOnly | QIODevice::Text));
        const QByteArray palette(
            "mode = \"light\"\n"
            "accent = \"#112233\"\n"
            "selection = \"#445566\"\n"
            "background = \"#fefefe\"\n"
            "foreground = \"#101010\"\n");
        QCOMPARE(colorsFile.write(palette), qint64(palette.size()));
        colorsFile.close();

        Backend backend;
        QCOMPARE(backend.themeBackground(), QStringLiteral("#fefefe"));
        QCOMPARE(backend.themeForeground(), QStringLiteral("#101010"));
        QCOMPARE(backend.themeAccent(), QStringLiteral("#112233"));
        QCOMPARE(backend.themeSelection(), QStringLiteral("#445566"));
        QVERIFY(!backend.darkMode());
    }

    void ignoresFileWatcherEventsForSavedContents() {
        QTemporaryDir directory;
        QVERIFY(directory.isValid());

        const QString path = directory.filePath(QStringLiteral("first-save.md"));
        Backend backend;
        QSignalSpy externalChangeSpy(&backend, &Backend::externalChangeDetected);

        backend.saveAs(QUrl::fromLocalFile(path));
        QVERIFY(QFileInfo::exists(path));

        QFile sameContents(path);
        QVERIFY(sameContents.open(QIODevice::WriteOnly | QIODevice::Truncate));
        sameContents.close();
        QTest::qWait(100);
        QCOMPARE(externalChangeSpy.count(), 0);

        QFile changedContents(path);
        QVERIFY(changedContents.open(QIODevice::WriteOnly | QIODevice::Truncate));
        QCOMPARE(changedContents.write("changed elsewhere"), qint64(17));
        changedContents.close();
        QTRY_COMPARE(externalChangeSpy.count(), 1);
    }

    void keepsCursorAndSelectionStableAcrossInsertions() {
        const QString mutationsPath = QFINDTESTDATA("../src/EditorMutations.js");
        QVERIFY(!mutationsPath.isEmpty());

        QQmlEngine engine;
        QQmlComponent component(&engine);
        const QByteArray harness = R"QML(
            import QtQuick
            import "EditorMutations.js" as EditorMutations

            TextEdit {
                property string insertionText
                property int insertionCursor
                property string wrappedText
                property int wrappedSelectionStart
                property int wrappedSelectionEnd

                Component.onCompleted: {
                    text = "alpha omega";
                    cursorPosition = 5;
                    EditorMutations.replaceRange(this, 5, 5, "one\r\ntwo");
                    insertionText = text;
                    insertionCursor = cursorPosition;

                    text = "alpha beta omega";
                    select(6, 10);
                    EditorMutations.replaceRange(this, selectionStart, selectionEnd,
                                                 "**beta**", 2, 6);
                    wrappedText = text;
                    wrappedSelectionStart = selectionStart;
                    wrappedSelectionEnd = selectionEnd;
                }
            }
        )QML";
        const QUrl harnessUrl = QUrl::fromLocalFile(
            QFileInfo(mutationsPath).absolutePath() + QStringLiteral("/MutationHarness.qml"));
        component.setData(harness, harnessUrl);
        QVERIFY2(component.isReady(), qPrintable(component.errorString()));
        QScopedPointer<QObject> editor(component.create());
        QVERIFY2(editor, qPrintable(component.errorString()));

        QCOMPARE(editor->property("insertionText").toString(),
                 QStringLiteral("alphaone\ntwo omega"));
        QCOMPARE(editor->property("insertionCursor").toInt(), 12);
        QCOMPARE(editor->property("wrappedText").toString(),
                 QStringLiteral("alpha **beta** omega"));
        QCOMPARE(editor->property("wrappedSelectionStart").toInt(), 8);
        QCOMPARE(editor->property("wrappedSelectionEnd").toInt(), 12);
    }

    void savesAndOpensFromFooterButtons() {
        const QString mainQmlPath = QFINDTESTDATA("../src/Main.qml");
        QVERIFY(!mainQmlPath.isEmpty());

        Backend backend;
        QQmlEngine engine;
        engine.rootContext()->setContextProperty(QStringLiteral("backend"), &backend);
        QQmlComponent component(&engine, QUrl::fromLocalFile(mainQmlPath));
        QVERIFY2(component.isReady(), qPrintable(component.errorString()));
        QScopedPointer<QObject> window(component.create());
        QVERIFY2(window, qPrintable(component.errorString()));

        QVERIFY(window->findChild<QObject *>(QStringLiteral("sourceEditor")));
        QVERIFY(!window->findChild<QObject *>(QStringLiteral("renderedPreview")));
        QVERIFY(!window->findChild<QObject *>(QStringLiteral("modeToggle")));

        QObject *saveButton = window->findChild<QObject *>(QStringLiteral("saveButton"));
        QObject *openButton = window->findChild<QObject *>(QStringLiteral("openButton"));
        QVERIFY(saveButton);
        QVERIFY(openButton);

        QSignalSpy saveDialogSpy(&backend, &Backend::saveDialogRequested);
        QVERIFY(QMetaObject::invokeMethod(saveButton, "clicked"));
        QCOMPARE(saveDialogSpy.count(), 1);

        QSignalSpy openDialogSpy(&backend, &Backend::openDialogRequested);
        QVERIFY(QMetaObject::invokeMethod(openButton, "clicked"));
        QCOMPARE(openDialogSpy.count(), 1);
    }

    void scalesTextWithDesktopTextSize() {
        const QString mainQmlPath = QFINDTESTDATA("../src/Main.qml");
        QVERIFY(!mainQmlPath.isEmpty());

        Backend backend;
        QQmlEngine engine;
        engine.rootContext()->setContextProperty(QStringLiteral("backend"), &backend);
        QQmlComponent component(&engine, QUrl::fromLocalFile(mainQmlPath));
        QVERIFY2(component.isReady(), qPrintable(component.errorString()));
        QScopedPointer<QObject> window(component.create());
        QVERIFY2(window, qPrintable(component.errorString()));

        QObject *editor = window->findChild<QObject *>(QStringLiteral("sourceEditor"));
        QVERIFY(editor);
        QCOMPARE(editor->property("font").value<QFont>().pixelSize(), 20);

        // `omarchy display text size 16` sets the GNOME factor to 16/12.
        backend.setTextScale(16.0 / 12.0);
        QCOMPARE(window->property("editorFontPixelSize").toInt(), 27);
        QCOMPARE(editor->property("font").value<QFont>().pixelSize(), 27);

        backend.setTextScale(9.0 / 12.0);
        QCOMPARE(window->property("editorFontPixelSize").toInt(), 15);
        QCOMPARE(editor->property("font").value<QFont>().pixelSize(), 15);
    }

    void remembersLastSaveDirectory() {
        QTemporaryDir saveDirectory;
        QVERIFY(saveDirectory.isValid());

        const QString savedPath = saveDirectory.filePath(QStringLiteral("first.md"));
        Backend savedDocument;
        savedDocument.saveAs(QUrl::fromLocalFile(savedPath));

        Backend nextDocument;
        QSignalSpy saveDialogSpy(&nextDocument, &Backend::saveDialogRequested);
        nextDocument.saveAsDialog();
        QCOMPARE(saveDialogSpy.count(), 1);

        const QUrl suggestedUrl = saveDialogSpy.takeFirst().constFirst().toUrl();
        QCOMPARE(QFileInfo(suggestedUrl.toLocalFile()).absolutePath(),
                 saveDirectory.path());
        QCOMPARE(QFileInfo(suggestedUrl.toLocalFile()).fileName(),
                 QStringLiteral("Untitled.md"));

        QSettings().setValue(QStringLiteral("file/lastSaveDirectory"),
                             saveDirectory.filePath(QStringLiteral("missing")));
        Backend fallbackDocument;
        QSignalSpy fallbackDialogSpy(&fallbackDocument, &Backend::saveDialogRequested);
        fallbackDocument.saveAsDialog();
        const QUrl fallbackUrl = fallbackDialogSpy.takeFirst().constFirst().toUrl();
        QCOMPARE(QFileInfo(fallbackUrl.toLocalFile()).absolutePath(), QDir::homePath());
    }

private:
    QTemporaryDir m_settingsDirectory;
};

QTEST_MAIN(OmawriteTest)
#include "tst_omawrite.moc"
