#!/bin/bash

installprefix="$HOME/prog/school/epq/dest/"
tempdir="/tmp/itch/build"
pkgpath="/var/lib/itch/pkgs"

shareddir="/var/lib/itch/shared"
filedbdir="$shareddir/files.gdbm"
pkgdbdir="$shareddir/pkgs.gdbm"
pythonupdatedir="$HOME/prog/school/epq/main/updatedb.py" # UPDATE WITH TRUE INSTALLED LOCATION!
pythonuninstalldir="$HOME/prog/school/epq/main/uninstalldb.py" # UPDATE WITH TRUE INSTALLED LOCATION!

configure() {
    echo "configure as normal, ensuring the following is added:"
    echo "    --prefix=$installprefix"
}

build() {
    echo "make as normal"
}

install() {
    rm -rf "$tempdir" # in case not properly cleaned before
    mkdir -p $tempdir

    make DESTDIR="$tempdir" install # install in temp dir

    findname

    sudo mkdir -p "$pkgpath/$pkgname"

    sudo tar czf "$itchpkgpath" -C "$tempdir$installprefix" .

    installpkg
}

installpkg() { # existing tarball in pkgpath
    cd "$installprefix"

    pkgfiles=$(tar tzf "$itchpkgpath")

    # finds existing files that will be overwritten - credit https://github.com/skeeto/dotfiles/blob/master/bin/qpkg (with significant modifications)
    for file in $(tar tzf "$itchpkgpath" | grep -v '/$'); do
        if [ -e "$file" ]; then
            printf "Overwrites '%s'\n" "${file#./}"
        fi
    done

    read -p "Proceed? (yes/NO): " confirmation

    if [ "${confirmation,,}" = "yes" ] || [ "${confirmation,,}" = "y" ]; then # ${[string],,} converts to lower case
        updateshared
        tar xf "$itchpkgpath" # files extracted into install dir
    else
        echo "Aborted!"
    fi

    rm -rf "$tempdir"
}

uninstall() {
    gdbmout="$(echo "fetch $pkgname" | sudo gdbmtool "$pkgdbdir" 2>/dev/null)" # empty if not existing

    if [ "$gdbmout" != "I" ]; then
        echo "Error! Package not installed to begin with!"
        exit
    fi

    pkgfiles="$(tar tzf "$itchpkgpath")"

    toremove="$(printf "%s" "${pkgfiles[@]}" | sudo python "$pythonuninstalldir" "$filedbdir" "$pkgname" "$itchpkgpath")"

    echo "$toremove"

    IFS=$'\n' read -rd '' -a toremovearr <<< "$toremove"

    for file in "${toremovearr[@]}"; do
        echo "$file"
        sudo rm -rf "$installprefix/$file"
    done

    echo "delete $pkgname" | sudo gdbmtool "$pkgdbdir" 2>/dev/null
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

    itchpkgpath="$pkgpath/$pkgname/$pkgname.itchpkg"
}

getnamepkgd() { # get name for a pkg that has been packaged into a .itchpkg
    pkgname="$2"

    itchpkgpath="$pkgpath/$pkgname/$pkgname.itchpkg"

    if [ ! -f "$itchpkgpath" ]; then
        echo "Error! Package archive not found!"
        exit
    fi
}

updateshared() {
    # create dir if not already existing | python handles creation of non-existent db
    sudo mkdir -p "$shareddir"

    # root due to location of file made
    printf "%s" "${pkgfiles[@]}" | sudo python "$pythonupdatedir" "$filedbdir" "$pkgname"

    # define the pkg as 'installed'
    echo "store $pkgname I" | sudo gdbmtool "$pkgdbdir" 2>/dev/null
}

case "$1" in
    "-c")
        configure ;;
    "-b")
        build ;;
    "-i")
        if [ -z "$2" ]; then
            install
        else # implies an itchpkg has been given - verification NEEDED!
            getnamepkgd "$@"
            installpkg
        fi ;;
    "-u")
        if [ -z "$2" ]; then
            echo "Error!"
        else
            getnamepkgd "$@"
            uninstall "$@"
        fi ;;
    *)
        echo "Error!"
        ;;
esac
