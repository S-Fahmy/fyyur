#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import date
import sys

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120),  nullable=False)
    state = db.Column(db.String(120),  nullable=False)
    address = db.Column(db.String(120),  nullable=False)
    phone = db.Column(db.String(120),  nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

    genres = db.Column(db.String)
    website = db.Column(db.String)
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String)

    shows = db.relationship("Show", backref="venue",
                            lazy=True, cascade="all, delete-orphan")
    # Show.venue() should return an artist object


class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website = db.Column(db.String)
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String)
    shows = db.relationship("Show", backref="artist", lazy=True)


# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.


class Show(db.Model):
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime)

    # child for artists tables and venues tables.
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'))
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'))


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.

    # fetch all venues data from db and store in a list of objects
    allVenues = Venue.query.all()

    # group venues in an array of dictionaries grouped by cities
    myData = groupByCity(allVenues)

    # data = [{
    #     "city": "San Francisco",
    #     "state": "CA",
    #     "venues": [{
    #         "id": 1,
    #         "name": "The Musical Hop",
    #         "num_upcoming_shows": 0,
    #     }, {
    #         "id": 3,
    #         "name": "Park Square Live Music & Coffee",
    #         "num_upcoming_shows": 1,
    #     }]
    # }, {
    #     "city": "New York",
    #     "state": "NY",
    #     "venues": [{
    #         "id": 2,
    #         "name": "The Dueling Pianos Bar",
    #         "num_upcoming_shows": 0,
    #     }]
    # }]
    return render_template('pages/venues.html', areas=myData)


@ app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    foundVenues = db.session.query(Venue.id, Venue.name).filter(
        Venue.name.ilike('%' + request.form['search_term']+'%')).all()
    data = []

    # need to go in a loop to fill the num upcomingshows values as requested.
    for venue in foundVenues:
        data.append({
            "id": venue[0],
            "name": venue[1],
            "num_upcoming_shows": countNumberOfUpcomingShows(id=venue[0], modelType='venue')
        })

    response = {
        "count": len(foundVenues),
        "data": data
    }
    # response = {
    #     "count": 1,
    #     "data": [{
    #         "id": 2,
    #         "name": "The Dueling Pianos Bar",
    #         "num_upcoming_shows": 0,
    #     }]
    # }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@ app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    myData = {}

    venueShowsAndArtists = db.session.query(Venue, Artist.id, Artist.name, Artist.image_link, Show.start_time).outerjoin(
        Venue.shows).outerjoin(Show.artist).filter(Venue.id == venue_id).all()

    if len(venueShowsAndArtists) > 0:

        venueData = venueShowsAndArtists[0][0]
        currentTime = datetime.now()
        upcoming_shows = []
        past_shows = []

        # if the venue will have or had any shows fill the 2 arrays
        if venueShowsAndArtists[0][4] != None:

            for venueShows in venueShowsAndArtists:
                if venueShows.start_time > currentTime:

                    upcoming_shows.append({
                        "artist_id": venueShows[1],
                        "artist_name": venueShows[2],
                        "artist_image_link": venueShows[3],
                        "start_time": venueShows[4].strftime("%Y-%m-%d %H:%M:%S")
                    })

                elif venueShows.start_time < currentTime:
                    past_shows.append({
                        "artist_id": venueShows[1],
                        "artist_name": venueShows[2],
                        "artist_image_link": venueShows[3],
                        "start_time": venueShows[4].strftime("%Y-%m-%d %H:%M:%S")
                    })

        myData = {
            "id": venueData.id,
            "name": venueData.name,
            "genres": ListFromString(venueData.genres),
            "address": venueData.address,
            "city": venueData.city,
            "state": venueData.state,
            "phone": venueData.phone,
            "website": venueData.website,
            "facebook_link": venueData.facebook_link,
            "seeking_talent": venueData.seeking_talent,
            "seeking_description": venueData.seeking_description,
            "image_link": venueData.image_link,
            "past_shows": past_shows,
            "upcoming_shows": upcoming_shows,
            "past_shows_count": len(past_shows),
            "upcoming_shows_count": len(upcoming_shows),

        }

    # data1 = {
    #     "id": 1,
    #     "name": "The Musical Hop",
    #     "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    #     "address": "1015 Folsom Street",
    #     "city": "San Francisco",
    #     "state": "CA",
    #     "phone": "123-123-1234",
    #     "website": "https://www.themusicalhop.com",
    #     "facebook_link": "https://www.facebook.com/TheMusicalHop",
    #     "seeking_talent": True,
    #     "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    #     "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
    #     "past_shows": [{
    #         "artist_id": 4,
    #         "artist_name": "Guns N Petals",
    #         "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    #         "start_time": "2019-05-21T21:30:00.000Z"
    #     }],
    #     "upcoming_shows": [],
    #     "past_shows_count": 1,
    #     "upcoming_shows_count": 0,
    # }
    # data2 = {
    #     "id": 2,
    #     "name": "The Dueling Pianos Bar",
    #     "genres": ["Classical", "R&B", "Hip-Hop"],
    #     "address": "335 Delancey Street",
    #     "city": "New York",
    #     "state": "NY",
    #     "phone": "914-003-1132",
    #     "website": "https://www.theduelingpianos.com",
    #     "facebook_link": "https://www.facebook.com/theduelingpianos",
    #     "seeking_talent": False,
    #     "image_link": "https://images.unsplash.com/photo-1497032205916-ac775f0649ae?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=750&q=80",
    #     "past_shows": [],
    #     "upcoming_shows": [],
    #     "past_shows_count": 0,
    #     "upcoming_shows_count": 0,
    # }
    # data3 = {
    #     "id": 3,
    #     "name": "Park Square Live Music & Coffee",
    #     "genres": ["Rock n Roll", "Jazz", "Classical", "Folk"],
    #     "address": "34 Whiskey Moore Ave",
    #     "city": "San Francisco",
    #     "state": "CA",
    #     "phone": "415-000-1234",
    #     "website": "https://www.parksquarelivemusicandcoffee.com",
    #     "facebook_link": "https://www.facebook.com/ParkSquareLiveMusicAndCoffee",
    #     "seeking_talent": False,
    #     "image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
    #     "past_shows": [{
    #         "artist_id": 5,
    #         "artist_name": "Matt Quevedo",
    #         "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    #         "start_time": "2019-06-15T23:00:00.000Z"
    #     }],
    #     "upcoming_shows": [{
    #         "artist_id": 6,
    #         "artist_name": "The Wild Sax Band",
    #         "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    #         "start_time": "2035-04-01T20:00:00.000Z"
    #     }, {
    #         "artist_id": 6,
    #         "artist_name": "The Wild Sax Band",
    #         "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    #         "start_time": "2035-04-08T20:00:00.000Z"
    #     }, {
    #         "artist_id": 6,
    #         "artist_name": "The Wild Sax Band",
    #         "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    #         "start_time": "2035-04-15T20:00:00.000Z"
    #     }],
    #     "past_shows_count": 1,
    #     "upcoming_shows_count": 1,
    # }
    # data = list(filter(lambda d: d['id'] ==
    #                    venue_id, [data1, data2, data3]))[0]

    return render_template('pages/show_venue.html', venue=myData)

#  Create Venue
#  ----------------------------------------------------------------


# @ app.route('/venues/create', methods=['GET'])
# def create_venue_form():
#     form = VenueForm()
#     return render_template('forms/new_venue.html', form=form)

# i combined both get and post requests in one method so i can have form validation access on post request

@ app.route('/venues/create', methods=['GET', 'POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    form = VenueForm()

    if form.validate_on_submit():

        venueData = {}
        try:

            newVenue = Venue(name=request.form['name'], city=request.form['city'], state=request.form['state'], address=request.form['address'], phone=request.form['phone'], genres=','.join(
                request.form.getlist('genres')), facebook_link=request.form['facebook_link'], image_link=request.form['image_link'])

            db.session.add(newVenue)
            db.session.commit()

        # TODO: modify data to be the data object returned from db insertion

            venueData['id'] = newVenue.id
            venueData['name'] = newVenue.name
            venueData['city'] = newVenue.city
            venueData['state'] = newVenue.state
            venueData['address'] = newVenue.address
            venueData['phone'] = newVenue.phone
            venueData['genres'] = ListFromString(newVenue.genres)
            venueData['facebook_link'] = newVenue.facebook_link
            venueData['image_link'] = newVenue.image_link

            # on successful db insert, flash success
            flash('Venue ' + request.form['name'] +
                  ' was successfully listed!')

        except:
            db.session.rollback()
            print(sys.exc_info())

        # TODO: on unsuccessful db insert, flash an error instead.
            flash('Venue ' + request.form['name'] + ' was not listed!')
            abort(500)

        finally:
            db.session.close()

        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        return render_template('pages/show_venue.html', venue=venueData)

    return render_template('forms/new_venue.html', form=form, errorsMessages=form.errors)


@ app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    print("made it here")
    try:

        #this way let the cascading rules apply, which deletes related shows too.
        venue = Venue.query.filter_by(id=venue_id).first()
        db.session.delete(venue)
        db.session.commit()

        flash("Venue deleted!")
    except:
        print("exeption happend")
        db.session.rollback()
        abort(500)
        flash("Venue not deleted!!")

    finally:
        db.session.close()
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    print("WHY ARE U NOT FUCKING RETURNING")
    return jsonify({'success': True})


#  Artists
#  ----------------------------------------------------------------


@ app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    artistsList = Artist.query.all()
    # data = [{
    #     "id": 4,
    #     "name": "Guns N Petals",
    # }, {
    #     "id": 5,
    #     "name": "Matt Quevedo",
    # }, {
    #     "id": 6,
    #     "name": "The Wild Sax Band",
    # }]
    return render_template('pages/artists.html', artists=artistsList)


@ app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".

    foundArtists = db.session.query(Artist.id, Artist.name).filter(
        Artist.name.ilike('%' + request.form['search_term']+'%')).all()
    data = []
    for artist in foundArtists:
        data.append({
            "id": artist[0],
            "name": artist[1],
            "num_upcoming_shows": countNumberOfUpcomingShows(id=artist[0], modelType='artist')
        })

    response = {
        "count": len(foundArtists),
        "data": data
    }

    # response = {
    #     "count": 1,
    #     "data": [{
    #         "id": 4,
    #         "name": "Guns N Petals",
    #         "num_upcoming_shows": 0,
    #     }]
    # }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@ app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue(artist?) page with the given venue_id(artist_id)
    myData = {}
    # TODO: replace with real venue(artist?) data from the venues table, using venue_id
    ArtistShowsAndVenues = db.session.query(Artist, Venue.id, Venue.name, Venue.image_link, Show.start_time).outerjoin(
        Artist.shows).outerjoin(Show.venue).filter(Artist.id == artist_id).all()


    if len(ArtistShowsAndVenues) > 0:


        artistData = ArtistShowsAndVenues[0][0]
        currentTime = datetime.now()
        upcoming_shows = []
        past_shows = []

        # if the venue will have or had any shows fill the 2 arrays otherwise they will be left empty
        if ArtistShowsAndVenues[0][4] != None:

            for artistShows in ArtistShowsAndVenues:
                if artistShows.start_time > currentTime:

                    upcoming_shows.append({
                        "venue_id": artistShows[1],
                        "venue_name": artistShows[2],
                        "venue_image_link": artistShows[3],
                        "start_time": artistShows[4].strftime("%Y-%m-%d %H:%M:%S")
                    })

                elif artistShows.start_time < currentTime:
                    past_shows.append({
                        "venue_id": artistShows[1],
                        "venue_name": artistShows[2],
                        "venue_image_link": artistShows[3],
                        "start_time": artistShows[4].strftime("%Y-%m-%d %H:%M:%S")
                    })

        myData = {
            "id": artistData.id,
            "name": artistData.name,
            "genres": ListFromString(artistData.genres),
            "city": artistData.city,
            "state": artistData.state,
            "phone": artistData.phone,
            "website": artistData.website,
            "facebook_link": artistData.facebook_link,
            "seeking_venue": artistData.seeking_venue,
            "seeking_description": artistData.seeking_description,
            "image_link": artistData.image_link,
            "past_shows": past_shows,
            "upcoming_shows": upcoming_shows,
            "past_shows_count": len(past_shows),
            "upcoming_shows_count": len(upcoming_shows),

        }

    # data1 = {
    #     "id": 4,
    #     "name": "Guns N Petals",
    #     "genres": ["Rock n Roll"],
    #     "city": "San Francisco",
    #     "state": "CA",
    #     "phone": "326-123-5000",
    #     "website": "https://www.gunsnpetalsband.com",
    #     "facebook_link": "https://www.facebook.com/GunsNPetals",
    #     "seeking_venue": True,
    #     "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    #     "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    #     "past_shows": [{
    #         "venue_id": 1,
    #         "venue_name": "The Musical Hop",
    #         "venue_image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
    #         "start_time": "2019-05-21T21:30:00.000Z"
    #     }],
    #     "upcoming_shows": [],
    #     "past_shows_count": 1,
    #     "upcoming_shows_count": 0,
    # }
    # data2 = {
    #     "id": 5,
    #     "name": "Matt Quevedo",
    #     "genres": ["Jazz"],
    #     "city": "New York",
    #     "state": "NY",
    #     "phone": "300-400-5000",
    #     "facebook_link": "https://www.facebook.com/mattquevedo923251523",
    #     "seeking_venue": False,
    #     "image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    #     "past_shows": [],
    #     "upcoming_shows": [],
    #     "past_shows_count": 0,
    #     "upcoming_shows_count": 0,
    # }
    # data3 = {
    #     "id": 6,
    #     "name": "The Wild Sax Band",
    #     "genres": ["Jazz", "Classical"],
    #     "city": "San Francisco",
    #     "state": "CA",
    #     "phone": "432-325-5432",
    #     "seeking_venue": False,
    #     "image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    #     "past_shows": [],
    #     "upcoming_shows": [{
    #         "venue_id": 3,
    #         "venue_name": "Park Square Live Music & Coffee",
    #         "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
    #         "start_time": "2035-04-01T20:00:00.000Z"
    #     }, {
    #         "venue_id": 3,
    #         "venue_name": "Park Square Live Music & Coffee",
    #         "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
    #         "start_time": "2035-04-08T20:00:00.000Z"
    #     }, {
    #         "venue_id": 3,
    #         "venue_name": "Park Square Live Music & Coffee",
    #         "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
    #         "start_time": "2035-04-15T20:00:00.000Z"
    #     }],
    #     "past_shows_count": 0,
    #     "upcoming_shows_count": 3,
    # }
    # data = list(filter(lambda d: d['id'] ==
    #                    artist_id, [data1, data2, data3]))[0]
    return render_template('pages/show_artist.html', artist=myData)

#  Update
#  ----------------------------------------------------------------


@ app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)

    # initialize default values for the select fields on the form
    form = ArtistForm(state=artist.state, genres=ListFromString(artist.genres))
    # artist = {
    #     "id": 4,
    #     "name": "Guns N Petals",
    #     "genres": ["Rock n Roll"],
    #     "city": "San Francisco",
    #     "state": "CA",
    #     "phone": "326-123-5000",
    #     "website": "https://www.gunsnpetalsband.com",
    #     "facebook_link": "https://www.facebook.com/GunsNPetals",
    #     "seeking_venue": True,
    #     "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    #     "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
    # }
    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@ app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    try:
        artist = Artist.query.get(artist_id)
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        artist.genres = ','.join(request.form.getlist('genres'))
        artist.facebook_link = request.form['facebook_link']

        db.session.commit()
        flash('Edited!')
    except:
        db.session.rollback()
        abort(500)
        flash('Editing failed!')

    finally:
        db.session.close

    return redirect(url_for('show_artist', artist_id=artist_id))


@ app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id)
    # initialize default values
    form = VenueForm(state=venue.state, genres=ListFromString(venue.genres))
    # venue = {
    #     "id": 1,
    #     "name": "The Musical Hop",
    #     "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    #     "address": "1015 Folsom Street",
    #     "city": "San Francisco",
    #     "state": "CA",
    #     "phone": "123-123-1234",
    #     "website": "https://www.themusicalhop.com",
    #     "facebook_link": "https://www.facebook.com/TheMusicalHop",
    #     "seeking_talent": True,
    #     "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    #     "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
    # }
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@ app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    try:
        venue = Venue.query.get(venue_id)
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.phone = request.form['phone']
        venue.genres = ','.join(request.form.getlist('genres'))
        venue.facebook_link = request.form['facebook_link']

        db.session.commit()
        flash('Edited!')
    except:
        db.session.rollback()
        abort(500)
        flash('Editing failed!')

    finally:
        db.session.close

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


# @ app.route('/artists/create', methods=['GET'])
# def create_artist_form():
#     form = ArtistForm()
#     return render_template('forms/new_artist.html', form=form)

# i combined both get and post requests in one method so i can have form validation access on post request

@ app.route('/artists/create', methods=['GET', 'POST'])
def create_artist_submission():
    form = ArtistForm()

    # called upon submitting the new artist listing form
    if form.validate_on_submit():
        print("attempting submit")
        artistData = {}
        try:

            newArtist = Artist(name=request.form['name'], city=request.form['city'], state=request.form['state'], phone=request.form['phone'], genres=','.join(
                request.form.getlist('genres')), facebook_link=request.form['facebook_link'], image_link=request.form['image_link'])

            db.session.add(newArtist)
            db.session.commit()

        #   for the response object

            artistData['id'] = newArtist.id
            artistData['name'] = newArtist.name
            artistData['city'] = newArtist.city
            artistData['state'] = newArtist.state
            artistData['phone'] = newArtist.phone
            artistData['genres'] = ListFromString(newArtist.genres)
            artistData['facebook_link'] = newArtist.facebook_link
            artistData['image_link'] = newArtist.image_link

            # on successful db insert, flash success
            flash('Artist ' + request.form['name'] +
                  ' was successfully registered!')

        except:
            db.session.rollback()
            print(sys.exc_info())

        # TODO: on unsuccessful db insert, flash an error instead.
            flash('Venue ' + request.form['name'] + ' was not registered!')
            abort(500)

        finally:
            db.session.close()
        return render_template('pages/show_artist.html', artist=artistData)

    print(form.errors)

    return render_template('forms/new_artist.html', form=form, errorsMessages=form.errors)

#  Shows
#  ----------------------------------------------------------------


@ app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.

    shows = Show.query.all()
    myData = []
    for show in shows:
        myData.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
        })

    # data = [{
    #     "venue_id": 1,
    #     "venue_name": "The Musical Hop",
#     "artist_id": 4,
    #     "artist_name": "Guns N Petals",
    #     "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    #     "start_time": "2019-05-21T21:30:00.000Z"
    # }, {
    #     "venue_id": 3,
    #     "venue_name": "Park Square Live Music & Coffee",
    #     "artist_id": 5,
    #     "artist_name": "Matt Quevedo",
    #     "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    #     "start_time": "2019-06-15T23:00:00.000Z"
    # }, {
    #     "venue_id": 3,
    #     "venue_name": "Park Square Live Music & Coffee",
    #     "artist_id": 6,
    #     "artist_name": "The Wild Sax Band",
    #     "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    #     "start_time": "2035-04-01T20:00:00.000Z"
    # }, {
    #     "venue_id": 3,
    #     "venue_name": "Park Square Live Music & Coffee",
    #     "artist_id": 6,
    #     "artist_name": "The Wild Sax Band",
    #     "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    #     "start_time": "2035-04-08T20:00:00.000Z"
    # }, {
    #     "venue_id": 3,
    #     "venue_name": "Park Square Live Music & Coffee",
    #     "artist_id": 6,
    #     "artist_name": "The Wild Sax Band",
    #     "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    #     "start_time": "2035-04-15T20:00:00.000Z"
    # }]
    return render_template('pages/shows.html', shows=myData)


@ app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@ app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    try:
        newShow = Show(artist_id=request.form['artist_id'],
                       venue_id=request.form['venue_id'], start_time=request.form['start_time'])
        db.session.add(newShow)
        db.session.commit()
        flash('Show successfully listed!')

    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('Show was not registered!')
        abort(500)
    finally:
        db.session.close()

    return render_template('pages/home.html')


@ app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@ app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


def groupByCity(venues):
    # create an empty list of dictionaries for the grouped data
    groupedVenues = []

    # loop through the venues objects and check the state and city values.
    for venue in venues:

        # if list is still fresh
        if len(groupedVenues) == 0:
            groupedVenues.append(buildNewVenueData(venue))
            continue

        stateExist = False
        cityExist = False

        for groupedVenue in groupedVenues:
            # if state and city already exist in the groupedList then add the new venue then break.
            if groupedVenue["state"] == venue.state:
                stateExist = True

                if groupedVenue["city"] == venue.city:
                    cityExist = True
                    groupedVenue["venues"].append({
                        "id": venue.id,
                        "name": venue.name,
                        "num_upcoming_shows": countNumberOfUpcomingShows(id=venue.id, modelType='artist')
                    })

                    break

        # if state or city don't exist in the grouped dic then it gets added a new record
        # this ensures if 2 cities have the same name but from different states they don't count as the same
        if stateExist == False or cityExist == False:
            groupedVenues.append(buildNewVenueData(venue))

    return groupedVenues


def countNumberOfUpcomingShows(id, modelType):

    # count show events that have a date in the future for venue or artist

    currentTime = datetime.now()
    count = 0
    if modelType == 'venue':
        count = Show.query.filter(
            Show.venue_id == id, Show.start_time > currentTime).count()
    else:
        count = Show.query.filter(
            Show.artist_id == id, Show.start_time > currentTime).count()

    return count


def buildNewVenueData(venue):
    return {
        "city": venue.city,
        "state": venue.state,
        "venues": [{
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": countNumberOfUpcomingShows(id=venue.id, modelType='venue')
        }]
    }


def ListFromString(delimitedString):
    generatedList = []

    if delimitedString != None and len(delimitedString) > 0:
        generatedList = delimitedString.split(',')

    return generatedList


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
