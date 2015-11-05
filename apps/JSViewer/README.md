JSVizRenderViewer
=================

Simple JavaScript viewer to interact with the Visualization Web Services.

INSTALL
=======

Local Install
-------------
Install dependencies:

```
sudo apt-get install npm
sudo apt-get install node nodejs-legacy
sudo npm config set prefix $PWD
sudo npm install bower
sudo npm install grunt grunt-cli
export PATH=$PWD/node_modules/bower/bin:$PWD/node_modules/grunt-cli/bin:$PATH
export LD_LIBRARY_PATH=$PWD/node_modules/bower/lib:$PWD/node_modules/grunt-cli/lib:$LD_LIBRARY_PATH
sudo npm install
bower install
```

run
```
grunt serve
```

