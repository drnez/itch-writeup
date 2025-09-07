# python script to update gdbm file for new pkg
# all capabilities of before
# no need for gdbmtool anymore (though gdbm needed so trivial) - IGNORE, NEEDED AGAIN IN v4
# checks for duplicates in the case of reinstallation
# completes in milliseconds, rather than minutes!

import sys
import dbm.gnu

dbdir = sys.argv[1]
pkgname = sys.argv[2]

db = dbm.gnu.open(dbdir, 'c');

for i in range(3, len(sys.argv)):
    file = sys.argv[i]

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
