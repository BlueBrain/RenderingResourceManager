Changelog {#Changelog}
============

## Rendering Resource Manager

# Release 0.6.0

* [73](https://github.com/BlueBrain/RenderingResourceManager/pull/73):
  Added Unicore allocation manager

# Release 0.4.0

* [46](https://github.com/BlueBrain/RenderingResourceManager/pull/46):
  Fixed scheduling request management
* [45](https://github.com/BlueBrain/RenderingResourceManager/pull/45):
  Added extra parameters to scheduling API (nb_cpus, nb_gpus, etc)
* [44](https://github.com/BlueBrain/RenderingResourceManager/pull/44):
  Fixed request body forwarding to rendering resource
* [43](https://github.com/BlueBrain/RenderingResourceManager/pull/43):
  Fixed slurm command line arguments 
* [42](https://github.com/BlueBrain/RenderingResourceManager/pull/42):
  Unified json HTTP responses 
* [40](https://github.com/BlueBrain/RenderingResourceManager/pull/40):
  Added name and description to rendering resource configuration

# Release 0.3.0

* [39](https://github.com/BlueBrain/RenderingResourceManager/pull/39):
  Deployment adjustments
* [38](https://github.com/BlueBrain/RenderingResourceManager/pull/38):
  Removed dependency to Saga library

# Release 0.2.0

* [27](https://github.com/BlueBrain/RenderingResourceManager/pull/27):
  Improved stability by introducing timeouts and cleanups
* [26](https://github.com/BlueBrain/RenderingResourceManager/pull/26):
  Switched to gevent workers
* [25](https://github.com/BlueBrain/RenderingResourceManager/pull/25):
  Fixed dependencies
* [24](https://github.com/BlueBrain/RenderingResourceManager/pull/24):
  Replaced urllib2 by requests
* [23](https://github.com/BlueBrain/RenderingResourceManager/pull/23):
  - Upgraded to latest ZeroBuf implementation in C++ renderers
  - Added convertion to boolean in settings management
  - Added sample script for starting rendering resource together with VNC Server
* [22](https://github.com/BlueBrain/RenderingResourceManager/pull/22):
  Added Provides_Vocabulary attribute to Rendering Resource configuration
* [21](https://github.com/BlueBrain/RenderingResourceManager/pull/21):
  Job manager now uses renderer id instead of renderer command
* [20](https://github.com/BlueBrain/RenderingResourceManager/pull/20):
  Added documentation to AngularVwsViewer
* [19](https://github.com/BlueBrain/RenderingResourceManager/pull/19):
  Added AngularVwsViewer example as well as static files support for testing purposes.
  REMINDER: Django should NOT be used for production.

# Release 0.1.0

* [18](https://github.com/BlueBrain/RenderingResourceManager/pull/18):

* [17](https://github.com/BlueBrain/RenderingResourceManager/pull/17):
  Added DemoLauncher as a sample application
* [16](https://github.com/BlueBrain/RenderingResourceManager/pull/16):
  Updated deployment files
* [15](https://github.com/BlueBrain/RenderingResourceManager/pull/15):
  Bug fix in the return value of the list of available configurations
* [14](https://github.com/BlueBrain/RenderingResourceManager/pull/14):
  Bug fix in the handling of session destruction
* [13](https://github.com/BlueBrain/RenderingResourceManager/pull/13):
  Fixed exception error in the image feed manager
* [12](https://github.com/BlueBrain/RenderingResourceManager/pull/12):
  Bug fix in image streamer
* [11](https://github.com/BlueBrain/RenderingResourceManager/pull/11):
  Fixed cookie transmission from RRM to HISS
* [10](https://github.com/BlueBrain/RenderingResourceManager/pull/10):
  Added image streaming support
* [9](https://github.com/BlueBrain/RenderingResourceManager/pull/9):
  Fix in log API
* [8](https://github.com/BlueBrain/RenderingResourceManager/pull/8):
  Added API for job and process logs
* [7](https://github.com/BlueBrain/RenderingResourceManager/pull/7):
  Updated licencing
* [6](https://github.com/BlueBrain/RenderingResourceManager/pull/6):
  Removed unused documentation images
* [5](https://github.com/BlueBrain/RenderingResourceManager/pull/5):
  Added technical architecture documentation
* [4](https://github.com/BlueBrain/RenderingResourceManager/pull/4):
  Fixed process opening and GUI for standalone run
* [3](https://github.com/BlueBrain/RenderingResourceManager/pull/3):
  Added Javascript sample application
* [2](https://github.com/BlueBrain/RenderingResourceManager/pull/2):
  Added Wiki Images
* [1](https://github.com/BlueBrain/RenderingResourceManager/pull/1):
  Added admin interface
