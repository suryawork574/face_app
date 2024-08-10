Curl command to invoke upload api
curl --location 'http://127.0.0.1:5000/upload' \
--form 'files=@"/Users/srivaishnavi/Downloads/img.jpg"' \
--form 'files=@"/Users/srivaishnavi/Downloads/nandu1.png"' \
--form 'student_id="12347"'

Curl command to invoke compare api
curl --location 'http://127.0.0.1:5000/compare' \
--form 'file=@"/Users/srivaishnavi/Downloads/img2.jpeg"' \
--form 'student_id="12347"'

