#!/usr/bin/env bash

################################################
# Copyright 2021 AutraTech. All Rights Reserved.
################################################

set -e

CPP_FILE_SUFFIX="c cc cpp cxx c++ C h hh hpp hxx inc"

TOP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
source ${TOP_DIR}/autra.bashrc

# TODO(xiaopeng): Revisit here to decide whether keep cpplint format.
#                 If so, we need to move logic of autra_lint to this file.
function _cpplint_format() {
  pushd "${AUTRA_ROOT_DIR}" >/dev/null 
  local output=$(./buildtools/autra_lint.sh "$@")
  IFS=$'\n'
  for line in $output
  do
    eval $line
  done
  popd >/dev/null
}

# Check other types of BUILD file
function _bazel_family_ext() {
  local __ext="$(file_ext $1)"
  for ext in "bzl" "bazel" "BUILD"; do
    if [ "${ext}" == "${__ext}" ]; then
      return 0
    fi
  done
  return 1
}

function _code_format() {
  pushd "${AUTRA_ROOT_DIR}" >/dev/null 
  # Get all modified files
  # TODO(xiaopeng): Support more cpp file types.
  local base_commit_sha=$(git merge-base HEAD origin/master)
  local modified_file_list=$(git diff ${base_commit_sha} --name-only --diff-filter=ACM \
    | awk '{print $1}')
  IFS=$'\n'
  for modified_file in $modified_file_list
  do
    if [[ ${modified_file} == experimental* ]]; then
      :  # Do nothing
    elif [[ ${modified_file} =~ \.(h|cc|cpp|c)$ ]]; then
      # TODO(xiaopeng): Figure out why we missed clang-format-diff in docker.
      git diff ${base_commit_sha} ${modified_file} | clang-format-diff-10 -p1 -i
    elif [ "$(basename "${modified_file}")" = "BUILD" ] || _bazel_family_ext "${modified_file}"; then
      bash ./scripts/run_in_dk.sh ./scripts/buildifier.sh "${modified_file}"
    fi
  done
  popd >/dev/null
}

function main() {
  _code_format
}

main
