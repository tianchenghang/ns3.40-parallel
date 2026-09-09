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


earfcn = 500;



for run = 1:2

  for nrbs = [6 25 100]

    bw = nrbs * 180000;

    for txpowdBm = [10 30]

      basename = ["txpowdB" num2str(txpowdBm, "%d") "nrb" num2str(nrbs, "%d") "run" num2str(run, "%d") "earfcn" num2str(earfcn,"%d")];
      svname = [ "spectrumValue_" basename];
      arname = [ "activeRbs_" basename];

      activeRbsMask = round (rand (1,nrbs));
      activeRbs = find (activeRbsMask) - 1;
      txpowW = (10.^(txpowdBm/10))/1000;
      txpsd = txpowW.*activeRbsMask./bw;

      printf("std::vector<int> %s (%d);\n", arname, length(activeRbs));
      print_C_vector (activeRbs, arname);

      printf("SpectrumValue %s (LteSpectrumValueHelper::GetSpectrumModel (%d, %d));\n",
	     svname, earfcn, nrbs);
      print_C_vector (txpsd, svname);

      printf("AddTestCase (new LteTxPsdTestCase (\"%s\", %d, %d, %f, %s, %s));\n\n",
	     basename, earfcn, nrbs, txpowdBm, arname, svname);

    endfor

  endfor

endfor










