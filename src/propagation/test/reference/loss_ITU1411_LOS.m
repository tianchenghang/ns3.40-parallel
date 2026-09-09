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

function g = loss_ITU1411_LOS (d, hb, hm, f)

  %%
  %% function g = loss_ITU1411_LOS(d, hb, hm, f)
  %%
  %% returns the loss at d meters for f frequency and mobile height m and
  %% base station height of hb

  assert(isscalar(f));
  assert(f > 0);


  lambda = 299792458 / f;
  Lbp = abs(20*log10(lambda^2/(8*pi*hb*hm)));
  Rbp = (4*hb*hm) / lambda;
  if (d<=Rbp)
    Ll = Lbp + 20.*log10(d./Rbp);
    Lu = Lbp + 20 + 25.*log10(d./Rbp);
  else
    Ll = Lbp + 40.*log10(d./Rbp);
    Lu = Lbp + 20 + 40.*log10(d./Rbp);
  endif

  g = zeros(size(d));
  g(find(d > 0)) = (Ll.+Lu)./2;

  g(find(d <= 0)) = 1;

