# Thanks CorpNewt for this source code
cd "$(dirname "$0")"
args=( "$@" )
dir="${0%/*}"
script="${0##*/}"
target="${script%.*}.py"
use_py3="TRUE"
just_installing="FALSE"
tempdir=""
compare_to_version () {
    if [ -z "$1" ] || [ -z "$2" ]; then
        return
    fi
    local current_os= comp=
    current_os="$(sw_vers -productVersion)"
    comp="$(vercomp "$current_os" "$2")"
    if [[ "$1" == "3" && ("$comp" == "1" || "$comp" == "0") ]] || [[ "$1" == "4" && ("$comp" == "2" || "$comp" == "0") ]] || [[ "$comp" == "$1" ]]; then
        echo "1"
    else
        echo "0"
    fi
}

set_use_py3_if () {
    if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
        return
    fi
    if [ "$(compare_to_version "$1" "$2")" == "1" ]; then
        use_py3="$3"
    fi
}

get_remote_py_version () {
    local pyurl= py_html= py_vers= py_num="3"
    pyurl="https://www.python.org/downloads/macos/"
    py_html="$(curl -L $pyurl 2>&1)"
    if [ -z "$use_py3" ]; then
        use_py3="TRUE"
    fi
    if [ "$use_py3" == "FALSE" ]; then
        py_num="2"
    fi
    py_vers="$(echo "$py_html" | grep -i "Latest Python $py_num Release" | awk '{print $8}' | cut -d'<' -f1)"
    echo "$py_vers"
}

download_py () {
    local vers="$1" url=
    clear
    echo "  ###                        ###"
    echo " #     Downloading Python     #"
    echo "###                        ###"
    echo
    if [ -z "$vers" ]; then
        echo "Gathering latest version..."
        vers="$(get_remote_py_version)"
    fi
    if [ -z "$vers" ]; then
        print_error
    fi
    echo "Located Version:  $vers"
    echo
    echo "Building download url..."
    url="$(curl -L https://www.python.org/downloads/release/python-${vers//./}/ 2>&1 | grep -iE "python-$vers-macos.*.pkg\"" | awk -F'"' '{ print $2 }')"
    if [ -z "$url" ]; then
        print_error
    fi
    echo " - $url"
    echo
    echo "Downloading..."
    echo
    tempdir="$(mktemp -d 2>/dev/null || mktemp -d -t 'tempdir')"
    curl "$url" -o "$tempdir/python.pkg"
    if [ "$?" != "0" ]; then
        echo
        echo " - Failed to download python installer!"
        echo
        exit $?
    fi
    echo
    echo "Running python install package..."
    echo
    sudo installer -pkg "$tempdir/python.pkg" -target /
    if [ "$?" != "0" ]; then
        echo
        echo " - Failed to install python!"
        echo
        exit $?
    fi
    pkgutil --expand "$tempdir/python.pkg" "$tempdir/python"
    if [ -e "$tempdir/python/Python_Shell_Profile_Updater.pkg/Scripts/postinstall" ]; then
        echo
        echo "Updating PATH..."
        echo
        "$tempdir/python/Python_Shell_Profile_Updater.pkg/Scripts/postinstall"
    fi
    vers_folder="Python $(echo "$vers" | cut -d'.' -f1 -f2)"
    if [ -f "/Applications/$vers_folder/Install Certificates.command" ]; then
        echo
        echo "Updating Certificates..."
        echo
        "/Applications/$vers_folder/Install Certificates.command"
    fi
    echo
    echo "Cleaning up..."
    cleanup
    echo
    if [ "$just_installing" == "TRUE" ]; then
        echo "Done."
    else
        echo "Rechecking py..."
        downloaded="TRUE"
        clear
        main
    fi
}

cleanup () {
    if [ -d "$tempdir" ]; then
        rm -Rf "$tempdir"
    fi
}

print_error() {
    clear
    cleanup
    echo "  ###                      ###"
    echo " #     Python Not Found     #"
    echo "###                      ###"
    echo
    echo "Python is not installed or not found in your PATH var."
    echo
    if [ "$kernel" == "Darwin" ]; then
        echo "Please go to https://www.python.org/downloads/macos/ to"
        echo "download and install the latest version, then try again."
    else
        echo "Please install python through your package manager and"
        echo "try again."
    fi
    echo
    exit 1
}

print_target_missing() {
    clear
    cleanup
    echo "  ###                      ###"
    echo " #     Target Not Found     #"
    echo "###                      ###"
    echo
    echo "Could not locate $target!"
    echo
    exit 1
}

format_version () {
    local vers="$1"
    echo "$(echo "$1" | awk -F. '{ printf("%d%03d%03d%03d\n", $1,$2,$3,$4); }')"
}

vercomp () {
    local ver1="$(format_version "$1")" ver2="$(format_version "$2")"
    if [ $ver1 -gt $ver2 ]; then
        echo "1"
    elif [ $ver1 -lt $ver2 ]; then
        echo "2"
    else
        echo "0"
    fi
}

get_local_python_version() {
    local py_name="$1" max_version= python= python_version= python_path=
    if [ -z "$py_name" ]; then
        py_name="python3"
    fi
    py_list="$(which -a "$py_name" 2>/dev/null)"
    while read python; do
        if [ -z "$python" ]; then
            continue
        fi
        if [ "$check_py3_stub" == "1" ] && [ "$python" == "/usr/bin/python3" ]; then
            xcode-select -p > /dev/null 2>&1
            if [ "$?" != "0" ]; then
                continue
            fi
        fi
        python_version="$(get_python_version $python)"
        if [ -z "$python_version" ]; then
            continue
        fi
        if [ -z "$max_version" ] || [ "$(vercomp "$python_version" "$max_version")" == "1" ]; then
            max_version="$python_version"
            python_path="$python"
        fi
    done <<< "$py_list"
    echo "$python_path"
}

get_python_version() {
    local py_path="$1" py_version=
    py_version="$($py_path -V 2>&1 | grep -i python | cut -d' ' -f2 | grep -E "[A-Za-z\d\.]+")"
    if [ ! -z "$py_version" ]; then
        echo "$py_version"
    fi
}

prompt_and_download() {
    if [ "$downloaded" != "FALSE" ] || [ "$kernel" != "Darwin" ]; then
        print_error
    fi
    clear
    echo "  ###                      ###"
    echo " #     Python Not Found     #"
    echo "###                      ###"
    echo
    target_py="Python 3"
    printed_py="Python 2 or 3"
    if [ "$use_py3" == "FORCE" ]; then
        printed_py="Python 3"
    elif [ "$use_py3" == "FALSE" ]; then
        target_py="Python 2"
        printed_py="Python 2"
    fi
    echo "Could not locate $printed_py!"
    echo
    echo "This script requires $printed_py to run."
    echo
    while true; do
        read -p "Would you like to install the latest $target_py now? (y/n):  " yn
        case $yn in
            [Yy]* ) download_py;break;;
            [Nn]* ) print_error;;
        esac
    done
}

main() {
    local python= version=
    if [ ! -f "$dir/$target" ]; then
        print_target_missing
    fi
    if [ -z "$use_py3" ]; then
        use_py3="TRUE"
    fi
    if [ "$use_py3" != "FALSE" ]; then
        python="$(get_local_python_version python3)"
    fi
    if [ "$use_py3" != "FORCE" ] && [ -z "$python" ]; then
        python="$(get_local_python_version python2)"
        if [ -z "$python" ]; then
            python="$(get_local_python_version python)"
        fi
    fi
    if [ -z "$python" ]; then
        prompt_and_download
        return 1
    fi
    "$python" "$dir/$target" "${args[@]}"
}

kernel="$(uname -s)"
downloaded="FALSE"
check_py3_stub="$(compare_to_version "3" "10.15")"
trap cleanup EXIT
if [ "$1" == "--install-python" ] && [ "$kernel" == "Darwin" ]; then
    just_installing="TRUE"
    download_py
else
    main
fi
