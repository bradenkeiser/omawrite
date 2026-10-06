#pragma once

#include <QRegularExpression>
#include <QSyntaxHighlighter>
#include <QTextCharFormat>

#include "codelexer.h"

class MarkdownHighlighter : public QSyntaxHighlighter {
    Q_OBJECT

public:
    explicit MarkdownHighlighter(QTextDocument *document);

    void setDarkMode(bool darkMode);
    void setColors(const QString &background, const QString &foreground, const QString &accent);
    void setSearch(const QString &query, int currentMatchStart);
    void refreshFont();

    struct Span {
        int start;
        int length;
    };

    enum class InlineKind { Bold, Italic, Link };

    // Block states at or above CodeBlockState mark lines inside (or opening) a
    // ``` / ~~~ code block, where no markdown is styled or hidden. The offset
    // from CodeBlockState is the block's CodeLexer::Language.
    static constexpr int CodeBlockState = 1;
    static bool isCodeBlockState(int state) { return state >= CodeBlockState; }

    struct InlineMarkup {
        InlineKind kind;
        Span content;
        Span markers[2];
    };

    // Single source of truth for inline markdown spans: the highlighter uses it
    // to style content and hide markers, and the editor uses it (via
    // Backend::hiddenRangesAt) to skip the caret over the hidden markers.
    static QList<InlineMarkup> inlineMarkup(const QString &text);

protected:
    void highlightBlock(const QString &text) override;

private:
    void rebuildFormats();
    bool highlightCodeFence(const QString &text);
    void highlightMarkers(const QString &text);
    void highlightInline(const QString &text);
    void highlightSearch(const QString &text);

    bool m_darkMode = true;
    QString m_customBackground;
    QString m_customForeground;
    QString m_customAccent;
    QTextCharFormat m_markerFormat;
    QTextCharFormat m_hiddenMarkerFormat;
    QTextCharFormat m_headingFormat;
    QTextCharFormat m_boldFormat;
    QTextCharFormat m_italicFormat;
    QTextCharFormat m_codeFormat;
    QTextCharFormat m_codeTokenFormats[6]; // indexed by CodeLexer::Kind
    QTextCharFormat m_quoteFormat;
    QTextCharFormat m_linkFormat;
    QString m_searchQuery;
    int m_currentMatchStart = -1;
    QTextCharFormat m_searchFormat;
    QTextCharFormat m_currentSearchFormat;
};
