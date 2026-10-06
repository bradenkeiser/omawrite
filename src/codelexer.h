#pragma once

#include <QList>
#include <QString>

// A deliberately small, line-at-a-time lexer for coloring fenced code blocks.
// It knows comments, strings, numbers, keywords and shell-style variables for
// a handful of common languages; anything else renders as plain code.
namespace CodeLexer {

enum class Language { Plain, Shell, PowerShell, Python, CLike, JavaScript, Json, Yaml, Toml, Sql };

enum class Kind { Keyword, String, Comment, Number, Variable, Key };

struct Token {
    Kind kind;
    int start;
    int length;
};

// Maps a fence info string ("bash", "py", "c++", ...) to a language.
Language languageForName(const QString &name);

QList<Token> lex(Language language, const QString &line);

} // namespace CodeLexer
