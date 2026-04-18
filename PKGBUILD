# Maintainer: Natalie Spiva <natalie@acreetionos.org>
pkgname=openrouter-tui
pkgver=0.1.0
pkgrel=1
pkgdesc="Terminal chat client for the OpenRouter API"
arch=('any')
url="https://github.com/spivanatalie64/openrouter-tui-silly"
license=('MIT')
depends=('python' 'python-requests' 'python-prompt-toolkit')
makedepends=('git')
source=("${pkgname}-${pkgver}.tar.gz")
sha256sums=('SKIP')

# No build step; this is a simple script install
build() {
  :
}

package() {
  # Install from the extracted source directory to avoid path issues
  srcdir_subdir="$srcdir/${pkgname}-${pkgver}"
  install -Dm755 "$srcdir_subdir/main.py" "$pkgdir/usr/bin/openrouter-tui"

  mkdir -p "$pkgdir/usr/share/$pkgname"
  install -Dm644 "$srcdir_subdir/openrouter_client.py" "$pkgdir/usr/share/$pkgname/openrouter_client.py"
  if [[ -f "$srcdir_subdir/README.md" ]]; then
    install -Dm644 "$srcdir_subdir/README.md" "$pkgdir/usr/share/doc/$pkgname/README.md"
  fi
  if [[ -f "$srcdir_subdir/requirements.txt" ]]; then
    install -Dm644 "$srcdir_subdir/requirements.txt" "$pkgdir/usr/share/doc/$pkgname/requirements.txt"
  fi

  # Include tests for downstream developers
  if [[ -d "$srcdir_subdir/tests" ]]; then
    mkdir -p "$pkgdir/usr/share/$pkgname/tests"
    cp -a "$srcdir_subdir/tests/"* "$pkgdir/usr/share/$pkgname/tests/"
  fi
}
