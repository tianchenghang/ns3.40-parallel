// Copyright 2026 hangtiancheng
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.


clear all;
close all;

for nrbs = [6 15 25 50 75 100]

%%  earfcn = 500;
%%  fcMHz = 2160;

  earfcn = 19400;
  fcMHz = 1730;

  fc = fcMHz * 1e6;

  rbbw = 180e3;
  bw = rbbw * nrbs;

  fcv = linspace (fc - bw/2 + rbbw/2, fc + bw/2 - rbbw/2, nrbs);
  name = ["fc" num2str(fcMHz, "%d") "nrb" num2str(nrbs, "%d")];
  printf("std::vector<double> %s (%s);\n",  name, num2str (length(fcv)));
  print_C_vector (fcv, name);
  printf("AddTestCase (new LteSpectrumModelTestCase (\"%s\", %d, %d, %s));\n\n", name, earfcn, nrbs, name);


endfor











