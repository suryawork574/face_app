import os
from deepface import DeepFace
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import numpy as np
import pymongo
from bson import ObjectId, Binary
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max file size

mongo_client = pymongo.MongoClient("mongodb://test:testpassword@localhost:27017/")
db = mongo_client["face_app"]
students_collection = db["student_face_data"]

# Ensure the upload directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def home():
    return 'Hello, Flask!'


@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({'error': 'No files part in the request'}), 400

    files = request.files.getlist('files')  # Access multiple files
    student_id = request.form.get('student_id')

    if not files:
        return jsonify({'error': 'No files selected for uploading'}), 400

    if not student_id:
        return jsonify({'error': 'No student ID provided'}), 400

    embeddings = []
    for file in files:
        if file and file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            embedding = DeepFace.represent(file_path, model_name="VGG-Face")[0]['embedding']
            embeddings.append(Binary(np.array(embedding, dtype=np.float32).tobytes()))

    if embeddings:
        student_data = students_collection.find_one({"student_id": student_id})

        if student_data:
            # Ensure `data` is an array before updating
            students_collection.update_one(
                {"student_id": student_id},
                {"$set": {"data": embeddings}}
            )
        else:
            # Add new record
            new_student = {
                "student_id": student_id,
                "data": embeddings,
                "uploaded_at": datetime.now()
            }
            students_collection.insert_one(new_student)

        return jsonify({'message': 'Files uploaded successfully', 'student_id': student_id}), 200
    else:
        return jsonify({'error': 'No valid files found for uploading'}), 400


@app.route('/compare', methods=['POST'])
def compare_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files.get('file')  # Access single file using 'file'
    student_id = request.form.get('student_id')

    if not file:
        return jsonify({'error': 'No file selected for comparison'}), 400

    if not student_id:
        return jsonify({'error': 'No student ID provided'}), 400

    if file and file.filename:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Get embedding for the uploaded file
        embedding = DeepFace.represent(file_path, model_name="VGG-Face")[0]['embedding']
        embedding = np.array(embedding, dtype=np.float32)  # Ensure it's a NumPy array with the correct dtype

        # Retrieve stored embeddings from MongoDB
        student_data = students_collection.find_one({"student_id": student_id})
        if not student_data:
            return jsonify({'error': 'Student ID not found'}), 404

        stored_embeddings = student_data['data']

        # Compare against all stored embeddings
        threshold = 0.6
        for stored_embedding_blob in stored_embeddings:
            stored_embedding = np.frombuffer(stored_embedding_blob, dtype=np.float32)

            # Cosine similarity calculation
            dot_product = np.dot(stored_embedding, embedding)
            norm_stored = np.linalg.norm(stored_embedding)
            norm_embedding = np.linalg.norm(embedding)
            similarity = dot_product / (norm_stored * norm_embedding)

            if similarity >= threshold:
                print(f'The faces match. Match similarity {similarity}')
                match_result = f'The faces match.'
                return jsonify({'result': match_result}), 200
            else:
                print(f'The faces do not match. Match similarity {similarity}')
        print(f'The faces do not match. No matches found.')
        match_result = f'The faces do not match.'
        return jsonify({'result': match_result}), 400
    else:
        return jsonify({'error': 'File has no filename'}), 400


if __name__ == '__main__':
    app.run(debug=True)
