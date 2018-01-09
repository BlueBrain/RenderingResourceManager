#modules that have tests
TEST_MODULES=rendering_resource_manager_service

#modules that are installable (ie: ones w/ setup.py)
INSTALL_MODULES=.

#packages to cover
COVER_PACKAGES=hbp_rendering_resource_manager_service

#documented modules
DOC_MODULES=docs

#no need to do coverage on the mock objects
IGNORE_LINT=docs/conf.py

#need a later version than 1.4.1 to install ipywidgets and ipython
#we choose 9.0.1 here to match the pip version in collab notebooks
PYTHON_PIP_VERSION=pip==9.0.1

##### DO NOT MODIFY BELOW #####################

ifndef CI_DIR
CI_REPO?=ssh://bbpcode.epfl.ch/platform/ContinuousIntegration.git
CI_DIR?=ContinuousIntegration

FETCH_CI := $(shell \
		if [ ! -d $(CI_DIR) ]; then \
			git clone $(CI_REPO) $(CI_DIR) > /dev/null;\
			pushd $(CI_DIR);\
			git checkout 478d1c4c58bddacde1983666a7d24cfc9c7ffab6;\
			popd;\
		fi;\
		echo $(CI_DIR) )
endif

include $(CI_DIR)/python/common_makefile
