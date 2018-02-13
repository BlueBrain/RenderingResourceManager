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

/* global console, THREE, Detector */
'use strict';

var serviceUrl = 'http://bbpcd015.epfl.ch/viz/rendering-resource-manager/v1';

// constants
var SESSION_STATUS_STOPPED = 0;
var SESSION_STATUS_SCHEDULED = 1;
var SESSION_STATUS_STARTING = 2;
var SESSION_STATUS_RUNNING = 3;
var SESSION_STATUS_STOPPING = 4;

// Variables
var secondsBeforeStartSession = 1; // sec
var vocabularyRetrieved = 0;
var sessionStatus = SESSION_STATUS_STOPPED;
var firstImageRetrieved = false;
var rendering = false;
var container;
var camera, controls;
var cameraMatrix = new THREE.Matrix4();
var positionChangeCounter = 0;
var renderedImage = document.getElementById('renderedImage');
var currentCameraPos;
var error;
var openSessionParams = {
    owner: 'bbpvizuser',
    configuration_id: parent.document.getElementById('renderer').value
};

/*
 * rest 'client'
 */
function doRequest(method, url, callback, body) {
    var oReq = new XMLHttpRequest();
    var bodyStr;
    oReq.onload = callback;
    oReq.withCredentials = true;
    oReq.open(method, url, true);
    if (body) {
        oReq.setRequestHeader('Content-Type', 'application/json');
        bodyStr = JSON.stringify(body);
    }
    oReq.send(bodyStr);
    return oReq.response
}

function getImage() {
    if (sessionStatus === SESSION_STATUS_RUNNING) {
        doRequest('GET', serviceUrl + '/session/IMAGEJPEG', function (event) {
            if (event.target.status === 200) {
                var jsonObject = JSON.parse(event.target.responseText);
                renderedImage.src = "data:image/jpg;base64," + jsonObject["data"];
                var frame = parent.document.getElementById('mainFrame');
                renderedImage.height = frame.clientHeight * 0.95;
                renderedImage.width = frame.clientHeight * 16 / 9 * 0.95;
                firstImageRetrieved = true;
            } else {
                var sessionStatusControl = parent.document.getElementById('sessionstatus');
                sessionStatusControl.innerHTML = event.target.responseText;
            }
        });
    }
}

var statusQuery = setInterval(function () {
    doRequest('GET', serviceUrl + '/session/status', function (event) {
        var sessionStatusControl = parent.document.getElementById('sessionstatus');
        sessionStatusControl.innerHTML = event.target.responseText;
        if (event.target.status === 200) {
            var obj = JSON.parse(event.target.responseText);
            sessionStatusControl.innerHTML = obj.description;
            sessionStatus = obj.code
            if (obj.code === SESSION_STATUS_RUNNING) { // Rendering resource is running
                var continuousRendering = parent.document.getElementById('continuousrendering').checked;
                if (!firstImageRetrieved || continuousRendering) {
                    positionChangeCounter = 0;
                    //getImage();
                    doRequest('GET', serviceUrl + '/session/vocabulary', function (event) {
                        if (event.target.status === 200) {
                            parent.document.getElementById('btnSnapshot').disabled = false;
                            // Application is now available.
                            // Request for image streaming
                            doRequest('GET', serviceUrl + '/session/imagefeed', function (event) {
                                var obj = JSON.parse(event.target.responseText);
                                console.log('Image streaming from ' + obj.uri)
                                renderedImage.src = 'http://' + obj.uri
                                firstImageRetrieved = true;
                            });
                        }
                    });

                    if (openSessionParams.configuration_id === 'brayns') {
                        doRequest('GET', serviceUrl + '/session/CAMERA', function (event) {
                            var res = JSON.parse(event.target.responseText);
                            camera.position.x = res.matrix[0];
                            camera.position.y = res.matrix[1];
                            camera.position.z = res.matrix[2];
                        });
                    }
                }
            }
        }
    });

    doRequest('GET', serviceUrl + '/session/log', function (event) {
        if (event.target.status === 200) {
            var span = parent.document.getElementById('renderingresourceidlog');
            var response = event.target.responseText;
            response = response.replace(/[\n\r]/g, '<br/>');
            span.innerHTML = response;
            span.className = 'show';
        }
    });
}, 2000);

/*
 * functions to create/destroy a session
 */
function sessionHandler(action, callback) {
    doRequest(action === 'delete' ? 'DELETE' : 'POST', serviceUrl + '/session/', callback, openSessionParams);
}

function createSession(callback) {
    sessionHandler('create', callback);
}

function deleteSession(callback) {
    renderedImage.src = ''
    sessionHandler('delete', callback);
}

/*
 * starts the renderer once the session is opened.
 */
function startRenderer(event) {
    console.log("startRenderer");
    if (event.target.status === 201) {
        var parameters = parent.document.getElementById('params').value;
        var dataSource = parent.document.getElementById('datasource').value;
        var dataSourceType = parent.document.getElementById('datasourcetype').value;
        var environment = parent.document.getElementById('environment').value;

        // Rendering options
        if (openSessionParams.configuration_id === 'brayns') {
            parameters += ' --renderer exobj';
            if (parent.document.getElementById('ambientocclusion').checked) {
                parameters += ' --ambient-occlusion';
            }
            if (!parent.document.getElementById('shading').checked) {
                parameters += ' --no-shading';
            }
            if (parent.document.getElementById('softshadows').checked) {
                parameters += ' --shadows --soft-shadows';
            }
            if (parent.document.getElementById('electronshading').checked) {
                parameters += ' --electron-shading';
            }
            if (parent.document.getElementById('productionquality').checked) {
                parameters += ' --quality 50';
            } else {
                parameters += ' --quality 5';
            }
        }

        // Data source
        if (openSessionParams.configuration_id === 'livre') {
            parameters += ' --volume ' + dataSourceType + '://' + dataSource;
        }
        if (openSessionParams.configuration_id === 'rtneuron') {
            parameters += ' -b ' + dataSource;
        }
        if (openSessionParams.configuration_id === 'brayns') {
            parameters += ' --' + dataSourceType + '-folder ' + dataSource;
        }
        
        console.log(parameters);

        // Image size
        var snapshotResolution = parent.document.getElementById('snapshotresolution').value;
        var frame = parent.document.getElementById('mainFrame');
        var width = 800;
        var height = 400;
        if (snapshotResolution === '1k') {
            width = 1920;
            height = 1080;
        }
        else if (snapshotResolution === '2k') {
            width = 1920;
            height = 1080;
        } else if (snapshotResolution === '4k') {
            width = 3840;
            height = 2160;
        } else if (snapshotResolution === 'dw') {
            width = 7680;
            height = 3240;
        }

        if (openSessionParams.configuration_id === 'brayns') {
            if (parameters.indexOf('buffer-height') === -1) {
                parameters += ' --buffer-height ' + height;
            }
            if (parameters.indexOf('buffer-width') === -1) {
                parameters += ' --buffer-width ' + width;
            }
        } else {
            if (environment.indexOf('EQ_WINDOW_IATTR_HINT_HEIGHT') === -1) {
                if (environment !== "") environment += ',';
                environment += 'EQ_WINDOW_IATTR_HINT_HEIGHT=' + height;
            }
            if (environment.indexOf('EQ_WINDOW_IATTR_HINT_WIDTH') === -1) {
                if (environment !== "") environment += ',';
                environment += 'EQ_WINDOW_IATTR_HINT_WIDTH=' + width;
            }
        }

        var rendererParams = {
            params: parameters,
            environment: environment,
        };

        doRequest('PUT', serviceUrl + '/session/schedule', function (eventSchedule) {
            if (eventSchedule.target.status === 200) {
                setTimeout(init, secondsBeforeStartSession * 1000);
            } else {
                var sessionStatusControl = parent.document.getElementById('sessionstatus');
                sessionStatusControl.innerHTML = eventSchedule.target.responseText;
            }
        }, rendererParams);
    } else if (event.target.status === 409) {
        // assume the renderer is already started
        setTimeout(init, secondsBeforeStartSession * 1000);
    } else {
        error = event.target.responseText;
        var span = parent.document.getElementById('errorMessage');
        span.innerHTML = error;
        span.className = 'show';
    }
}

/*
 * init three.js controls and camera.
 */
function init() {
    camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 1, 1000);
    camera.position.z = 2;

    cameraMatrix = {
        matrix: [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, -1, 1]
    };
    controls = new THREE.TrackballControls(camera);
    controls.rotateSpeed = 1.0;
    controls.zoomSpeed = 1.2;
    controls.panSpeed = 0.8;
    controls.noZoom = false;
    controls.noPan = false;
    controls.staticMoving = true;
    controls.dynamicDampingFactor = 0.3;
    controls.keys = [65, 83, 68];
    controls.addEventListener('change', render);

    container = document.getElementById('container');
    window.addEventListener('resize', onWindowResize, false);
    render();
    animate();
}

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    controls.handleResize();
    render();
}

function animate() {
    requestAnimationFrame(animate);
    controls.update();
}

Number.prototype.toFixedDown = function (digits) {
    var n = this - Math.pow(10, -digits) / 2;
    n += n / Math.pow(2, 53);
    return n.toFixed(digits);
};


/*
 *positon change callback.
 */
function render() {
    if (camera.position.z != 0.0) {
        if (openSessionParams.configuration_id == "brayns") {
            cameraMatrix.matrix[0] = -camera.position.x;
            cameraMatrix.matrix[1] = camera.position.y;
            cameraMatrix.matrix[2] = -camera.position.z;
        } else {
            // Rotation
            var scaling = 1;
            if (openSessionParams.configuration_id === "rtneuron") {
                scaling = 1000;
            }
            var alpha = -Math.asin(camera.position.x / camera.position.z);
            var beta = Math.asin(camera.position.y / camera.position.z);

            if (Math.abs(alpha) <= 1.0 && Math.abs(beta) <= 1.0) {
                alpha *= 4.0;
                beta *= 4.0;
                var m = new THREE.Matrix4();
                var m1 = new THREE.Matrix4();
                var m2 = new THREE.Matrix4();

                m1.makeRotationX(beta);
                m2.makeRotationY(alpha);
                m.multiplyMatrices(m1, m2);

                cameraMatrix.matrix[0] = m.elements[0];
                cameraMatrix.matrix[1] = m.elements[1];
                cameraMatrix.matrix[2] = m.elements[2];

                cameraMatrix.matrix[4] = m.elements[4];
                cameraMatrix.matrix[5] = m.elements[5];
                cameraMatrix.matrix[6] = m.elements[6];

                cameraMatrix.matrix[8] = m.elements[8];
                cameraMatrix.matrix[9] = m.elements[9];
                cameraMatrix.matrix[10] = m.elements[10];

                cameraMatrix.matrix[14] = -camera.position.z * scaling;
            }
        }
        doRequest('PUT', serviceUrl + '/session/CAMERA', function () {}, cameraMatrix);
    }
    positionChangeCounter++;
}

window.onbeforeunload = function () {
    deleteSession();
    parent.document.getElementById('btnSnapshot').disabled = true;
};

// init application
// 1st remove current session, if any
deleteSession(function () {
    // 2nd create a new one
    var span = parent.document.getElementById('renderingresourceidlog');
    span.innerHTML = '';
    createSession(startRenderer);
});
