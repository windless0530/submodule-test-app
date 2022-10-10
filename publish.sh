#!/usr/bin/env bash

################################################
# Copyright 2021 AutraTech. All Rights Reserved.
################################################

set -e

TOP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/." && pwd -P)"
GITHUB_API_DIR=${TOP_DIR}/scripts/github_api
READABILITY_DIR=${TOP_DIR}/scripts/readability
BUILDTOOLS_DIR=${TOP_DIR}/buildtools
GITHUB_UTILS_PATH=${GITHUB_API_DIR}/github_utils.py

source ${TOP_DIR}/scripts/autra.bashrc
ENABLE_BROWSER="${ENABLE_BROWSER:-0}"

SKIP_CODE_FORMAT=0
SKIP_FORMAT_CHECK=0

function show_usage() {
    cat <<EOF
Usage: $0 [options] ... [--skip-build | --clang-format mode] ...

Options and arguments:

--skip-code-format     : Skip code format. We will reformat your code and commit it without this flag.
--skip-format-check    : Skip code style check. We will check the code style and report issues without
                         this flag.
--skip-build           : Skip frontend_update and unittest.
--help                 : show this help message.
EOF
}

function check_workspace_is_clean() {
    if [[ -n $(git status --short) ]]; then
        error "Git workspace is not clean, please commit your change firstly."
        exit 1
    fi
}

function parse_arguments() {
    while [ "$#" -gt 0 ]; do
        case "$1" in
            -h|--help) 
                shift
                show_usage
                exit 0
                ;;
            --skip-code-format)
                shift
                SKIP_CODE_FORMAT=1
                ;;
            --skip-format-check)
                shift
                SKIP_FORMAT_CHECK=1
                ;;
            --)
                shift
                break
                ;;
            *)
                error "Unknown command or option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

function code_format() {
    echo "Code format started."
    bash $READABILITY_DIR/diff_format.sh
    echo "Code format finished."

    if [[ -n $(git status --short) ]]; then
        git add .
        git commit -m "Code format by diff_format.sh"
        echo "Code format change is commited."
    else
        echo "No code format change is detected."
    fi
}

function format_check() {
    echo "Format check started."
    bash $BUILDTOOLS_DIR/autra_lint.sh
    echo "Format check finished."
}

# TODO(xiaopeng): Add a python script to wrap git, replace this publish script.
function main() {
    parse_arguments "$@"
    # check_workspace_is_clean
    if [[ "${SKIP_CODE_FORMAT}" == 0 ]]; then
        code_format
    fi
    if [[ "${SKIP_FORMAT_CHECK}" == 0 ]]; then
        format_check
    fi
    repos_name=$(git remote show origin | grep "Fetch URL" | awk -F'[:.]' '{print $(NF-1)}')
    python3 ${GITHUB_UTILS_PATH} --repos-name=$repos_name \
        --command publish --browser=$ENABLE_BROWSER --mark-ut-success=0 \
        --mark-format-check-success=$((1-SKIP_FORMAT_CHECK))
}

main "$@"
