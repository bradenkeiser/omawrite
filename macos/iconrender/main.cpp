#include <QGuiApplication>
#include <QSvgRenderer>
#include <QImage>
#include <QPainter>
#include <QPainterPath>
// Renders an icon SVG at several sizes, clipped to the macOS icon body
// (824px rounded square inset 100px on a 1024 grid), since QtSvg ignores clipPath.
int main(int argc, char **argv) {
    QGuiApplication app(argc, argv);
    QSvgRenderer svg(QString::fromLocal8Bit(argv[1]));
    for (int i = 3; i < argc; i += 2) {
        const int size = atoi(argv[i]);
        const qreal k = size / 1024.0;
        QImage img(size, size, QImage::Format_ARGB32_Premultiplied);
        img.fill(Qt::transparent);
        QPainter p(&img);
        p.setRenderHint(QPainter::Antialiasing);
        QPainterPath body;
        body.addRoundedRect(QRectF(100 * k, 100 * k, 824 * k, 824 * k), 185 * k, 185 * k);
        p.setClipPath(body);
        svg.render(&p);
        p.end();
        img.save(QString::fromLocal8Bit(argv[2]) + "/" + argv[i + 1]);
    }
}
