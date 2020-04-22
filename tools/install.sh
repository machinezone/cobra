#!/bin/sh

which python3 || {
    echo "Python3 is missing. cobra cannot be installed"
    exit 1
}

cd
mkdir -p sandbox/cobra || {
    echo "Cannot create a sandbox location where cobra will be installed"
    exit 1
}

echo "Creating a python virtualenv to install cobra without dirtying your system python install"
cd sandbox/cobra
python3 -m venv venv || {
    echo "Cannot create a virtualenv"
    exit 1
}

venv/bin/pip3 install --upgrade pip

venv/bin/pip3 install -U cobras || {
    echo "cobra failed to install. You might be missing a C compiler to install hiredis"
    echo "Install XCode, XCode developer tools, clang or gcc"
    exit 1
}

venv/bin/cobra
echo
venv/bin/cobra --version

cat <<EOF

cobras is now installed in $PWD/venv/bin/cobra

You can create aliases with
alias cobra='$PWD/venv/bin/cobra'
alias bavarde='$PWD/venv/bin/bavarde'

or update your PATH
export PATH=$PWD/venv/bin:\$PATH

Come say hi with:

bavarde client
EOF
