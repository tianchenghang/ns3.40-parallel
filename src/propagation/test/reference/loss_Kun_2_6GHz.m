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

function g = loss_Kun_2_6GHz (d)

  %%
  %% function g = loss_Kun_2_6GHz (d, c)
  %%
  %% returns the loss at d meters for f frequency and mobile height m and
  %% base station height of hb

  %assert(isscalar(f));
  %assert(f > 0);


  g = zeros(size(d));
  g(find(d > 0)) = 36 + 26.*log10(d);

  g(find(d <= 0)) = 1;

