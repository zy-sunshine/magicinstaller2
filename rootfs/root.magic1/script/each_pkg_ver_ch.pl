#!/usr/bin/perl
use warnings;
use strict;

my $chfile=$ARGV[0];
open (CH_FILE, $chfile)  or die "Can't open '$chfile':$!";

#从xml中获取旧的包名
my @pkg_name = `perl ch_file.pl $chfile`;

my @rpm_list;			 #最后获取的所有rpm 中的 file 列表

my $root_dir = '/mnt/magic_iso/MagicLinux/packages';		#新rpm包所在目录

# 用于标记过程中的错误
my $error_num = 0;
my @error_strs;

@pkg_name = &get_pkg_change_version(@pkg_name);

my @pkg_new_list = &get_new_pkg_list(@pkg_name);

@rpm_list = &get_new_pkg_file(@pkg_new_list);

@rpm_list = &clean_blank_line(@rpm_list);

#验证过程中是否出现错误

my @change_file_list = &update_xml(@rpm_list);
&print_sz(@change_file_list);


if ($error_num){
	&print_error_sz(@error_strs);
	exit(0);
}


sub update_xml()
{
	my @rpm_list = @_;
	my @change_file_list;
	my $start =0;
	my $end = 1;
	my $pkg_count = 0;
	while (<CH_FILE>){
		chomp;
		if(index($_, '#') == 0){
			push @change_file_list, "$_";
			next;
		}
		if(m/<files>.*?-[\d,\.]+.*\.rpm<\/files>/){
			my $line_tmp = '#'.$_;
			s/([^>]*?)-[\d,\.]+.*\.rpm/$pkg_new_list[$pkg_count]/;
			$line_tmp .= "\n$_";
			push @change_file_list, $line_tmp;
			$pkg_count++;
			next;
		}
		if($start and m/.*<\/install>.*/){
			$end = 1;
			$start = 0;
			push @change_file_list, "$_";
			next;
		}elsif($end and m/.*<install>.*/){
			$start = 1;
			$end = 0;
			push @change_file_list, "$_";
			next;
		}
		if($start ==0 and $end == 1){
			#print;
			push @change_file_list, "$_";
		}else{
			if(index($_, '+') == 0){
				push @change_file_list, "$_";
				next;
			}
			if(index($_, '@') == 0){
				push @change_file_list, "$_";
				next;
			}
			my ($max_len, $new_file) = &match_similar($_, @rpm_list);
			if($max_len != -1){
				#print $new_file;
				push @change_file_list, "#$_\n$new_file";
			}else{
				push @change_file_list, "#$_";
				$error_num = 2;
				push @error_strs, "(EE)$_ 没有相似文件";
			}
		}
	}
	return @change_file_list;
	
	sub match_similar()
	{
		my($old_file, @rpm_list) = @_;
		my $max_p = -1;
		my $max_len = 0;
		my $p = 0;
		while($p < scalar(@rpm_list)){
			my $each_file = substr($rpm_list[$p], 1);
			#print "$each_file\n";
			#print "$old_file\n";
			my $len = &length_similar( $old_file,  $each_file);
			if ($max_len < $len){
				$max_p = $p;
				$max_len = $len;
			}
			$p++;
		}
		my $similar_str = substr($rpm_list[$max_p], 1);
		if( index ($similar_str, '/', $max_len-1) != -1){
			# 路径都没有完全匹配 max_len为匹配是否有效的判断值
			$max_len = -1;
		}
		return ($max_len, $similar_str);
	}
	sub length_similar()
	{
		my($old_file, $rpm_file) = @_;
		chomp($old_file);
		chomp($rpm_file);
		my @old_file_list=split "", $old_file;
		my @rpm_file_list=split "", $rpm_file; 
		my $length = 0;
		my $p = 0;
		while($p < scalar(@old_file_list) and $p < scalar(@rpm_file_list)){
			if($old_file_list[$p]  eq $rpm_file_list[$p]){
				$length ++;
			}else{
				last;
			}
			$p++;
		}
		return $length;
	}
}

sub get_pkg_change_version()
{
	my @pkg_name = @_;
	my @tmp_list;
	for my $pkg (@pkg_name){
		$_ = $pkg;
		if( m/([^>]*?)-[\d,\.]+.*\.rpm/){
			push @tmp_list, $1;
		}
	}
	@pkg_name = @tmp_list;
	return @pkg_name;
}
sub get_new_pkg_file()
{
	my @pkg_name = @_;
	my @rpm_list = ();
	for my $pkg (@pkg_name){
		#print "rpm -qpl $root_dir/$pkg\n";
		if(index($pkg, 'UNFINDPKG') == 0){
			# UNFINDPKG
			next;
		}
		my @tmp_rpm_list = `rpm -qpl $root_dir/$pkg`;
		
		push @rpm_list, @tmp_rpm_list;	
	}
	return @rpm_list;
}

sub get_new_pkg_list(){
	my @tmp_list;
	my @pkg_name = @_;
	my @pkg_new_list = `ls $root_dir`;
	@tmp_list=();
	my $btn = 0;
	for my $pkg (@pkg_name){
		chomp($pkg);
		for my $pkg_new (@pkg_new_list){
			chomp($pkg_new);
			if($pkg_new =~ m/$pkg-[\d,\.]+-[^-]+.*\.rpm/){
				if(not $btn){
					#print $pkg_new."\n";
					push @tmp_list, $pkg_new;
					$btn = 1;
				}else{
					$error_num = 1;
					push @error_strs, "***Duplicate PKG: $pkg <-- $pkg_new***\n";
				}
			}
		}
		if (not $btn){
			push @tmp_list, "UNFINDPKG $pkg";
			$error_num = 1;
			push @error_strs, "***UNFIND PKG: $pkg***\n";
		}else{
			$btn = 0;
		}
	}
	@pkg_name = @tmp_list;
	return @pkg_name;
}
sub clean_blank_line()
{
	my @list;
	foreach(@_){
		chomp;
		if($_ ne ""){
			push @list, $_;
		}
	}
	return @list;
}
sub print_sz()
{
	foreach (@_){
		print "$_\n";
	}
}
sub print_error_sz()
{
	foreach (@_){
		print STDERR "$_\n";
	}
}
#while(<CH_FILE>){
#if( s/^LAST_DIR=.*/LAST_DIR=0/){
#	if( m/(.*?)-[\d,\.].*\.rpm/){
#		print $1."\n";
#	}
#}
