#modules that have tests
TEST_MODULES=rendering_resource_manager_service

#modules that are installable (ie: ones w/ setup.py)
INSTALL_MODULES=.

#packages to cover
COVER_PACKAGES=hbp_rendering_resource_manager_service

#documented modules
DOC_MODULES=

#no need to do coverage on the mock objects
IGNORE_LINT=

##### DO NOT MODIFY BELOW #####################

ifndef CI_DIR
CI_REPO?=ssh://bbpcode.epfl.ch/platform/ContinuousIntegration.git
CI_DIR?=ContinuousIntegration

FETCH_CI := $(shell \
		if [ ! -d $(CI_DIR) ]; then \
			git clone $(CI_REPO) $(CI_DIR) > /dev/null ;\
		fi;\
		echo $(CI_DIR) )
endif

include $(CI_DIR)/python/common_makefile