# Maintainer: Bernardo Kuri <aur@bkuri.com>
pkgname=jesse-mcp
pkgver=1.0.0
pkgrel=1
pkgdesc="MCP server for Jesse algorithmic trading framework"
arch=('any')
url="https://github.com/bkuri/jesse-mcp"
license=('MIT')
depends=(
    'python'
    'python-mcp'
    'python-fastmcp'
    'python-jedi'
    'python-numpy'
    'python-pandas'
    'python-pydantic'
    'python-scikit-learn'
    'python-scipy'
    'python-websockets'
    'python-requests'
    'python-typing-extensions'
)
makedepends=(
    'python-build'
    'python-installer'
    'python-wheel'
    'python-hatchling'
)
optdepends=(
    'python-optuna: hyperparameter optimization support'
    'python-pytest: running tests'
)
source=("$pkgname-$pkgver.tar.gz::$url/archive/v$pkgver.tar.gz")
sha256sums=('SKIP')

build() {
    cd "$pkgname-$pkgver"
    python -m build --wheel --no-isolation
}

package() {
    cd "$pkgname-$pkgver"
    python -m installer --destdir="$pkgdir" dist/*.whl

    install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
