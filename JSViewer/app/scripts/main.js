(function () {
    'use strict';

    function init() {
        document.getElementById('btnRender').addEventListener("click", refreshMainFrame, false);
        document.getElementById('btnSnapshot').addEventListener("click", renderSnapshot, false);
        document.getElementById('renderer').addEventListener("change", function (event) {
            populateParams(event.target);
        }, false);
    }

    function refreshMainFrame() {
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
    }
})();