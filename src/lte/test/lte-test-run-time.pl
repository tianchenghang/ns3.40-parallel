#!/usr/bin/perl
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

use strict;
use IO::CaptureOutput qw(capture qxx qxy);
use Statistics::Descriptive;

my $nIterations = 1;

open( FILE, '>lteTimes.csv' );
print FILE "#sTime\tnFloors\tnEnb\tnUe\trTime\trTDev\n";

my @nUe = (1, 5, 10, 15, 20, 25, 30);
my @nEnb = (1, 2, 4, 6, 8, 12, 14, 18, 22);
my @nFloors = (0, 1);
my @simTime = (5, 10);

# Configure and complite first the program to avoid counting compilation time as running time
my $launch = "CXXFLAGS=\"-O3 -w\" ./ns3 configure -d optimized --enable-static --enable-examples --enable-modules=lte";
my $out;
my $err;
capture { system($launch ) } \$out, \$err;
$launch = "./ns3 run \'lena-profiling --simTime=0.1 --nUe=1 --nEnb=1 --nFloors=0\'";
capture { system($launch ) } \$out, \$err;

foreach my $time (@simTime)
{
   foreach my $floor (@nFloors)
   {
      foreach my $enb (@nEnb)
      {
         foreach my $ue (@nUe)
         {
            my $timeStats = Statistics::Descriptive::Full->new();
            for ( my $iteration = 0 ; $iteration < $nIterations ; $iteration++ )
            {
               $launch = "time -f \"real%E\" ./ns3 run \'lena-profiling --simTime=$time --nUe=$ue --nEnb=$enb --nFloors=$floor\'";
               print "$launch\n";
               capture { system($launch ) } \$out, \$err;
               $err =~ /real(.+):(.+)/;
               my $minutes = $1;
               my $seconds = $minutes * 60 + $2;
               $timeStats->add_data($seconds);
            }
            print FILE "$time\t$floor\t$enb\t$ue\t";
            print FILE $timeStats->mean() . "\t"
              . $timeStats->standard_deviation() . "\n";
         }
      }
   }
}
