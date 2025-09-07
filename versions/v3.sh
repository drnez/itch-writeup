#!/bin/bash

# refer to v2.sh
# changes are listed in v3-updatepython.py
# note python script location upon installation must be specified!

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

    sudo mkdir -p "$pkgpath"

    sudo tar czf "$itchpkgpath" -C "$temp_dir$install_prefix" .

    installpkg
}

installpkg() { # existing tarball in pkgpath
    cd "$install_prefix"

    pkgfiles=()

    # finds existing files that will be overwritten - credit https://github.com/skeeto/dotfiles/blob/master/bin/qpkg (with significant modifications)
    for file in $(tar tzf "$itchpkgpath" | grep -v '/$'); do
        pkgfiles+=( "$file" )
        if [ -e "$file" ]; then
            printf "Overwrites '%s'\n" "${file#./}"
        fi
    done

    read -p "Proceed? (yes/NO): " confirmation

    if [ "$confirmation" = "yes" ] || [ "$confirmation" = "y" ]; then
        updateshared
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

    pkgpath="/var/lib/itch/pkgs/$pkgname"
    itchpkgpath="$pkgpath/$pkgname.itchpkg"
}

getname() {
    pkgname="$2"

    pkgpath="/var/lib/itch/pkgs/$pkgname"
    itchpkgpath="$pkgpath/$pkgname.itchpkg"

    if [ ! -f "$itchpkgpath" ]; then
        echo "Error!"
        exit
    fi
}

updateshared() {
    shareddir="/var/lib/itch/shared"
    dbdir="$shareddir/files.gdbm"
    pythonupdatedir="/home/shayan/prog/school/epq/main/updatedb.py" # UPDATE WITH TRUE INSTALLED LOCATION!

    # create dir if not already existing | python handles creation of non-existent db
    sudo mkdir -p "$shareddir"

    # root due to location of file made
    sudo python "$pythonupdatedir" "$dbdir" "$pkgname" "${pkgfiles[@]}"
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
            getname "$@"
            installpkg
        fi ;;
    "-n")
        findname ;;
    *)
        echo "Error!"
        ;;
esac
