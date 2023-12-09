#!/usr/bin/perl
#
# One-stop perl script to demonstrate how to interact with Flickr API via OAuth 1.0
# Gerry Mulvenna, 24 Aug 2023
#
# + stores the initial API object as a tmp file, which persists until the non-expiring access token is received.
# + access token is stored as a cookie
use strict;
use Data::Dumper;
use CGI;
use CGI::Carp qw(fatalsToBrowser);
use Flickr::API;
use JSON;

require "./credentials.pl";
# you'll need to create this file: credentials.pl with your specific Flickr API credentials. Here's a template:
#
# #!/usr/bin/perl
# # sensitive info, not included in repository
# package FlickrCredentials;
# use strict;
# 
# our $consumer_key = "<YOUR Flickr API CONSUMER KEY>";
# our $consumer_secret = "<YOUR Flickr API CONSUMER SECRET>";
# our $redirect_uri = "<YOUR Flickr API CALLBACK URL>";
# our $FlickrCredentials::config_file = "<SERVER PATH TO INITIAL CONFIG FILE>"; # e.g. '/tmp/'.$consumer_key.'.st';

1;

my $cgi = CGI->new();
my $title = "Flickr move-by-name";
my $token = $cgi->cookie('Flickr_token');
my $secret = $cgi->cookie('Flickr_secret');
my $api;

if (-f $FlickrCredentials::config_file)
{
	$api = Flickr::API->import_storable_config($FlickrCredentials::config_file);
}
elsif ($token && $secret)
{
	$api = Flickr::API->new({'consumer_key' => $FlickrCredentials::consumer_key,
									'consumer_secret' => $FlickrCredentials::consumer_secret,
									'callback' => $FlickrCredentials::redirect_uri,
									'token'=>$token,
									'token_secret'=>$secret});
}
else
{
	$api = Flickr::API->new({'consumer_key' => $FlickrCredentials::consumer_key,
							'consumer_secret' => $FlickrCredentials::consumer_secret});
}

my $oauth_verifier = $cgi->param('oauth_verifier');
my $operation = $cgi->param('operation');
my $action = $cgi->param('action');
if (defined $operation)
{
	if ($operation eq 'revoke')
	{
		if (-f $FlickrCredentials::config_file)
		{
			unlink $FlickrCredentials::config_file;
		}
		# remove the cookies
		my $token_cookie = $cgi->cookie(-name=>'Flickr_token',-value=>'',-expires=>'-1d');
		my $secret_cookie = $cgi->cookie(-name=>'Flickr_secret',-value=>'',-expires=>'-1d');
		print $cgi->header(-type=>'text/html', -cookie=>[$token_cookie, $secret_cookie]);
		print head($title, "Disconnected - click to continue");
	}
	elsif ($operation eq 'get')
	{
		my $call = $cgi->param('call');
		my $response = $api->execute_method($call);
		print $cgi->header('text/html');
		print head($title, "API response - click to continue");
		print "<pre>\n";
		print Dumper ($response->as_hash());
		print "</pre>";
	}
	elsif ($operation eq 'json')
	{
		if ($action eq 'albums')
		{
			my $page = $cgi->param('page');
			if (not defined $page) {$page = 1;}
			my $response = $api->execute_method('flickr.photosets.getList', {'per_page'=>'500','page'=>$page});
			my @albums;
			my $set;
			my $data = $response->as_hash();
			my $photosets = $data->{'photosets'};
			if (defined $photosets)
			{
				foreach $set (@{ $photosets->{'photoset'} })
				{
					push (@albums, {'id'=>$set->{'id'},'title'=>$set->{'title'},'photos'=>$set->{'photos'}, 'videos'=>$set->{'videos'}});
				}		
				print $cgi->header('application/json');
				my $json = {'total' => $photosets->{'total'},'page' => $photosets->{'page'},'pages' => $photosets->{'pages'},'perpage' => $photosets->{'perpage'},'albums'=>\@albums};
				print encode_json($json);
			}
		}
		elsif ($action eq 'photos')
		{
			my $page = $cgi->param('page');
			my $photoset_id = $cgi->param('photoset_id');
			if (not defined $page) {$page = 1;}
			my $response = $api->execute_method('flickr.auth.oauth.checkToken');
			my $hash_ref = $response->as_hash();
			my $nsid = $hash_ref->{'oauth'}->{'user'}->{'nsid'};
			if (defined $nsid)
			{
				my $response = $api->execute_method('flickr.photosets.getPhotos', {'per_page'=>'500','page'=>$page,'photoset_id'=>$photoset_id,'user_id'=>$nsid});
				my @photos;
				my $photo;
				my $data = $response->as_hash();
				my $photoset = $data->{'photoset'};
				if (defined $photoset)
				{
					foreach $photo (@{ $photoset->{'photo'} })
					{
						push (@photos, {'id'=>$photo->{'id'},'title'=>$photo->{'title'}});
					}		
					print $cgi->header('application/json');
					my $json = {'total' => $photoset->{'total'},'page' => $photoset->{'page'},'pages' => $photoset->{'pages'},'perpage' => $photoset->{'perpage'},'photos'=>\@photos};
					print encode_json($json);
				}
			}
		}
		elsif ($action eq 'move')
		{
			my $photo_id = $cgi->param('photo_id');
			my $source = $cgi->param('source');
			my $destination = $cgi->param('destination');
			if (defined $photo_id && defined $source && defined $destination)
			{
				my $add_rc = $api->execute_method('flickr.photosets.addPhoto', {'photo_id'=>$photo_id,'photoset_id'=>$destination});
				my $remove_rc = $api->execute_method('flickr.photosets.removePhoto', {'photo_id'=>$photo_id,'photoset_id'=>$source});
				my $add_dump = Dumper($add_rc);
				my $remove_dump = Dumper($remove_rc);
				my $json = {'id'=>$photo_id,'source'=>$source,'destination'=>$destination,'add_rc'=>$add_dump, 'remove_rc'=>$remove_dump};
				print $cgi->header('application/json');
				print encode_json($json);
			}
		}
	}
}
elsif ($oauth_verifier)  
{
	my %request_token;
	$request_token{'verifier'} = $oauth_verifier;
	$request_token{'token'} = $cgi->param('oauth_token');

	my $ac_rc = $api->oauth_access_token(\%request_token);
	if ( $ac_rc eq 'ok' ) {
		unlink $FlickrCredentials::config_file;
		my %config = $api->export_config();
		my $token_cookie = $cgi->cookie(-name=>'Flickr_token',-value=>$config{'token'},-expires=>'+6M');
		my $secret_cookie = $cgi->cookie(-name=>'Flickr_secret',-value=>$config{'token_secret'},-expires=>'+6M');
	 
		my $response = $api->execute_method('flickr.auth.oauth.checkToken');
		my $hash_ref = $response->as_hash();
		my $perms = $hash_ref->{'oauth'}->{'perms'};
		my $fullname = $hash_ref->{'oauth'}->{'user'}->{'fullname'};
		my $username = $hash_ref->{'oauth'}->{'user'}->{'username'};
		my $nsid = $hash_ref->{'oauth'}->{'user'}->{'nsid'};
		my $name = ($fullname) ? $fullname : $username;
		print $cgi->header(-type=>'text/html', -cookie=>[$token_cookie, $secret_cookie]);
		print head($title, "Connected - click to continue");
	}
	else
	{
		print $cgi->header('text/html');
		print head($title, "Error - click to continue");
		print "<pre>\n";
		print Dumper ($ac_rc);
		print "</pre>";
	}
}
elsif(defined $api->{'oauth'}->{'callback'})
{
	my $response = $api->execute_method('flickr.auth.oauth.checkToken');
	my $hash_ref = $response->as_hash();
	my $perms = $hash_ref->{'oauth'}->{'perms'};
	my $fullname = $hash_ref->{'oauth'}->{'user'}->{'fullname'};
	my $username = $hash_ref->{'oauth'}->{'user'}->{'username'};
	my $nsid = $hash_ref->{'oauth'}->{'user'}->{'nsid'};
	my $name = ($fullname) ? $fullname : $username;
	print $cgi->header('text/html');
	print head($title, "Home", 1);  #include extra js and css stuff
	print search_form();
#	print move_form();
	my $text = sprintf ("Authenticated for %s access to<br><a href=\"https://www.flickr.com/photos/%s/\">%s's Flickr</a>", $perms, $nsid, $name);
	print footer($text);
}
else
{
	my $rt_rc =  $api->oauth_request_token( { 'callback'=> $FlickrCredentials::redirect_uri} );
	if ( $rt_rc eq 'ok' ) {
	 
		$api->export_storable_config($FlickrCredentials::config_file);
		print $cgi->header('text/html');
		print head($title);
		print connect_button($api, 'write', 'Connect to Flickr');
	}
	else
	{
		print $cgi->header('text/html');
		print head($title, "Error - click to continue");
		print "<pre>\n";
		print Dumper ($rt_rc);
		print "</pre>";
	}
}


# return HTML for <head>  + start of <body> sections, params $title and $js == true for including javascript
sub head 
{
	my ($title, $home, $js) = @_;
	
	$home = (defined $home) ? $home : "Home";
	my $html = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
	<html>
	<head>
	<meta charset="utf-8">
	<meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<title>' . $title . '</title>
	<link rel="stylesheet" href="/css/fonts.css">
	<link rel="stylesheet" href="/css/mini-default.css">
	<link rel="stylesheet" href="/css/style.css">
	<style>
		html { text-align: center;}
		.card {margin: 0 auto; }
		.form-group {width: 100%; display: none;}
		.form-element {width: 85%;}
		:root {--header-back-color: rgb(15,15,15);}
		input[type="button"] {margin: calc(0.5 * var(--universal-margin));}
		label {float: left;	margin: calc(0.2 * var(--universal-margin)); padding: var(--universal-padding) var(--universal-padding);}
	</style>';
	if ($js)
	{
		$html .= '
	<link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.3.1/css/all.css" integrity="sha384-mzrmE5qonljUremFsqc01SB46JvROS7bZs3IO2EmfFsd15uHvIt+Y8vEf7N7fWAU" crossorigin="anonymous">
	<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/1.12.1/jquery.min.js"></script>
	<script src="flickr.js"></script>';
	}
	$html .= '</head><body>
	<header class="sticky">
	<H2>' . $title . '</h2>
	</header>
	<div class="container">
	<div class="card">
	<a id="home" class="button tertiary" href="./">' . $home . '</a>
	<p>move photos between albums on Flickr<br>based on title / filename</p>
	</div>
	';
}

sub connect_button
{
	my ($api, $perms, $prompt) = @_;
	
	my $uri = $api->oauth_authorize_uri({ 'perms' => $perms });
 
	my $html = '<div class="card"><a class="button tertiary" href="' . $uri . '">' . $prompt . '</a></div>';
}	

sub footer
{
	my ($text) = @_;
	my $html = '<div class="footer"><div class="card"><p>' . $text . '</p><a class="button secondary" href="./?operation=revoke">Revoke access</a></div></div></footer>';
}	

sub get_api_button
{
	my ($call, %args) = @_;
	
	my $html = '<a class="button tertiary" href="./?operation=get&call=' . $call . '">'. $call . '</a>';
}

sub simple_button
{
	my ($id, $text) = @_;
	my $html = '<button class="button tertiary" id="' . $id . '">'. $text . '</button>';
}

sub search_form
{
	my $html = '
<div class="card" id="searchform">
	<div id="elem1" class="form-group">			
		<label for="target_album">1.</label>
		<select class="form-element" name="target_album" id="target_album" placeholder="Select album to search"></select>
	</div>
	<div id="elem2" class="form-group">			
		<label for="selectAlbum">2.</label>
		<select class="form-element" name="albumDropdown" id="selectAlbum"></select>
	</div>
	<div id="elem3" class="form-group">			
		<label for="searchtext">3.</label>
		<input class="form-element" type="search" id="searchtext" name="searchtext" size="22" placeholder="search pattern (regular expression)">
	</div>
	<div id="elem4" class="form-group">			
		<label for="search">4.</label>
		<input type="button" id="search" name="search" value="search" class="tertiary form-element">
	</div>
	<div id="elem5" class="form-group">			
		<label for="movePhotos">5.</label>
		<input type="button" id="movePhotos" name="move photos" value="move photos" class="primary form-element">
	</div>
</div>';
}

sub move_form
{
	my $html='<div class="card" id="move"><select name="albumDropdown" id="selectAlbum"></select><input type="submit" id="movePhotos" name="move photos" value="move photos" class="primary"></div>';
}