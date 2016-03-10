#!/usr/bin/perl
use warnings;
use strict;

my $chfile=$ARGV[0];
open (CH_FILE, $chfile)  or die "Can't open '$chfile':$!";
# $^I=".bak";
while(<CH_FILE>){
#if( s/^LAST_DIR=.*/LAST_DIR=0/){
	if( m/([^>]*?)-[\d,\.]+.*\.rpm/){
		print $1."\n";
	}
}
