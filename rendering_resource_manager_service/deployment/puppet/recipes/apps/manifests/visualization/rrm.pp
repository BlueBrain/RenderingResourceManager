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
class apps::visualization::rrm{
  include ::apps
  include ::supervisor
  include ::repo::epel
  include ::repo::bbp  # need this for the user_gid for the supervisor user
  include ::user::localservice
  include ::sqlite
  include ::nodejs
  include ::apps::python
  include ::apps::nginx_lua
  include ::nginx

  # nginx-lua configuration
  $nginx_lua_conf     = "${::nginx::confd}/rrm.conf"
  $nginx_lua_conf_ext = "${module_name}/rrm/rrm.conf.erb"
  $nginx_port         = '8000'
  $service_name       = 'rendering-resource-manager/v1'
  $swagger_ui         = true
  $upstream_name      = 'rendering-resource-manager'
  $service_port       = '8383'

  ## user configuration
  $user_name  = 'localservice'
  $user_group = 'localservice'
  $user_home  = "/home/${user_name}"

  $pymodule    = 'rendering_resource_manager_service'
  $bbp_pypi    = hiera("bbp_pypi::${::environment}")
  $app_dir     = "/opt/${pymodule}"
  $db_dir      = "/var/${upstream_name}"
  $virtualenv  = "${app_dir}/virtualenv"
  $module_bin  = "${virtualenv}/bin"

  #django setup
  $secret_key  = hiera('rrm::secret_key')
  $slurm_username = hiera('rrm::slurm_username')
  $slurm_password = hiera('rrm::slurm_password')
  $client_id = hiera('rrm::client_id')
  $ui_base_url = hiera('rrm::ui_base_url')
  $static_root = "${app_dir}/static/"
  $static_path = 'rrm/static/'
  $back_version = hiera('rrm::back_version')

  ########## front end setup
  $pkgname               = 'viz-render-viewer'
  $path                  = '/opt/visualization'
  $www_root              = "${path}/node_modules/${pkgname}/dist"
  $front_port            = '80'
  $registry              = hiera('apps::nodejs::npmregistry')
  $server_names          = hiera('rrm::server::server_names')
  $static_asset_expires  = hiera('rrm::server::static_asset_expires')
  $dynamic_asset_expires = hiera('rrm::server::dynamic_asset_expires')
  $port                  = hiera('rrm::server::port')
  $listen_options        = hiera('rrm::server::listen_options')
  #for NPM package
  $front_version = hiera('rrm::front_version')


  python::virtualenv { $virtualenv :
    ensure  => present,
    owner   => $user_name,
    require => [File[$app_dir],
                ],
  }

  python::pip { $pymodule :
    virtualenv   => $virtualenv,
    url          => $bbp_pypi,
    install_args => '--pre --upgrade',
    version      => $back_version,
    egg          => $pymodule,
    require      => [Python::Virtualenv[$virtualenv],
                    ],
  }

  python::pip { 'gunicorn':
    virtualenv => $virtualenv,
    url        => $bbp_pypi,
    version    => '19.1.1',
    egg        => 'gunicorn',
    require    => [Python::Virtualenv[$virtualenv],
                  ],
  }

  file { $app_dir:
    ensure  => directory,
    owner   => $user_name,
    group   => $user_group,
    mode    => '0755',
    require => [Class['::user::localservice'],
                ]
  }

  file { $db_dir:
    ensure  => directory,
    owner   => $user_name,
    group   => $user_group,
    mode    => '0755',
    require => [File[$app_dir],
                ],
  }

  file { $static_root:
    ensure  => directory,
    owner   => $user_name,
    group   => $user_group,
    mode    => '0755',
    require => [File[$app_dir],
                ]
  }

  file { 'local_settings':
    ensure  => present,
    path    => "${virtualenv}/lib/python2.6/site-packages/${pymodule}/local_settings.py",
    owner   => $user_name,
    group   => $user_group,
    mode    => '0644',
    replace => true,
    content => template("${module_name}/rrm/local_settings.py.erb"),
    require => [Python::Pip[$pymodule],
                ],
  }

  exec { "syncdb_${pymodule}":
    command => "python ${virtualenv}/lib/python2.6/site-packages/${pymodule}/manage.py syncdb --noinput",
    path    => $module_bin,
    cwd     => $virtualenv,
    user    => $user_name,
    timeout => 0,
    require => [File['local_settings'],
                File[$db_dir]
                ]
  }

  exec { 'setup_db_config_livre':
    command => "curl -curl --dump-header - -H \"Accept:application/json\" -H \"Content-Type:application/json\" -X POST --data \'{\"id\": \"livre\", \"command_line\": \"livre\", \"environment_variables\": \"\", \"process_rest_parameters_format\": \"--use-rest --rest-host \${rest_hostname} --rest-port \${rest_port} --zeq-schema \${rest_schema}\", \"scheduler_rest_parameters_format\": \"--use-rest --rest-host \$SLURMD_NODENAME --rest-port \${rest_port} --zeq-schema \${rest_schema}\", \"graceful_exit\": \"True\" }\' http://localhost:${service_port}/${service_name}/config/",
    path    => '/usr/bin/',
    require => Supervisor::Service['rrm']
  }

  exec { 'setup_db_config_rtneuron':
    command => "curl -curl --dump-header - -H \"Accept:application/json\" -H \"Content-Type:application/json\" -X POST --data \'{\"id\": \"rtneuron\", \"command_line\": \"rtneuron-app.py\", \"environment_variables\": \"\", \"process_rest_parameters_format\": \"--rest \${rest_hostname}:\${rest_port}\", \"scheduler_rest_parameters_format\": \"--rest \$SLURMD_NODENAME:\${rest_port}\", \"graceful_exit\": \"True\" }\' http://localhost:${service_port}/${service_name}/config/",
    path    => '/usr/bin/',
    require => Supervisor::Service['rrm']
  }

  exec { 'setup_db_config_hbpNeuronViewer':
    command => "curl -curl --dump-header - -H \"Accept:application/json\" -H \"Content-Type:application/json\" -X POST --data \'{\"id\": \"hbpneuronviewer\", \"command_line\": \"hbpNeuronViewer\", \"environment_variables\": \"\", \"process_rest_parameters_format\": \"--rest-hostname \${rest_hostname} --rest-port \${rest_port} --rest-schema \${rest_schema}\", \"scheduler_rest_parameters_format\": \"--rest-hostname \$SLURMD_NODENAME --rest-port \${rest_port} --rest-schema \${rest_schema}\", \"graceful_exit\": \"True\" }\' http://localhost:${service_port}/${service_name}/config/",
    path    => '/usr/bin/',
    require => Supervisor::Service['rrm']
  }

  exec { 'setup_db_config_hbpProteinViewer':
    command => "curl -curl --dump-header - -H \"Accept:application/json\" -H \"Content-Type:application/json\" -X POST --data \'{\"id\": \"hbpproteinviewer\", \"command_line\": \"hbpProteinViewer\", \"environment_variables\": \"\", \"process_rest_parameters_format\": \"--rest-hostname \${rest_hostname} --rest-port \${rest_port} --rest-schema \${rest_schema}\", \"scheduler_rest_parameters_format\": \"--rest-hostname \$SLURMD_NODENAME --rest-port \${rest_port} --rest-schema \${rest_schema}\", \"graceful_exit\": \"True\" }\' http://localhost:${service_port}/${service_name}/config/",
    path    => '/usr/bin/',
    require => Supervisor::Service['rrm']
  }

  exec { "collectstatic_${pymodule}":
    command => "python ${virtualenv}/lib/python2.6/site-packages/${pymodule}/manage.py collectstatic --noinput",
    path    => $module_bin,
    user    => $user_name,
    timeout => 0,
    require => [File[$static_root],
                File['local_settings'],
                ],
    }

  supervisor::service { 'rrm':
    ensure      => present,
    name        => 'rrm',
    enable      => true,
    command     => "${module_bin}/gunicorn \
                    ${pymodule}.service.wsgi \
                    -b 127.0.0.1:${service_port} --log-level debug --log-file - ",
    user        => $user_name,
    group       => $user_group,
    directory   => $virtualenv,
    environment => "HOME=/home/${user_name},USER=${user_name},\
LOGNAME=${user_name},PWD=${virtualenv}",
    require     => [Python::Pip[$pymodule],
                    Python::Pip['gunicorn'],
                    Class['::repo::bbp'],
                    Exec["collectstatic_${pymodule}"],
                  ],
    subscribe   => [Python::Pip[$pymodule],
                    File[$static_root],
                    File['local_settings'],
                    ],
  }

  file { $nginx_lua_conf:
    ensure  => present,
    path    => $nginx_lua_conf,
    owner   => $user_name,
    group   => $user_group,
    content => template('apps/viz-nosecurity-nginx-common.conf.erb'),
    require => [
        Class['::user::localservice']
    ],
    notify  => Service['nginx-lua'],
  }

  # Disable selinux
  exec { 'disable selinux on host':
    user    => 'root',
    command => '/usr/sbin/setenforce 0',
  }

  # install sshpass
  exec { 'sshpass installation':
    command => '/usr/bin/yum install -y sshpass',
    timeout => 1800,
  }

  # back-end port
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

  # Install node package ( will install manually )
  nodejs::npm { "${path}:${pkgname}":
    ensure      => present,
    version     => $front_version,
    require     => File[$path],
    install_opt => "--registry ${registry}"
  }

  # Create configuration file using data in hiera ( will need later )
  file { "${www_root}/config.json":
    ensure  => file,
    content => fact_to_json(hiera('bbp::config::platform')),
    require => Nodejs::Npm["${path}:${pkgname}"]
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
  nginx::resource::location { "jsvizviewer-${upstream_name}":
    location            => "/${upstream_name}",
    location_alias      => $www_root,
    vhost               => 'jsvizviewer',
    location_cfg_append => {
      proxy_pass => "http://127.0.0.1:${service_port}",
    }
  }
}
