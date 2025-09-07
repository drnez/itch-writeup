import sys
import dbm.gnu

dbdir = sys.argv[1]
pkgname = sys.argv[2]

pkgfiles = [line.strip() for line in sys.stdin]

db = dbm.gnu.open(dbdir, 'c');

for file in pkgfiles:
    gdbmout = db.get(file)

    if gdbmout is not None:
        pkgs = gdbmout.decode().split(' ')
    else:
        pkgs = []

    # don't add pkgname if already existing - eg for reinstallations
    if pkgname not in pkgs:
        pkgs.append(pkgname)

    db[file] = " ".join(pkgs)

db.close()
