from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import face_recognition
import io
import os

app = FastAPI()

UPLOAD_FOLDER = 'face_upload'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def encode_faces_in_folder():
    known_faces = []
    image_filenames = []
    
    for filename in os.listdir(UPLOAD_FOLDER):
        image_path = os.path.join(UPLOAD_FOLDER, filename)
        try:
            img = face_recognition.load_image_file(image_path)
            face_encodings = face_recognition.face_encodings(img)
            
            if face_encodings:
                known_faces.append(face_encodings[0])  
                image_filenames.append(filename)
        except Exception as e:
            continue
    
    return known_faces, image_filenames

known_faces, image_filenames = encode_faces_in_folder()

@app.post("/api/v1/face_reco")
async def face_reco(image: UploadFile = File(...)):
    try:
        image_data = await image.read()
        img = face_recognition.load_image_file(io.BytesIO(image_data))

        face_locations = face_recognition.face_locations(img)
        face_encodings = face_recognition.face_encodings(img, face_locations)

        matched_faces = []
        face_confidences = []
        
        for encoding in face_encodings:
            distances = face_recognition.face_distance(known_faces, encoding)

            best_match_index = distances.argmin()
            best_match_distance = distances[best_match_index]

            if best_match_distance < 0.6:  
                matched_faces.append(image_filenames[best_match_index])
                face_confidences.append(1 - best_match_distance)  

        return JSONResponse(
            content={
                "message": "Face recognition successful",
                "num_faces": len(face_locations),
                "face_locations": face_locations,
                "matched_faces": matched_faces,  
                "face_confidences": face_confidences  
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"message": f"Error: {str(e)}"}
        )
