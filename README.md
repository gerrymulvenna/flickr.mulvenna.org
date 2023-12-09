# flickr.mulvenna.org
A simple Flickr app using the Flickr::API Perl module

## PURPOSE

This code creates a Flickr app to move images from one of your Flickr albums to another based on their title or filename.

For the Flickr user, the 5-step process once authenticated is as follows:

1. select the album to search in
2. select the destination album
3. enter a search pattern (simple text or a regular expression)
4. search for items in the first album selected
5. move those items to the destination album

## INSTALLATION

* Deploy this repository to a web server
* Setup an app on your Flickr account at https://www.flickr.com/services/apps/create/
* Copy the _credentials.sample_ file to a _credentials.pl_ file and fill in your API key, secret, callback URL and path to a temporary config file on the server
* Your callback URL will be the web address of where you have deployed the code, e.g. if you deploy it on https://example.com/flickr/ that will be your callback URL. The index.cgi is a one-stop shop
