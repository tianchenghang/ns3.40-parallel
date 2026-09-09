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

% Generation of the quantiles of the Bernoulli distribution at 99.9%
% related to phy error model test

n = 1000;
p_vect = [0.35 0.11 0.02 0.3 0.55 0.14];
for i=1:length(p_vect)
  p = p_vect(i)
  cdf = 0.0;
  kmin = 0.0;
  kmax = 0.0;
  lambda = n * p
  for k=1:n
    pk = bincoeff(n,k)* p^k * (1-p)^(n-k);
    cdf = cdf + pk;
    if cdf > 0.0005 & kmin == 0.0
      kmin = lambda - k
    end
    if cdf > 0.9995 & kmax == 0.0
      kmax = k - lambda
    end
  end

end


