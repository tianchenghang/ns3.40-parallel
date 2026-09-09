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

%% LTE from theory to practice
%% Table 22.7 Reference sensitivity.

f = 2160e6;  % carrier freq Hz, EARFCN = 500 (downlink)
nrbs = 25; % tx bandwidth configuration in number of RBs
bw = nrbs * 180000; % bandwidth in Hz, note that this is smaller than
		    % the nominal Channel Bandwidth, see TS 36.101 fig 5.6-1
kT = -174; % noise PSD in dBm / Hz
n = kT + 10*log10(bw);  % noise power dBm
p = 30;  % tx power dBm
txPsd = p - 10*log10(bw); % power / bandwidth in linear units
nf = 9; % receiver noise figure in dB

d = logspace (0,5,100);
g = 10.*log10 (gain_freespace(d,f)); % propagation gain in dB

snr = p + g - n - nf; % dB
%%snr = txPsd + g - kT - nf ; % dB


semilogx (d, snr, ";friis;");
xlabel ("distance (m)");
ylabel ("SNR (dB)");
title ("LTE link budget");

grid on;
print ("lte_link_budget.png", "-dpng");



