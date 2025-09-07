import sys
import dbm.gnu

dbdir = sys.argv[1]
pkgname = sys.argv[2]
itchpkgpath = sys.argv[3]

pkgfiles = [line.strip() for line in sys.stdin]

db = dbm.gnu.open(dbdir, 'c');

for file in pkgfiles:
    gdbmout = db.get(file)

    if gdbmout is not None:
        pkgs = gdbmout.decode().split(' ')
    else: # must have been an error
        pkgs = []
        continue

    pkgs.remove(pkgname)

    if len(pkgs) == 0:
        print(file)
        del db[file]
    else:
        db[file] = " ".join(pkgs)

db.close()
