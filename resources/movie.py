import requests
from flask import Blueprint, request, jsonify
from models.movie import Movie, db
from models.theatre import Theatre
from models.user import User
from flask_jwt_extended import jwt_required, get_jwt_identity

movie_bp = Blueprint("movie_bp", __name__)

API_URL = "https://api.themoviedb.org/3/discover/movie"
API_KEY = "abbef35f11cad16e5640f14b9057e4d1"
GENRE_URL = "https://api.themoviedb.org/3/genre/movie/list"


@movie_bp.route("/add_movie", methods=["POST"])  # for adding movies manualy
@jwt_required()
def add_movie():
    current_user_id = get_jwt_identity()  # Get the logged-in user's ID
    current_user = User.query.get(current_user_id)  # Get the logged-in user

    if not current_user or not current_user.admin:
        return jsonify({"success": False, "message": "Admin access required"}), 403

    data = request.json
    id = data.get("id")
    name = data.get("name")
    img = data.get("img")
    genre = data.get("genre")
    theatre_id = data.get("theatre_id")

    if not (id and name and img and genre and theatre_id):
        return jsonify({"success": False, "message": "All fields are required"}), 400

    theatre = Theatre.query.get(theatre_id)
    if not theatre:
        return jsonify({"success": False, "message": "Invalid theatre ID"}), 400

    movie = Movie(id=id, name=name, img=img, genre=genre, theatre_id=theatre_id)

    db.session.add(movie)
    db.session.commit()

    return jsonify({"success": True, "message": "Movie added successfully"})


@movie_bp.route("/fetch_movies", methods=["POST"])
def fetch_and_add_movies():
    data = request.json
    page_number = data.get("page_number", 1)  # Default to page 1 if not provided

    # Fetch genres from TMDb API
    genre_response = requests.get(GENRE_URL, params={"api_key": API_KEY})
    if genre_response.status_code != 200:
        return (
            jsonify(
                {"success": False, "message": "Failed to fetch genres from TMDb API"}
            ),
            genre_response.status_code,
        )

    genre_data = genre_response.json().get("genres", [])
    genre_map = {genre["id"]: genre["name"] for genre in genre_data}

    # Fetch movies from TMDb API
    response = requests.get(API_URL, params={"api_key": API_KEY, "page": page_number})
    if response.status_code != 200:
        return (
            jsonify(
                {"success": False, "message": "Failed to fetch data from external API"}
            ),
            response.status_code,
        )

    movies_data = response.json().get("results", [])

    for movie_data in movies_data:
        id = str(movie_data.get("id"))
        name = movie_data.get("title")
        img = f"https://image.tmdb.org/t/p/w500{movie_data.get('poster_path')}"
        genre_ids = movie_data.get("genre_ids", [])
        theatre_id = None

        existing_movie = Movie.query.filter_by(id=id).first()
        if existing_movie:
            continue

        # Map genre IDs to genre names
        genres = [
            genre_map.get(genre_id) for genre_id in genre_ids if genre_map.get(genre_id)
        ]

        # Create a new Movie object and add it to the database
        movie = Movie(
            id=id, name=name, img=img, genre=", ".join(genres), theatre_id=theatre_id
        )
        db.session.add(movie)

    db.session.commit()

    return jsonify(
        {
            "success": True,
            "message": "Movies fetched from TMDb API and added successfully",
        }
    )


@movie_bp.route("/movies", methods=["GET"])
def get_movies():
    movies = Movie.query.all()
    movies_data = [movie.to_dict() for movie in movies]
    return jsonify(movies_data)


@movie_bp.route("/movies_by_theatre/<string:theatre_id>", methods=["GET"])
def get_movies_by_theatre(theatre_id):
    movies = Movie.query.filter_by(theatre_id=theatre_id).all()
    movies_data = [movie.to_dict() for movie in movies]
    return jsonify(movies_data)


@movie_bp.route("/movies/<string:name>", methods=["GET"])
def get_movie_by_name(name):
    movies = Movie.query.filter_by(name=name)
    movies_data = [movie.to_dict() for movie in movies]
    return jsonify(movies_data)


@movie_bp.route("/remove_movie/<string:movie_id>", methods=["DELETE"])
@jwt_required()
def remove_movie(movie_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user.admin:
        return jsonify({"success": False, "message": "Admin access required"}), 403

    movie = Movie.query.get(movie_id)
    if not movie:
        return jsonify({"success": False, "message": "Movie not found"}), 404

    db.session.delete(movie)
    db.session.commit()

    return jsonify({"success": True, "message": "Movie deleted successfully"}), 200


@movie_bp.route("/edit_movie/<string:movie_id>", methods=["PUT"])
@jwt_required()
def edit_movie(movie_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user.admin:
        return jsonify({"success": False, "message": "Admin access required"}), 403

    data = request.json
    movie = Movie.query.get(movie_id)

    if not movie:
        return jsonify({"success": False, "message": "Movie not found"}), 404

    movie.name = data.get("name", movie.name)
    movie.img = data.get("img", movie.img)
    movie.genre = data.get("genre", movie.genre)
    movie.theatre_id = data.get("theatre_id", movie.theatre_id)

    db.session.commit()

    return jsonify({"success": True, "message": "Movie updated successfully"}), 200
