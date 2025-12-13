project('composure',
  version: '0.1.0',
  meson_version: '>= 0.62.0',
)

python = import('python')
py_installation = python.find_installation('python3')

# Application ID
app_id = 'io.github.composure'

# Install Python sources
python_dir = py_installation.get_install_dir()
install_subdir('src', install_dir: python_dir / 'composure')

# Install data files
install_data('data/io.github.composure.desktop',
  install_dir: get_option('datadir') / 'applications')

install_data('data/io.github.composure.svg',
  install_dir: get_option('datadir') / 'icons/hicolor/scalable/apps')

# Create launcher script
configure_file(
  input: 'data/composure.in',
  output: 'composure',
  configuration: {
    'PYTHON': py_installation.full_path(),
    'PYTHONDIR': python_dir,
  },
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x',
)
