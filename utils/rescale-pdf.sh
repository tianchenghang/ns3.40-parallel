#!/usr/bin/env bash
# Copyright 2026 hangtiancheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

TMPDIR=${TMPDIR:-/tmp}

TMPFILE=$(mktemp -t $(basename ${2}).XXXXXX)

ME=$(basename $0)
echo "$ME $(basename ${2}) to ${1}"

echo "
\documentclass{book}
  \usepackage{pdfpages}
  \begin{document}
    \includepdf[width=${1},fitpaper]{${2}}
  \end{document}
" \
	>${TMPFILE}.tex

pdflatex -output-directory ${TMPDIR} ${TMPFILE}.tex >/dev/null 2>/dev/null
cp ${TMPFILE}.pdf ${2}
rm -f ${TMPFILE}{,.{tex,aux,log,pdf}}
