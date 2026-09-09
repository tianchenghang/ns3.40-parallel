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

function g = loss_OH_suburban(d, hb, hm, f)

  %%
  %% function g = loss_OH_suburban(d, hb, hm, f)
  %%
  %% returns the loss at d meters for f frequency and mobile height m and
  %% base station height of hb

  assert(isscalar(f));
  assert(f > 0);

  Ch = 0.8 + (1.1*log10(f)-0.7)*hm -(1.56*log10(f));

  g = zeros(size(d));
  g(find(d > 0)) = 69.55 + (26.16*log10(f)) - (13.82*log10(hb)) + (44.9-(6.55*log10(hb))).*log10(d) - Ch - 2*(log10(f/28))^2 -5.4;

  g(find(d <= 0)) = 1;

