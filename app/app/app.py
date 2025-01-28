import uuid
from fastapi import FastAPI, Response

from app.models import FeedbackCreatedResponse, FeedbackForm


app = FastAPI()

@app.post('/feedbacks', status_code=201)
def submit_feedback(form: FeedbackForm, response: Response):
    id = uuid.uuid4()

    response.headers['Location'] = f'/feedbacks/{id}'
    return FeedbackCreatedResponse(id=id)
