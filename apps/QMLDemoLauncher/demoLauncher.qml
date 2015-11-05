/* Copyright (c) 2014-2015, Human Brain Project
 *                          Pawel Podhajski <pawel.podhajski@epfl.ch>
 *
 * This file is part of RenderingResourceManager
 * <https://github.com/BlueBrain/RenderingResourceManager>
 *
 * This library is free software; you can redistribute it and/or modify it under
 * the terms of the GNU Lesser General Public License version 3.0 as published
 * by the Free Software Foundation.
 *
 * This library is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
 * details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this library; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
 */

import QtQuick 2.4
import "utils.js" as Utils
import QtQuick.Window 2.2

Item {
    function updateStatusBox(v) {
        console.log("reload " + v)
        infoText.text=v
        return v;
    }

    id: root
    objectName: "Click to launch"
    property string demoFolder: "/gpfs/bbp.cscs.ch/scratch/gss/viz/nachbaur/dev/Livre/apps/livreGUI/resources"
    Rectangle {
            width: 400
            height: 2100
            color: "lightsteelblue"
            onWindowChanged: {
            window.height = 2100;
            window.width = 400;
            window.maximumHeight = 2100;
            window.minimumHeight = 2100;
            window.maximumWidth = 400;
            window.minimumWidth = 400;
        }

        ListModel {
             ListElement {
                //name: "ISC RTneuron"
                demo: "demo_isc_rtneuron_01"
                img: "isc_rtneuron_01.png"
            }
            id: myModel
            ListElement {
                //name: "Synthesized morphologies"
                demo: "demo_brayns_01"
                img: "morphologies_01.png"}
            ListElement {
                //name: "Rat brain"
                demo: "demo_livre_01"
                img: "ratbrain_01.png"
            }
             ListElement {
               // name: "ISC Livre"
                demo: "demo_isc_livre_01"
                img: "isc_livre_01.png"
            }
            ListElement {
               // name: "ISC Neuroscheme"
                demo: "demo_isc_neuroscheme_01"
                img: "isc_neuroscheme_01.png"
            }
            
         
           

        }

        Component {
            id: myDelegate
            Rectangle {
                anchors.left: parent.left
                anchors.leftMargin: 2
                anchors.right: parent.right
                anchors.rightMargin: 2
                height: 400
                width: 400
                Image {
                    source: img
                    anchors.fill: parent
                }
                MouseArea {
                    anchors.fill: parent
                    //onPressed: {view.currentIndex = index }
                    onClicked: {
                        view.currentIndex = index
                        Utils.launch(demo)
                        timer.interval = 2000;
                        timer.repeat = true;
                        timer.start();
                    }
                }
                Text {
                    text: name
                    font.pixelSize : 25
                }
            }
        }

        ListView {
            id: view
            anchors.fill: parent
            model: myModel
            delegate: myDelegate
            highlight:
            Rectangle {
                color: "lightsteelblue"
                opacity: 0.4
                z: view.currentItem.z + 1
            }
            spacing: 5
            Component.onCompleted: {
                Utils.internalQmlObject.statusSignal.connect(updateStatusBox);
            }
        }

        Timer {
            id: timer
            onTriggered: {
                Utils.updateStatus()
            }
        }

        Rectangle {
            id: infoRect
            color: "white"
            anchors.bottom: parent.bottom
            height: 75
            width: 400
            Text {
                anchors.fill: parent
                id: infoText
                anchors.margins: 10
                text: ""
                font.pixelSize : 14
                wrapMode: "WordWrap"
            }
        }
    }
}