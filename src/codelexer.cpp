#include "codelexer.h"

#include <QHash>
#include <QSet>
#include <QStringList>

namespace CodeLexer {

namespace {

QSet<QString> words(const char *list) {
    QSet<QString> set;
    for (const QString &word : QString::fromLatin1(list).split(QLatin1Char(' '), Qt::SkipEmptyParts))
        set.insert(word);
    return set;
}

const QSet<QString> &keywords(Language language) {
    static const QHash<Language, QSet<QString>> table{
        {Language::Shell, words("if then else elif fi for while until do done case esac in function "
                                "return local export readonly declare unset shift break continue "
                                "exit set source alias echo printf read cd test trap eval exec "
                                "sudo time select")},
        {Language::PowerShell, words("if else elseif foreach for while do until switch function "
                                     "return param begin process end try catch finally throw "
                                     "break continue exit filter in class using")},
        {Language::Python, words("False None True and as assert async await break class continue "
                                 "def del elif else except finally for from global if import in "
                                 "is lambda nonlocal not or pass raise return try while with "
                                 "yield match case self print")},
        {Language::CLike, words("auto bool break case catch char class const constexpr continue "
                                "default delete do double else enum explicit extern false float "
                                "for friend goto if inline int long namespace new nullptr operator "
                                "private protected public return short signed sizeof static "
                                "struct switch template this throw true try typedef typename "
                                "union unsigned using virtual void volatile while func package "
                                "import var type go defer chan map range fn let mut impl trait "
                                "pub use mod match self Self string interface")},
        {Language::JavaScript, words("async await break case catch class const continue default "
                                     "delete do else export extends false finally for from "
                                     "function if import in instanceof let new null of return "
                                     "static super switch this throw true try typeof undefined "
                                     "var void while yield interface type enum implements")},
        {Language::Json, words("true false null")},
        {Language::Yaml, words("true false null yes no on off")},
        {Language::Toml, words("true false")},
        {Language::Sql, words("select from where insert into values update set delete create "
                              "table drop alter add join left right inner outer on and or not "
                              "null is as order by group having limit distinct union all index "
                              "primary key foreign references in like between case when then "
                              "else end exists")},
    };
    static const QSet<QString> none;
    const auto it = table.constFind(language);
    return it == table.constEnd() ? none : *it;
}

bool hashComments(Language language) {
    return language == Language::Shell || language == Language::PowerShell
        || language == Language::Python || language == Language::Yaml
        || language == Language::Toml;
}

bool isIdentifierStart(QChar c) { return c.isLetter() || c == QLatin1Char('_'); }

bool isIdentifierPart(QChar c, Language language) {
    return c.isLetterOrNumber() || c == QLatin1Char('_')
        || (c == QLatin1Char('-') && (language == Language::Shell || language == Language::PowerShell));
}

} // namespace

Language languageForName(const QString &name) {
    static const QHash<QString, Language> names{
        {QStringLiteral("bash"), Language::Shell}, {QStringLiteral("sh"), Language::Shell},
        {QStringLiteral("zsh"), Language::Shell}, {QStringLiteral("shell"), Language::Shell},
        {QStringLiteral("console"), Language::Shell}, {QStringLiteral("fish"), Language::Shell},
        {QStringLiteral("powershell"), Language::PowerShell}, {QStringLiteral("ps1"), Language::PowerShell},
        {QStringLiteral("pwsh"), Language::PowerShell}, {QStringLiteral("ps"), Language::PowerShell},
        {QStringLiteral("python"), Language::Python}, {QStringLiteral("py"), Language::Python},
        {QStringLiteral("c"), Language::CLike}, {QStringLiteral("cpp"), Language::CLike},
        {QStringLiteral("c++"), Language::CLike}, {QStringLiteral("h"), Language::CLike},
        {QStringLiteral("java"), Language::CLike}, {QStringLiteral("go"), Language::CLike},
        {QStringLiteral("rust"), Language::CLike}, {QStringLiteral("rs"), Language::CLike},
        {QStringLiteral("cs"), Language::CLike}, {QStringLiteral("csharp"), Language::CLike},
        {QStringLiteral("swift"), Language::CLike}, {QStringLiteral("kotlin"), Language::CLike},
        {QStringLiteral("js"), Language::JavaScript}, {QStringLiteral("javascript"), Language::JavaScript},
        {QStringLiteral("ts"), Language::JavaScript}, {QStringLiteral("typescript"), Language::JavaScript},
        {QStringLiteral("jsx"), Language::JavaScript}, {QStringLiteral("tsx"), Language::JavaScript},
        {QStringLiteral("json"), Language::Json}, {QStringLiteral("jsonc"), Language::Json},
        {QStringLiteral("yaml"), Language::Yaml}, {QStringLiteral("yml"), Language::Yaml},
        {QStringLiteral("toml"), Language::Toml}, {QStringLiteral("ini"), Language::Toml},
        {QStringLiteral("conf"), Language::Toml}, {QStringLiteral("sql"), Language::Sql},
    };
    return names.value(name.trimmed().toLower(), Language::Plain);
}

QList<Token> lex(Language language, const QString &line) {
    QList<Token> tokens;
    if (language == Language::Plain)
        return tokens;

    const int n = line.length();
    int i = 0;

    // YAML/TOML keys: the leading "key:" / "key =" of a line.
    if (language == Language::Yaml || language == Language::Toml) {
        int start = 0;
        while (start < n && line.at(start).isSpace())
            ++start;
        if (start < n && line.at(start) == QLatin1Char('-') && language == Language::Yaml) {
            ++start;
            while (start < n && line.at(start).isSpace())
                ++start;
        }
        int end = start;
        while (end < n && (isIdentifierPart(line.at(end), language) || line.at(end) == QLatin1Char('.')
                           || line.at(end) == QLatin1Char('-')))
            ++end;
        int after = end;
        while (after < n && line.at(after) == QLatin1Char(' '))
            ++after;
        const QChar separator = language == Language::Yaml ? QLatin1Char(':') : QLatin1Char('=');
        if (end > start && after < n && line.at(after) == separator) {
            tokens.append({Kind::Key, start, end - start});
            i = after + 1;
        }
    }

    while (i < n) {
        const QChar c = line.at(i);

        const bool hashComment = hashComments(language) && c == QLatin1Char('#')
            && (i == 0 || line.at(i - 1).isSpace());
        const bool slashComment = (language == Language::CLike || language == Language::JavaScript
                                   || language == Language::Json)
            && c == QLatin1Char('/') && i + 1 < n && line.at(i + 1) == QLatin1Char('/');
        const bool dashComment = language == Language::Sql && c == QLatin1Char('-')
            && i + 1 < n && line.at(i + 1) == QLatin1Char('-');
        if (hashComment || slashComment || dashComment) {
            tokens.append({Kind::Comment, i, n - i});
            break;
        }

        if (c == QLatin1Char('"') || c == QLatin1Char('\'')
                || (c == QLatin1Char('`') && language == Language::JavaScript)) {
            int j = i + 1;
            while (j < n && line.at(j) != c) {
                // Single-quoted shell strings have no escapes.
                if (line.at(j) == QLatin1Char('\\')
                        && !(language == Language::Shell && c == QLatin1Char('\'')))
                    ++j;
                ++j;
            }
            const int end = qMin(n, j + 1);
            int after = end;
            while (after < n && line.at(after) == QLatin1Char(' '))
                ++after;
            const bool jsonKey = language == Language::Json && after < n
                && line.at(after) == QLatin1Char(':');
            tokens.append({jsonKey ? Kind::Key : Kind::String, i, end - i});
            i = end;
            continue;
        }

        if ((language == Language::Shell || language == Language::PowerShell)
                && c == QLatin1Char('$') && i + 1 < n) {
            int j = i + 1;
            if (line.at(j) == QLatin1Char('{')) {
                while (j < n && line.at(j) != QLatin1Char('}'))
                    ++j;
                j = qMin(n, j + 1);
            } else if (line.at(j).isDigit() || QStringLiteral("@#?*!$-").contains(line.at(j))) {
                ++j;
            } else {
                while (j < n && (line.at(j).isLetterOrNumber() || line.at(j) == QLatin1Char('_')
                                 || (language == Language::PowerShell && line.at(j) == QLatin1Char(':'))))
                    ++j;
            }
            if (j > i + 1) {
                tokens.append({Kind::Variable, i, j - i});
                i = j;
                continue;
            }
        }

        if (c.isDigit() && (i == 0 || !isIdentifierPart(line.at(i - 1), language))) {
            int j = i;
            while (j < n && (line.at(j).isLetterOrNumber() || line.at(j) == QLatin1Char('.')
                             || line.at(j) == QLatin1Char('_')))
                ++j;
            tokens.append({Kind::Number, i, j - i});
            i = j;
            continue;
        }

        if (isIdentifierStart(c)) {
            int j = i;
            while (j < n && isIdentifierPart(line.at(j), language))
                ++j;
            QString word = line.mid(i, j - i);
            if (language == Language::Sql || language == Language::PowerShell)
                word = word.toLower();
            // Shell assignments (name=value) and option-like words aren't keywords.
            const bool assignment = language == Language::Shell && j < n && line.at(j) == QLatin1Char('=');
            if (!assignment && keywords(language).contains(word))
                tokens.append({Kind::Keyword, i, j - i});
            else if (assignment)
                tokens.append({Kind::Variable, i, j - i});
            i = j;
            continue;
        }

        ++i;
    }
    return tokens;
}

} // namespace CodeLexer
