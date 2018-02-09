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

// Variables
var internalQmlObject = Qt.createQmlObject('import QtQuick 2.0; QtObject { signal statusSignal(string value) }', Qt.application, 'InternalQmlObject');
var serviceUrl = 'https://visualization-dev.humanbrainproject.eu/viz/rendering-resource-manager/v1';
var connected = false;
var STATUS_NONE = 0;
var STATUS_SESSION_CREATED = 1;
var STATUS_SESSION_RUNNING = 2;
var currentStatus = STATUS_NONE;

var openSessionParams = {
    owner: 'bbpdemolauncher',
    configuration_id: ''
};

var rendererParams = {
}

function doRequest(method, url, body) {
    var oReq = new XMLHttpRequest();
    oReq.withCredentials = true;
    oReq.onreadystatechange = function() {
        if (oReq.readyState == XMLHttpRequest.DONE) {
            switch( currentStatus ) {
                case STATUS_NONE:
                currentStatus = STATUS_SESSION_CREATED;
                startRenderer();
                break;
                case STATUS_SESSION_CREATED:
                currentStatus = STATUS_NONE;
            }
        }
    }
    oReq.open(method, url, true);
    oReq.setRequestHeader('HBP', openSessionParams.configuration_id);
    var bodyStr
    if (body) {
        bodyStr = JSON.stringify(body);
        oReq.setRequestHeader('Content-Type', 'application/json');
    }
    oReq.send(bodyStr);
}

function createSession(demo) {
    openSessionParams.configuration_id=demo
    doRequest('POST', serviceUrl + '/session/',  openSessionParams  );
}

function startRenderer(){
    doRequest('PUT', serviceUrl + '/session/schedule',  rendererParams);
}

function updateStatus(){
    var oReq = new XMLHttpRequest();
    oReq.withCredentials = true;
    oReq.onreadystatechange = function() {
        if (oReq.readyState == 4 ) {
            var sig;
            try {
                sig = JSON.parse(oReq.responseText).description
            }
            catch(err) {
                sig = oReq.responseText
            }
            internalQmlObject.statusSignal(sig);
        }
    }
    oReq.open('GET', serviceUrl + '/session/status', true);
    oReq.setRequestHeader('HBP', openSessionParams.configuration_id);
    oReq.send();
}

function launch(demo) {
        createSession(demo)
    }

