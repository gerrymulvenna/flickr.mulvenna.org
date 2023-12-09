// globals

const target_album = "auto upload";  //should be lower case
const target_count = 0;
let albums = [];
let albumNames = [];
let albumIDs = [];
let photos = [];

let home_button_text = "";
let search_button_text = "";
let album_loading = false;
let photo_loading = false;
let move_in_progress = false;
let albumPage = 1;
let albumTotal = 0;
let photoPage = 1;
let photoTotal = 0;
const albumsURL = "?operation=json&action=albums";
const photosURL = "?operation=json&action=photos";
const moveURL = "?operation=json&action=move";

function fetchAlbumData(albumPage) {
  return $.ajax({
    url: `${albumsURL}&page=${albumPage}`,
    method: 'GET',
    dataType: 'json',
  });
}

function fetchPhotoData(photoPage) {
	const photoset_id = $("#target_album").val();
	if (photoset_id > 0)
	{
		return $.ajax({
			url: `${photosURL}&page=${photoPage}&photoset_id=${photoset_id}`,
			method: 'GET',
			dataType: 'json',
		});
	}
}

function initiateMove(photo_id, source, destination) {
  return $.ajax({
    url: `${moveURL}&photo_id=${photo_id}&source=${source}&destination=${destination}`,
    method: 'GET',
    dataType: 'json',
  });
}

function handleAlbumData(data) {
	albumTotal += data.albums.length;
	var pc = Math.round(100 * albumTotal / data.total,0);
	$("#home").html("Loading albums: " + pc + "%");
	albums.push(...data.albums);

	// Check if there are more pages to fetch.
	if (albumTotal < data.total) 
	{
		albumPage++;
		fetchAlbumData(albumPage).done(handleAlbumData);
	} 
	else 
	{
	// All data has been fetched.
	$("#home").html(home_button_text);
	albums.sort(function(a, b) {
		if (a.title.toLowerCase() > b.title.toLowerCase())
		{
			return 1;
		}
		if (a.title.toLowerCase() < b.title.toLowerCase())
		{
			return -1;
		}
		return 0;
	});
	for (album of albums)
	{
		albumNames[album['id']] = album['title'];
		albumIDs[String(album['title']).toLowerCase()] = album['id'];
	}
	$("#elem1").show();
	$("#target_album").html(albumDropdown(albums, "Select source album", ""));
	$("#search").prop('disabled', false);
	$("#selectAlbum").html(albumDropdown(albums, "Select destination album", ""));
  }
}

function handlePhotoData(data) {
	photoTotal += data.photos.length;
	var pc = Math.round(100 * photoTotal / data.total,0);
	$("#search").val("Searching " + data.total + " photos: " + pc + "%");
	photos.push(...matchesTitle(data.photos, $("#searchtext").val()));
	$("#movePhotos").val("Move " + photos.length + " photos");

	photoPage++;
	// Check if there are more pages to fetch.
	if (photoPage <= data.pages) 
	{
		fetchPhotoData(photoPage).done(handlePhotoData).fail(errorPhoto);
	} 
	else 
	{
		// All data has been fetched.
		$("#search").val(search_button_text);
		photo_loading = false;
		$("#search").prop('disabled', false);
		$("#movePhotos").prop('disabled', false);
	}
}

function handleMove(data) {
	var id = data.id;
	var photo = photos.shift();
	$("#movePhotos").val(photos.length + " remaining");

	// Check if there are more moves to make.
	if (photos.length > 0) 
	{
		initiateMove(photos[0].id,$("#target_album").val(),$("#selectAlbum").val()).done(handleMove).fail(errorMove);
	} 
	else 
	{
		// All moves have been made
		$("#movePhotos").val("Move complete");
		$("#search").prop('disabled', false);
		$("#movePhotos").prop('disabled', false);
		move_in_progress = false;
	}
}

function errorPhoto(data) {
	console.log(data)
	alert ("Flickr API error code (" + data.status +")");
	$("#search").prop('disabled', false);
	$("#movePhotos").prop('disabled', false);
	photo_loading = false;
}

function errorMove(data) {
	console.log(data)
	alert ("Flickr API error code (" + data.status +")");
	$("#search").prop('disabled', false);
	$("#movePhotos").prop('disabled', false);
	move_in_progress = false;
}


$(window).ready(function () 
{
	home_button_text = $("#home").html();
	search_button_text = $("#search").val();
	$("#search").prop('disabled', true);
	$("#movePhotos").prop('disabled', true);
	if (album_loading == false)
	{
		album_loading = true;
		$("#home").html("Loading albums:  0%");
		fetchAlbumData(albumPage).done(handleAlbumData);
	}
	$("#target_album").on("change", function () {
		var album = getObjects(albums,'id',$("#target_album").val());
		if (album.length > 0)
		{
			target_total = parseInt(album[0].photos) + parseInt(album[0].videos);
			$("#search").val("search " + target_total + " photos");
			search_button_text = $("#search").val();
		}
		$("#elem2").show();
	});
	$("#selectAlbum").on("change", function () {
		$("#elem3").show();
		$("#elem4").show();
	});
	$("#search").on("click", function () {
		if (photo_loading == false)
		{
			var text = $("#searchtext").val();
			if (text.length > 0)
			{
				photoPage = 1;
				photoTotal = 0;
				photos.length=0;
				photo_loading = true;
				$("#search").prop('disabled', true);
				if (target_total > 0)
				{
					$("#search").val("Searching " + target_total + " photos:  0%");
				}
				else
				{
					$("#search").val("Searching photos:  0%");
				}
				$("#elem5").show();
				fetchPhotoData(photoPage).done(handlePhotoData).fail(errorPhoto);
			}
			else
			{
				alert("Search field is empty!");
			}
		}
	});
	$("#movePhotos").on("click", function () {
		if ($("#selectAlbum").val() > 0)
		{
			if ($("#target_album").val() >0 &&  photos.length > 0)
			{
				move_in_progress = true;
				$("#search").prop('disabled', true);
				$("#movePhotos").prop('disabled', true);
				$("#movePhotos").val(photos.length + " remaining");
				initiateMove(photos[0].id,$("#target_album").val(),$("#selectAlbum").val()).done(handleMove).fail(errorMove);
			}
		}
		else
		{
			alert("No destination album selected!");
		}
	});
});

function matchesTitle (arr, text)
{
	var matches = [];
	var pattern = new RegExp(text, 'i');
	
	for (const element of arr)
	{
		if (element.title.search(pattern) > -1)
		{
			matches.push(element);
		}
	}
	return matches;
}

// return option tags for a dropdown of available albums excluding target_album
function albumDropdown (arr, prompt, exclusion)
{
	var items=[];
	for (element of arr)
	{
		if (element.title.toLowerCase() != exclusion)
		{
			var total = parseInt(element.photos) + parseInt(element.videos);
			items.push('<option value="' + element.id + '">' + element.title + ' (' + total + ')</option>');
		}
	}
	return '<option value="0">' + prompt + '</option>' + items.join("<br>\n");
}

// examine an object array (obj) for a key (key) matching a value (val) and return the matching object
function getObjects(obj, key, val) {
    var objects = [];
    for (var i in obj) {
        if (!obj.hasOwnProperty(i)) continue;
        if (typeof obj[i] == 'object') {
            objects = objects.concat(getObjects(obj[i], key, val));
        } else
        //if key matches and value matches or if key matches and value is not passed (eliminating the case where key matches but passed value does not)
        if (i == key && obj[i] == val || i == key && val == '') { //
            objects.push(obj);
        } else if (obj[i] == val && key == '') {
            //only add if the object is not already in the array
            if (objects.lastIndexOf(obj) == -1) {
                objects.push(obj);
            }
        }
    }
    return objects;
}
