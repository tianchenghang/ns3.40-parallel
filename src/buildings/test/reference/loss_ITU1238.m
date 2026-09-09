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

function g = loss_ITU1238 (d, f, n_floors, build_t)

  %%
  %% function g = loss_ITU1411_NLOS_street_canyons(d, c)
  %%
  %% returns the loss at d meters for f frequency and mobile height m and
  %% base station height of hb
  %% build_t = 0:residential; 1:office; 2:commercial

  assert(isscalar(f));
  assert(f > 0);


  lambda = 300000000.0 / f;


  if (build_t ==1)
    N = 28;
    Lf = 4*n_floors;
  elseif (build_t==2)
    N = 30
    Lf = 15+4*(n_floors-1);
  else
    N = 22;
    Lf = 6 + 3*(n_floors-1);
  endif

  g(find(d > 0)) = 20*log10(f) + (N*log10(d)) + Lf - 28;

  g(find(d <= 0)) = 1;
