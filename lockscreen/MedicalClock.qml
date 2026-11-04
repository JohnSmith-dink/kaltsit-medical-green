// SPDX-License-Identifier: MIT
import QtQuick
import org.kde.plasma.clock as PlasmaClock
import "MedicalPalette.js" as Palette

// The same optical left edge and baselines as the SDDM v6 clock. Let Plasma's
// clock handle minute changes, time zones and the first tick after resume.
Item {
    id: clock
    required property string family
    readonly property var weekdays: [qsTr("星期日"), qsTr("星期一"), qsTr("星期二"), qsTr("星期三"),
                                     qsTr("星期四"), qsTr("星期五"), qsTr("星期六")]
    height: 176
    PlasmaClock.Clock { id: source; trackSeconds: false }
    TextMetrics { id: timeInk; font: time.font; text: time.text; renderType: time.renderType }
    TextMetrics { id: dateInk; font: date.font; text: date.text; renderType: date.renderType }
    Text {
        id: time
        objectName: "medicalLockTime"
        x: -timeInk.tightBoundingRect.x
        y: 71.75 - baselineOffset - timeInk.tightBoundingRect.y
        text: Qt.formatTime(source.dateTime, "HH:mm")
        textFormat: Text.PlainText
        color: Palette.text
        font.family: clock.family
        font.pixelSize: 72
        font.weight: Font.Normal
        font.letterSpacing: -0.5
        font.features: { "tnum": 1 }
    }
    Text {
        id: date
        x: -dateInk.tightBoundingRect.x
        y: 152.25 - baselineOffset - dateInk.tightBoundingRect.y
        text: Qt.formatDate(source.dateTime, qsTr("yyyy年M月d日")) + " " + clock.weekdays[source.dateTime.getDay()]
        textFormat: Text.PlainText
        color: Palette.text
        font.family: clock.family
        font.pixelSize: 18
        font.weight: Font.Normal
    }
}
