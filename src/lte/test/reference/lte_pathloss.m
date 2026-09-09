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

%% LTE pathloss model

%% ITU1411, COST231, OH, etc. scripts are in the propagation module
addpath ("../../../propagation/test/reference/");

%% ITU1238 script is in the buildings module
addpath ("../../../buildings/test/reference/");


d = 104.12;
fmhz = 2130;
f = 2130e6;
hb = 30;
hm = 1;
hr = 20;
l = 80;
b = 50;
st_w = 20;
phi = 45;
big = 1; % metropolitan centre
g = loss_ITU1411_LOS (d, hb, hm, f);
printf ("Test #11: the value of ITU1411 in LOS is: %f\n", g);

d = d = 500.84;
g = loss_ITU1411_NLOS_over_rooftop (d, hb, hm, hr, f, l, b, st_w, phi, big);
printf ("Test #10: the value of ITU1411 in NLOS over the roof-top is: %f\n", g);


d = 1.50028; % km
g = loss_COST231_large_cities_urban (d, hb, hm, fmhz);
printf ("Test #11: the value of COST231 for large cities is: %f\n", g);


%%snr = txPsd + g - kT - nf ; % dB




