from flask import request, jsonify
from flask_restful import Resource
from models.review import Review
from models.db import db
from flask_jwt_extended import jwt_required, get_jwt_identity


class Reviews(Resource):
    @jwt_required()
    def post(self):
        data = request.get_json()
        content = data.get("content")
        rating = data.get("rating")
        user_id = data.get("user_id")
        movie_id = data.get("movie_id")
        current_user = get_jwt_identity()
        if not all([content, rating, user_id, movie_id]):
            return (
                jsonify({"message": "All fields are required for review creation"}),
                400,
            )

        new_review = Review(content, rating, current_user, movie_id)
        db.session.add(new_review)
        db.session.commit()
        return jsonify({"message": "Review created successfully"}), 201


class ReviewDetails(Resource):
    def get(self, review_id):
        review = Review.query.get(review_id)
        if not review:
            return jsonify({"message": "Review not found"}), 404

        return jsonify(review.to_dict()), 200
