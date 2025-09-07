#!/bin/bash

# This takes a compiled package, and installs in temp dir, then moves to installation prefix with tar
# No support for custom install
# Warns about overriding installed files
# No uninstallation capacity
# Does not store installed "dupe" files in a file so as not to be deleted in the future
# Find package name using current or parent's (if current is build) dir name

install_prefix="$HOME/prog/school/epq/dest/"
temp_dir="/tmp/itch/build"

configure() {
    echo "configure as normal, ensuring the following is added:"
    echo "    --prefix=$install_prefix"
}

build() {
    echo "make as normal"
}

install() {
    rm -rf "$temp_dir" # in case not properly cleaned before
    mkdir -p $temp_dir

    make DESTDIR="$temp_dir" install # install in temp dir

    findname

    pkgpath="/var/lib/itch/pkgs/$pkgname"
    itchpkgpath="$pkgpath/$pkgname.itchpkg"

    sudo mkdir -p "$pkgpath"

    sudo tar czf "$itchpkgpath" -C "$temp_dir$install_prefix" .

    cd $install_prefix

    # finds existing files that will be overwritten - credit https://github.com/skeeto/dotfiles/blob/master/bin/qpkg (with modifications)
    for file in $(tar tzf "$itchpkgpath" | grep -v '/$'); do
        if [ -e "$file" ]; then
            printf "Overwrites '%s'\n" "${file#./}"
        fi
    done

    read -p "Proceed? (yes/NO): " confirmation

    if [ "$confirmation" = "yes" ] || [ "$confirmation" = "y" ]; then
        tar xf "$itchpkgpath"
    else
        echo "Aborted!"
    fi

    rm -rf "$temp_dir"
}

findname() {
    pkgname=$(basename "$(pwd)")

    # tries to find package name (either current dir or parent if in build dir)
    if [ "$pkgname" = "build" ]; then
        pkgname=$(basename "$(dirname "$(pwd)")")
    fi

    echo "Enter package name (blank for [$pkgname]):"
    read input

    if [ "$input" != "" ]; then
        pkgname="$input"
    fi
}

case "$1" in
    "-c")
        configure ;;
    "-b")
        build ;;
    "-i")
        install ;;
    "-n")
        findname ;;
    *)
        echo "Error!"
        ;;
esac
