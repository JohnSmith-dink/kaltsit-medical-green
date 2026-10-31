// SPDX-FileCopyrightText: 2026 Xinyan
// SPDX-License-Identifier: MIT
// Test-only: reveal the unmodified native greeter UI in a private compositor.
#include <QCoreApplication>
#include <QFileInfo>
#include <QFile>
#include <QGuiApplication>
#include <QQuickItem>
#include <QQuickWindow>
#include <QTimer>
#include <QWindow>

static bool privatePreview()
{
    const auto root = qEnvironmentVariable("KALTSIT_TEST_ROOT");
    const auto args = QCoreApplication::arguments();
    return !root.isEmpty()
        && qEnvironmentVariable("HOME") == root + "/home"
        && qEnvironmentVariable("XDG_RUNTIME_DIR") == root + "/runtime"
        && qEnvironmentVariable("WAYLAND_DISPLAY") == "kaltsit-test"
        && args.contains("--testing") && !args.isEmpty()
        && args.first().contains("kscreenlocker_greet");
}

static void installPreviewWakeup()
{
    QMetaObject::invokeMethod(qApp, [] {
        if (!privatePreview()) return;
        auto timer = new QTimer(qApp);
        timer->setInterval(100);
        QObject::connect(timer, &QTimer::timeout, timer, [timer] {
            if (!privatePreview()) { timer->stop(); return; }
            const auto marker = qEnvironmentVariable("KALTSIT_TEST_ROOT") + "/show-unlock";
            if (!QFileInfo::exists(marker)) return;
            const auto reveal = [](auto &&self, QQuickItem *item) -> bool {
                if (!item) return false;
                if (item->metaObject()->indexOfProperty("uiVisible") >= 0
                    && item->metaObject()->indexOfProperty("seenPositionChange") >= 0) {
                    return item->setProperty("uiVisible", true) && item->property("uiVisible").toBool();
                }
                for (auto child : item->childItems()) if (self(self, child)) return true;
                return false;
            };
            for (auto window : QGuiApplication::allWindows()) {
                auto quick = qobject_cast<QQuickWindow *>(window);
                if (quick && reveal(reveal, quick->contentItem())) {
                    timer->stop();
                    QFile shown(qEnvironmentVariable("KALTSIT_TEST_ROOT") + "/unlock-shown");
                    shown.open(QIODevice::WriteOnly);
                    return;
                }
            }
        });
        timer->start();
    }, Qt::QueuedConnection);
}
Q_COREAPP_STARTUP_FUNCTION(installPreviewWakeup)
