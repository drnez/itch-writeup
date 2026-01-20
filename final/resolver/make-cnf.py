import sys
import dbm.gnu
import re
import os
from pathlib import Path
import json

core_dir = sys.argv[1] # /var/lib/itch-resolver/
global_db_dir = core_dir + "global.gdbm"
pkgs_dir = core_dir + "pkgs/"

local_pkgs_core_dir = sys.argv[2] # /var/lib/itch/
local_pkgs_db_dir = local_pkgs_core_dir + "shared/pkgs.gdbm" # /var/lib/itch/shared/pkgs.gdbm
local_pkgs_dir = local_pkgs_core_dir + "pkgs/"

new_pkg_name = sys.argv[3]
new_pkg_version = sys.argv[4] # NOTE: new pkg MUST be in global db

global_db = dbm.gnu.open(global_db_dir, 'c')

sat_clauses = list()

# mapping of pkgs to CNF number
pkg_to_num = dict()
num_to_pkg = dict()

pkg_to_deps = dict()
pkg_to_versions = dict()
pkg_to_deps = dict()
pkg_to_conflicts = dict()
pkg_to_provides = dict()

def build_pkg_dicts():
    return

def get_versions(pkg):
    dir = pkgs_dir + pkg

    if pkg in pkg_to_versions:
        return pkg_to_versions[pkg]

    if not Path(dir).exists():
        return []

    versions = os.listdir(dir)

    pkg_to_versions[pkg] = versions

    return versions

def version_in_range(version, lower, upper):
    if compare_versions(version, lower) == "<":
        return False
    if upper and compare_versions(version, upper) == ">":
        return False

    return True

def compare_versions(version_1, version_2):
    if version_1 == version_2:
        return "="

    v1a, v1b, v1c = split_version(version_1)
    v2a, v2b, v2c = split_version(version_2)

    if v1a > v2a:
        return ">"
    if v1a < v2a:
        return "<"

    for i in range(0, min(len(v1b), len(v2b))):
        if v1b[i] > v2b[i]:
            return ">"
        if v1b[i] < v2b[i]:
            return "<"

    if len(v1b) > len(v2b):
        return ">"
    if len(v1b) < len(v2b):
        return "<"

    if v1c > v2c:
        return ">"
    if v1c < v2c:
        return "<"

    return "="

def split_version(version):
    if ":" in version:
        epoch_str, version = version.split(":", 1)
        epoch = int(epoch_str)
    else:
        epoch = 0

    if "+" in version:
        version = version.split("+", 1)[0]

    if "-" in version:
        main_str, end_str = version.rsplit("-", 1) # rsplit gets last occurance
    else:
        main_str, end_str = version, "0"

    # split into array by .
    main = [int(x) for x in main_str.split(".") if x.isnumeric()]

    # strip text at end of c - only present in debian files
    m = re.match(r"(\\d+)", end_str)
    end = int(m.group(1)) if m else 0

    return epoch, main, end


# encode "dependencies must be met, or the package not be installed"
def encode_deps(pkg, version):
    dep_to_versions = get_deps(pkg, version)
    
    for dep, vers in dep_to_versions.items():
        new_clause = "-" + pkg_to_num[pkg, version] + " "
        
        entered = False

        for ver in vers:
            entered = True
            new_clause += pkg_to_num[dep, ver] + " "

        new_clause += "0"

        if (entered):
            sat_clauses.append(new_clause)

# encode "conflicts must not exist, or the package not be installed"
def encode_conflicts(pkg, version):
    conflict_to_versions = get_conflicts(pkg, version)
    
    for dep, vers in conflict_to_versions.items():
        new_clause = "-" + pkg_to_num[pkg, version] + " "

        entered = False

        for ver in vers:
            entered = True

            if (dep, ver) in provides:
                for providing_pkg, providing_ver in provides[dep, ver]:
                    new_clause += "-" + pkg_to_num[providing_pkg, providing_ver] + " "
            else:
                new_clause += "-" + pkg_to_num[dep, ver] + " " # not pkg or not conflict

        new_clause += "0"

        if (entered):
            sat_clauses.append(new_clause)

def get_deps(pkg, version):
    pkg_dir = pkgs_dir + pkg + "/" + version + "/"
    dep_file = pkg_dir + "depends.itch"

    if (pkg, version) in pkg_to_deps:
        return pkg_to_deps[pkg, version]

    results = dict()

    if not Path(dep_file).exists():
        pkg_to_deps[pkg, version] = results
        return results

    with open(dep_file) as file:
        for line in file:
            fields = line.strip().split()

            dep_name = fields[0]
            lower = fields[1]
            upper = ""

            if len(fields) > 2:
                upper = fields[2]

            dep_versions = []

            for ver in get_versions(dep_name):
                if version_in_range(ver, lower, upper):
                    dep_versions.append(ver)

            results[dep_name] = dep_versions # maps dependency name -> list of allowed versions

    pkg_to_deps[pkg, version] = results

    return results

def get_conflicts(pkg, version):
    pkg_dir = pkgs_dir + pkg + "/" + version + "/"
    conflict_file = pkg_dir + "conflicts.itch"

    results = dict()

    if not Path(conflict_file).exists():
        return results

    with open(conflict_file) as file:
        for line in file:
            fields = line.strip().split()

            conflict_name = fields[0]
            lower = fields[1]
            upper = ""

            if len(fields) > 2:
                upper = fields[2]

            conflict_versions = []

            for ver in get_versions(conflict_name):
                if version_in_range(ver, lower, upper):
                    conflict_versions.append(ver)

            results[conflict_name] = conflict_versions # maps conflict name -> list of not allowed versions

    return results

def set_provides(pkg, version):
    pkg_dir = pkgs_dir + pkg + "/" + version + "/"
    provide_file = pkg_dir + "provides.itch"

    if not Path(provide_file).exists():
        return

    with open(provide_file) as file:
        for line in file:
            provided_pkg, provided_ver = line.strip().split()

            if (provided_pkg, provided_ver) in provides:
                provides[provided_pkg, provided_ver].append((pkg, version))
            else:
                provides[provided_pkg, provided_ver] = [(pkg, version)]

def get_closure(pkg, ver):
    start = (pkg, ver)
    queue = [start]
    visited = set()

    while len(queue) > 0:
        (p, v) = queue.pop()

        if (p, v) in visited:
            continue

        visited.add((p, v))

        deps = get_deps(p, v)
        for dep in deps.keys():
            for allowed_ver in deps[dep]:
                queue.append((dep, allowed_ver))

    return visited


pkgs = global_db.keys()
provides = dict() # mapping of (provided pkg, provided pkg version) -> list of (pkg, version)

count = 1
for pkg in pkgs:
    versions = global_db[pkg.decode()].decode().split()

    for version in versions:
        pkg_to_num[pkg.decode(), version] = str(count)
        num_to_pkg[count] = (pkg.decode(), version)

        count += 1

        set_provides(pkg.decode(), version)

for pkg in pkgs: # needs second loop so mappings (and provides) are complete!
    versions = global_db[pkg.decode()].decode().split()

    for version in versions:
        encode_deps(pkg.decode(), version)
        encode_conflicts(pkg.decode(), version)

    # encode "only one version of each package"
    for i in range(0, len(versions)):
        for j in range(i+1, len(versions)):
            sat_clauses.append("-" + pkg_to_num[pkg.decode(), versions[i]] +  " "
                             + "-" + pkg_to_num[pkg.decode(), versions[j]] + " 0")

local_pkgs_db = dbm.gnu.open(local_pkgs_db_dir, 'c')

local_pkgs = local_pkgs_db.keys()

full_closure = set()

for pkg in local_pkgs:
    # encode "each package installed should be installed (but whatever version)"
    versions = global_db[pkg.decode()].decode().split() # all available versions

    new_clause = ""
    for version in versions:
        new_clause += pkg_to_num[pkg.decode(), version] + " "

        full_closure.update(get_closure(pkg.decode(), version)) # get closure of each installed/installable pkg-ver
    new_clause += "0"
    
    sat_clauses.append(new_clause)

full_closure.update(get_closure(new_pkg_name, new_pkg_version))

# encode "pkg to install should be installed with GIVEN version"
sat_clauses.append(pkg_to_num[new_pkg_name, new_pkg_version] + " 0")

for pkg_num, (pkg, version) in num_to_pkg.items():
    if (pkg, version) not in full_closure:
        sat_clauses.append("-" + str(pkg_num) + " 0")

for clause in sat_clauses:
    print(clause)

num_to_pkg_closure = dict()

for (pkg, ver) in full_closure:
    num_to_pkg_closure[pkg_to_num[pkg, ver]] = (pkg, ver)

with open(sys.argv[5], 'w') as file:
    json.dump(num_to_pkg_closure, file)
