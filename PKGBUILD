# Maintainer: Natalie Spiva <natalie@acreetionos.org>
pkgname=openrouter-tui
pkgver=0.1.0
pkgrel=1
pkgdesc="Terminal chat client for the OpenRouter API"
arch=('any')
url="https://github.com/spivanatalie64/openrouter-tui-silly"
license=('MIT')
depends=('python' 'python-requests')
makedepends=('git' 'python-pip')
source=("${pkgname}-${pkgver}.tar.gz")
sha256sums=('6fb6acab7d3c02352e4017e50bb37300ed890562ff269089a8e894c3dcc418d5')

# No build step; this is a simple script install
build() {
  :
}

package() {
  # Install from the extracted source directory to avoid path issues
  srcdir_subdir="$srcdir/${pkgname}-${pkgver}"
  install -Dm755 "$srcdir_subdir/main.py" "$pkgdir/usr/bin/openrouter-tui"

  # Install the Python module into site-packages so it's importable as a module
  _pyver=$(python -c "import sysconfig; print(sysconfig.get_python_version())")
  _pydir="$pkgdir/usr/lib/python${_pyver}/site-packages"
  mkdir -p "$_pydir"
  install -Dm644 "$srcdir_subdir/openrouter_client.py" "$_pydir/openrouter_client.py"
  if [[ -f "$srcdir_subdir/README.md" ]]; then
    install -Dm644 "$srcdir_subdir/README.md" "$pkgdir/usr/share/doc/$pkgname/README.md"
  fi
  if [[ -f "$srcdir_subdir/requirements.txt" ]]; then
    # Install Python dependencies into the package root so system upgrade doesn't need them
    python -m pip install --root "$pkgdir" --prefix=/usr -r "$srcdir_subdir/requirements.txt" --no-build-isolation --ignore-installed
    install -Dm644 "$srcdir_subdir/requirements.txt" "$pkgdir/usr/share/doc/$pkgname/requirements.txt"
  fi

  # Include tests for downstream developers
  if [[ -d "$srcdir_subdir/tests" ]]; then
    mkdir -p "$pkgdir/usr/share/$pkgname/tests"
    cp -a "$srcdir_subdir/tests/"* "$pkgdir/usr/share/$pkgname/tests/"
  fi
}
