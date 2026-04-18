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
  install -Dm755 "main.py" "$pkgdir/usr/bin/openrouter-tui"

  mkdir -p "$pkgdir/usr/share/$pkgname"
  install -Dm644 "openrouter_client.py" "$pkgdir/usr/share/$pkgname/openrouter_client.py"
  if [[ -f README.md ]]; then
    install -Dm644 "README.md" "$pkgdir/usr/share/doc/$pkgname/README.md"
  fi
  if [[ -f requirements.txt ]]; then
    install -Dm644 "requirements.txt" "$pkgdir/usr/share/doc/$pkgname/requirements.txt"
  fi

  # Include tests for downstream developers
  if [[ -d tests ]]; then
    mkdir -p "$pkgdir/usr/share/$pkgname/tests"
    cp -a tests/* "$pkgdir/usr/share/$pkgname/tests/"
  fi
}
