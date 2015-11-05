# = Class: apps::visualization::rrm
#
# Rendering resource manager recipe
#
# == Copyright
#
# [apps::nodejs::npmregistry]
#     Global variable holding the registry.
#
# [bbp::config::platform] ( will need later )
#     Global variable holding the platform configuration.
#
# == Dependencies
#
# [nodejs] to retrieve the package
# .... others
#
# Copyright (c) 2014, EPFL/Blue Brain Project
#
class apps::visualization::rrm (
  $user,
  $group,
  $home,
){
  include ::apps
  include ::supervisor
  include ::repo::epel
  include ::repo::bbp  # need this for the user_gid for the supervisor user
  include ::sqlite
  include ::nodejs
  include ::apps::python
  include ::apps::nginx_lua
  include ::nginx

  # nginx-lua configuration
  $nginx_lua_conf     = "${::nginx::confd}/rrm.conf"
  $nginx_lua_conf_ext = "${module_name}/rrm/rrm.conf.erb"
  $nginx_port         = '8000'
  $swagger_ui         = true

  # Python setup
  $bbp_pypi    = hiera("bbp_pypi::${::environment}")
  $python_venv = '/opt/virtualenv'

  # Rendering Resource Manager Service Setup
  $rrm_upstream_name  = hiera('vws::rrm_name')
  $rrm_api_version    = hiera('vws::rrm_api_version')
  $rrm_service_name   = "${rrm_upstream_name}/${rrm_api_version}"
  $rrm_service_port   = hiera('vws::rrm_port')
  $secret_key         = hiera('vws::secret_key')
  $slurm_username     = hiera('vws::slurm_username')
  $slurm_project      = hiera('vws::slurm_project')
  $client_id          = hiera('vws::client_id')
  $rrm_version        = hiera('vws::rrm_version')
  $rrm_module         = 'rendering_resource_manager_service'
  $db_dir             = "/var/${rrm_upstream_name}"
  $rrm_module_bin     = "${python_venv}/bin"

  # Image Streaming Service Setup
  $hiss_upstream_name = hiera('vws::hiss_name')
  $hiss_api_version   = hiera('vws::hiss_api_version')
  $hiss_service_name  = "${hiss_upstream_name}/${hiss_api_version}"
  $hiss_service_port  = hiera('vws::hiss_port')
  $hiss_version       = hiera('vws::hiss_version')
  $hiss_module        = 'http_image_streaming_service'
  $hiss_module_bin    = "${python_venv}/bin"

  # Front-end Setup
  $pkgname               = 'viz-render-viewer'
  $front_prefix          = hiera('vws::front_prefix')
  $front_version         = hiera('vws::front_version')
  $path                  = '/opt/visualization'
  $prefixed_path         = "${path}/${front_prefix}"
  $front_port            = '80'
  $www_root              = "${prefixed_path}/node_modules/${pkgname}/dist"
  $registry              = hiera('apps::nodejs::npmregistry')
  $server_names          = hiera('vws::server::server_names')
  $static_asset_expires  = hiera('vws::server::static_asset_expires')
  $dynamic_asset_expires = hiera('vws::server::dynamic_asset_expires')
  $port                  = hiera('vws::server::port')
  $listen_options        = hiera('vws::server::listen_options')
  $config                = "{\"version\": \"${front_version}\", \"api\": { \"${rrm_api_version}\": \"http://${::fqdn}/${front_prefix}/${rrm_service_name}\"}}"

  # ----------------------------------------------------------------------------
  # Global environment settings
  # ----------------------------------------------------------------------------

  # Disable selinux
  exec { 'disable selinux on host':
    user    => 'root',
    command => '/usr/sbin/setenforce 0',
  }

  # Create python virtual environment folder
  file { $python_venv:
    ensure => directory,
    owner  => $user,
    group  => $group,
    mode   => '0755',
  }

  # Create python virtual environment
  python::virtualenv { $python_venv :
    ensure  => present,
    owner   => $user,
    require => [File[$python_venv],
                ],
  }

  # Deploy gunicorn
  python::pip { 'gunicorn':
    virtualenv => $python_venv,
    url        => $bbp_pypi,
    version    => '19.1.1',
    egg        => 'gunicorn',
    require    => [Python::Virtualenv[$python_venv],
                  ],
  }

  # ----------------------------------------------------------------------------
  # Rendering Resource Manager service
  # ----------------------------------------------------------------------------

  # Install RRM module
  python::pip { $rrm_module :
    virtualenv   => $python_venv,
    url          => $bbp_pypi,
    install_args => '--pre --upgrade',
    version      => $rrm_version,
    egg          => $rrm_module,
    require      => [Python::Virtualenv[$python_venv],
                    ],
  }

  # Create RRM machine specific settings
  file { 'rrm_local_settings':
    ensure  => present,
    path    => "${python_venv}/lib/python2.6/site-packages/${rrm_module}/local_settings.py",
    owner   => $user,
    group   => $group,
    mode    => '0644',
    replace => true,
    content => template("${module_name}/rrm/local_settings.py.erb"),
    require => [Python::Pip[$rrm_module],
                ],
  }

  # Create and populate RRM database
  file { $db_dir:
    ensure => directory,
    owner  => $user,
    group  => $group,
    mode   => '0755',
  }
  exec { "syncdb_${rrm_module}":
    command => "${python_venv}/bin/python ${python_venv}/lib/python2.6/site-packages/${rrm_module}/manage.py syncdb --noinput",
    path    => $rrm_module_bin,
    cwd     => $python_venv,
    user    => $user,
    timeout => 0,
    require => [File['rrm_local_settings'],
                File[$db_dir]
                ]
  }

  exec { 'setup_db_config_livre':
    command => "curl -curl --dump-header - -H \"Accept:application/json\" -H \"Content-Type:application/json\" -X POST --data \'{\"id\": \"livre\", \"command_line\": \"livre\", \"modules\": \"BBP/viz/latest\", \"environment_variables\": \"\", \"process_rest_parameters_format\": \"--rest \${rest_hostname}:\${rest_port} --zeq-schema \${rest_schema}://\", \"scheduler_rest_parameters_format\": \"--rest \$SLURMD_NODENAME:\${rest_port} --zeq-schema \${rest_schema}://\", \"graceful_exit\": \"True\" }\' http://localhost:${rrm_service_port}/${rrm_service_name}/config/",
    path    => '/usr/bin/',
    require => Supervisor::Service['rrm']
  }

  exec { 'setup_db_config_rtneuron':
    command => "curl -curl --dump-header - -H \"Accept:application/json\" -H \"Content-Type:application/json\" -X POST --data \'{\"id\": \"rtneuron\", \"command_line\": \"rtneuron-app.py\", \"modules\": \"BBP/viz/latest\", \"environment_variables\": \"\", \"process_rest_parameters_format\": \"--rest \${rest_hostname}:\${rest_port} --zeq-schema \${rest_schema}\", \"scheduler_rest_parameters_format\": \"--rest \$SLURMD_NODENAME:\${rest_port} --zeq-schema \${rest_schema}\", \"graceful_exit\": \"True\" }\' http://localhost:${rrm_service_port}/${rrm_service_name}/config/",
    path    => '/usr/bin/',
    require => Supervisor::Service['rrm']
  }

  exec { 'setup_db_config_BRayns':
    command => "curl -curl --dump-header - -H \"Accept:application/json\" -H \"Content-Type:application/json\" -X POST --data \'{\"id\": \"brayns\", \"command_line\": \"braynsService\", \"modules\": \"BBP/viz/latest\", \"environment_variables\": \"\", \"process_rest_parameters_format\": \"--rest \${rest_hostname}:\${rest_port} --zeq-schema \${rest_schema}\", \"scheduler_rest_parameters_format\": \"--rest \$SLURMD_NODENAME:\${rest_port} --zeq-schema \${rest_schema}\", \"graceful_exit\": \"True\" }\' http://localhost:${rrm_service_port}/${rrm_service_name}/config/",
    path    => '/usr/bin/',
    require => Supervisor::Service['rrm']
  }

  # Configure RRM in gunicorn
  supervisor::service { 'rrm':
    ensure      => present,
    name        => 'rrm',
    enable      => true,
    command     => "${rrm_module_bin}/gunicorn \
                    ${rrm_module}.service.wsgi \
                    -w 4 -b 127.0.0.1:${rrm_service_port} --log-file - ",
    user        => $user,
    group       => $group,
    directory   => $python_venv,
    environment => "HOME=${home},USER=${user},\
LOGNAME=${user},PWD=${python_venv}",
    require     => [Python::Pip[$rrm_module],
                    Python::Pip['gunicorn'],
                    Class['::repo::bbp'],
                  ],
    subscribe   => [Python::Pip[$rrm_module],
                    File['hiss_local_settings'],
                    ],
  }

  # ----------------------------------------------------------------------------
  # Image Streaming service
  # ----------------------------------------------------------------------------

  # Install HISS module
  python::pip { $hiss_module :
    virtualenv   => $python_venv,
    url          => $bbp_pypi,
    install_args => '--pre --upgrade',
    version      => $hiss_version,
    egg          => $hiss_module,
    require      => [Python::Virtualenv[$python_venv],
                    ],
  }

  # Create HISS machine specific settings
  file { 'hiss_local_settings':
    ensure  => present,
    path    => "${python_venv}/lib/python2.6/site-packages/${hiss_module}/service/settings.py",
    owner   => $user,
    group   => $group,
    mode    => '0644',
    replace => true,
    content => template("${module_name}/hiss/local_settings.py.erb"),
    require => [Python::Pip[$hiss_module],
                ],
  }

  supervisor::service { 'hiss':
    ensure      => present,
    name        => 'hiss',
    enable      => true,
    command     => "${hiss_module_bin}/gunicorn \
                    ${hiss_module}.service.wsgi \
                    -w 4 -b 127.0.0.1:${hiss_service_port} --log-file - ",
    user        => $user,
    group       => $group,
    directory   => $python_venv,
    environment => "HOME=${home},USER=${user},\
LOGNAME=${user},PWD=${python_venv}",
    require     => [Python::Pip[$hiss_module],
                    Python::Pip['gunicorn'],
                    Class['::repo::bbp'],
                  ],
    subscribe   => [Python::Pip[$hiss_module],
                    File['hiss_local_settings'],
                    ],
  }

  # ----------------------------------------------------------------------------
  # NGINX configuration
  # ----------------------------------------------------------------------------
  file { $nginx_lua_conf:
    ensure  => present,
    path    => $nginx_lua_conf,
    owner   => $user,
    group   => $group,
    content => template('apps/viz-nosecurity-nginx-common.conf.erb'),
    notify  => Service['nginx-lua'],
  }

  # rrm port
  @firewall { "${nginx_port}-v4 allow http":
    state  => 'NEW',
    proto  => 'tcp',
    dport  => $nginx_port,
    action => 'accept',
  }
  @firewall { "${nginx_port}-v6 allow http":
    state    => 'NEW',
    proto    => 'tcp',
    dport    => $nginx_port,
    action   => 'accept',
    provider => 'ip6tables',
  }

  # front-end port
  @firewall { "${front_port}-v4 allow http":
    state  => 'NEW',
    proto  => 'tcp',
    dport  => $front_port,
    action => 'accept',
  }
  @firewall { "${front_port}-v6 allow http":
    state    => 'NEW',
    proto    => 'tcp',
    dport    => $front_port,
    action   => 'accept',
    provider => 'ip6tables',
  }

  ########## front end
  # Ensure installation directory exists.
  file { $path:
    ensure => directory
  }
  file { $prefixed_path:
    ensure => directory
  }

  # Install node package ( will install manually )
  nodejs::npm { "${prefixed_path}:${pkgname}":
    ensure      => present,
    version     => $front_version,
    require     => File[$prefixed_path],
    install_opt => "--registry ${registry}"
  }

  # This vhost should respond to any request (IP, localhost, dnsname.epfl.ch)
  nginx::resource::vhost { 'jsvizviewer':
    ensure              => present,
    server_name         => $server_names,
    listen_port         => $port,
    listen_options      => $listen_options,
    www_root            => $www_root,
    location_cfg_append => {
      expires  => $static_asset_expires,
      # the trailing '#' ensure that the appended ';' will be considered
      # as a comment instead of a syntax error.
      location => "~* \\.(html|json)$ { expires ${dynamic_asset_expires}; } # ",
    }
  }

  # This will redirect URLs starting with rendering-resource-manager to the
  # rrm service
  nginx::resource::location { $rrm_upstream_name:
    location            => "/${front_prefix}/${rrm_upstream_name}",
    location_alias      => $www_root,
    vhost               => 'jsvizviewer',
    location_cfg_append => {
      proxy_pass => "http://127.0.0.1:${rrm_service_port}/${rrm_upstream_name}",
    }
  }

  # This will redirect URLs starting with image_streaming to the
  # rrm service
  nginx::resource::location { $hiss_upstream_name:
    location            => "/${front_prefix}/${hiss_upstream_name}",
    location_alias      => $www_root,
    vhost               => 'jsvizviewer',
    location_cfg_append => {
      proxy_pass => "http://127.0.0.1:${hiss_service_port}/${hiss_upstream_name}",
    }
  }

  # Create configuration file using data in hiera.
  file { "${www_root}/config.json":
    ensure  => file,
    content => $config,
    require => Nodejs::Npm["${prefixed_path}:${pkgname}"]
  }
}
