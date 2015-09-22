/* Copyright (c) 2014-2015, Human Brain Project
 *                          Cyrille Favreau <cyrille.favreau@epfl.ch>
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

'use strict';

function init() {
    document.getElementById('btnRender').addEventListener("click", refreshMainFrame, false);
    document.getElementById('btnSnapshot').addEventListener("click", renderSnapshot, false);
    document.getElementById('renderer').addEventListener("change", function (event) {
        populateParams(event.target);
    }, false);
}

function refreshMainFrame() {
    console.log("refreshMainFrame");
    var frame = document.getElementById('mainFrame');
    document.getElementById('mainFrame').style.display = "inherit"
    frame.contentWindow.location.reload(true)
}

function renderSnapshot() {
    var frame = document.getElementById('mainFrame').contentWindow.document;
    var img = frame.getElementById('renderedImage').src;
    window.open(img, 'snapshot');
}

function populateParams(sel) {
    var value = sel.options[sel.selectedIndex].value;
    document.getElementById('datasource').value = "";
    document.getElementById('datasourcetype').value = 'unknown';
    switch (value) {
    case "brayns":
        document.getElementById('params').value = '';
        document.getElementById('ambientocclusion').disabled = false;
        document.getElementById('shading').disabled = false;
        document.getElementById('softshadows').disabled = false;
        document.getElementById('environment').value = "";
        break;
    case "rtneuron":
        document.getElementById('params').value = "--no-cuda --target MiniColumn_2 --idle-AA 1";
        document.getElementById('ambientocclusion').disabled = true;
        document.getElementById('shading').disabled = true;
        document.getElementById('softshadows').disabled = true;
        document.getElementById('environment').value = "";
        break;
    case "livre":
        document.getElementById('params').value = "";
        document.getElementById('ambientocclusion').disabled = true;
        document.getElementById('shading').disabled = true;
        document.getElementById('softshadows').disabled = true;
        document.getElementById('environment').value = "";
        break;
    default:
        document.getElementById('params').value = "";
        document.getElementById('ambientocclusion').disabled = true;
        document.getElementById('shading').disabled = true;
        document.getElementById('softshadows').disabled = true;
        document.getElementById('environment').value = "";
        break;
    }
};

init();